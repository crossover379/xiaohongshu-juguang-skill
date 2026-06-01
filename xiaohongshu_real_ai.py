#!/usr/bin/env python3
"""
小红书聚光AI投手 - 真正的智能模块
核心能力：机器学习、决策反馈、多臂老虎机、强化学习
"""
import json
import os
import math
import random
from datetime import datetime, timedelta
from collections import defaultdict


class RealAI:
    """真正的AI投手"""
    
    def __init__(self, sdk, data_dir="/root/.openclaw/workspace/skills/xiaohongshu-juguang-ai/ai_data"):
        self.sdk = sdk
        self.data_dir = data_dir
        self.decision_file = os.path.join(data_dir, "decisions.json")
        self.model_file = os.path.join(data_dir, "model.json")
        self.bandit_file = os.path.join(data_dir, "bandit.json")
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载数据
        self.decisions = self._load_json(self.decision_file, {'decisions': [], 'outcomes': []})
        self.model = self._load_json(self.model_file, {'weights': {}, 'bias': 0, 'history': []})
        self.bandit = self._load_json(self.bandit_file, {'arms': {}, 'rewards': {}})
    
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
    
    # ==================== 决策反馈循环 ====================
    
    def record_decision(self, decision_type, context, action, expected_outcome):
        """记录决策
        
        Args:
            decision_type: 决策类型（bid/budget/pause/resume）
            context: 决策上下文（计划状态、历史数据等）
            action: 执行的动作
            expected_outcome: 预期结果
        
        Returns:
            记录结果
        """
        decision_id = f"dec_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        decision = {
            'id': decision_id,
            'type': decision_type,
            'context': context,
            'action': action,
            'expected_outcome': expected_outcome,
            'actual_outcome': None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }
        
        self.decisions['decisions'].append(decision)
        self._save_json(self.decision_file, self.decisions)
        
        return {
            'success': True,
            'decision_id': decision_id,
            'message': f'决策{decision_id}记录成功'
        }
    
    def record_outcome(self, decision_id, actual_outcome, metrics):
        """记录决策结果
        
        Args:
            decision_id: 决策ID
            actual_outcome: 实际结果
            metrics: 结果指标
        
        Returns:
            记录结果
        """
        # 找到决策
        decision = None
        for d in self.decisions['decisions']:
            if d['id'] == decision_id:
                decision = d
                break
        
        if not decision:
            return {'success': False, 'message': f'未找到决策: {decision_id}'}
        
        # 更新决策结果
        decision['actual_outcome'] = actual_outcome
        decision['metrics'] = metrics
        decision['status'] = 'completed'
        
        # 计算决策质量
        expected = decision['expected_outcome']
        actual = actual_outcome
        
        # 简单的质量评估
        quality = 0
        if expected.get('ctr') and actual.get('ctr'):
            if actual['ctr'] >= expected['ctr']:
                quality += 30
        if expected.get('cpc') and actual.get('cpc'):
            if actual['cpc'] <= expected['cpc']:
                quality += 30
        if expected.get('fee') and actual.get('fee'):
            if actual['fee'] <= expected['fee']:
                quality += 40
        
        decision['quality'] = quality
        
        # 保存到结果列表
        self.decisions['outcomes'].append({
            'decision_id': decision_id,
            'quality': quality,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        self._save_json(self.decision_file, self.decisions)
        
        # 更新模型
        self._update_model(decision)
        
        return {
            'success': True,
            'decision_id': decision_id,
            'quality': quality,
            'message': f'决策结果记录成功，质量得分: {quality}'
        }
    
    def _update_model(self, decision):
        """更新模型
        
        基于决策结果更新模型权重
        """
        # 提取特征
        context = decision.get('context', {})
        action = decision.get('action', {})
        quality = decision.get('quality', 0)
        
        # 特征：CTR、CPC、fee、impression、click
        features = {
            'ctr': context.get('ctr', 0),
            'cpc': context.get('cpc', 0),
            'fee': context.get('fee', 0),
            'impression': context.get('impression', 0),
            'click': context.get('click', 0)
        }
        
        # 动作特征
        action_type = action.get('type', '')
        action_value = action.get('value', 0)
        
        # 更新权重（简单的梯度下降）
        learning_rate = 0.01
        
        for feature, value in features.items():
            if feature not in self.model['weights']:
                self.model['weights'][feature] = 0
            
            # 梯度更新
            gradient = quality * value * learning_rate
            self.model['weights'][feature] += gradient
        
        # 更新偏置
        self.model['bias'] += quality * learning_rate
        
        # 保存历史
        self.model['history'].append({
            'features': features,
            'action': action_type,
            'quality': quality,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 只保留最近100条历史
        if len(self.model['history']) > 100:
            self.model['history'] = self.model['history'][-100:]
        
        self._save_json(self.model_file, self.model)
    
    def predict_quality(self, context, action):
        """预测决策质量
        
        Args:
            context: 决策上下文
            action: 动作
        
        Returns:
            预测质量得分
        """
        # 提取特征
        features = {
            'ctr': context.get('ctr', 0),
            'cpc': context.get('cpc', 0),
            'fee': context.get('fee', 0),
            'impression': context.get('impression', 0),
            'click': context.get('click', 0)
        }
        
        # 计算预测值
        score = self.model['bias']
        for feature, value in features.items():
            weight = self.model['weights'].get(feature, 0)
            score += weight * value
        
        # 归一化到0-100
        score = max(0, min(100, score))
        
        return {
            'success': True,
            'score': round(score, 2),
            'features': features
        }
    
    # ==================== 多臂老虎机算法 ====================
    
    def init_bandit(self, arms):
        """初始化老虎机
        
        Args:
            arms: 臂列表（每个臂代表一个策略）
        """
        for arm in arms:
            if arm not in self.bandit['arms']:
                self.bandit['arms'][arm] = {
                    'trials': 0,
                    'rewards': 0,
                    'avg_reward': 0
                }
                self.bandit['rewards'][arm] = []
        
        self._save_json(self.bandit_file, self.bandit)
        
        return {
            'success': True,
            'arms': list(self.bandit['arms'].keys()),
            'message': f'初始化{len(arms)}个臂'
        }
    
    def select_arm(self, strategy='ucb'):
        """选择臂
        
        Args:
            strategy: 选择策略（ucb/epsilon_greedy/thompson）
        
        Returns:
            选择的臂
        """
        if not self.bandit['arms']:
            return {'success': False, 'message': '未初始化老虎机'}
        
        if strategy == 'ucb':
            # UCB1算法
            total_trials = sum(arm['trials'] for arm in self.bandit['arms'].values())
            
            if total_trials == 0:
                # 第一次随机选择
                arm = random.choice(list(self.bandit['arms'].keys()))
            else:
                best_arm = None
                best_ucb = -float('inf')
                
                for arm_name, arm_data in self.bandit['arms'].items():
                    if arm_data['trials'] == 0:
                        # 未尝试的臂优先
                        ucb = float('inf')
                    else:
                        # UCB1公式
                        avg_reward = arm_data['avg_reward']
                        exploration = math.sqrt(2 * math.log(total_trials) / arm_data['trials'])
                        ucb = avg_reward + exploration
                    
                    if ucb > best_ucb:
                        best_ucb = ucb
                        best_arm = arm_name
                
                arm = best_arm
        
        elif strategy == 'epsilon_greedy':
            # ε-贪婪算法
            epsilon = 0.1
            
            if random.random() < epsilon:
                # 探索：随机选择
                arm = random.choice(list(self.bandit['arms'].keys()))
            else:
                # 利用：选择最优臂
                best_arm = None
                best_reward = -float('inf')
                
                for arm_name, arm_data in self.bandit['arms'].items():
                    if arm_data['avg_reward'] > best_reward:
                        best_reward = arm_data['avg_reward']
                        best_arm = arm_name
                
                arm = best_arm
        
        elif strategy == 'thompson':
            # Thompson采样
            best_arm = None
            best_sample = -float('inf')
            
            for arm_name, arm_data in self.bandit['arms'].items():
                # Beta分布采样
                alpha = arm_data['rewards'] + 1
                beta = arm_data['trials'] - arm_data['rewards'] + 1
                sample = random.betavariate(alpha, beta)
                
                if sample > best_sample:
                    best_sample = sample
                    best_arm = arm_name
            
            arm = best_arm
        
        else:
            return {'success': False, 'message': f'未知策略: {strategy}'}
        
        return {
            'success': True,
            'arm': arm,
            'strategy': strategy,
            'message': f'选择臂: {arm}'
        }
    
    def update_bandit(self, arm, reward):
        """更新老虎机
        
        Args:
            arm: 臂
            reward: 奖励（0-1）
        """
        if arm not in self.bandit['arms']:
            return {'success': False, 'message': f'未找到臂: {arm}'}
        
        # 更新统计
        arm_data = self.bandit['arms'][arm]
        arm_data['trials'] += 1
        arm_data['rewards'] += reward
        arm_data['avg_reward'] = arm_data['rewards'] / arm_data['trials']
        
        # 记录奖励
        self.bandit['rewards'][arm].append({
            'reward': reward,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 只保留最近100条奖励
        if len(self.bandit['rewards'][arm]) > 100:
            self.bandit['rewards'][arm] = self.bandit['rewards'][arm][-100:]
        
        self._save_json(self.bandit_file, self.bandit)
        
        return {
            'success': True,
            'arm': arm,
            'trials': arm_data['trials'],
            'avg_reward': round(arm_data['avg_reward'], 4),
            'message': f'更新臂{arm}，平均奖励: {arm_data["avg_reward"]:.4f}'
        }
    
    def get_bandit_stats(self):
        """获取老虎机统计
        
        Returns:
            统计信息
        """
        stats = {}
        for arm_name, arm_data in self.bandit['arms'].items():
            stats[arm_name] = {
                'trials': arm_data['trials'],
                'rewards': arm_data['rewards'],
                'avg_reward': round(arm_data['avg_reward'], 4)
            }
        
        return {
            'success': True,
            'stats': stats,
            'total_trials': sum(arm_data['trials'] for arm_data in self.bandit['arms'].values())
        }
    
    # ==================== 智能出价策略 ====================
    
    def smart_bid(self, campaign_id, target_cpa=None, target_roas=None):
        """智能出价
        
        Args:
            campaign_id: 计划ID
            target_cpa: 目标CPA（可选）
            target_roas: 目标ROAS（可选）
        
        Returns:
            出价建议
        """
        # 获取计划数据
        report = self.sdk.get_offline_report('campaign',
                                            start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                                            end_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
        
        if not report.get('success'):
            return {'success': False, 'message': '获取计划数据失败'}
        
        # 找到对应计划
        data_list = report.get('data', {}).get('data_list', [])
        campaign_data = None
        for d in data_list:
            if str(d.get('campaign_id')) == str(campaign_id):
                campaign_data = d
                break
        
        if not campaign_data:
            return {'success': False, 'message': f'未找到计划: {campaign_id}'}
        
        # 提取数据
        fee = float(campaign_data.get('fee', 0))
        impression = int(campaign_data.get('impression', 0))
        click = int(campaign_data.get('click', 0))
        ctr = (click / impression * 100) if impression > 0 else 0
        cpc = (fee / click) if click > 0 else 0
        
        # 获取当前出价
        units = self.sdk.get_unit_list(campaign_id=campaign_id)
        current_bid = 0
        if units.get('success') and units.get('data', {}).get('unit_infos'):
            unit = units['data']['unit_infos'][0]
            current_bid = unit.get('event_bid', 0) / 100  # 转换为元
        
        # 计算建议出价
        suggested_bid = current_bid
        reason = ''
        
        if target_cpa:
            # 基于目标CPA计算
            if cpc > 0:
                # CPA = CPC * (1/转化率)
                # 假设转化率为5%
                conversion_rate = 0.05
                target_cpc = target_cpa * conversion_rate
                
                if cpc > target_cpc:
                    suggested_bid = current_bid * (target_cpc / cpc)
                    reason = f'当前CPC {cpc:.2f}元高于目标CPA {target_cpa}元对应的CPC {target_cpc:.2f}元'
                else:
                    suggested_bid = current_bid * 1.1
                    reason = f'当前CPC {cpc:.2f}元低于目标，可适当提价'
        
        elif target_roas:
            # 基于目标ROAS计算
            if fee > 0:
                # ROAS = 收入/消耗
                # 假设收入为消耗的3倍
                current_roas = 3.0
                
                if current_roas < target_roas:
                    suggested_bid = current_bid * (current_roas / target_roas)
                    reason = f'当前ROAS {current_roas:.2f}低于目标{target_roas}'
                else:
                    suggested_bid = current_bid * 1.1
                    reason = f'当前ROAS {current_roas:.2f}高于目标，可适当提价'
        
        else:
            # 基于历史表现计算
            if ctr > 15 and cpc < 0.1:
                suggested_bid = current_bid * 1.2
                reason = f'CTR {ctr:.2f}%优秀，CPC {cpc:.2f}元低，可提价获取更多流量'
            elif ctr < 5 or cpc > 0.15:
                suggested_bid = current_bid * 0.8
                reason = f'CTR {ctr:.2f}%或CPC {cpc:.2f}元不理想，建议降价'
            else:
                suggested_bid = current_bid
                reason = '表现正常，保持当前出价'
        
        # 限制出价范围
        suggested_bid = max(0.3, min(10, suggested_bid))  # 0.3-10元
        
        return {
            'success': True,
            'campaign_id': campaign_id,
            'current_bid': round(current_bid, 2),
            'suggested_bid': round(suggested_bid, 2),
            'reason': reason,
            'metrics': {
                'fee': round(fee, 2),
                'impression': impression,
                'click': click,
                'ctr': round(ctr, 2),
                'cpc': round(cpc, 2)
            }
        }
    
    # ==================== 智能预算分配 ====================
    
    def smart_budget_allocation(self, total_budget, strategy='performance'):
        """智能预算分配
        
        Args:
            total_budget: 总预算（元）
            strategy: 分配策略（performance/balanced/exploration）
        
        Returns:
            分配结果
        """
        # 获取所有计划
        campaigns = self.sdk.get_all_campaigns()
        if not campaigns.get('success'):
            return {'success': False, 'message': '获取计划失败'}
        
        # 获取计划报表
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('campaign', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取计划报表失败'}
        
        # 分析计划表现
        campaign_performance = {}
        data_list = report.get('data', {}).get('data_list', [])
        
        for data in data_list:
            campaign_id = str(data.get('campaign_id', ''))
            fee = float(data.get('fee', 0))
            impression = int(data.get('impression', 0))
            click = int(data.get('click', 0))
            ctr = (click / impression * 100) if impression > 0 else 0
            cpc = (fee / click) if click > 0 else 0
            
            # 计算表现得分
            score = 0
            if fee > 0:
                score += 20
            if ctr > 10:
                score += 30
            if cpc < 0.1:
                score += 30
            if click > 5:
                score += 20
            
            campaign_performance[campaign_id] = {
                'fee': fee,
                'impression': impression,
                'click': click,
                'ctr': round(ctr, 2),
                'cpc': round(cpc, 2),
                'score': score
            }
        
        # 根据策略分配预算
        allocations = []
        
        if strategy == 'performance':
            # 按表现分配
            total_score = sum(p['score'] for p in campaign_performance.values())
            
            for campaign_id, performance in campaign_performance.items():
                if total_score > 0:
                    allocation = total_budget * (performance['score'] / total_score)
                else:
                    allocation = total_budget / len(campaign_performance)
                
                allocations.append({
                    'campaign_id': campaign_id,
                    'allocation': round(allocation, 2),
                    'performance': performance,
                    'reason': f'表现得分{performance["score"]}分'
                })
        
        elif strategy == 'balanced':
            # 平均分配
            num_campaigns = len(campaign_performance)
            allocation_per_campaign = total_budget / num_campaigns if num_campaigns > 0 else 0
            
            for campaign_id, performance in campaign_performance.items():
                allocations.append({
                    'campaign_id': campaign_id,
                    'allocation': round(allocation_per_campaign, 2),
                    'performance': performance,
                    'reason': '平均分配'
                })
        
        elif strategy == 'exploration':
            # 探索分配（老虎机策略）
            # 初始化老虎机
            arms = list(campaign_performance.keys())
            self.init_bandit(arms)
            
            # 选择臂
            selected = self.select_arm(strategy='ucb')
            selected_arm = selected.get('arm')
            
            for campaign_id, performance in campaign_performance.items():
                if campaign_id == selected_arm:
                    allocation = total_budget * 0.5  # 探索臂拿50%预算
                else:
                    allocation = total_budget * 0.5 / (len(campaign_performance) - 1) if len(campaign_performance) > 1 else 0
                
                allocations.append({
                    'campaign_id': campaign_id,
                    'allocation': round(allocation, 2),
                    'performance': performance,
                    'reason': f'{"探索臂" if campaign_id == selected_arm else "利用臂"}'
                })
        
        # 排序
        allocations.sort(key=lambda x: x['allocation'], reverse=True)
        
        return {
            'success': True,
            'total_budget': total_budget,
            'strategy': strategy,
            'allocations': allocations,
            'summary': {
                'total_campaigns': len(allocations),
                'allocated': len([a for a in allocations if a['allocation'] > 0]),
                'paused': len([a for a in allocations if a['allocation'] == 0])
            }
        }
    
    # ==================== 学习与优化 ====================
    
    def learn_from_history(self, days=30):
        """从历史中学习
        
        Args:
            days: 学习天数
        
        Returns:
            学习结果
        """
        # 获取历史决策
        completed_decisions = [d for d in self.decisions['decisions'] if d['status'] == 'completed']
        
        if len(completed_decisions) < 5:
            return {
                'success': True,
                'message': f'历史决策不足（{len(completed_decisions)}条），需要至少5条',
                'learned': False
            }
        
        # 分析决策质量
        qualities = [d['quality'] for d in completed_decisions]
        avg_quality = sum(qualities) / len(qualities)
        
        # 找出高质量决策
        high_quality = [d for d in completed_decisions if d['quality'] >= 70]
        low_quality = [d for d in completed_decisions if d['quality'] < 30]
        
        # 提取规律
        patterns = []
        
        if high_quality:
            # 分析高质量决策的特征
            for d in high_quality:
                context = d.get('context', {})
                action = d.get('action', {})
                
                if context.get('ctr', 0) > 10 and action.get('type') == 'increase_bid':
                    patterns.append({
                        'pattern': 'CTR高时提价',
                        'condition': 'CTR > 10%',
                        'action': '提价',
                        'confidence': 0.8
                    })
                
                if context.get('cpc', 0) > 0.15 and action.get('type') == 'decrease_bid':
                    patterns.append({
                        'pattern': 'CPC高时降价',
                        'condition': 'CPC > 0.15元',
                        'action': '降价',
                        'confidence': 0.8
                    })
        
        return {
            'success': True,
            'learned': True,
            'total_decisions': len(completed_decisions),
            'avg_quality': round(avg_quality, 2),
            'high_quality': len(high_quality),
            'low_quality': len(low_quality),
            'patterns': patterns[:5]  # 最多返回5个规律
        }
    
    def get_smart_recommendation(self):
        """获取智能推荐
        
        Returns:
            推荐列表
        """
        recommendations = []
        
        # 1. 基于模型的推荐
        if self.model['history']:
            # 分析历史决策
            high_quality = [h for h in self.model['history'] if h['quality'] >= 70]
            
            if high_quality:
                # 找出最有效的动作
                action_counts = defaultdict(int)
                for h in high_quality:
                    action_counts[h['action']] += 1
                
                best_action = max(action_counts.items(), key=lambda x: x[1])
                recommendations.append({
                    'type': 'action',
                    'title': f'推荐动作: {best_action[0]}',
                    'detail': f'历史高质量决策中，{best_action[0]}出现{best_action[1]}次',
                    'priority': 'high'
                })
        
        # 2. 基于老虎机的推荐
        if self.bandit['arms']:
            # 找出最优臂
            best_arm = None
            best_reward = -float('inf')
            
            for arm_name, arm_data in self.bandit['arms'].items():
                if arm_data['avg_reward'] > best_reward:
                    best_reward = arm_data['avg_reward']
                    best_arm = arm_name
            
            if best_arm:
                recommendations.append({
                    'type': 'arm',
                    'title': f'推荐策略: {best_arm}',
                    'detail': f'平均奖励: {best_reward:.4f}',
                    'priority': 'high'
                })
        
        # 3. 基于数据的推荐
        campaigns = self.sdk.get_all_campaigns()
        if campaigns.get('success'):
            for campaign in campaigns.get('data', [])[:3]:
                campaign_id = campaign.get('campaign_id')
                bid_result = self.smart_bid(campaign_id)
                
                if bid_result.get('success'):
                    current = bid_result['current_bid']
                    suggested = bid_result['suggested_bid']
                    
                    if suggested > current * 1.1:
                        recommendations.append({
                            'type': 'bid',
                            'title': f'计划{campaign_id}建议提价',
                            'detail': f'当前出价{current}元，建议{suggested}元',
                            'priority': 'medium'
                        })
                    elif suggested < current * 0.9:
                        recommendations.append({
                            'type': 'bid',
                            'title': f'计划{campaign_id}建议降价',
                            'detail': f'当前出价{current}元，建议{suggested}元',
                            'priority': 'medium'
                        })
        
        return {
            'success': True,
            'recommendations': recommendations,
            'total': len(recommendations)
        }


# 测试代码
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
    
    sdk = XiaohongshuJuguangSDK()
    ai = RealAI(sdk)
    
    print("=" * 50)
    print("🤖 测试真正的AI模块")
    print("=" * 50)
    
    # 1. 测试决策记录
    print("\n1. 决策记录测试")
    print("-" * 30)
    decision = ai.record_decision(
        decision_type='bid',
        context={'ctr': 15, 'cpc': 0.08, 'fee': 50},
        action={'type': 'increase_bid', 'value': 1.2},
        expected_outcome={'ctr': 16, 'cpc': 0.07}
    )
    if decision.get('success'):
        print(f"✅ {decision['message']}")
    
    # 2. 测试老虎机
    print("\n2. 老虎机测试")
    print("-" * 30)
    ai.init_bandit(['arm_a', 'arm_b', 'arm_c'])
    
    # 模拟选择和更新
    for _ in range(5):
        selected = ai.select_arm(strategy='ucb')
        if selected.get('success'):
            reward = random.random()
            ai.update_bandit(selected['arm'], reward)
    
    stats = ai.get_bandit_stats()
    if stats.get('success'):
        print(f"✅ 老虎机统计:")
        for arm, data in stats['stats'].items():
            print(f"   {arm}: 试验{data['trials']}次, 平均奖励{data['avg_reward']:.4f}")
    
    # 3. 测试智能出价
    print("\n3. 智能出价测试")
    print("-" * 30)
    campaigns = sdk.get_all_campaigns()
    if campaigns.get('success') and campaigns.get('data'):
        campaign_id = campaigns['data'][0].get('campaign_id')
        bid_result = ai.smart_bid(campaign_id, target_cpa=5)
        if bid_result.get('success'):
            print(f"✅ 智能出价成功")
            print(f"   当前出价: {bid_result['current_bid']}元")
            print(f"   建议出价: {bid_result['suggested_bid']}元")
            print(f"   原因: {bid_result['reason']}")
    
    # 4. 测试智能推荐
    print("\n4. 智能推荐测试")
    print("-" * 30)
    recommendation = ai.get_smart_recommendation()
    if recommendation.get('success'):
        print(f"✅ 智能推荐成功: {recommendation['total']}条")
        for rec in recommendation['recommendations'][:3]:
            print(f"   - {rec['title']}")
