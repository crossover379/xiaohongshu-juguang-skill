#!/usr/bin/env python3
"""
小红书聚光AI投手大脑模块
核心能力：智能决策、自动学习、预测分析、创意生成
"""
import sys, os as _sys_os
_scripts_dir = _sys_os.path.dirname(_sys_os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict


class AIBrain:
    """AI投手大脑"""
    
    def __init__(self, sdk, data_dir=None):
        import os as _os
        if data_dir is None:
            data_dir = (
                _os.environ.get('WORKBUDDY_SKILL_DATA_DIR') or
                _os.path.join(_os.path.expanduser('~'), '.workbuddy', 'skills',
                              'xiaohongshu-juguang-ai', 'brain_data')
            )
        _os.makedirs(data_dir, exist_ok=True)
        self.sdk = sdk
        self.data_dir = data_dir
        self.learning_file = os.path.join(data_dir, "learning_data.json")
        self.history_file = os.path.join(data_dir, "decision_history.json")
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载学习数据
        self.learning_data = self._load_learning_data()
        self.decision_history = self._load_decision_history()
    
    def _load_learning_data(self):
        """加载学习数据"""
        if os.path.exists(self.learning_file):
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'campaigns': {},  # 计划历史表现
            'units': {},      # 单元历史表现
            'creatives': {},  # 创意历史表现
            'notes': {},      # 笔记历史表现
            'keywords': {},   # 关键词历史表现
            'patterns': {},   # 发现的规律
            'last_update': None
        }
    
    def _save_learning_data(self):
        """保存学习数据"""
        self.learning_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.learning_file, 'w', encoding='utf-8') as f:
            json.dump(self.learning_data, f, ensure_ascii=False, indent=2)
    
    def _load_decision_history(self):
        """加载决策历史"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'decisions': [], 'outcomes': []}
    
    def _save_decision_history(self):
        """保存决策历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.decision_history, f, ensure_ascii=False, indent=2)
    
    # ==================== 自动学习功能 ====================
    
    def learn_from_data(self, days=30):
        """从历史数据中学习
        
        Args:
            days: 学习天数
        
        Returns:
            学习结果
        """
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 1. 学习计划表现
        campaigns = self.sdk.get_all_campaigns()
        if campaigns.get('success'):
            for campaign in campaigns.get('data', []):
                campaign_id = str(campaign.get('campaign_id'))
                if campaign_id not in self.learning_data['campaigns']:
                    self.learning_data['campaigns'][campaign_id] = {
                        'name': campaign.get('campaign_name', ''),
                        'history': [],
                        'patterns': {}
                    }
        
        # 2. 学习创意表现
        creatives = self.sdk.get_all_creatives()
        if creatives.get('success'):
            for creative in creatives.get('data', []):
                creative_id = str(creative.get('creative_id'))
                note_id = creative.get('note_id', '')
                if creative_id not in self.learning_data['creatives']:
                    self.learning_data['creatives'][creative_id] = {
                        'note_id': note_id,
                        'history': [],
                        'patterns': {}
                    }
        
        # 3. 学习笔记表现
        notes = self.sdk.get_all_notes()
        if notes.get('success'):
            for note in notes.get('data', []):
                note_id = str(note.get('note_id'))
                if note_id not in self.learning_data['notes']:
                    self.learning_data['notes'][note_id] = {
                        'title': note.get('title', ''),
                        'history': [],
                        'patterns': {}
                    }
        
        # 4. 获取报表数据学习
        report = self.sdk.get_offline_report('account', start_date, end_date)
        if report.get('success'):
            data_list = report.get('data', {}).get('data_list', [])
            for data in data_list:
                # 学习账户整体表现
                if 'account_patterns' not in self.learning_data['patterns']:
                    self.learning_data['patterns']['account_patterns'] = []
                
                self.learning_data['patterns']['account_patterns'].append({
                    'date': data.get('stat_datetime', ''),
                    'fee': float(data.get('fee', 0)),
                    'impression': int(data.get('impression', 0)),
                    'click': int(data.get('click', 0)),
                    'ctr': float(data.get('click', 0)) / float(data.get('impression', 1)) * 100 if float(data.get('impression', 0)) > 0 else 0,
                    'cpc': float(data.get('fee', 0)) / float(data.get('click', 1)) if float(data.get('click', 0)) > 0 else 0
                })
        
        # 5. 保存学习数据
        self._save_learning_data()
        
        return {
            'success': True,
            'learned_campaigns': len(self.learning_data['campaigns']),
            'learned_creatives': len(self.learning_data['creatives']),
            'learned_notes': len(self.learning_data['notes']),
            'learned_patterns': len(self.learning_data['patterns'])
        }
    
    def discover_patterns(self):
        """发现投放规律
        
        Returns:
            发现的规律
        """
        patterns = []
        
        # 1. 分析账户数据规律
        account_patterns = self.learning_data['patterns'].get('account_patterns', [])
        if len(account_patterns) >= 7:
            # 计算周均值
            recent_7 = account_patterns[-7:]
            avg_fee = sum(p['fee'] for p in recent_7) / 7
            avg_ctr = sum(p['ctr'] for p in recent_7) / 7
            avg_cpc = sum(p['cpc'] for p in recent_7) / 7
            
            # 发现消耗趋势
            fees = [p['fee'] for p in recent_7]
            if all(fees[i] <= fees[i+1] for i in range(len(fees)-1)):
                patterns.append({
                    'type': 'trend',
                    'pattern': '消耗持续上涨',
                    'detail': f'近7天消耗持续上涨，从{fees[0]:.2f}元涨到{fees[-1]:.2f}元',
                    'suggestion': '关注预算控制，防止超支'
                })
            elif all(fees[i] >= fees[i+1] for i in range(len(fees)-1)):
                patterns.append({
                    'type': 'trend',
                    'pattern': '消耗持续下降',
                    'detail': f'近7天消耗持续下降，从{fees[0]:.2f}元降到{fees[-1]:.2f}元',
                    'suggestion': '检查计划状态，可能需要调整出价或创意'
                })
            
            # 发现CTR规律
            if avg_ctr < 5:
                patterns.append({
                    'type': 'performance',
                    'pattern': 'CTR偏低',
                    'detail': f'近7天平均CTR仅{avg_ctr:.2f}%，低于行业基准5%',
                    'suggestion': '优化创意内容或暂停低效创意'
                })
            
            # 发现CPC规律
            if avg_cpc > 0.15:
                patterns.append({
                    'type': 'performance',
                    'pattern': 'CPC偏高',
                    'detail': f'近7天平均CPC{avg_cpc:.2f}元，高于行业基准0.15元',
                    'suggestion': '降低出价或优化定向'
                })
        
        # 2. 分析创意表现规律
        for creative_id, creative_data in self.learning_data['creatives'].items():
            history = creative_data.get('history', [])
            if len(history) >= 3:
                # 计算创意平均表现
                avg_ctr = sum(h.get('ctr', 0) for h in history[-3:]) / 3
                avg_fee = sum(h.get('fee', 0) for h in history[-3:]) / 3
                
                if avg_ctr > 15 and avg_fee > 30:
                    patterns.append({
                        'type': 'creative',
                        'pattern': '优质创意',
                        'detail': f'创意{creative_id}近3天平均CTR{avg_ctr:.2f}%，消耗{avg_fee:.2f}元',
                        'suggestion': '建议加推此创意'
                    })
                elif avg_ctr < 5 and avg_fee > 10:
                    patterns.append({
                        'type': 'creative',
                        'pattern': '低效创意',
                        'detail': f'创意{creative_id}近3天平均CTR仅{avg_ctr:.2f}%，消耗{avg_fee:.2f}元',
                        'suggestion': '建议暂停此创意'
                    })
        
        # 保存规律
        self.learning_data['patterns']['discovered'] = patterns
        self._save_learning_data()
        
        return {
            'success': True,
            'patterns': patterns,
            'total': len(patterns)
        }
    
    # ==================== 智能决策功能 ====================
    
    def analyze_and_decide(self):
        """分析数据并做出决策
        
        Returns:
            决策建议
        """
        decisions = []
        
        # 1. 获取当前数据
        campaigns = self.sdk.get_all_campaigns()
        if not campaigns.get('success'):
            return {'success': False, 'message': '获取计划失败'}
        
        # 2. 分析每个计划
        for campaign in campaigns.get('data', []):
            campaign_id = campaign.get('campaign_id')
            campaign_name = campaign.get('campaign_name', '')
            explore_status = campaign.get('explore_status', 0)
            
            # 只分析投放中的计划
            if explore_status != 1:
                continue
            
            # 获取计划报表
            report = self.sdk.get_offline_report('campaign',
                                                start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                                                end_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
            
            if not report.get('success'):
                continue
            
            # 找到对应计划数据
            data_list = report.get('data', {}).get('data_list', [])
            campaign_data = None
            for d in data_list:
                if str(d.get('campaign_id')) == str(campaign_id):
                    campaign_data = d
                    break
            
            if not campaign_data:
                continue
            
            fee = float(campaign_data.get('fee', 0))
            impression = int(campaign_data.get('impression', 0))
            click = int(campaign_data.get('click', 0))
            ctr = (click / impression * 100) if impression > 0 else 0
            cpc = (fee / click) if click > 0 else 0
            
            # 决策逻辑
            decision = None
            reason = None
            confidence = 0
            
            # 规则1: CTR过低，建议暂停
            if ctr < 5 and fee > 10:
                decision = 'pause_campaign'
                reason = f'CTR仅{ctr:.2f}%，远低于行业基准5%，消耗{fee:.2f}元但效果差'
                confidence = 85
            
            # 规则2: CPC过高，建议降低出价
            elif cpc > 0.15 and fee > 20:
                decision = 'reduce_bid'
                reason = f'CPC{cpc:.2f}元，高于行业基准0.15元，成本过高'
                confidence = 80
            
            # 规则3: 高效计划，建议加预算
            elif ctr > 15 and fee > 50 and cpc < 0.1:
                decision = 'increase_budget'
                reason = f'CTR{ctr:.2f}%，CPC仅{cpc:.2f}元，表现优秀'
                confidence = 90
            
            # 规则4: 无消耗，建议检查
            elif fee == 0 and explore_status == 1:
                decision = 'check_campaign'
                reason = '计划在投但无消耗，可能有问题'
                confidence = 70
            
            if decision:
                decisions.append({
                    'campaign_id': campaign_id,
                    'campaign_name': campaign_name,
                    'decision': decision,
                    'reason': reason,
                    'confidence': confidence,
                    'data': {
                        'fee': fee,
                        'impression': impression,
                        'click': click,
                        'ctr': round(ctr, 2),
                        'cpc': round(cpc, 2)
                    }
                })
        
        # 3. 记录决策
        for decision in decisions:
            self.decision_history['decisions'].append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'decision': decision['decision'],
                'campaign_id': decision['campaign_id'],
                'reason': decision['reason'],
                'confidence': decision['confidence']
            })
        self._save_decision_history()
        
        return {
            'success': True,
            'decisions': decisions,
            'total': len(decisions)
        }
    
    def get_smart_recommendation(self):
        """获取智能推荐
        
        Returns:
            推荐列表
        """
        recommendations = []
        
        # 1. 获取优质创意推荐
        top_creatives = self.sdk.get_top_creatives(days=7, top_n=5, min_fee=1.0, min_ctr=10.0)
        if top_creatives:
            recommendations.append({
                'type': 'creative_boost',
                'title': '优质创意加推',
                'detail': f'发现{len(top_creatives)}个优质创意，建议加推',
                'items': [{'note_id': c['note_id'], 'ctr': c['ctr'], 'fee': c['fee']} for c in top_creatives[:3]],
                'priority': 'high'
            })
        
        # 2. 获取关键词拓展推荐
        campaigns = self.sdk.get_all_campaigns()
        if campaigns.get('success') and campaigns.get('data'):
            # 找到消耗最高的计划
            sorted_campaigns = sorted(campaigns['data'], 
                                    key=lambda x: float(x.get('fee', 0) or 0), 
                                    reverse=True)
            if sorted_campaigns:
                top_campaign = sorted_campaigns[0]
                campaign_name = top_campaign.get('campaign_name', '')
                
                # 从计划名提取关键词
                keywords_to_expand = []
                for word in ['酒店', '民宿', '旅游', '美食', '景点']:
                    if word in campaign_name:
                        keywords_to_expand.append(word)
                
                if keywords_to_expand:
                    recommendations.append({
                        'type': 'keyword_expand',
                        'title': '关键词拓展',
                        'detail': f'计划"{campaign_name}"消耗最高，建议拓展相关关键词',
                        'items': keywords_to_expand,
                        'priority': 'medium'
                    })
        
        # 3. 预算优化推荐
        recommendations.append({
            'type': 'budget_optimize',
            'title': '预算优化',
            'detail': '建议将预算集中在高效计划上',
            'items': ['暂停低效计划', '增加高效计划预算'],
            'priority': 'medium'
        })
        
        return {
            'success': True,
            'recommendations': recommendations,
            'total': len(recommendations)
        }
    
    # ==================== 预测功能 ====================
    
    def predict_tomorrow_cost(self):
        """预测明天消耗
        
        Returns:
            预测结果
        """
        # 获取近7天数据
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('account', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取历史数据失败'}
        
        data_list = report.get('data', {}).get('data_list', [])
        if len(data_list) < 3:
            return {'success': False, 'message': '历史数据不足'}
        
        # 计算趋势
        fees = [float(d.get('fee', 0)) for d in data_list]
        avg_fee = sum(fees) / len(fees)
        
        # 简单线性预测
        if len(fees) >= 3:
            recent_avg = sum(fees[-3:]) / 3
            trend = (fees[-1] - fees[-3]) / 2
            predicted = recent_avg + trend
        else:
            predicted = avg_fee
        
        # 计算置信区间
        std_dev = (sum((f - avg_fee) ** 2 for f in fees) / len(fees)) ** 0.5
        confidence_low = max(0, predicted - std_dev)
        confidence_high = predicted + std_dev
        
        return {
            'success': True,
            'predicted_cost': round(predicted, 2),
            'confidence_interval': {
                'low': round(confidence_low, 2),
                'high': round(confidence_high, 2)
            },
            'recent_avg': round(avg_fee, 2),
            'trend': '上涨' if predicted > avg_fee else '下降',
            'trend_pct': round((predicted - avg_fee) / avg_fee * 100, 2) if avg_fee > 0 else 0
        }
    
    def predict_budget_runout(self):
        """预测预算耗尽时间
        
        Returns:
            预测结果
        """
        # 获取账户预算
        budget = self.sdk.get_account_budget()
        if not budget.get('success'):
            return {'success': False, 'message': '获取账户预算失败'}
        
        budget_data = budget.get('data', {})
        limit_day_budget = budget_data.get('limit_day_budget', 0)
        day_budget = budget_data.get('campaign_day_budget', 0) / 100  # 转换为元
        
        if limit_day_budget == 0:
            return {
                'success': True,
                'unlimited': True,
                'message': '账户不限预算'
            }
        
        # 获取近7天平均消耗
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('account', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取历史数据失败'}
        
        data_list = report.get('data', {}).get('data_list', [])
        if not data_list:
            return {'success': False, 'message': '无历史数据'}
        
        avg_daily_cost = sum(float(d.get('fee', 0)) for d in data_list) / len(data_list)
        
        if avg_daily_cost <= 0:
            return {
                'success': True,
                'days_remaining': '无限',
                'message': '日均消耗为0'
            }
        
        # 计算剩余天数
        today_cost = self.sdk.get_daily_cost(datetime.now().strftime('%Y-%m-%d'))
        today_fee = today_cost.get('total_cost', 0) if today_cost.get('success') is not False else 0
        remaining_budget = day_budget - today_fee
        
        if remaining_budget <= 0:
            days_remaining = 0
        else:
            days_remaining = remaining_budget / avg_daily_cost
        
        return {
            'success': True,
            'day_budget': day_budget,
            'today_cost': round(today_fee, 2),
            'remaining_budget': round(remaining_budget, 2),
            'avg_daily_cost': round(avg_daily_cost, 2),
            'days_remaining': round(days_remaining, 1),
            'warning': days_remaining < 3
        }
    
    # ==================== 创意生成功能 ====================
    
    def generate_creative_suggestions(self, industry='酒店'):
        """生成创意建议
        
        Args:
            industry: 行业
        
        Returns:
            创意建议
        """
        suggestions = []
        
        # 1. 获取优质创意
        top_creatives = self.sdk.get_top_creatives(days=30, top_n=5, min_fee=1.0, min_ctr=10.0)
        
        # 2. 获取关键词推荐
        keywords = self.sdk.keyword_recommend(industry)
        keyword_list = []
        if keywords.get('success'):
            keyword_list = [w.get('keyword', '') for w in keywords['data'].get('word_list', [])[:5]]
        
        # 3. 生成创意模板
        templates = [
            {
                'type': '痛点型',
                'template': f'还在为{industry}烦恼？这个方法让你省心又省钱',
                'keywords': keyword_list[:3]
            },
            {
                'type': '数据型',
                'template': f'{industry}数据大揭秘：90%的人都不知道这个技巧',
                'keywords': keyword_list[:3]
            },
            {
                'type': '故事型',
                'template': f'我的{industry}体验：从踩坑到避坑的全过程',
                'keywords': keyword_list[:3]
            },
            {
                'type': '对比型',
                'template': f'{industry}哪家好？亲测5家后的真实推荐',
                'keywords': keyword_list[:3]
            },
            {
                'type': '攻略型',
                'template': f'{industry}攻略：手把手教你选到心仪的',
                'keywords': keyword_list[:3]
            }
        ]
        
        # 4. 添加优质创意参考
        if top_creatives:
            suggestions.append({
                'type': 'reference',
                'title': '优质创意参考',
                'detail': '这些创意表现优秀，可以参考',
                'items': [{'note_id': c['note_id'], 'ctr': c['ctr'], 'fee': c['fee']} for c in top_creatives[:3]]
            })
        
        suggestions.append({
            'type': 'templates',
            'title': '创意模板',
            'detail': f'基于{industry}行业生成的创意模板',
            'items': templates
        })
        
        return {
            'success': True,
            'suggestions': suggestions,
            'keywords': keyword_list
        }
    
    # ==================== 决策执行功能 ====================
    
    def execute_decision(self, decision, dry_run=True):
        """执行决策
        
        Args:
            decision: 决策信息
            dry_run: 是否仅模拟运行
        
        Returns:
            执行结果
        """
        action = decision.get('decision')
        campaign_id = decision.get('campaign_id')
        
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'action': action,
                'campaign_id': campaign_id,
                'message': f'模拟执行: {action}'
            }
        
        # 实际执行
        if action == 'pause_campaign':
            result = self.sdk.update_campaign_status([campaign_id], 2)
            return {
                'success': result.get('success', False),
                'action': action,
                'campaign_id': campaign_id,
                'result': result
            }
        
        elif action == 'reduce_bid':
            # 获取单元
            units = self.sdk.get_unit_list(campaign_id=campaign_id)
            if units.get('success') and units.get('data', {}).get('unit_infos'):
                unit = units['data']['unit_infos'][0]
                current_bid = unit.get('event_bid', 0)
                new_bid = int(current_bid * 0.8)
                result = self.sdk.update_unit_bid([{
                    'unit_id': unit.get('unit_id'),
                    'event_bid': new_bid
                }])
                return {
                    'success': result.get('success', False),
                    'action': action,
                    'campaign_id': campaign_id,
                    'old_bid': current_bid,
                    'new_bid': new_bid,
                    'result': result
                }
        
        elif action == 'increase_budget':
            # 获取计划详情
            campaigns = self.sdk.get_all_campaigns()
            for campaign in campaigns.get('data', []):
                if str(campaign.get('campaign_id')) == str(campaign_id):
                    current_budget = campaign.get('campaign_day_budget', 0) / 100
                    new_budget = int(current_budget * 1.5 * 100)  # 增加50%
                    result = self.sdk.update_campaign(
                        campaign_id=campaign_id,
                        limit_day_budget=1,
                        origin_campaign_day_budget=new_budget
                    )
                    return {
                        'success': result.get('success', False),
                        'action': action,
                        'campaign_id': campaign_id,
                        'old_budget': current_budget,
                        'new_budget': new_budget / 100,
                        'result': result
                    }
        
        return {
            'success': False,
            'action': action,
            'campaign_id': campaign_id,
            'message': f'未知动作: {action}'
        }


# 测试代码
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
    
    sdk = XiaohongshuJuguangSDK()
    brain = AIBrain(sdk)
    
    print("=" * 50)
    print("🧠 测试AI投手大脑")
    print("=" * 50)
    
    # 1. 测试自动学习
    print("\n1. 自动学习测试")
    print("-" * 30)
    learn_result = brain.learn_from_data(days=7)
    if learn_result.get('success'):
        print(f"✅ 学习成功")
        print(f"   学习计划: {learn_result['learned_campaigns']}个")
        print(f"   学习创意: {learn_result['learned_creatives']}个")
        print(f"   学习笔记: {learn_result['learned_notes']}个")
    else:
        print(f"❌ 学习失败: {learn_result.get('message', '')}")
    
    # 2. 测试规律发现
    print("\n2. 规律发现测试")
    print("-" * 30)
    patterns = brain.discover_patterns()
    if patterns.get('success'):
        print(f"✅ 发现{patterns['total']}个规律")
        for p in patterns['patterns'][:3]:
            print(f"   - {p['pattern']}: {p['detail']}")
    else:
        print(f"❌ 规律发现失败: {patterns.get('message', '')}")
    
    # 3. 测试智能决策
    print("\n3. 智能决策测试")
    print("-" * 30)
    decisions = brain.analyze_and_decide()
    if decisions.get('success'):
        print(f"✅ 生成{decisions['total']}个决策")
        for d in decisions['decisions'][:3]:
            print(f"   - {d['campaign_name']}: {d['decision']} ({d['reason']})")
    else:
        print(f"❌ 决策生成失败: {decisions.get('message', '')}")
    
    # 4. 测试预测功能
    print("\n4. 预测功能测试")
    print("-" * 30)
    prediction = brain.predict_tomorrow_cost()
    if prediction.get('success'):
        print(f"✅ 预测成功")
        print(f"   预测明天消耗: {prediction['predicted_cost']}元")
        print(f"   置信区间: {prediction['confidence_interval']['low']}-{prediction['confidence_interval']['high']}元")
        print(f"   趋势: {prediction['trend']} {prediction['trend_pct']}%")
    else:
        print(f"❌ 预测失败: {prediction.get('message', '')}")
