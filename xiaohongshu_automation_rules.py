"""
小红书聚光API自动化投放规则引擎 v1.0
基于2026星云5.0最终版 - 核心决策逻辑
"""

import json
import os
from datetime import datetime, timedelta
from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK


# ==================== 行业初始基准（顶级投手真实数据，非官方） ====================
INDUSTRY_BENCHMARKS = {
    "通用默认": {
        "图文CTR": 2.5, "视频CTR": 4.0, "互动率": 15, "评论权重比": 0.2,
        "平均CPA": 50, "平均eCPM": 30, "平均CPC": 1.2
    },
    "本地生活": {
        "图文CTR": 3.0, "视频CTR": 4.5, "互动率": 18, "评论权重比": 0.25,
        "平均CPA": 40, "平均eCPM": 25, "平均CPC": 1.0
    },
    "电商零售": {
        "图文CTR": 2.8, "视频CTR": 4.2, "互动率": 16, "评论权重比": 0.22,
        "平均CPA": 60, "平均eCPM": 35, "平均CPC": 1.3
    },
    "知识教育": {
        "图文CTR": 2.2, "视频CTR": 3.8, "互动率": 14, "评论权重比": 0.18,
        "平均CPA": 80, "平均eCPM": 40, "平均CPC": 1.5
    },
    "旅游酒旅": {
        "图文CTR": 2.6, "视频CTR": 4.1, "互动率": 17, "评论权重比": 0.23,
        "平均CPA": 70, "平均eCPM": 32, "平均CPC": 1.2
    },
    "美妆护肤": {
        "图文CTR": 3.2, "视频CTR": 4.8, "互动率": 20, "评论权重比": 0.28,
        "平均CPA": 55, "平均eCPM": 28, "平均CPC": 1.1
    },
}


class AutomationRuleEngine:
    """自动化规则引擎"""
    
    def __init__(self, sdk=None, industry="旅游酒旅"):
        self.sdk = sdk or XiaohongshuJuguangSDK()
        self.industry = industry
        self.benchmark = INDUSTRY_BENCHMARKS.get(industry, INDUSTRY_BENCHMARKS["通用默认"])
    
    # ==================== 创意评分系统 ====================
    def calculate_creative_score(self, creative_data, dynamic_benchmark=None):
        """
        计算创意综合评分（0-100分）
        创意得分=流量获取分(40%) + 用户互动分(25%) + 转化效率分(30%) + 生命周期分(5%)
        """
        benchmark = dynamic_benchmark or self.benchmark
        
        # 提取数据
        impression = int(creative_data.get('impression', 0))
        click = int(creative_data.get('click', 0))
        fee = float(creative_data.get('fee', 0))
        like = int(creative_data.get('like', 0))
        collect = int(creative_data.get('collect', 0))
        comment = int(creative_data.get('comment', 0))
        share = int(creative_data.get('share', 0))
        follow = int(creative_data.get('follow', 0))
        leads = int(creative_data.get('leads', 0))
        
        # 计算指标
        ctr = (click / impression * 100) if impression > 0 else 0
        cpc = (fee / click) if click > 0 else 0
        cpa = (fee / leads) if leads > 0 else float('inf')
        engagement_rate = ((like + collect + comment + share) / click * 100) if click > 0 else 0
        comment_weight_ratio = (comment / like) if like > 0 else 0
        
        # 1. 流量获取分（40分）
        dynamic_ctr = benchmark.get('图文CTR', 2.5)
        traffic_score = min(ctr / dynamic_ctr * 40, 40)
        
        # 2. 用户互动分（25分）
        dynamic_engagement = benchmark.get('互动率', 15)
        dynamic_comment_ratio = benchmark.get('评论权重比', 0.2)
        engagement_score = min(
            engagement_rate / dynamic_engagement * 15 + 
            comment_weight_ratio / dynamic_comment_ratio * 10, 
            25
        )
        
        # 3. 转化效率分（30分）
        dynamic_cpa = benchmark.get('平均CPA', 50)
        if cpa != float('inf') and cpa > 0:
            conversion_score = min(dynamic_cpa / cpa * 30, 30)
        else:
            conversion_score = 0
        
        # 4. 生命周期分（5分）
        create_time = creative_data.get('creativity_create_time', '')
        if create_time:
            try:
                create_dt = datetime.strptime(create_time, '%Y-%m-%d %H:%M:%S')
                days = (datetime.now() - create_dt).days
                lifecycle_score = min(days / 30 * 5, 5)
            except:
                lifecycle_score = 0
        else:
            lifecycle_score = 0
        
        # 总分
        total_score = traffic_score + engagement_score + conversion_score + lifecycle_score
        
        return {
            'total_score': round(total_score, 1),
            'traffic_score': round(traffic_score, 1),
            'engagement_score': round(engagement_score, 1),
            'conversion_score': round(conversion_score, 1),
            'lifecycle_score': round(lifecycle_score, 1),
            'level': self._get_creative_level(total_score),
            'metrics': {
                'ctr': round(ctr, 2),
                'engagement_rate': round(engagement_rate, 2),
                'comment_weight_ratio': round(comment_weight_ratio, 2),
                'cpa': round(cpa, 2) if cpa != float('inf') else None,
                'cpc': round(cpc, 2),
            }
        }
    
    def _get_creative_level(self, score):
        """获取创意等级"""
        if score >= 80:
            return 'S级爆款'
        elif score >= 60:
            return 'A级优质'
        elif score >= 40:
            return 'B级普通'
        else:
            return 'C级垃圾'
    
    def get_creative_action(self, score_result):
        """根据创意评分获取自动执行动作"""
        level = score_result['level']
        
        if level == 'S级爆款':
            return {
                'level': 'S级爆款',
                'actions': [
                    '复制该创意到3-5个新计划放量',
                    '将该创意所在计划的预算增加30%',
                    '标记为"标杆素材"',
                    '启动以旧带新：搭配2条新创意在同一单元投放',
                ],
                'priority': '高',
            }
        elif level == 'A级优质':
            return {
                'level': 'A级优质',
                'actions': [
                    '保持当前投放状态',
                    '每周监控数据衰减率',
                    '基于该创意衍生3条新创意进行测试',
                ],
                'priority': '中',
            }
        elif level == 'B级普通':
            return {
                'level': 'B级普通',
                'actions': [
                    '限制该创意日预算不超过总预算的10%',
                    '观察3天，若得分无提升则暂停',
                ],
                'priority': '低',
            }
        else:  # C级垃圾
            return {
                'level': 'C级垃圾',
                'actions': [
                    '立即暂停该创意',
                    '标记为"失败素材"',
                    '记录其特征供后续避坑',
                ],
                'priority': '紧急',
            }
    
    # ==================== 计划健康度评分系统 ====================
    def calculate_campaign_health(self, campaign_data, target_cpa=None, target_roi=None):
        """
        计划健康度评分（0-100分）
        计划得分=消耗完成分(30%) + 成本达标分(40%) + ROI达标分(20%) + 稳定性分(10%)
        """
        # 提取数据
        fee = float(campaign_data.get('fee', 0))
        impression = int(campaign_data.get('impression', 0))
        click = int(campaign_data.get('click', 0))
        leads = int(campaign_data.get('leads', 0))
        roi = float(campaign_data.get('roi', 0))
        
        # 计算指标
        cpa = (fee / leads) if leads > 0 else float('inf')
        
        # 1. 消耗完成分（30分）- 假设目标消耗为日预算的80%
        daily_budget = float(campaign_data.get('daily_budget', 0))
        if daily_budget > 0:
            consume_ratio = fee / daily_budget
            consume_score = min(consume_ratio * 30, 30)
        else:
            consume_score = 15  # 无预算设置给中间分
        
        # 2. 成本达标分（40分）
        if target_cpa and cpa != float('inf'):
            if cpa <= target_cpa:
                cost_score = 40
            elif cpa <= target_cpa * 1.2:
                cost_score = 30
            elif cpa <= target_cpa * 1.5:
                cost_score = 20
            else:
                cost_score = 10
        else:
            cost_score = 20  # 无目标给中间分
        
        # 3. ROI达标分（20分）
        if target_roi and roi > 0:
            if roi >= target_roi:
                roi_score = 20
            elif roi >= target_roi * 0.8:
                roi_score = 15
            elif roi >= target_roi * 0.6:
                roi_score = 10
            else:
                roi_score = 5
        else:
            roi_score = 10  # 无目标给中间分
        
        # 4. 稳定性分（10分）- 简化版
        stability_score = 10  # 默认稳定
        
        # 总分
        total_score = consume_score + cost_score + roi_score + stability_score
        
        return {
            'total_score': round(total_score, 1),
            'consume_score': round(consume_score, 1),
            'cost_score': round(cost_score, 1),
            'roi_score': round(roi_score, 1),
            'stability_score': round(stability_score, 1),
            'level': self._get_campaign_level(total_score),
            'metrics': {
                'fee': fee,
                'cpa': round(cpa, 2) if cpa != float('inf') else None,
                'roi': roi,
                'consume_ratio': round(fee / daily_budget * 100, 1) if daily_budget > 0 else None,
            }
        }
    
    def _get_campaign_level(self, score):
        """获取计划等级"""
        if score >= 80:
            return '优秀'
        elif score >= 60:
            return '良好'
        elif score >= 40:
            return '预警'
        else:
            return '失败'
    
    def get_campaign_action(self, health_result):
        """根据计划健康度获取自动执行动作"""
        level = health_result['level']
        
        if level == '优秀':
            return {
                'level': '优秀',
                'actions': [
                    '增加日预算20%-30%',
                    '延长投放周期',
                    '复制到新账户/新单元进行扩量',
                ],
                'priority': '高',
            }
        elif level == '良好':
            return {
                'level': '良好',
                'actions': [
                    '保持当前预算',
                    '暂停计划内得分最低的创意',
                    '微调定向和出价（幅度≤10%）',
                ],
                'priority': '中',
            }
        elif level == '预警':
            return {
                'level': '预警',
                'actions': [
                    '减少日预算30%-50%',
                    '暂停计划内所有B级及以下创意',
                    '启动异常诊断流程',
                ],
                'priority': '高',
            }
        else:  # 失败
            return {
                'level': '失败',
                'actions': [
                    '立即暂停该计划',
                    '生成失败原因分析报告',
                    '7天后重新搭建新计划测试',
                ],
                'priority': '紧急',
            }
    
    # ==================== 出价分析系统 ====================
    def analyze_bidding_strategy(self, campaign_data, dynamic_benchmark=None):
        """出价合理性分析"""
        benchmark = dynamic_benchmark or self.benchmark
        
        # 提取数据
        fee = float(campaign_data.get('fee', 0))
        impression = int(campaign_data.get('impression', 0))
        click = int(campaign_data.get('click', 0))
        leads = int(campaign_data.get('leads', 0))
        
        # 计算指标
        ecpm = (fee / impression * 1000) if impression > 0 else 0
        cpc = (fee / click) if click > 0 else 0
        cpa = (fee / leads) if leads > 0 else float('inf')
        
        # 动态基准
        dynamic_ecpm = benchmark.get('平均eCPM', 30)
        dynamic_cpc = benchmark.get('平均CPC', 1.2)
        
        # 出价竞争力判断
        if ecpm < dynamic_ecpm * 0.8:
            competitiveness = '出价过低'
            suggestion = '提高出价10%-20%'
        elif ecpm > dynamic_ecpm * 1.5:
            competitiveness = '出价过高'
            suggestion = '降低出价5%-10%'
        else:
            competitiveness = '出价合理'
            suggestion = '保持当前出价'
        
        return {
            'competitiveness': competitiveness,
            'suggestion': suggestion,
            'metrics': {
                'ecpm': round(ecpm, 2),
                'cpc': round(cpc, 2),
                'cpa': round(cpa, 2) if cpa != float('inf') else None,
                'dynamic_ecpm': dynamic_ecpm,
                'dynamic_cpc': dynamic_cpc,
            }
        }
    
    # ==================== 时段出价规则 ====================
    def get_hourly_bid_coefficient(self, hour):
        """获取时段出价系数"""
        if 19 <= hour <= 24:
            return 1.4  # 高峰时段
        elif 8 <= hour < 19:
            return 1.0  # 正常时段
        else:
            return 0.7  # 低谷时段
    
    def get_keyword_bid_coefficient(self, keyword_type):
        """获取关键词出价系数"""
        coefficients = {
            '高转化': 1.3,
            '低转化': 0.6,
            '未知': 1.0,
        }
        return coefficients.get(keyword_type, 1.0)
    
    # ==================== 异常检测系统 ====================
    def detect_creative_anomaly(self, creative_data, prev_data=None):
        """创意异常检测"""
        anomalies = []
        
        # 提取数据
        ctr = float(creative_data.get('ctr', '0%').replace('%', ''))
        ecpm = float(creative_data.get('cpm', 0))
        
        # 如果有前一天数据，进行对比
        if prev_data:
            prev_ctr = float(prev_data.get('ctr', '0%').replace('%', ''))
            prev_ecpm = float(prev_data.get('cpm', 0))
            
            # CTR下降预警
            if prev_ctr > 0 and (prev_ctr - ctr) / prev_ctr >= 0.3:
                anomalies.append({
                    'type': 'CTR下降预警',
                    'level': '警告',
                    'detail': f'CTR从{prev_ctr:.1f}%下降到{ctr:.1f}%，降幅{(prev_ctr-ctr)/prev_ctr*100:.0f}%',
                    'action': '立即暂停，更换全新创意重新投放',
                })
            
            # eCPM上涨预警
            if prev_ecpm > 0 and (ecpm - prev_ecpm) / prev_ecpm >= 0.5:
                anomalies.append({
                    'type': 'eCPM上涨预警',
                    'level': '警告',
                    'detail': f'eCPM从{prev_ecpm:.1f}上涨到{ecpm:.1f}，涨幅{(ecpm-prev_ecpm)/prev_ecpm*100:.0f}%',
                    'action': '检查出价是否过高，优化创意质量',
                })
        
        return anomalies
    
    def detect_campaign_anomaly(self, campaign_data, target_cpa=None):
        """计划异常检测"""
        anomalies = []
        
        # 提取数据
        fee = float(campaign_data.get('fee', 0))
        leads = int(campaign_data.get('leads', 0))
        roi = float(campaign_data.get('roi', 0))
        daily_budget = float(campaign_data.get('daily_budget', 0))
        
        cpa = (fee / leads) if leads > 0 else float('inf')
        
        # CPA超标预警
        if target_cpa and cpa != float('inf') and cpa > target_cpa * 1.5:
            anomalies.append({
                'type': 'CPA超标预警',
                'level': '警告',
                'detail': f'CPA {cpa:.1f}元，超过目标{target_cpa:.1f}元的1.5倍',
                'action': '暂停高成本创意，优化定向',
            })
        
        # 消耗超标预警
        if daily_budget > 0 and fee > daily_budget * 1.2:
            anomalies.append({
                'type': '消耗超标预警',
                'level': '警告',
                'detail': f'消耗{fee:.1f}元，超过日预算{daily_budget:.1f}元的120%',
                'action': '检查预算设置，必要时暂停计划',
            })
        
        return anomalies
    
    # ==================== 综合分析报告 ====================
    def generate_analysis_report(self, creatives, campaigns, target_cpa=None, target_roi=None):
        """生成综合分析报告"""
        report = f"📊 自动化规则引擎分析报告\n{'═'*45}\n\n"
        
        # 1. 创意分析
        report += f"🎨 创意分析\n{'─'*40}\n"
        creative_scores = []
        for creative in creatives:
            score = self.calculate_creative_score(creative)
            creative_scores.append((creative, score))
        
        # 按分数排序
        creative_scores.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        # 统计各等级数量
        level_counts = {'S级爆款': 0, 'A级优质': 0, 'B级普通': 0, 'C级垃圾': 0}
        for _, score in creative_scores:
            level_counts[score['level']] += 1
        
        report += f"  S级爆款: {level_counts['S级爆款']}个\n"
        report += f"  A级优质: {level_counts['A级优质']}个\n"
        report += f"  B级普通: {level_counts['B级普通']}个\n"
        report += f"  C级垃圾: {level_counts['C级垃圾']}个\n\n"
        
        # Top3创意
        if creative_scores:
            report += "Top3创意:\n"
            for i, (creative, score) in enumerate(creative_scores[:3], 1):
                name = creative.get('creative_name', creative.get('creativity_name', '未命名'))[:25]
                report += f"  {i}. {name}... ({score['total_score']}分/{score['level']})\n"
        
        # 2. 计划分析
        report += f"\n📈 计划分析\n{'─'*40}\n"
        campaign_scores = []
        for campaign in campaigns:
            health = self.calculate_campaign_health(campaign, target_cpa, target_roi)
            campaign_scores.append((campaign, health))
        
        # 按分数排序
        campaign_scores.sort(key=lambda x: x[1]['total_score'], reverse=True)
        
        # 统计各等级数量
        level_counts = {'优秀': 0, '良好': 0, '预警': 0, '失败': 0}
        for _, health in campaign_scores:
            level_counts[health['level']] += 1
        
        report += f"  优秀: {level_counts['优秀']}个\n"
        report += f"  良好: {level_counts['良好']}个\n"
        report += f"  预警: {level_counts['预警']}个\n"
        report += f"  失败: {level_counts['失败']}个\n"
        
        return report


if __name__ == "__main__":
    engine = AutomationRuleEngine(industry="旅游酒旅")
    
    # 测试创意评分
    test_creative = {
        'impression': 1000,
        'click': 50,
        'fee': 100,
        'like': 20,
        'collect': 10,
        'comment': 5,
        'share': 2,
        'leads': 3,
        'creativity_create_time': '2026-05-20 10:00:00',
    }
    
    score = engine.calculate_creative_score(test_creative)
    print(f"创意评分: {score}")
    
    action = engine.get_creative_action(score)
    print(f"建议操作: {action}")
