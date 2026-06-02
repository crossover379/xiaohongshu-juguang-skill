#!/usr/bin/env python3
"""
小红书聚光AI投手 - 自动执行闭环模块
核心能力：自动执行优化操作、决策反馈、策略迭代
"""
import sys, os as _sys_os
_scripts_dir = _sys_os.path.dirname(_sys_os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import json
import os
import time
from datetime import datetime, timedelta
from collections import defaultdict


class AutoExecutor:
    """自动执行闭环"""
    
    def __init__(self, sdk, data_dir=None):
        import os as _os
        if data_dir is None:
            data_dir = (
                _os.environ.get('WORKBUDDY_SKILL_DATA_DIR') or
                _os.path.join(_os.path.expanduser('~'), '.workbuddy', 'skills',
                              'xiaohongshu-juguang-ai', 'executor_data')
            )
        _os.makedirs(data_dir, exist_ok=True)
        self.sdk = sdk
        self.data_dir = data_dir
        self.execution_file = os.path.join(data_dir, "executions.json")
        self.strategy_file = os.path.join(data_dir, "strategies.json")
        self.rules_file = os.path.join(data_dir, "rules.json")
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载数据
        self.executions = self._load_json(self.execution_file, {'history': [], 'stats': {}})
        self.strategies = self._load_json(self.strategy_file, {'active': {}, 'history': []})
        self.rules = self._load_json(self.rules_file, {'rules': [], 'active_rules': []})
        
        # 初始化默认规则
        if not self.rules['rules']:
            self._init_default_rules()
    
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
    
    def _init_default_rules(self):
        """初始化默认规则"""
        self.rules['rules'] = [
            {
                'id': 'rule_001',
                'name': 'CTR过低暂停',
                'condition': 'ctr < 3',
                'action': 'pause_unit',
                'params': {'reason': 'CTR过低'},
                'priority': 'high',
                'enabled': True
            },
            {
                'id': 'rule_002',
                'name': 'CPC过高降价',
                'condition': 'cpc > 0.15',
                'action': 'decrease_bid',
                'params': {'ratio': 0.8},
                'priority': 'medium',
                'enabled': True
            },
            {
                'id': 'rule_003',
                'name': '高效计划加价',
                'condition': 'ctr > 15 and cpc < 0.08',
                'action': 'increase_bid',
                'params': {'ratio': 1.2},
                'priority': 'medium',
                'enabled': True
            },
            {
                'id': 'rule_004',
                'name': '消耗突增预警',
                'condition': 'fee_increase > 50',
                'action': 'alert',
                'params': {'message': '消耗突增，请检查'},
                'priority': 'high',
                'enabled': True
            },
            {
                'id': 'rule_005',
                'name': '余额不足预警',
                'condition': 'balance < 500',
                'action': 'alert',
                'params': {'message': '余额不足，请充值'},
                'priority': 'high',
                'enabled': True
            }
        ]
        self.rules['active_rules'] = [r['id'] for r in self.rules['rules'] if r['enabled']]
        self._save_json(self.rules_file, self.rules)
    
    # ==================== 规则引擎 ====================
    
    def evaluate_rules(self, data):
        """评估规则
        
        Args:
            data: 数据字典
        
        Returns:
            触发的规则列表
        """
        triggered_rules = []
        
        for rule in self.rules['rules']:
            if not rule['enabled']:
                continue
            
            # 评估条件
            condition = rule['condition']
            try:
                # 安全评估
                if self._evaluate_condition(condition, data):
                    triggered_rules.append({
                        'rule': rule,
                        'data': data,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            except Exception as e:
                print(f"规则评估失败: {rule['id']} - {e}")
        
        return triggered_rules
    
    def _evaluate_condition(self, condition, data):
        """评估条件
        
        Args:
            condition: 条件字符串
            data: 数据字典
        
        Returns:
            是否满足条件
        """
        # 简单条件解析
        if 'and' in condition:
            parts = condition.split(' and ')
            return all(self._evaluate_single_condition(p.strip(), data) for p in parts)
        elif 'or' in condition:
            parts = condition.split(' or ')
            return any(self._evaluate_single_condition(p.strip(), data) for p in parts)
        else:
            return self._evaluate_single_condition(condition, data)
    
    def _evaluate_single_condition(self, condition, data):
        """评估单个条件
        
        Args:
            condition: 条件字符串
            data: 数据字典
        
        Returns:
            是否满足条件
        """
        # 解析条件
        for op in ['>=', '<=', '>', '<', '==', '!=']:
            if op in condition:
                left, right = condition.split(op, 1)
                left = left.strip()
                right = right.strip()
                
                # 获取值
                if left in data:
                    value = data[left]
                else:
                    return False
                
                # 转换类型
                try:
                    value = float(value)
                    right = float(right)
                except (ValueError, TypeError):
                    return False
                
                # 比较
                if op == '>=':
                    return value >= right
                elif op == '<=':
                    return value <= right
                elif op == '>':
                    return value > right
                elif op == '<':
                    return value < right
                elif op == '==':
                    return value == right
                elif op == '!=':
                    return value != right
        
        return False
    
    # ==================== 自动执行 ====================
    
    def execute_rule(self, rule, data, dry_run=False):
        """执行规则
        
        Args:
            rule: 规则
            data: 数据
            dry_run: 试运行
        
        Returns:
            执行结果
        """
        action = rule['action']
        params = rule['params']
        
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            'execution_id': execution_id,
            'rule_id': rule['id'],
            'rule_name': rule['name'],
            'action': action,
            'params': params,
            'data': data,
            'dry_run': dry_run,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }
        
        if dry_run:
            result['status'] = 'dry_run'
            result['message'] = f'试运行：{rule["name"]}'
        else:
            # 执行动作
            try:
                if action == 'pause_unit':
                    unit_id = data.get('unit_id')
                    if unit_id:
                        exec_result = self.sdk.pause_adunit(unit_id)
                        result['status'] = 'success' if exec_result.get('success') else 'failed'
                        result['message'] = exec_result.get('message', '')
                
                elif action == 'increase_bid':
                    unit_id = data.get('unit_id')
                    current_bid = data.get('bid', 0)
                    if unit_id and current_bid:
                        new_bid = current_bid * params.get('ratio', 1.2)
                        exec_result = self.sdk.update_adunit(unit_id, event_bid=int(new_bid * 100))
                        result['status'] = 'success' if exec_result.get('success') else 'failed'
                        result['message'] = f'出价从{current_bid}元调整为{new_bid:.2f}元'
                
                elif action == 'decrease_bid':
                    unit_id = data.get('unit_id')
                    current_bid = data.get('bid', 0)
                    if unit_id and current_bid:
                        new_bid = current_bid * params.get('ratio', 0.8)
                        exec_result = self.sdk.update_adunit(unit_id, event_bid=int(new_bid * 100))
                        result['status'] = 'success' if exec_result.get('success') else 'failed'
                        result['message'] = f'出价从{current_bid}元调整为{new_bid:.2f}元'
                
                elif action == 'alert':
                    result['status'] = 'success'
                    result['message'] = params.get('message', '告警')
                
                else:
                    result['status'] = 'failed'
                    result['message'] = f'未知动作: {action}'
            
            except Exception as e:
                result['status'] = 'failed'
                result['message'] = str(e)
        
        # 保存执行记录
        self.executions['history'].append(result)
        
        # 只保留最近100条
        if len(self.executions['history']) > 100:
            self.executions['history'] = self.executions['history'][-100:]
        
        self._save_json(self.execution_file, self.executions)
        
        return result
    
    def auto_optimize(self, dry_run=True):
        """自动优化
        
        Args:
            dry_run: 试运行
        
        Returns:
            优化结果
        """
        # 获取数据
        campaigns = self.sdk.get_all_campaigns()
        if not campaigns.get('success'):
            return {'success': False, 'message': '获取计划失败'}
        
        # 获取报表
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('campaign', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取报表失败'}
        
        # 分析数据并执行规则
        results = []
        data_list = report.get('data', {}).get('data_list', [])
        
        for data in data_list:
            campaign_id = str(data.get('campaign_id', ''))
            fee = float(data.get('fee', 0))
            impression = int(data.get('impression', 0))
            click = int(data.get('click', 0))
            ctr = (click / impression * 100) if impression > 0 else 0
            cpc = (fee / click) if click > 0 else 0
            
            # 构建数据字典
            rule_data = {
                'campaign_id': campaign_id,
                'fee': fee,
                'impression': impression,
                'click': click,
                'ctr': ctr,
                'cpc': cpc
            }
            
            # 评估规则
            triggered = self.evaluate_rules(rule_data)
            
            # 执行规则
            for trigger in triggered:
                result = self.execute_rule(trigger['rule'], rule_data, dry_run)
                results.append(result)
        
        # 统计结果
        success_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len([r for r in results if r['status'] == 'failed'])
        
        return {
            'success': True,
            'dry_run': dry_run,
            'total_triggered': len(results),
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }
    
    # ==================== 策略管理 ====================
    
    def create_strategy(self, name, rules, description=''):
        """创建策略
        
        Args:
            name: 策略名称
            rules: 规则列表
            description: 描述
        
        Returns:
            创建结果
        """
        strategy_id = f"strategy_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        strategy = {
            'id': strategy_id,
            'name': name,
            'description': description,
            'rules': rules,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'active',
            'performance': {
                'executions': 0,
                'successes': 0,
                'failures': 0
            }
        }
        
        self.strategies['active'][strategy_id] = strategy
        self._save_json(self.strategy_file, self.strategies)
        
        return {
            'success': True,
            'strategy_id': strategy_id,
            'name': name,
            'message': f'策略"{name}"创建成功'
        }
    
    def apply_strategy(self, strategy_id, dry_run=True):
        """应用策略
        
        Args:
            strategy_id: 策略ID
            dry_run: 试运行
        
        Returns:
            应用结果
        """
        if strategy_id not in self.strategies['active']:
            return {'success': False, 'message': f'未找到策略: {strategy_id}'}
        
        strategy = self.strategies['active'][strategy_id]
        
        # 更新规则
        self.rules['rules'] = strategy['rules']
        self.rules['active_rules'] = [r['id'] for r in strategy['rules'] if r.get('enabled', True)]
        self._save_json(self.rules_file, self.rules)
        
        # 执行优化
        result = self.auto_optimize(dry_run)
        
        # 更新策略性能
        strategy['performance']['executions'] += 1
        if result.get('success'):
            strategy['performance']['successes'] += 1
        else:
            strategy['performance']['failures'] += 1
        
        self._save_json(self.strategy_file, self.strategies)
        
        return {
            'success': True,
            'strategy_id': strategy_id,
            'strategy_name': strategy['name'],
            'optimization_result': result,
            'message': f'策略"{strategy["name"]}"应用成功'
        }
    
    def get_strategy_performance(self):
        """获取策略性能
        
        Returns:
            策略性能列表
        """
        performance = []
        
        for strategy_id, strategy in self.strategies['active'].items():
            perf = strategy['performance']
            success_rate = (perf['successes'] / perf['executions'] * 100) if perf['executions'] > 0 else 0
            
            performance.append({
                'id': strategy_id,
                'name': strategy['name'],
                'executions': perf['executions'],
                'success_rate': round(success_rate, 2),
                'created_at': strategy['created_at']
            })
        
        # 按成功率排序
        performance.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return {
            'success': True,
            'strategies': performance,
            'total': len(performance)
        }
    
    # ==================== 执行历史 ====================
    
    def get_execution_history(self, limit=20):
        """获取执行历史
        
        Args:
            limit: 返回数量
        
        Returns:
            执行历史
        """
        history = self.executions['history'][-limit:]
        
        # 统计
        total = len(self.executions['history'])
        success = len([e for e in self.executions['history'] if e['status'] == 'success'])
        failed = len([e for e in self.executions['history'] if e['status'] == 'failed'])
        
        return {
            'success': True,
            'history': history,
            'stats': {
                'total': total,
                'success': success,
                'failed': failed,
                'success_rate': round(success / total * 100, 2) if total > 0 else 0
            }
        }
    
    def clear_execution_history(self):
        """清空执行历史
        
        Returns:
            清空结果
        """
        self.executions['history'] = []
        self.executions['stats'] = {}
        self._save_json(self.execution_file, self.executions)
        
        return {
            'success': True,
            'message': '执行历史已清空'
        }


# 测试代码
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
    
    sdk = XiaohongshuJuguangSDK()
    executor = AutoExecutor(sdk)
    
    print("=" * 50)
    print("⚡ 测试自动执行闭环")
    print("=" * 50)
    
    # 1. 测试规则评估
    print("\n1. 规则评估测试")
    print("-" * 30)
    test_data = {
        'ctr': 2.5,
        'cpc': 0.18,
        'fee': 100,
        'impression': 1000,
        'click': 25
    }
    triggered = executor.evaluate_rules(test_data)
    print(f"✅ 触发{len(triggered)}条规则")
    for t in triggered:
        print(f"   - {t['rule']['name']}")
    
    # 2. 测试自动优化（试运行）
    print("\n2. 自动优化测试（试运行）")
    print("-" * 30)
    result = executor.auto_optimize(dry_run=True)
    if result.get('success'):
        print(f"✅ 自动优化成功")
        print(f"   触发规则: {result['total_triggered']}条")
        print(f"   成功: {result['success_count']}条")
        print(f"   失败: {result['failed_count']}条")
    
    # 3. 测试创建策略
    print("\n3. 创建策略测试")
    print("-" * 30)
    strategy_result = executor.create_strategy(
        name='保守策略',
        rules=executor.rules['rules'][:3],
        description='只执行低风险规则'
    )
    if strategy_result.get('success'):
        print(f"✅ {strategy_result['message']}")
    
    # 4. 测试执行历史
    print("\n4. 执行历史测试")
    print("-" * 30)
    history = executor.get_execution_history()
    if history.get('success'):
        print(f"✅ 获取执行历史成功")
        print(f"   总数: {history['stats']['total']}")
        print(f"   成功率: {history['stats']['success_rate']}%")
    
    # 5. 测试策略性能
    print("\n5. 策略性能测试")
    print("-" * 30)
    performance = executor.get_strategy_performance()
    if performance.get('success'):
        print(f"✅ 获取策略性能成功")
        print(f"   策略数量: {performance['total']}")
