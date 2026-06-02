#!/usr/bin/env python3
"""
小红书聚光AI投手 - 创意生成与异常检测模块
核心能力：创意生成、异常检测、智能定向
"""
import sys, os as _sys_os
_scripts_dir = _sys_os.path.dirname(_sys_os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import json
import os
import math
from datetime import datetime, timedelta
from collections import defaultdict


class CreativeAI:
    """创意生成与异常检测"""
    
    def __init__(self, sdk, data_dir=None):
        import os as _os
        if data_dir is None:
            data_dir = (
                _os.environ.get('WORKBUDDY_SKILL_DATA_DIR') or
                _os.path.join(_os.path.expanduser('~'), '.workbuddy', 'skills',
                              'xiaohongshu-juguang-ai', 'creative_data')
            )
        _os.makedirs(data_dir, exist_ok=True)
        self.sdk = sdk
        self.data_dir = data_dir
        self.creative_file = os.path.join(data_dir, "creative_templates.json")
        self.anomaly_file = os.path.join(data_dir, "anomaly_data.json")
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载数据
        self.creative_templates = self._load_json(self.creative_file, {'templates': [], 'history': []})
        self.anomaly_data = self._load_json(self.anomaly_file, {'anomalies': [], 'baselines': {}})
    
    def _load_json(self, path, default):
        """加载JSON文件"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    
    def _save_json(self, path, data):
        """保存JSON文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ==================== 创意生成功能 ====================
    
    def generate_creative(self, industry='酒店', style='痛点型', keywords=None):
        """生成创意
        
        Args:
            industry: 行业
            style: 风格（痛点型/数据型/故事型/对比型/攻略型）
            keywords: 关键词列表
        
        Returns:
            创意内容
        """
        # 获取关键词推荐
        if not keywords:
            keyword_result = self.sdk.keyword_recommend(industry)
            if keyword_result.get('success'):
                keywords = [w.get('keyword', '') for w in keyword_result['data'].get('word_list', [])[:5]]
            else:
                keywords = [industry]
        
        # 获取优质创意参考
        top_creatives = self.sdk.get_top_creatives(days=30, top_n=3, min_fee=1.0, min_ctr=10.0)
        
        # 生成创意
        creatives = []
        
        if style == '痛点型':
            for keyword in keywords[:3]:
                creatives.append({
                    'title': f'还在为{keyword}烦恼？这个方法让你省心又省钱',
                    'content': f'很多人为{keyword}头疼，其实只要掌握这几个技巧，就能轻松解决...',
                    'keywords': [keyword],
                    'style': style,
                    'expected_ctr': '15-20%'
                })
        
        elif style == '数据型':
            for keyword in keywords[:3]:
                creatives.append({
                    'title': f'{keyword}数据大揭秘：90%的人都不知道这个技巧',
                    'content': f'根据最新数据统计，{keyword}领域有90%的人不知道这个技巧...',
                    'keywords': [keyword],
                    'style': style,
                    'expected_ctr': '12-18%'
                })
        
        elif style == '故事型':
            for keyword in keywords[:3]:
                creatives.append({
                    'title': f'我的{keyword}体验：从踩坑到避坑的全过程',
                    'content': f'作为一个{keyword}小白，我踩过很多坑，今天分享我的经验...',
                    'keywords': [keyword],
                    'style': style,
                    'expected_ctr': '10-15%'
                })
        
        elif style == '对比型':
            for keyword in keywords[:3]:
                creatives.append({
                    'title': f'{keyword}哪家好？亲测5家后的真实推荐',
                    'content': f'作为一个{keyword}爱好者，我亲测了5家，今天给大家分享我的真实体验...',
                    'keywords': [keyword],
                    'style': style,
                    'expected_ctr': '12-16%'
                })
        
        elif style == '攻略型':
            for keyword in keywords[:3]:
                creatives.append({
                    'title': f'{keyword}攻略：手把手教你选到心仪的',
                    'content': f'作为一个{keyword}达人，今天给大家分享我的选购攻略...',
                    'keywords': [keyword],
                    'style': style,
                    'expected_ctr': '10-14%'
                })
        
        # 添加优质创意参考
        reference = []
        if top_creatives:
            for c in top_creatives[:3]:
                reference.append({
                    'note_id': c['note_id'],
                    'ctr': c['ctr'],
                    'fee': c['fee']
                })
        
        # 保存到历史
        self.creative_templates['history'].append({
            'industry': industry,
            'style': style,
            'keywords': keywords,
            'creatives': creatives,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self._save_json(self.creative_file, self.creative_templates)
        
        return {
            'success': True,
            'industry': industry,
            'style': style,
            'creatives': creatives,
            'reference': reference,
            'total': len(creatives)
        }
    
    def optimize_creative(self, creative_id):
        """优化创意
        
        Args:
            creative_id: 创意ID
        
        Returns:
            优化建议
        """
        # 获取创意报表
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('creative', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取创意报表失败'}
        
        # 找到对应创意
        data_list = report.get('data', {}).get('data_list', [])
        creative_data = None
        for d in data_list:
            if str(d.get('creative_id')) == str(creative_id):
                creative_data = d
                break
        
        if not creative_data:
            return {'success': False, 'message': f'未找到创意: {creative_id}'}
        
        # 提取数据
        fee = float(creative_data.get('fee', 0))
        impression = int(creative_data.get('impression', 0))
        click = int(creative_data.get('click', 0))
        ctr = (click / impression * 100) if impression > 0 else 0
        cpc = (fee / click) if click > 0 else 0
        
        # 生成优化建议
        suggestions = []
        
        if ctr < 5:
            suggestions.append({
                'type': 'ctr_low',
                'title': 'CTR过低',
                'detail': f'当前CTR仅{ctr:.2f}%，远低于行业基准5%',
                'action': '建议优化创意标题和封面图',
                'priority': 'high'
            })
        
        if cpc > 0.15:
            suggestions.append({
                'type': 'cpc_high',
                'title': 'CPC过高',
                'detail': f'当前CPC{cpc:.2f}元，高于行业基准0.15元',
                'action': '建议降低出价或优化定向',
                'priority': 'high'
            })
        
        if impression < 100:
            suggestions.append({
                'type': 'impression_low',
                'title': '曝光不足',
                'detail': f'当前曝光仅{impression}次',
                'action': '建议提高出价或扩大定向范围',
                'priority': 'medium'
            })
        
        if not suggestions:
            suggestions.append({
                'type': 'good',
                'title': '表现良好',
                'detail': f'CTR {ctr:.2f}%，CPC {cpc:.2f}元，表现优秀',
                'action': '建议保持当前策略',
                'priority': 'low'
            })
        
        return {
            'success': True,
            'creative_id': creative_id,
            'metrics': {
                'fee': round(fee, 2),
                'impression': impression,
                'click': click,
                'ctr': round(ctr, 2),
                'cpc': round(cpc, 2)
            },
            'suggestions': suggestions
        }
    
    # ==================== 异常检测功能 ====================
    
    def detect_anomaly(self, date=None, threshold=2.0):
        """检测异常
        
        Args:
            date: 日期（默认昨天）
            threshold: 异常阈值（标准差倍数）
        
        Returns:
            异常检测结果
        """
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 获取历史数据
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('account', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取历史数据失败'}
        
        data_list = report.get('data', {}).get('data_list', [])
        if len(data_list) < 7:
            return {'success': False, 'message': '历史数据不足，需要至少7天'}
        
        # 计算基准
        fees = [float(d.get('fee', 0)) for d in data_list]
        impressions = [int(d.get('impression', 0)) for d in data_list]
        clicks = [int(d.get('click', 0)) for d in data_list]
        
        avg_fee = sum(fees) / len(fees)
        avg_impression = sum(impressions) / len(impressions)
        avg_click = sum(clicks) / len(clicks)
        
        std_fee = math.sqrt(sum((f - avg_fee) ** 2 for f in fees) / len(fees))
        std_impression = math.sqrt(sum((i - avg_impression) ** 2 for i in impressions) / len(impressions))
        std_click = math.sqrt(sum((c - avg_click) ** 2 for c in clicks) / len(clicks))
        
        # 获取当天数据
        daily_cost = self.sdk.get_daily_cost(date)
        if daily_cost.get('success') is False:
            return {'success': False, 'message': '获取当天数据失败'}
        
        today_fee = daily_cost.get('total_cost', 0)
        today_impression = daily_cost.get('total_impression', 0)
        today_click = daily_cost.get('total_click', 0)
        
        # 检测异常
        anomalies = []
        
        # 消耗异常
        if std_fee > 0:
            fee_z = (today_fee - avg_fee) / std_fee
            if abs(fee_z) > threshold:
                anomalies.append({
                    'type': 'fee',
                    'metric': '消耗',
                    'today': round(today_fee, 2),
                    'avg': round(avg_fee, 2),
                    'std': round(std_fee, 2),
                    'z_score': round(fee_z, 2),
                    'level': 'high' if abs(fee_z) > 3 else 'medium',
                    'message': f'消耗{"突增" if fee_z > 0 else "突降"}：{today_fee:.2f}元，历史均值{avg_fee:.2f}元'
                })
        
        # 曝光异常
        if std_impression > 0:
            impression_z = (today_impression - avg_impression) / std_impression
            if abs(impression_z) > threshold:
                anomalies.append({
                    'type': 'impression',
                    'metric': '曝光',
                    'today': today_impression,
                    'avg': int(avg_impression),
                    'std': int(std_impression),
                    'z_score': round(impression_z, 2),
                    'level': 'high' if abs(impression_z) > 3 else 'medium',
                    'message': f'曝光{"突增" if impression_z > 0 else "突降"}：{today_impression}次，历史均值{int(avg_impression)}次'
                })
        
        # 点击异常
        if std_click > 0:
            click_z = (today_click - avg_click) / std_click
            if abs(click_z) > threshold:
                anomalies.append({
                    'type': 'click',
                    'metric': '点击',
                    'today': today_click,
                    'avg': int(avg_click),
                    'std': int(std_click),
                    'z_score': round(click_z, 2),
                    'level': 'high' if abs(click_z) > 3 else 'medium',
                    'message': f'点击{"突增" if click_z > 0 else "突降"}：{today_click}次，历史均值{int(avg_click)}次'
                })
        
        # CTR异常
        today_ctr = (today_click / today_impression * 100) if today_impression > 0 else 0
        avg_ctr = (avg_click / avg_impression * 100) if avg_impression > 0 else 0
        ctrs = [(c / i * 100) if i > 0 else 0 for c, i in zip(clicks, impressions)]
        std_ctr = math.sqrt(sum((c - avg_ctr) ** 2 for c in ctrs) / len(ctrs))
        
        if std_ctr > 0:
            ctr_z = (today_ctr - avg_ctr) / std_ctr
            if abs(ctr_z) > threshold:
                anomalies.append({
                    'type': 'ctr',
                    'metric': 'CTR',
                    'today': round(today_ctr, 2),
                    'avg': round(avg_ctr, 2),
                    'std': round(std_ctr, 2),
                    'z_score': round(ctr_z, 2),
                    'level': 'high' if abs(ctr_z) > 3 else 'medium',
                    'message': f'CTR{"异常偏高" if ctr_z > 0 else "异常偏低"}：{today_ctr:.2f}%，历史均值{avg_ctr:.2f}%'
                })
        
        # 保存异常数据
        if anomalies:
            self.anomaly_data['anomalies'].append({
                'date': date,
                'anomalies': anomalies,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # 只保留最近100条异常
            if len(self.anomaly_data['anomalies']) > 100:
                self.anomaly_data['anomalies'] = self.anomaly_data['anomalies'][-100:]
            
            self._save_json(self.anomaly_file, self.anomaly_data)
        
        return {
            'success': True,
            'date': date,
            'anomalies': anomalies,
            'total': len(anomalies),
            'baselines': {
                'fee': {'avg': round(avg_fee, 2), 'std': round(std_fee, 2)},
                'impression': {'avg': int(avg_impression), 'std': int(std_impression)},
                'click': {'avg': int(avg_click), 'std': int(std_click)},
                'ctr': {'avg': round(avg_ctr, 2), 'std': round(std_ctr, 2)}
            }
        }
    
    def get_anomaly_history(self, days=7):
        """获取异常历史
        
        Args:
            days: 天数
        
        Returns:
            异常历史
        """
        # 获取历史异常
        anomalies = self.anomaly_data.get('anomalies', [])
        
        # 按日期筛选
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        filtered = [a for a in anomalies if a.get('date', '') >= cutoff_date]
        
        # 统计异常类型
        type_counts = defaultdict(int)
        for a in filtered:
            for anomaly in a.get('anomalies', []):
                type_counts[anomaly.get('type', '')] += 1
        
        return {
            'success': True,
            'days': days,
            'total': len(filtered),
            'type_counts': dict(type_counts),
            'history': filtered
        }
    
    # ==================== 智能定向功能 ====================
    
    def recommend_targeting(self, industry='酒店'):
        """推荐定向
        
        Args:
            industry: 行业
        
        Returns:
            定向推荐
        """
        # 获取人群预估
        crowd = self.sdk.estimate_crowd()
        
        # 获取定向模板
        templates = self.sdk.get_target_template_list()
        
        # 基于行业推荐定向
        recommendations = []
        
        if industry == '酒店':
            recommendations.append({
                'type': 'age',
                'title': '年龄定向',
                'detail': '建议18-45岁，酒店主力消费人群',
                'value': '18-45'
            })
            recommendations.append({
                'type': 'gender',
                'title': '性别定向',
                'detail': '建议不限，男女均有需求',
                'value': '不限'
            })
            recommendations.append({
                'type': 'interest',
                'title': '兴趣定向',
                'detail': '建议旅游、美食、生活方式',
                'value': ['旅游', '美食', '生活方式']
            })
            recommendations.append({
                'type': 'location',
                'title': '地域定向',
                'detail': '建议一二线城市+旅游城市',
                'value': ['北京', '上海', '广州', '深圳', '成都', '杭州', '厦门']
            })
        
        elif industry == '美食':
            recommendations.append({
                'type': 'age',
                'title': '年龄定向',
                'detail': '建议18-35岁，美食爱好者',
                'value': '18-35'
            })
            recommendations.append({
                'type': 'interest',
                'title': '兴趣定向',
                'detail': '建议美食、探店、烹饪',
                'value': ['美食', '探店', '烹饪']
            })
        
        else:
            recommendations.append({
                'type': 'age',
                'title': '年龄定向',
                'detail': '建议18-50岁',
                'value': '18-50'
            })
            recommendations.append({
                'type': 'interest',
                'title': '兴趣定向',
                'detail': f'建议{industry}相关兴趣',
                'value': [industry]
            })
        
        return {
            'success': True,
            'industry': industry,
            'recommendations': recommendations,
            'crowd_estimate': crowd.get('data', {}) if crowd.get('success') else None
        }
    
    def analyze_audience(self, days=30):
        """分析受众
        
        Args:
            days: 分析天数
        
        Returns:
            受众分析结果
        """
        # 获取定向模板
        templates = self.sdk.get_target_template_list()
        if not templates.get('success'):
            return {'success': False, 'message': '获取定向模板失败'}
        
        # 分析定向数据
        template_list = templates.get('data', [])
        
        # 统计定向使用情况
        targeting_stats = defaultdict(int)
        for template in template_list:
            targeting = template.get('targeting', {})
            
            # 统计年龄定向
            if 'age' in targeting:
                targeting_stats['age'] += 1
            
            # 统计性别定向
            if 'gender' in targeting:
                targeting_stats['gender'] += 1
            
            # 统计地域定向
            if 'location' in targeting:
                targeting_stats['location'] += 1
            
            # 统计兴趣定向
            if 'interest' in targeting:
                targeting_stats['interest'] += 1
        
        return {
            'success': True,
            'days': days,
            'total_templates': len(template_list),
            'targeting_stats': dict(targeting_stats),
            'recommendations': [
                '建议使用年龄定向，精准定位目标人群',
                '建议使用兴趣定向，提高投放精准度',
                '建议使用地域定向，聚焦目标市场'
            ]
        }
    
    # ==================== 综合分析功能 ====================
    
    def comprehensive_analysis(self, days=7):
        """综合分析
        
        Args:
            days: 分析天数
        
        Returns:
            综合分析结果
        """
        # 1. 异常检测
        anomaly_result = self.detect_anomaly()
        
        # 2. 创意分析
        creative_report = self.sdk.get_offline_report('creative',
                                                     start_date=(datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                                                     end_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
        
        creative_analysis = {}
        if creative_report.get('success'):
            data_list = creative_report.get('data', {}).get('data_list', [])
            
            # 分析创意表现
            for data in data_list:
                creative_id = str(data.get('creative_id', ''))
                fee = float(data.get('fee', 0))
                impression = int(data.get('impression', 0))
                click = int(data.get('click', 0))
                ctr = (click / impression * 100) if impression > 0 else 0
                cpc = (fee / click) if click > 0 else 0
                
                creative_analysis[creative_id] = {
                    'fee': round(fee, 2),
                    'impression': impression,
                    'click': click,
                    'ctr': round(ctr, 2),
                    'cpc': round(cpc, 2),
                    'level': '优秀' if ctr > 15 and cpc < 0.1 else '良好' if ctr > 10 else '一般' if ctr > 5 else '差'
                }
        
        # 3. 生成建议
        suggestions = []
        
        if anomaly_result.get('success') and anomaly_result.get('anomalies'):
            suggestions.append({
                'type': 'anomaly',
                'title': '发现异常',
                'detail': f'检测到{len(anomaly_result["anomalies"])}个异常',
                'action': '建议检查异常指标',
                'priority': 'high'
            })
        
        # 找出低效创意
        poor_creatives = [c_id for c_id, data in creative_analysis.items() if data['level'] == '差']
        if poor_creatives:
            suggestions.append({
                'type': 'creative',
                'title': '低效创意',
                'detail': f'发现{len(poor_creatives)}个低效创意',
                'action': '建议暂停或优化低效创意',
                'priority': 'medium'
            })
        
        # 找出优质创意
        excellent_creatives = [c_id for c_id, data in creative_analysis.items() if data['level'] == '优秀']
        if excellent_creatives:
            suggestions.append({
                'type': 'creative',
                'title': '优质创意',
                'detail': f'发现{len(excellent_creatives)}个优质创意',
                'action': '建议加推优质创意',
                'priority': 'medium'
            })
        
        return {
            'success': True,
            'days': days,
            'anomaly': anomaly_result,
            'creative_analysis': creative_analysis,
            'suggestions': suggestions,
            'summary': {
                'total_creatives': len(creative_analysis),
                'excellent': len(excellent_creatives),
                'poor': len(poor_creatives),
                'anomalies': len(anomaly_result.get('anomalies', []))
            }
        }


# 测试代码
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
    
    sdk = XiaohongshuJuguangSDK()
    creative_ai = CreativeAI(sdk)
    
    print("=" * 50)
    print("🎨 测试创意生成与异常检测")
    print("=" * 50)
    
    # 1. 测试创意生成
    print("\n1. 创意生成测试")
    print("-" * 30)
    result = creative_ai.generate_creative(industry='酒店', style='痛点型')
    if result.get('success'):
        print(f"✅ 生成{result['total']}个创意")
        for i, c in enumerate(result['creatives'][:2]):
            print(f"   {i+1}. {c['title']}")
    
    # 2. 测试异常检测
    print("\n2. 异常检测测试")
    print("-" * 30)
    anomaly = creative_ai.detect_anomaly()
    if anomaly.get('success'):
        print(f"✅ 检测{anomaly['total']}个异常")
        for a in anomaly['anomalies'][:3]:
            print(f"   - {a['message']}")
    
    # 3. 测试智能定向
    print("\n3. 智能定向测试")
    print("-" * 30)
    targeting = creative_ai.recommend_targeting(industry='酒店')
    if targeting.get('success'):
        print(f"✅ 推荐{len(targeting['recommendations'])}个定向")
        for r in targeting['recommendations'][:3]:
            print(f"   - {r['title']}: {r['detail']}")
    
    # 4. 测试综合分析
    print("\n4. 综合分析测试")
    print("-" * 30)
    analysis = creative_ai.comprehensive_analysis(days=7)
    if analysis.get('success'):
        print(f"✅ 综合分析成功")
        print(f"   创意数量: {analysis['summary']['total_creatives']}")
        print(f"   优质创意: {analysis['summary']['excellent']}")
        print(f"   低效创意: {analysis['summary']['poor']}")
        print(f"   异常数量: {analysis['summary']['anomalies']}")
