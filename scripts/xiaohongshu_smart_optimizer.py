#!/usr/bin/env python3
"""
小红书聚光AI投手智能优化模块
包含：数据预警、智能投放、批量操作、报表自动化
"""
import sys, os as _sys_os
_scripts_dir = _sys_os.path.dirname(_sys_os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import sys
import json
from datetime import datetime, timedelta
sys.path.insert(0, '.')
from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK


class SmartOptimizer:
    """AI投手智能优化器"""
    
    def __init__(self, config_path=None):
        import os as _os
        if config_path is None:
            config_path = (
                _os.environ.get('XIAOHONGSHU_CONFIG_PATH') or
                _os.path.join(_os.path.expanduser('~'), '.workbuddy', 'skills',
                              'xiaohongshu-juguang-ai', 'xiaohongshu_config.json')
            )
        self.sdk = XiaohongshuJuguangSDK(config_path)
        self.alert_rules = []
    
    # ==================== 数据预警功能 ====================
    
    def add_alert_rule(self, rule_type, threshold, action="notify"):
        """添加预警规则
        
        Args:
            rule_type: 预警类型
                - cost_high: 消耗超标
                - ctr_low: CTR过低
                - cpc_high: CPC过高
                - balance_low: 余额不足
                - cost_zero: 消耗归零
                - cost_trend_down: 消耗趋势下降
            threshold: 阈值
            action: 动作
                - notify: 仅通知
                - pause: 暂停计划
                - reduce_bid: 降低出价
        """
        self.alert_rules.append({
            'type': rule_type,
            'threshold': threshold,
            'action': action
        })
        return {'success': True, 'message': f'添加预警规则成功: {rule_type}'}
    
    def check_alerts(self, date=None):
        """检查预警
        
        Args:
            date: 日期，默认昨天
        
        Returns:
            预警列表
        """
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        alerts = []
        
        # 获取消耗数据
        cost = self.sdk.get_daily_cost(date)
        if not cost.get('success') and 'success' in cost:
            return {'success': False, 'message': '获取消耗数据失败'}
        
        total_cost = cost.get('total_cost', 0)
        total_impression = cost.get('total_impression', 0)
        total_click = cost.get('total_click', 0)
        ctr = (total_click / total_impression * 100) if total_impression > 0 else 0
        cpc = (total_cost / total_click) if total_click > 0 else 0
        
        # 检查每条规则
        for rule in self.alert_rules:
            if rule['type'] == 'cost_high':
                if total_cost > rule['threshold']:
                    alerts.append({
                        'type': 'cost_high',
                        'level': 'warning',
                        'message': f'消耗超标: {total_cost:.2f}元 > {rule["threshold"]}元',
                        'action': rule['action'],
                        'data': {'cost': total_cost, 'threshold': rule['threshold']}
                    })
            
            elif rule['type'] == 'ctr_low':
                if ctr < rule['threshold']:
                    alerts.append({
                        'type': 'ctr_low',
                        'level': 'warning',
                        'message': f'CTR过低: {ctr:.2f}% < {rule["threshold"]}%',
                        'action': rule['action'],
                        'data': {'ctr': ctr, 'threshold': rule['threshold']}
                    })
            
            elif rule['type'] == 'cpc_high':
                if cpc > rule['threshold']:
                    alerts.append({
                        'type': 'cpc_high',
                        'level': 'warning',
                        'message': f'CPC过高: {cpc:.2f}元 > {rule["threshold"]}元',
                        'action': rule['action'],
                        'data': {'cpc': cpc, 'threshold': rule['threshold']}
                    })
            
            elif rule['type'] == 'cost_zero':
                if total_cost == 0:
                    alerts.append({
                        'type': 'cost_zero',
                        'level': 'info',
                        'message': '消耗归零: 无消耗数据',
                        'action': rule['action'],
                        'data': {'cost': 0}
                    })
        
        return {
            'success': True,
            'date': date,
            'alerts': alerts,
            'summary': {
                'cost': total_cost,
                'impression': total_impression,
                'click': total_click,
                'ctr': round(ctr, 2),
                'cpc': round(cpc, 2)
            }
        }
    
    def execute_alert_action(self, alert):
        """执行预警动作
        
        Args:
            alert: 预警信息
        
        Returns:
            执行结果
        """
        action = alert.get('action')
        
        if action == 'notify':
            return {'success': True, 'message': '通知已发送', 'action': 'notify'}
        
        elif action == 'pause':
            # 暂停低效计划
            campaigns = self.sdk.get_all_campaigns()
            if not campaigns.get('success'):
                return {'success': False, 'message': '获取计划失败'}
            
            paused_count = 0
            for campaign in campaigns.get('data', []):
                if campaign.get('explore_status') == 1:  # 投放中
                    result = self.sdk.update_campaign_status([campaign['campaign_id']], 2)
                    if result.get('success'):
                        paused_count += 1
            
            return {'success': True, 'message': f'已暂停{paused_count}个计划', 'action': 'pause'}
        
        elif action == 'reduce_bid':
            # 降低出价
            units = self.sdk.get_all_units()
            if not units.get('success'):
                return {'success': False, 'message': '获取单元失败'}
            
            reduced_count = 0
            for unit in units.get('data', []):
                current_bid = unit.get('event_bid', 0)
                if current_bid > 0:
                    new_bid = int(current_bid * 0.8)  # 降低20%
                    result = self.sdk.update_unit_bid([{
                        'unit_id': unit.get('unit_id'),
                        'event_bid': new_bid
                    }])
                    if result.get('success'):
                        reduced_count += 1
            
            return {'success': True, 'message': f'已降低{reduced_count}个单元出价', 'action': 'reduce_bid'}
        
        return {'success': False, 'message': f'未知动作: {action}'}
    
    # ==================== 智能投放功能 ====================
    
    def auto_create_campaign(self, industry, budget_yuan=100, bid_yuan=1.0, 
                            note_ids=None, keywords=None):
        """自动创建计划
        
        Args:
            industry: 行业关键词
            budget_yuan: 日预算（元）
            bid_yuan: 出价（元）
            note_ids: 笔记ID列表（可选，自动筛选优质笔记）
            keywords: 关键词列表（可选，自动推荐）
        
        Returns:
            创建结果
        """
        # 1. 获取优质创意
        if not note_ids:
            top_creatives = self.sdk.get_top_creatives(
                days=30, top_n=5, min_fee=1.0, min_ctr=10.0, 
                filter_existing_notes=True
            )
            if not top_creatives:
                return {'success': False, 'message': '未找到优质创意'}
            note_ids = [c['note_id'] for c in top_creatives]
        
        # 2. 获取关键词推荐
        if not keywords:
            keyword_result = self.sdk.keyword_recommend(industry)
            if keyword_result.get('success'):
                word_list = keyword_result['data'].get('word_list', [])[:5]
                keywords = [{
                    'keyword': w.get('keyword', ''),
                    'bid': int(w.get('bid', 200)),
                    'phrase_match_type': 0
                } for w in word_list if w.get('keyword')]
        
        # 3. 生成计划名称
        date_str = datetime.now().strftime('%m月%d日')
        campaign_name = f"{industry}客资_{date_str}_全站"
        
        # 4. 创建计划
        result = self.sdk.create_campaign_with_creatives(
            campaign_name=campaign_name,
            note_ids=note_ids,
            marketing_target=9,  # 客资收集
            placement=4,  # 全站
            daily_budget_yuan=budget_yuan,
            bid_yuan=bid_yuan,
            keywords=keywords,
            industry_keyword=industry
        )
        
        return result
    
    def auto_optimize_campaigns(self, dry_run=True):
        """自动优化计划
        
        Args:
            dry_run: 是否仅模拟运行（不实际执行）
        
        Returns:
            优化结果
        """
        # 1. 获取所有计划
        campaigns = self.sdk.get_all_campaigns()
        if not campaigns.get('success'):
            return {'success': False, 'message': '获取计划失败'}
        
        optimize_actions = []
        
        for campaign in campaigns.get('data', []):
            campaign_id = campaign.get('campaign_id')
            campaign_name = campaign.get('campaign_name', '')
            explore_status = campaign.get('explore_status', 0)
            
            # 只处理投放中的计划
            if explore_status != 1:
                continue
            
            # 获取计划报表
            report = self.sdk.get_offline_report('campaign', 
                                                start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                                                end_date=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
            
            if not report.get('success'):
                continue
            
            # 分析计划表现
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
            
            # 判断是否需要优化
            action = None
            reason = None
            
            if fee > 0 and ctr < 5:  # CTR过低
                action = 'pause'
                reason = f'CTR过低: {ctr:.2f}%'
            elif fee > 0 and cpc > 0.15:  # CPC过高
                action = 'reduce_bid'
                reason = f'CPC过高: {cpc:.2f}元'
            elif fee == 0 and explore_status == 1:  # 无消耗
                action = 'notify'
                reason = '无消耗'
            
            if action:
                optimize_actions.append({
                    'campaign_id': campaign_id,
                    'campaign_name': campaign_name,
                    'action': action,
                    'reason': reason,
                    'data': {
                        'fee': fee,
                        'impression': impression,
                        'click': click,
                        'ctr': round(ctr, 2),
                        'cpc': round(cpc, 2)
                    }
                })
        
        # 执行优化动作
        executed_actions = []
        for action in optimize_actions:
            if dry_run:
                executed_actions.append({
                    **action,
                    'executed': False,
                    'message': '模拟运行，未实际执行'
                })
            else:
                # 实际执行
                if action['action'] == 'pause':
                    result = self.sdk.update_campaign_status([action['campaign_id']], 2)
                    executed_actions.append({
                        **action,
                        'executed': True,
                        'result': result
                    })
                elif action['action'] == 'reduce_bid':
                    # 获取单元
                    units = self.sdk.get_unit_list(campaign_id=action['campaign_id'])
                    if units.get('success') and units.get('data', {}).get('unit_infos'):
                        unit = units['data']['unit_infos'][0]
                        current_bid = unit.get('event_bid', 0)
                        new_bid = int(current_bid * 0.8)
                        result = self.sdk.update_unit_bid([{
                            'unit_id': unit.get('unit_id'),
                            'event_bid': new_bid
                        }])
                        executed_actions.append({
                            **action,
                            'executed': True,
                            'result': result,
                            'new_bid': new_bid
                        })
                else:
                    executed_actions.append({
                        **action,
                        'executed': False,
                        'message': '仅通知，未执行'
                    })
        
        return {
            'success': True,
            'dry_run': dry_run,
            'total_campaigns': len(campaigns.get('data', [])),
            'optimize_actions': executed_actions
        }
    
    # ==================== 批量操作功能 ====================
    
    def batch_pause_campaigns(self, campaign_ids):
        """批量暂停计划
        
        Args:
            campaign_ids: 计划ID列表
        
        Returns:
            暂停结果
        """
        results = []
        batch_size = 20
        
        for i in range(0, len(campaign_ids), batch_size):
            batch = campaign_ids[i:i+batch_size]
            result = self.sdk.update_campaign_status(batch, 2)
            results.append({
                'batch': i // batch_size + 1,
                'campaign_ids': batch,
                'result': result
            })
        
        return {
            'success': True,
            'total': len(campaign_ids),
            'results': results
        }
    
    def batch_resume_campaigns(self, campaign_ids):
        """批量启动计划
        
        Args:
            campaign_ids: 计划ID列表
        
        Returns:
            启动结果
        """
        results = []
        batch_size = 20
        
        for i in range(0, len(campaign_ids), batch_size):
            batch = campaign_ids[i:i+batch_size]
            result = self.sdk.update_campaign_status(batch, 1)
            results.append({
                'batch': i // batch_size + 1,
                'campaign_ids': batch,
                'result': result
            })
        
        return {
            'success': True,
            'total': len(campaign_ids),
            'results': results
        }
    
    def batch_update_budget(self, campaign_budgets):
        """批量修改预算
        
        Args:
            campaign_budgets: [{campaign_id, budget_yuan}]
        
        Returns:
            修改结果
        """
        results = []
        
        for item in campaign_budgets:
            campaign_id = item['campaign_id']
            budget_yuan = item['budget_yuan']
            budget_fen = int(budget_yuan * 100)
            
            result = self.sdk.update_campaign(
                campaign_id=campaign_id,
                limit_day_budget=1,
                origin_campaign_day_budget=budget_fen
            )
            results.append({
                'campaign_id': campaign_id,
                'budget_yuan': budget_yuan,
                'result': result
            })
        
        return {
            'success': True,
            'total': len(campaign_budgets),
            'results': results
        }
    
    def batch_update_bid(self, unit_bids):
        """批量修改出价
        
        Args:
            unit_bids: [{unit_id, bid_yuan}]
        
        Returns:
            修改结果
        """
        results = []
        batch_size = 20
        
        for i in range(0, len(unit_bids), batch_size):
            batch = unit_bids[i:i+batch_size]
            event_bid_list = [{
                'unit_id': item['unit_id'],
                'event_bid': int(item['bid_yuan'] * 100)
            } for item in batch]
            
            result = self.sdk.update_unit_bid(event_bid_list)
            results.append({
                'batch': i // batch_size + 1,
                'result': result
            })
        
        return {
            'success': True,
            'total': len(unit_bids),
            'results': results
        }
    
    # ==================== 报表自动化功能 ====================
    
    def generate_daily_report(self, date=None):
        """生成日报
        
        Args:
            date: 日期，默认昨天
        
        Returns:
            日报数据
        """
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 1. 获取消耗数据
        cost = self.sdk.get_daily_cost(date)
        
        # 2. 获取计划数据
        campaigns = self.sdk.get_all_campaigns()
        campaign_count = campaigns.get('total_count', 0) if campaigns.get('success') else 0
        
        # 3. 获取创意数据
        creatives = self.sdk.get_all_creatives()
        creative_count = creatives.get('total_count', 0) if creatives.get('success') else 0
        
        # 4. 获取笔记数据
        notes = self.sdk.get_all_notes()
        note_count = notes.get('total_count', 0) if notes.get('success') else 0
        
        # 5. 计算指标
        total_cost = cost.get('total_cost', 0)
        total_impression = cost.get('total_impression', 0)
        total_click = cost.get('total_click', 0)
        ctr = (total_click / total_impression * 100) if total_impression > 0 else 0
        cpc = (total_cost / total_click) if total_click > 0 else 0
        
        return {
            'success': True,
            'date': date,
            'cost': {
                'normal': cost.get('normal_cost', 0),
                'easy': cost.get('easy_cost', 0),
                'total': total_cost
            },
            'impression': {
                'normal': cost.get('normal_impression', 0),
                'easy': cost.get('easy_impression', 0),
                'total': total_impression
            },
            'click': {
                'normal': cost.get('normal_click', 0),
                'easy': cost.get('easy_click', 0),
                'total': total_click
            },
            'metrics': {
                'ctr': round(ctr, 2),
                'cpc': round(cpc, 2),
                'cpm': round(total_cost / total_impression * 1000, 2) if total_impression > 0 else 0
            },
            'summary': {
                'campaign_count': campaign_count,
                'creative_count': creative_count,
                'note_count': note_count
            }
        }
    
    def generate_weekly_report(self, end_date=None):
        """生成周报
        
        Args:
            end_date: 结束日期，默认昨天
        
        Returns:
            周报数据
        """
        if end_date is None:
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = end_dt - timedelta(days=6)
        start_date = start_dt.strftime('%Y-%m-%d')
        
        # 获取每天的数据
        daily_reports = []
        current_dt = start_dt
        while current_dt <= end_dt:
            date_str = current_dt.strftime('%Y-%m-%d')
            daily = self.generate_daily_report(date_str)
            daily_reports.append(daily)
            current_dt += timedelta(days=1)
        
        # 汇总数据
        total_cost = sum(r['cost']['total'] for r in daily_reports)
        total_impression = sum(r['impression']['total'] for r in daily_reports)
        total_click = sum(r['click']['total'] for r in daily_reports)
        active_days = sum(1 for r in daily_reports if r['cost']['total'] > 0)
        
        return {
            'success': True,
            'start_date': start_date,
            'end_date': end_date,
            'daily_reports': daily_reports,
            'summary': {
                'total_cost': round(total_cost, 2),
                'total_impression': total_impression,
                'total_click': total_click,
                'active_days': active_days,
                'daily_avg_cost': round(total_cost / 7, 2),
                'ctr': round(total_click / total_impression * 100, 2) if total_impression > 0 else 0,
                'cpc': round(total_cost / total_click, 2) if total_click > 0 else 0
            }
        }
    
    def format_daily_report(self, report):
        """格式化日报
        
        Args:
            report: 日报数据
        
        Returns:
            格式化的日报文本
        """
        if not report.get('success'):
            return f"❌ 日报生成失败: {report.get('message', '')}"
        
        lines = [
            f"📊 聚光投放日报 {report['date']}",
            "=" * 40,
            "",
            "【消耗数据】",
            f"  标准投放: {report['cost']['normal']:.2f}元",
            f"  简单投放: {report['cost']['easy']:.2f}元",
            f"  总消耗: {report['cost']['total']:.2f}元",
            "",
            "【曝光数据】",
            f"  标准投放: {report['impression']['normal']}",
            f"  简单投放: {report['impression']['easy']}",
            f"  总曝光: {report['impression']['total']}",
            "",
            "【点击数据】",
            f"  标准投放: {report['click']['normal']}",
            f"  简单投放: {report['click']['easy']}",
            f"  总点击: {report['click']['total']}",
            "",
            "【效率指标】",
            f"  CTR: {report['metrics']['ctr']}%",
            f"  CPC: {report['metrics']['cpc']}元",
            f"  CPM: {report['metrics']['cpm']}元",
            "",
            "【账户概况】",
            f"  计划数量: {report['summary']['campaign_count']}",
            f"  创意数量: {report['summary']['creative_count']}",
            f"  笔记数量: {report['summary']['note_count']}",
        ]
        
        return "\n".join(lines)
    
    def format_weekly_report(self, report):
        """格式化周报
        
        Args:
            report: 周报数据
        
        Returns:
            格式化的周报文本
        """
        if not report.get('success'):
            return f"❌ 周报生成失败: {report.get('message', '')}"
        
        lines = [
            f"📊 聚光投放周报 {report['start_date']} ~ {report['end_date']}",
            "=" * 40,
            "",
            "【消耗趋势】",
        ]
        
        for daily in report['daily_reports']:
            date = daily['date']
            cost = daily['cost']['total']
            lines.append(f"  {date}: {cost:.2f}元")
        
        lines.extend([
            "",
            "【汇总数据】",
            f"  总消耗: {report['summary']['total_cost']:.2f}元",
            f"  日均消耗: {report['summary']['daily_avg_cost']:.2f}元",
            f"  总曝光: {report['summary']['total_impression']}",
            f"  总点击: {report['summary']['total_click']}",
            f"  有效天数: {report['summary']['active_days']}天",
            "",
            "【效率指标】",
            f"  CTR: {report['summary']['ctr']}%",
            f"  CPC: {report['summary']['cpc']}元",
        ])
        
        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    optimizer = SmartOptimizer()
    
    print("=" * 50)
    print("🔍 测试智能优化器")
    print("=" * 50)
    
    # 1. 测试数据预警
    print("\n1. 数据预警测试")
    print("-" * 30)
    optimizer.add_alert_rule('cost_high', 200, 'notify')
    optimizer.add_alert_rule('ctr_low', 5, 'notify')
    optimizer.add_alert_rule('cpc_high', 0.15, 'notify')
    
    alerts = optimizer.check_alerts()
    if alerts.get('success'):
        print(f"✅ 预警检查成功")
        print(f"   预警数量: {len(alerts.get('alerts', []))}")
        for alert in alerts.get('alerts', []):
            print(f"   - {alert['message']}")
    else:
        print(f"❌ 预警检查失败: {alerts.get('message', '')}")
    
    # 2. 测试日报生成
    print("\n2. 日报生成测试")
    print("-" * 30)
    daily = optimizer.generate_daily_report()
    if daily.get('success'):
        print(f"✅ 日报生成成功")
        print(optimizer.format_daily_report(daily))
    else:
        print(f"❌ 日报生成失败: {daily.get('message', '')}")
    
    # 3. 测试周报生成
    print("\n3. 周报生成测试")
    print("-" * 30)
    weekly = optimizer.generate_weekly_report()
    if weekly.get('success'):
        print(f"✅ 周报生成成功")
        print(optimizer.format_weekly_report(weekly))
    else:
        print(f"❌ 周报生成失败: {weekly.get('message', '')}")
