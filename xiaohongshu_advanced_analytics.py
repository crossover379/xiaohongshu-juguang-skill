#!/usr/bin/env python3
"""
小红书聚光AI投手高级分析模块
核心能力：预测分析、A/B测试、归因分析、预算分配
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict


class AdvancedAnalytics:
    """高级分析模块"""
    
    def __init__(self, sdk, data_dir="/root/.openclaw/workspace/skills/xiaohongshu-juguang-ai/analytics_data"):
        self.sdk = sdk
        self.data_dir = data_dir
        self.ab_test_file = os.path.join(data_dir, "ab_tests.json")
        self.attribution_file = os.path.join(data_dir, "attribution_data.json")
        self.budget_allocation_file = os.path.join(data_dir, "budget_allocation.json")
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载数据
        self.ab_tests = self._load_json(self.ab_test_file, {'tests': [], 'results': []})
        self.attribution_data = self._load_json(self.attribution_file, {'conversions': [], 'touchpoints': []})
        self.budget_allocation = self._load_json(self.budget_allocation_file, {'allocations': [], 'history': []})
    
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
    
    # ==================== 预测分析功能 ====================
    
    def predict_campaign_performance(self, campaign_id, days_ahead=7):
        """预测计划未来表现
        
        Args:
            campaign_id: 计划ID
            days_ahead: 预测天数
        
        Returns:
            预测结果
        """
        # 获取近14天历史数据
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('campaign', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取历史数据失败'}
        
        # 找到对应计划数据
        data_list = report.get('data', {}).get('data_list', [])
        campaign_data = [d for d in data_list if str(d.get('campaign_id')) == str(campaign_id)]
        
        if len(campaign_data) < 3:
            return {'success': False, 'message': '历史数据不足，至少需要3天数据'}
        
        # 提取历史指标
        fees = [float(d.get('fee', 0)) for d in campaign_data]
        impressions = [int(d.get('impression', 0)) for d in campaign_data]
        clicks = [int(d.get('click', 0)) for d in campaign_data]
        
        # 计算趋势
        avg_fee = sum(fees) / len(fees)
        avg_impression = sum(impressions) / len(impressions)
        avg_click = sum(clicks) / len(clicks)
        
        # 简单线性预测
        if len(fees) >= 3:
            recent_avg_fee = sum(fees[-3:]) / 3
            trend_fee = (fees[-1] - fees[-3]) / 2
            predicted_fee = recent_avg_fee + trend_fee * days_ahead
            
            recent_avg_impression = sum(impressions[-3:]) / 3
            trend_impression = (impressions[-1] - impressions[-3]) / 2
            predicted_impression = recent_avg_impression + trend_impression * days_ahead
            
            recent_avg_click = sum(clicks[-3:]) / 3
            trend_click = (clicks[-1] - clicks[-3]) / 2
            predicted_click = recent_avg_click + trend_click * days_ahead
        else:
            predicted_fee = avg_fee * days_ahead
            predicted_impression = avg_impression * days_ahead
            predicted_click = avg_click * days_ahead
        
        # 计算预测指标
        predicted_ctr = (predicted_click / predicted_impression * 100) if predicted_impression > 0 else 0
        predicted_cpc = (predicted_fee / predicted_click) if predicted_click > 0 else 0
        
        # 计算置信度
        std_fee = (sum((f - avg_fee) ** 2 for f in fees) / len(fees)) ** 0.5
        confidence = max(0, min(100, 100 - (std_fee / avg_fee * 100) if avg_fee > 0 else 50))
        
        return {
            'success': True,
            'campaign_id': campaign_id,
            'days_ahead': days_ahead,
            'prediction': {
                'fee': round(predicted_fee, 2),
                'impression': int(predicted_impression),
                'click': int(predicted_click),
                'ctr': round(predicted_ctr, 2),
                'cpc': round(predicted_cpc, 2)
            },
            'trend': {
                'fee': '上涨' if trend_fee > 0 else '下降',
                'fee_pct': round(trend_fee / avg_fee * 100, 2) if avg_fee > 0 else 0,
                'impression': '上涨' if trend_impression > 0 else '下降',
                'impression_pct': round(trend_impression / avg_impression * 100, 2) if avg_impression > 0 else 0
            },
            'confidence': round(confidence, 2),
            'historical_avg': {
                'fee': round(avg_fee, 2),
                'impression': int(avg_impression),
                'click': int(avg_click)
            }
        }
    
    def predict_keyword_performance(self, keyword, days_ahead=7):
        """预测关键词未来表现
        
        Args:
            keyword: 关键词
            days_ahead: 预测天数
        
        Returns:
            预测结果
        """
        # 获取关键词推荐数据
        recommend = self.sdk.keyword_recommend(keyword)
        if not recommend.get('success'):
            return {'success': False, 'message': '获取关键词数据失败'}
        
        word_list = recommend['data'].get('word_list', [])
        if not word_list:
            return {'success': False, 'message': '未找到关键词数据'}
        
        # 找到匹配的关键词
        keyword_data = None
        for w in word_list:
            if w.get('keyword') == keyword:
                keyword_data = w
                break
        
        if not keyword_data:
            keyword_data = word_list[0]
        
        # 提取数据
        month_pv = int(keyword_data.get('monthpv', 0))
        bid = int(keyword_data.get('bid', 0)) / 100  # 转换为元
        
        # 预测
        daily_pv = month_pv / 30
        predicted_impression = daily_pv * days_ahead * 0.1  # 假设10%的曝光率
        predicted_click = predicted_impression * 0.05  # 假设5%的点击率
        predicted_fee = predicted_click * bid
        
        return {
            'success': True,
            'keyword': keyword,
            'days_ahead': days_ahead,
            'prediction': {
                'impression': int(predicted_impression),
                'click': int(predicted_click),
                'fee': round(predicted_fee, 2),
                'cpc': round(bid, 2)
            },
            'market_data': {
                'month_pv': month_pv,
                'suggested_bid': round(bid, 2)
            }
        }
    
    # ==================== A/B测试功能 ====================
    
    def create_ab_test(self, name, test_type, variants, metric='ctr'):
        """创建A/B测试
        
        Args:
            name: 测试名称
            test_type: 测试类型（campaign/unit/creative/keyword）
            variants: 变体列表
            metric: 评估指标（ctr/cpc/conversion）
        
        Returns:
            创建结果
        """
        test_id = f"ab_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        test = {
            'id': test_id,
            'name': name,
            'type': test_type,
            'variants': variants,
            'metric': metric,
            'status': 'created',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'started_at': None,
            'ended_at': None,
            'results': {}
        }
        
        self.ab_tests['tests'].append(test)
        self._save_json(self.ab_test_file, self.ab_tests)
        
        return {
            'success': True,
            'test_id': test_id,
            'name': name,
            'variants': variants,
            'message': f'A/B测试"{name}"创建成功'
        }
    
    def start_ab_test(self, test_id):
        """启动A/B测试
        
        Args:
            test_id: 测试ID
        
        Returns:
            启动结果
        """
        # 找到测试
        test = None
        for t in self.ab_tests['tests']:
            if t['id'] == test_id:
                test = t
                break
        
        if not test:
            return {'success': False, 'message': f'未找到测试: {test_id}'}
        
        # 更新状态
        test['status'] = 'running'
        test['started_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 根据测试类型执行
        if test['type'] == 'campaign':
            # 创建测试计划
            for variant in test['variants']:
                variant_name = variant.get('name', '')
                variant_config = variant.get('config', {})
                
                # 创建计划
                result = self.sdk.create_campaign_with_creatives(
                    campaign_name=f"AB测试_{test['name']}_{variant_name}",
                    **variant_config
                )
                variant['campaign_id'] = result.get('data', {}).get('campaign_id') if result.get('success') else None
                variant['result'] = result
        
        elif test['type'] == 'keyword':
            # 创建关键词测试
            for variant in test['variants']:
                variant_name = variant.get('name', '')
                variant_keywords = variant.get('keywords', [])
                variant_unit_id = variant.get('unit_id')
                
                if variant_unit_id:
                    result = self.sdk.add_unit_keyword(variant_unit_id, variant_keywords)
                    variant['result'] = result
        
        self._save_json(self.ab_test_file, self.ab_tests)
        
        return {
            'success': True,
            'test_id': test_id,
            'status': 'running',
            'message': f'A/B测试"{test["name"]}"已启动'
        }
    
    def analyze_ab_test(self, test_id, days=7):
        """分析A/B测试结果
        
        Args:
            test_id: 测试ID
            days: 分析天数
        
        Returns:
            分析结果
        """
        # 找到测试
        test = None
        for t in self.ab_tests['tests']:
            if t['id'] == test_id:
                test = t
                break
        
        if not test:
            return {'success': False, 'message': f'未找到测试: {test_id}'}
        
        if test['status'] != 'running':
            return {'success': False, 'message': f'测试未运行: {test["status"]}'}
        
        # 获取数据
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        results = {}
        
        for variant in test['variants']:
            variant_name = variant.get('name', '')
            
            if test['type'] == 'campaign':
                campaign_id = variant.get('campaign_id')
                if campaign_id:
                    report = self.sdk.get_offline_report('campaign', start_date, end_date)
                    if report.get('success'):
                        data_list = report.get('data', {}).get('data_list', [])
                        campaign_data = [d for d in data_list if str(d.get('campaign_id')) == str(campaign_id)]
                        
                        if campaign_data:
                            total_fee = sum(float(d.get('fee', 0)) for d in campaign_data)
                            total_impression = sum(int(d.get('impression', 0)) for d in campaign_data)
                            total_click = sum(int(d.get('click', 0)) for d in campaign_data)
                            
                            results[variant_name] = {
                                'fee': round(total_fee, 2),
                                'impression': total_impression,
                                'click': total_click,
                                'ctr': round(total_click / total_impression * 100, 2) if total_impression > 0 else 0,
                                'cpc': round(total_fee / total_click, 2) if total_click > 0 else 0
                            }
            
            elif test['type'] == 'creative':
                creative_id = variant.get('creative_id')
                if creative_id:
                    report = self.sdk.get_offline_report('creative', start_date, end_date)
                    if report.get('success'):
                        data_list = report.get('data', {}).get('data_list', [])
                        creative_data = [d for d in data_list if str(d.get('creative_id')) == str(creative_id)]
                        
                        if creative_data:
                            total_fee = sum(float(d.get('fee', 0)) for d in creative_data)
                            total_impression = sum(int(d.get('impression', 0)) for d in creative_data)
                            total_click = sum(int(d.get('click', 0)) for d in creative_data)
                            
                            results[variant_name] = {
                                'fee': round(total_fee, 2),
                                'impression': total_impression,
                                'click': total_click,
                                'ctr': round(total_click / total_impression * 100, 2) if total_impression > 0 else 0,
                                'cpc': round(total_fee / total_click, 2) if total_click > 0 else 0
                            }
        
        # 找出赢家
        metric = test['metric']
        winner = None
        best_value = None
        
        for variant_name, data in results.items():
            value = data.get(metric, 0)
            if best_value is None:
                best_value = value
                winner = variant_name
            elif metric == 'ctr' and value > best_value:
                best_value = value
                winner = variant_name
            elif metric == 'cpc' and value < best_value:
                best_value = value
                winner = variant_name
        
        # 保存结果
        test['results'] = results
        test['winner'] = winner
        self._save_json(self.ab_test_file, self.ab_tests)
        
        return {
            'success': True,
            'test_id': test_id,
            'name': test['name'],
            'metric': metric,
            'results': results,
            'winner': winner,
            'winner_value': best_value
        }
    
    def end_ab_test(self, test_id):
        """结束A/B测试
        
        Args:
            test_id: 测试ID
        
        Returns:
            结束结果
        """
        # 找到测试
        test = None
        for t in self.ab_tests['tests']:
            if t['id'] == test_id:
                test = t
                break
        
        if not test:
            return {'success': False, 'message': f'未找到测试: {test_id}'}
        
        # 分析结果
        analysis = self.analyze_ab_test(test_id)
        
        # 更新状态
        test['status'] = 'completed'
        test['ended_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self._save_json(self.ab_test_file, self.ab_tests)
        
        return {
            'success': True,
            'test_id': test_id,
            'name': test['name'],
            'winner': analysis.get('winner'),
            'results': analysis.get('results'),
            'message': f'A/B测试"{test["name"]}"已结束'
        }
    
    # ==================== 归因分析功能 ====================
    
    def track_conversion(self, conversion_type, conversion_value, touchpoints):
        """追踪转化
        
        Args:
            conversion_type: 转化类型（click/impression/lead）
            conversion_value: 转化价值
            touchpoints: 触点列表
        
        Returns:
            追踪结果
        """
        conversion_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conversion = {
            'id': conversion_id,
            'type': conversion_type,
            'value': conversion_value,
            'touchpoints': touchpoints,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.attribution_data['conversions'].append(conversion)
        self._save_json(self.attribution_file, self.attribution_data)
        
        return {
            'success': True,
            'conversion_id': conversion_id,
            'message': f'转化{conversion_id}追踪成功'
        }
    
    def analyze_attribution(self, days=30, model='last_click'):
        """分析归因
        
        Args:
            days: 分析天数
            model: 归因模型（last_click/first_click/linear/time_decay）
        
        Returns:
            归因分析结果
        """
        # 获取报表数据
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 获取创意报表
        creative_report = self.sdk.get_offline_report('creative', start_date, end_date)
        if not creative_report.get('success'):
            return {'success': False, 'message': '获取创意报表失败'}
        
        # 分析归因
        attribution = {}
        data_list = creative_report.get('data', {}).get('data_list', [])
        
        for data in data_list:
            creative_id = str(data.get('creative_id', ''))
            note_id = data.get('note_id', '')
            fee = float(data.get('fee', 0))
            impression = int(data.get('impression', 0))
            click = int(data.get('click', 0))
            
            if creative_id not in attribution:
                attribution[creative_id] = {
                    'note_id': note_id,
                    'fee': 0,
                    'impression': 0,
                    'click': 0,
                    'conversions': 0
                }
            
            attribution[creative_id]['fee'] += fee
            attribution[creative_id]['impression'] += impression
            attribution[creative_id]['click'] += click
        
        # 计算归因权重
        total_click = sum(a['click'] for a in attribution.values())
        total_impression = sum(a['impression'] for a in attribution.values())
        
        for creative_id, data in attribution.items():
            if model == 'last_click':
                # 最后点击归因
                data['attribution_weight'] = data['click'] / total_click if total_click > 0 else 0
            elif model == 'first_click':
                # 首次点击归因
                data['attribution_weight'] = data['impression'] / total_impression if total_impression > 0 else 0
            elif model == 'linear':
                # 线性归因
                data['attribution_weight'] = 1 / len(attribution) if attribution else 0
            elif model == 'time_decay':
                # 时间衰减归因
                data['attribution_weight'] = data['fee'] / sum(a['fee'] for a in attribution.values())
            
            data['attributed_value'] = data['fee'] * data['attribution_weight']
        
        return {
            'success': True,
            'model': model,
            'period': f'{start_date} ~ {end_date}',
            'attribution': attribution,
            'summary': {
                'total_creatives': len(attribution),
                'total_fee': sum(a['fee'] for a in attribution.values()),
                'total_click': total_click,
                'total_impression': total_impression
            }
        }
    
    def get_creative_contribution(self, days=30):
        """获取创意贡献度
        
        Args:
            days: 分析天数
        
        Returns:
            贡献度分析
        """
        # 获取创意报表
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        creative_report = self.sdk.get_offline_report('creative', start_date, end_date)
        if not creative_report.get('success'):
            return {'success': False, 'message': '获取创意报表失败'}
        
        # 分析贡献度
        contributions = []
        data_list = creative_report.get('data', {}).get('data_list', [])
        
        for data in data_list:
            creative_id = str(data.get('creative_id', ''))
            note_id = data.get('note_id', '')
            fee = float(data.get('fee', 0))
            impression = int(data.get('impression', 0))
            click = int(data.get('click', 0))
            ctr = (click / impression * 100) if impression > 0 else 0
            cpc = (fee / click) if click > 0 else 0
            
            # 计算贡献度得分
            score = 0
            if fee > 0:
                score += 30  # 有消耗
            if ctr > 10:
                score += 30  # CTR优秀
            if cpc < 0.1:
                score += 20  # CPC低
            if click > 10:
                score += 20  # 有转化
            
            contributions.append({
                'creative_id': creative_id,
                'note_id': note_id,
                'fee': round(fee, 2),
                'impression': impression,
                'click': click,
                'ctr': round(ctr, 2),
                'cpc': round(cpc, 2),
                'score': score,
                'level': '优秀' if score >= 80 else '良好' if score >= 60 else '一般' if score >= 40 else '差'
            })
        
        # 排序
        contributions.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'success': True,
            'period': f'{start_date} ~ {end_date}',
            'contributions': contributions,
            'summary': {
                'total_creatives': len(contributions),
                'excellent': len([c for c in contributions if c['level'] == '优秀']),
                'good': len([c for c in contributions if c['level'] == '良好']),
                'normal': len([c for c in contributions if c['level'] == '一般']),
                'poor': len([c for c in contributions if c['level'] == '差'])
            }
        }
    
    # ==================== 预算分配功能 ====================
    
    def optimize_budget_allocation(self, total_budget, strategy='performance'):
        """优化预算分配
        
        Args:
            total_budget: 总预算（元）
            strategy: 分配策略（performance/balanced/aggressive）
        
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
        
        elif strategy == 'aggressive':
            # 激进分配（集中预算到高效计划）
            high_performance = {k: v for k, v in campaign_performance.items() if v['score'] >= 60}
            
            if high_performance:
                allocation_per_campaign = total_budget / len(high_performance)
                
                for campaign_id, performance in campaign_performance.items():
                    if campaign_id in high_performance:
                        allocations.append({
                            'campaign_id': campaign_id,
                            'allocation': round(allocation_per_campaign, 2),
                            'performance': performance,
                            'reason': '高效计划，集中预算'
                        })
                    else:
                        allocations.append({
                            'campaign_id': campaign_id,
                            'allocation': 0,
                            'performance': performance,
                            'reason': '低效计划，暂停预算'
                        })
            else:
                # 没有高效计划，平均分配
                num_campaigns = len(campaign_performance)
                allocation_per_campaign = total_budget / num_campaigns if num_campaigns > 0 else 0
                
                for campaign_id, performance in campaign_performance.items():
                    allocations.append({
                        'campaign_id': campaign_id,
                        'allocation': round(allocation_per_campaign, 2),
                        'performance': performance,
                        'reason': '无高效计划，平均分配'
                    })
        
        # 排序
        allocations.sort(key=lambda x: x['allocation'], reverse=True)
        
        # 保存分配记录
        self.budget_allocation['allocations'].append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_budget': total_budget,
            'strategy': strategy,
            'allocations': allocations
        })
        self._save_json(self.budget_allocation_file, self.budget_allocation)
        
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
    
    def apply_budget_allocation(self, allocations):
        """应用预算分配
        
        Args:
            allocations: 分配列表
        
        Returns:
            应用结果
        """
        results = []
        
        for allocation in allocations:
            campaign_id = allocation.get('campaign_id')
            budget = allocation.get('allocation', 0)
            
            if budget > 0:
                # 更新预算
                result = self.sdk.update_campaign(
                    campaign_id=campaign_id,
                    limit_day_budget=1,
                    origin_campaign_day_budget=int(budget * 100)
                )
                results.append({
                    'campaign_id': campaign_id,
                    'budget': budget,
                    'result': result
                })
            else:
                # 暂停计划
                result = self.sdk.update_campaign_status([campaign_id], 2)
                results.append({
                    'campaign_id': campaign_id,
                    'budget': 0,
                    'action': 'pause',
                    'result': result
                })
        
        return {
            'success': True,
            'total': len(results),
            'results': results
        }
    
    def get_budget_recommendation(self, target_cpa=None):
        """获取预算建议
        
        Args:
            target_cpa: 目标CPA（可选）
        
        Returns:
            预算建议
        """
        # 获取账户数据
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('account', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取账户数据失败'}
        
        data_list = report.get('data', {}).get('data_list', [])
        if not data_list:
            return {'success': False, 'message': '无历史数据'}
        
        # 计算平均指标
        total_fee = sum(float(d.get('fee', 0)) for d in data_list)
        total_click = sum(int(d.get('click', 0)) for d in data_list)
        total_impression = sum(int(d.get('impression', 0)) for d in data_list)
        
        avg_daily_fee = total_fee / len(data_list)
        avg_ctr = (total_click / total_impression * 100) if total_impression > 0 else 0
        avg_cpc = (total_fee / total_click) if total_click > 0 else 0
        
        # 计算建议
        recommendations = []
        
        if target_cpa:
            # 根据目标CPA计算
            target_clicks = total_fee / target_cpa if target_cpa > 0 else 0
            recommended_budget = target_clicks * avg_cpc
            recommendations.append({
                'type': 'target_cpa',
                'target_cpa': target_cpa,
                'recommended_budget': round(recommended_budget, 2),
                'expected_clicks': int(target_clicks)
            })
        
        # 基于历史表现的建议
        recommendations.append({
            'type': 'performance',
            'current_avg_daily': round(avg_daily_fee, 2),
            'suggested_min': round(avg_daily_fee * 0.8, 2),
            'suggested_max': round(avg_daily_fee * 1.5, 2),
            'reason': f'基于近7天日均消耗{avg_daily_fee:.2f}元'
        })
        
        return {
            'success': True,
            'recommendations': recommendations,
            'current_metrics': {
                'avg_daily_fee': round(avg_daily_fee, 2),
                'avg_ctr': round(avg_ctr, 2),
                'avg_cpc': round(avg_cpc, 2)
            }
        }


# 测试代码
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
    
    sdk = XiaohongshuJuguangSDK()
    analytics = AdvancedAnalytics(sdk)
    
    print("=" * 50)
    print("📊 测试高级分析模块")
    print("=" * 50)
    
    # 1. 测试A/B测试
    print("\n1. A/B测试创建")
    print("-" * 30)
    test_result = analytics.create_ab_test(
        name="创意文案测试",
        test_type="creative",
        variants=[
            {'name': '版本A', 'creative_id': '123'},
            {'name': '版本B', 'creative_id': '456'}
        ],
        metric='ctr'
    )
    if test_result.get('success'):
        print(f"✅ {test_result['message']}")
    else:
        print(f"❌ 创建失败: {test_result.get('message', '')}")
    
    # 2. 测试归因分析
    print("\n2. 归因分析测试")
    print("-" * 30)
    attribution = analytics.analyze_attribution(days=7, model='last_click')
    if attribution.get('success'):
        print(f"✅ 归因分析成功")
        print(f"   分析模型: {attribution['model']}")
        print(f"   创意数量: {attribution['summary']['total_creatives']}")
    else:
        print(f"❌ 归因分析失败: {attribution.get('message', '')}")
    
    # 3. 测试预算分配
    print("\n3. 预算分配测试")
    print("-" * 30)
    allocation = analytics.optimize_budget_allocation(
        total_budget=200,
        strategy='performance'
    )
    if allocation.get('success'):
        print(f"✅ 预算分配成功")
        print(f"   总预算: {allocation['total_budget']}元")
        print(f"   分配计划: {allocation['summary']['total_campaigns']}个")
        print(f"   暂停计划: {allocation['summary']['paused']}个")
    else:
        print(f"❌ 预算分配失败: {allocation.get('message', '')}")
    
    # 4. 测试预算建议
    print("\n4. 预算建议测试")
    print("-" * 30)
    recommendation = analytics.get_budget_recommendation(target_cpa=5)
    if recommendation.get('success'):
        print(f"✅ 预算建议成功")
        for rec in recommendation['recommendations']:
            print(f"   - {rec['type']}: {rec.get('recommended_budget', rec.get('suggested_max', ''))}元")
    else:
        print(f"❌ 预算建议失败: {recommendation.get('message', '')}")
