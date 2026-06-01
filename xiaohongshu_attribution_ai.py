#!/usr/bin/env python3
"""
小红书聚光AI投手 - 归因分析与创意A/B测试模块
核心能力：数据驱动归因、创意A/B测试、受众分析
"""
import json
import os
import math
import random
from datetime import datetime, timedelta
from collections import defaultdict


class AttributionAI:
    """归因分析与创意A/B测试"""
    
    def __init__(self, sdk, data_dir="/root/.openclaw/workspace/skills/xiaohongshu-juguang-ai/attribution_data"):
        self.sdk = sdk
        self.data_dir = data_dir
        self.attribution_file = os.path.join(data_dir, "attribution.json")
        self.ab_test_file = os.path.join(data_dir, "creative_ab_tests.json")
        self.audience_file = os.path.join(data_dir, "audience.json")
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载数据
        self.attribution_data = self._load_json(self.attribution_file, {'models': {}, 'history': []})
        self.ab_tests = self._load_json(self.ab_test_file, {'tests': [], 'results': []})
        self.audience_data = self._load_json(self.audience_file, {'segments': [], 'history': []})
    
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
    
    # ==================== 数据驱动归因 ====================
    
    def data_driven_attribution(self, days=30):
        """数据驱动归因
        
        Args:
            days: 分析天数
        
        Returns:
            归因分析结果
        """
        # 获取创意报表
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('creative', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取创意报表失败'}
        
        # 分析创意贡献
        creative_contributions = {}
        data_list = report.get('data', {}).get('data_list', [])
        
        for data in data_list:
            creative_id = str(data.get('creative_id', ''))
            note_id = data.get('note_id', '')
            fee = float(data.get('fee', 0))
            impression = int(data.get('impression', 0))
            click = int(data.get('click', 0))
            ctr = (click / impression * 100) if impression > 0 else 0
            cpc = (fee / click) if click > 0 else 0
            
            # 计算贡献度
            contribution_score = 0
            
            # 曝光贡献（权重30%）
            if impression > 0:
                contribution_score += 30 * min(1, impression / 1000)
            
            # 点击贡献（权重40%）
            if click > 0:
                contribution_score += 40 * min(1, click / 100)
            
            # 效率贡献（权重30%）
            if ctr > 10:
                contribution_score += 15
            if cpc < 0.1:
                contribution_score += 15
            
            creative_contributions[creative_id] = {
                'note_id': note_id,
                'fee': round(fee, 2),
                'impression': impression,
                'click': click,
                'ctr': round(ctr, 2),
                'cpc': round(cpc, 2),
                'contribution_score': round(contribution_score, 2),
                'contribution_level': '高' if contribution_score >= 60 else '中' if contribution_score >= 30 else '低'
            }
        
        # 计算归因权重
        total_score = sum(c['contribution_score'] for c in creative_contributions.values())
        
        for creative_id, data in creative_contributions.items():
            if total_score > 0:
                data['attribution_weight'] = round(data['contribution_score'] / total_score, 4)
            else:
                data['attribution_weight'] = 0
            
            data['attributed_value'] = round(data['fee'] * data['attribution_weight'], 2)
        
        # 排序
        sorted_creatives = sorted(creative_contributions.items(), 
                                 key=lambda x: x[1]['contribution_score'], 
                                 reverse=True)
        
        # 保存归因数据
        self.attribution_data['history'].append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'model': 'data_driven',
            'contributions': dict(sorted_creatives[:10]),  # 保存前10个
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # 只保留最近30天
        if len(self.attribution_data['history']) > 30:
            self.attribution_data['history'] = self.attribution_data['history'][-30:]
        
        self._save_json(self.attribution_file, self.attribution_data)
        
        return {
            'success': True,
            'model': 'data_driven',
            'period': f'{start_date} ~ {end_date}',
            'contributions': dict(sorted_creatives),
            'summary': {
                'total_creatives': len(creative_contributions),
                'high_contribution': len([c for c in creative_contributions.values() if c['contribution_level'] == '高']),
                'medium_contribution': len([c for c in creative_contributions.values() if c['contribution_level'] == '中']),
                'low_contribution': len([c for c in creative_contributions.values() if c['contribution_level'] == '低']),
                'total_fee': sum(c['fee'] for c in creative_contributions.values()),
                'total_click': sum(c['click'] for c in creative_contributions.values())
            }
        }
    
    def shapley_attribution(self, days=30):
        """Shapley值归因
        
        Args:
            days: 分析天数
        
        Returns:
            Shapley归因结果
        """
        # 获取创意报表
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('creative', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取创意报表失败'}
        
        # 分析创意数据
        creative_data = {}
        data_list = report.get('data', {}).get('data_list', [])
        
        for data in data_list:
            creative_id = str(data.get('creative_id', ''))
            fee = float(data.get('fee', 0))
            click = int(data.get('click', 0))
            impression = int(data.get('impression', 0))
            ctr = (click / impression * 100) if impression > 0 else 0
            
            creative_data[creative_id] = {
                'fee': fee,
                'click': click,
                'impression': impression,
                'ctr': ctr
            }
        
        # 计算Shapley值（简化版本）
        # Shapley值 = 边际贡献的加权平均
        shapley_values = {}
        
        for creative_id, data in creative_data.items():
            # 计算边际贡献
            # 简化：用CTR和点击率作为贡献指标
            marginal_contribution = data['ctr'] * 0.4 + (data['click'] / max(1, data['impression'])) * 100 * 0.6
            
            shapley_values[creative_id] = {
                'fee': round(data['fee'], 2),
                'click': data['click'],
                'impression': data['impression'],
                'ctr': round(data['ctr'], 2),
                'shapley_value': round(marginal_contribution, 4),
                'attribution_pct': 0  # 后续计算
            }
        
        # 计算归因百分比
        total_shapley = sum(s['shapley_value'] for s in shapley_values.values())
        
        for creative_id, data in shapley_values.items():
            if total_shapley > 0:
                data['attribution_pct'] = round(data['shapley_value'] / total_shapley * 100, 2)
        
        # 排序
        sorted_shapley = sorted(shapley_values.items(), 
                               key=lambda x: x[1]['shapley_value'], 
                               reverse=True)
        
        return {
            'success': True,
            'model': 'shapley',
            'period': f'{start_date} ~ {end_date}',
            'shapley_values': dict(sorted_shapley),
            'summary': {
                'total_creatives': len(shapley_values),
                'total_shapley': round(total_shapley, 4),
                'top_creative': sorted_shapley[0][0] if sorted_shapley else None
            }
        }
    
    # ==================== 创意A/B测试 ====================
    
    def create_creative_ab_test(self, name, variants):
        """创建创意A/B测试
        
        Args:
            name: 测试名称
            variants: 变体列表
        
        Returns:
            创建结果
        """
        test_id = f"creative_ab_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        test = {
            'id': test_id,
            'name': name,
            'variants': variants,
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
            'message': f'创意A/B测试"{name}"创建成功'
        }
    
    def start_creative_ab_test(self, test_id, campaign_id, budget_per_variant=100):
        """启动创意A/B测试
        
        Args:
            test_id: 测试ID
            campaign_id: 计划ID
            budget_per_variant: 每个变体预算
        
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
        test['campaign_id'] = campaign_id
        test['budget_per_variant'] = budget_per_variant
        
        # 为每个变体创建创意
        for variant in test['variants']:
            variant_name = variant.get('name', '')
            note_id = variant.get('note_id')
            
            if note_id:
                # 创建创意
                result = self.sdk.add_creative(
                    campaign_id=campaign_id,
                    note_id=note_id,
                    creative_name=f"AB测试_{test['name']}_{variant_name}"
                )
                variant['creative_id'] = result.get('data', {}).get('creative_id') if result.get('success') else None
                variant['result'] = result
        
        self._save_json(self.ab_test_file, self.ab_tests)
        
        return {
            'success': True,
            'test_id': test_id,
            'status': 'running',
            'message': f'创意A/B测试"{test["name"]}"已启动'
        }
    
    def analyze_creative_ab_test(self, test_id, days=7):
        """分析创意A/B测试结果
        
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
        
        report = self.sdk.get_offline_report('creative', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取创意报表失败'}
        
        # 分析每个变体
        results = {}
        data_list = report.get('data', {}).get('data_list', [])
        
        for variant in test['variants']:
            variant_name = variant.get('name', '')
            creative_id = variant.get('creative_id')
            
            if creative_id:
                # 找到对应创意数据
                creative_data = None
                for d in data_list:
                    if str(d.get('creative_id')) == str(creative_id):
                        creative_data = d
                        break
                
                if creative_data:
                    fee = float(creative_data.get('fee', 0))
                    impression = int(creative_data.get('impression', 0))
                    click = int(creative_data.get('click', 0))
                    ctr = (click / impression * 100) if impression > 0 else 0
                    cpc = (fee / click) if click > 0 else 0
                    
                    results[variant_name] = {
                        'creative_id': creative_id,
                        'fee': round(fee, 2),
                        'impression': impression,
                        'click': click,
                        'ctr': round(ctr, 2),
                        'cpc': round(cpc, 2)
                    }
        
        # 找出赢家（基于CTR）
        winner = None
        best_ctr = -1
        
        for variant_name, data in results.items():
            if data['ctr'] > best_ctr:
                best_ctr = data['ctr']
                winner = variant_name
        
        # 计算统计显著性
        significance = self._calculate_significance(results)
        
        # 保存结果
        test['results'] = results
        test['winner'] = winner
        test['significance'] = significance
        
        self._save_json(self.ab_test_file, self.ab_tests)
        
        return {
            'success': True,
            'test_id': test_id,
            'name': test['name'],
            'results': results,
            'winner': winner,
            'winner_ctr': best_ctr,
            'significance': significance
        }
    
    def _calculate_significance(self, results):
        """计算统计显著性
        
        Args:
            results: 测试结果
        
        Returns:
            显著性结果
        """
        if len(results) < 2:
            return {'significant': False, 'message': '变体数量不足'}
        
        # 提取CTR数据
        ctrs = [data['ctr'] for data in results.values()]
        
        # 计算均值和标准差
        avg_ctr = sum(ctrs) / len(ctrs)
        std_ctr = math.sqrt(sum((c - avg_ctr) ** 2 for c in ctrs) / len(ctrs))
        
        # 计算变异系数
        cv = std_ctr / avg_ctr if avg_ctr > 0 else 0
        
        # 判断显著性
        significant = cv > 0.1  # 变异系数大于10%认为显著
        
        return {
            'significant': significant,
            'cv': round(cv, 4),
            'avg_ctr': round(avg_ctr, 2),
            'std_ctr': round(std_ctr, 2),
            'message': f'{"显著" if significant else "不显著"}（变异系数: {cv:.4f}）'
        }
    
    def end_creative_ab_test(self, test_id):
        """结束创意A/B测试
        
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
        analysis = self.analyze_creative_ab_test(test_id)
        
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
            'significance': analysis.get('significance'),
            'message': f'创意A/B测试"{test["name"]}"已结束'
        }
    
    # ==================== 受众分析 ====================
    
    def analyze_audience_segments(self, days=30):
        """分析受众细分
        
        Args:
            days: 分析天数
        
        Returns:
            受众分析结果
        """
        # 获取定向模板
        templates = self.sdk.get_target_template_list()
        if not templates.get('success'):
            return {'success': False, 'message': '获取定向模板失败'}
        
        # 分析受众数据
        template_list = templates.get('data', []) or []
        
        # 统计受众特征
        audience_stats = {
            'age': defaultdict(int),
            'gender': defaultdict(int),
            'location': defaultdict(int),
            'interest': defaultdict(int)
        }
        
        for template in template_list:
            targeting = template.get('targeting', {})
            
            # 年龄统计
            if 'age' in targeting:
                age = targeting['age']
                if isinstance(age, dict):
                    min_age = age.get('min', 0)
                    max_age = age.get('max', 100)
                    age_range = f'{min_age}-{max_age}'
                else:
                    age_range = str(age)
                audience_stats['age'][age_range] += 1
            
            # 性别统计
            if 'gender' in targeting:
                gender = targeting['gender']
                audience_stats['gender'][gender] += 1
            
            # 地域统计
            if 'location' in targeting:
                location = targeting['location']
                if isinstance(location, list):
                    for loc in location:
                        audience_stats['location'][loc] += 1
                else:
                    audience_stats['location'][str(location)] += 1
            
            # 兴趣统计
            if 'interest' in targeting:
                interest = targeting['interest']
                if isinstance(interest, list):
                    for int_item in interest:
                        audience_stats['interest'][int_item] += 1
                else:
                    audience_stats['interest'][str(interest)] += 1
        
        # 转换为可序列化格式
        stats = {}
        for key, value in audience_stats.items():
            stats[key] = dict(value)
        
        # 生成推荐
        recommendations = []
        
        if stats['age']:
            most_common_age = max(stats['age'].items(), key=lambda x: x[1])
            recommendations.append({
                'type': 'age',
                'title': '年龄定向优化',
                'detail': f'最常用年龄定向: {most_common_age[0]}（{most_common_age[1]}次）',
                'action': '建议保持或微调'
            })
        
        if stats['interest']:
            most_common_interest = max(stats['interest'].items(), key=lambda x: x[1])
            recommendations.append({
                'type': 'interest',
                'title': '兴趣定向优化',
                'detail': f'最常用兴趣定向: {most_common_interest[0]}（{most_common_interest[1]}次）',
                'action': '建议保持或扩展相关兴趣'
            })
        
        return {
            'success': True,
            'days': days,
            'total_templates': len(template_list),
            'stats': stats,
            'recommendations': recommendations
        }
    
    def get_audience_insights(self, days=30):
        """获取受众洞察
        
        Args:
            days: 分析天数
        
        Returns:
            受众洞察
        """
        # 获取创意报表
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        report = self.sdk.get_offline_report('creative', start_date, end_date)
        if not report.get('success'):
            return {'success': False, 'message': '获取创意报表失败'}
        
        # 分析创意表现
        creative_performance = {}
        data_list = report.get('data', {}).get('data_list', [])
        
        for data in data_list:
            creative_id = str(data.get('creative_id', ''))
            fee = float(data.get('fee', 0))
            impression = int(data.get('impression', 0))
            click = int(data.get('click', 0))
            ctr = (click / impression * 100) if impression > 0 else 0
            
            creative_performance[creative_id] = {
                'fee': fee,
                'impression': impression,
                'click': click,
                'ctr': ctr
            }
        
        # 计算受众洞察
        insights = []
        
        # 找出高CTR创意
        high_ctr_creatives = [c_id for c_id, data in creative_performance.items() if data['ctr'] > 15]
        if high_ctr_creatives:
            insights.append({
                'type': 'high_ctr',
                'title': '高CTR创意',
                'detail': f'发现{len(high_ctr_creatives)}个高CTR创意（>15%）',
                'action': '建议分析这些创意的受众特征'
            })
        
        # 找出高曝光创意
        high_impression_creatives = [c_id for c_id, data in creative_performance.items() if data['impression'] > 1000]
        if high_impression_creatives:
            insights.append({
                'type': 'high_impression',
                'title': '高曝光创意',
                'detail': f'发现{len(high_impression_creatives)}个高曝光创意（>1000）',
                'action': '建议分析这些创意的受众特征'
            })
        
        # 找出低CPC创意
        low_cpc_creatives = [c_id for c_id, data in creative_performance.items() if data['click'] > 0 and (data['fee'] / data['click']) < 0.05]
        if low_cpc_creatives:
            insights.append({
                'type': 'low_cpc',
                'title': '低CPC创意',
                'detail': f'发现{len(low_cpc_creatives)}个低CPC创意（<0.05元）',
                'action': '建议分析这些创意的受众特征'
            })
        
        return {
            'success': True,
            'days': days,
            'total_creatives': len(creative_performance),
            'insights': insights
        }
    
    # ==================== 综合分析 ====================
    
    def comprehensive_attribution_analysis(self, days=30):
        """综合归因分析
        
        Args:
            days: 分析天数
        
        Returns:
            综合分析结果
        """
        # 1. 数据驱动归因
        data_driven = self.data_driven_attribution(days)
        
        # 2. Shapley值归因
        shapley = self.shapley_attribution(days)
        
        # 3. 受众分析
        audience = self.analyze_audience_segments(days)
        
        # 4. 生成综合建议
        suggestions = []
        
        if data_driven.get('success'):
            high_contribution = data_driven['summary']['high_contribution']
            if high_contribution > 0:
                suggestions.append({
                    'type': 'creative',
                    'title': '高贡献创意',
                    'detail': f'发现{high_contribution}个高贡献创意',
                    'action': '建议加推这些创意',
                    'priority': 'high'
                })
        
        if shapley.get('success'):
            top_creative = shapley['summary']['top_creative']
            if top_creative:
                suggestions.append({
                    'type': 'shapley',
                    'title': 'Shapley最优创意',
                    'detail': f'创意{top_creative}的Shapley值最高',
                    'action': '建议重点关注',
                    'priority': 'medium'
                })
        
        if audience.get('success'):
            for rec in audience.get('recommendations', []):
                suggestions.append({
                    'type': 'audience',
                    'title': rec['title'],
                    'detail': rec['detail'],
                    'action': rec['action'],
                    'priority': 'medium'
                })
        
        return {
            'success': True,
            'days': days,
            'data_driven': data_driven,
            'shapley': shapley,
            'audience': audience,
            'suggestions': suggestions,
            'summary': {
                'total_creatives': data_driven.get('summary', {}).get('total_creatives', 0),
                'high_contribution': data_driven.get('summary', {}).get('high_contribution', 0),
                'top_creative': shapley.get('summary', {}).get('top_creative', None)
            }
        }


# 测试代码
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
    
    sdk = XiaohongshuJuguangSDK()
    attribution_ai = AttributionAI(sdk)
    
    print("=" * 50)
    print("📊 测试归因分析与创意A/B测试")
    print("=" * 50)
    
    # 1. 测试数据驱动归因
    print("\n1. 数据驱动归因测试")
    print("-" * 30)
    data_driven = attribution_ai.data_driven_attribution(days=7)
    if data_driven.get('success'):
        print(f"✅ 数据驱动归因成功")
        print(f"   创意数量: {data_driven['summary']['total_creatives']}")
        print(f"   高贡献: {data_driven['summary']['high_contribution']}")
    
    # 2. 测试Shapley归因
    print("\n2. Shapley归因测试")
    print("-" * 30)
    shapley = attribution_ai.shapley_attribution(days=7)
    if shapley.get('success'):
        print(f"✅ Shapley归因成功")
        print(f"   创意数量: {shapley['summary']['total_creatives']}")
        print(f"   最优创意: {shapley['summary']['top_creative']}")
    
    # 3. 测试受众分析
    print("\n3. 受众分析测试")
    print("-" * 30)
    audience = attribution_ai.analyze_audience_segments(days=7)
    if audience.get('success'):
        print(f"✅ 受众分析成功")
        print(f"   模板数量: {audience['total_templates']}")
        print(f"   推荐数量: {len(audience['recommendations'])}")
    
    # 4. 测试受众洞察
    print("\n4. 受众洞察测试")
    print("-" * 30)
    insights = attribution_ai.get_audience_insights(days=7)
    if insights.get('success'):
        print(f"✅ 受众洞察成功")
        print(f"   创意数量: {insights['total_creatives']}")
        print(f"   洞察数量: {len(insights['insights'])}")
    
    # 5. 测试综合分析
    print("\n5. 综合分析测试")
    print("-" * 30)
    comprehensive = attribution_ai.comprehensive_attribution_analysis(days=7)
    if comprehensive.get('success'):
        print(f"✅ 综合分析成功")
        print(f"   创意数量: {comprehensive['summary']['total_creatives']}")
        print(f"   高贡献: {comprehensive['summary']['high_contribution']}")
        print(f"   建议数量: {len(comprehensive['suggestions'])}")
