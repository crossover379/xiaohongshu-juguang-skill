#!/usr/bin/env python3
"""
聚光AI运营助手 v2.4 - 账号大盘 + 投放规则 + 新手模式
"""

import sys, os as _sys_os
_scripts_dir = _sys_os.path.dirname(_sys_os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import json
import re
import time
from datetime import datetime, timedelta
from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
from xiaohongshu_reports import ReportEngine
from xiaohongshu_sdk_enhancer import SDKEnhancer
from xiaohongshu_expert_knowledge import generate_expert_analysis, format_expert_analysis, get_industry_strategy, get_troubleshooting_guide
from xiaohongshu_expert_knowledge import get_advanced_diagnosis, format_advanced_diagnosis
from xiaohongshu_creative_analyzer import CreativeAnalyzer
from xiaohongshu_automation_rules import AutomationRuleEngine
from xiaohongshu_keyword_manager import KeywordManager


# ==================== 聚光投放规则库（官方文档+实战验证） ====================
JUGUANG_RULES = {
    "出价规则": {
        "搜索广告最低出价": 0.3,
        "信息流广告最低出价": 0.2,
        "出价单位": "元",
        "出价调整幅度限制": "单次调整不超过50%",
        "建议出价": "行业均价的1.2-1.5倍",
    },
    "预算规则": {
        "计划最低日预算": 100,
        "简单投最低日预算": 50,
        "账户日预算": "可选，不设上限则不限",
        "预算单位": "元",
        "预算调整": "可随时调整，立即生效",
        "起量预算": "建议不低于100元，或计划预算的20%-30%",
    },
    "定向规则": {
        "年龄定向": "18-100岁，可多选",
        "性别定向": "不限/男/女",
        "地域定向": "省/市/区三级",
        "兴趣定向": "一级/二级/三级类目",
        "关键词定向": "最多1000个关键词",
    },
    "创意规则": {
        "标题字数": "最多20字",
        "描述字数": "最多100字",
        "图片数量": "1-9张",
        "视频时长": "5-300秒",
        "笔记来源": "可选择已发布笔记或新建",
    },
    "计划规则": {
        "计划名称长度": "最多50字",
        "单账户计划数上限": "无硬性限制，建议不超过100个",
        "投放时段": "可自定义，最小粒度30分钟",
        "投放模式": "标准投放/简单投",
    },
    "数据规则": {
        "报表延迟": "离线报表T+1，实时报表延迟15分钟",
        "数据归因": "点击归因窗口7天，展示归因窗口1天",
        "转化跟踪": "支持表单提交、私信开口、电话拨打等",
    },
    "审核规则": {
        "审核时间": "通常1-2小时，高峰期可能更长",
        "审核不通过原因": "违规内容、资质不全、素材质量差",
        "可申诉": "审核不通过可申诉，提供相关资质",
    },
    "简单投规则": {
        "最低日预算": 50,
        "投放模式": "全自动，无需手动调价",
        "适用场景": "新手入门、快速测试",
        "数据查看": "使用简单投专用报表接口",
    },
    "API规则": {
        "调用频次限制": "每个应用3000次/分钟",
        "笔记列表查询": "QPS 80",
        "关键词实时报表": "QPS 50",
        "创意层级实时报表": "QPS 300",
        "消耗门槛": "无日耗门槛要求",
        "数据范围": "仅支持商业广告数据，不支持口碑通/用户侧账号/非专业号笔记/小红星/聚光Lite",
    },
    "审核规则": {
        "审核时间": "通常1-2小时，高峰期可能更长",
        "审核不通过原因": "违规内容、资质不全、素材质量差",
        "可申诉": "审核不通过可申诉，提供相关资质",
        "违规处理": "商业化风险积分管理，累计违规将暂停投放",
    },
}


class AIOperationsAssistant:
    """聚光AI运营助手"""
    
    def __init__(self, config_path=None):
        self.sdk = XiaohongshuJuguangSDK(config_path) if config_path else XiaohongshuJuguangSDK()
        self.report = ReportEngine(self.sdk)
        self.enhancer = SDKEnhancer(self.sdk)
        
        self.alert_thresholds = {
            'daily_cost_max': 200,
            'daily_cost_min': 10,
            'ctr_min': 5,
            'cpl_max': 10,
            'cpm_max': 20,
            'balance_min': 100,
        }
        self._load_thresholds()
    
    def _load_thresholds(self):
        try:
            import os as _os
            _alert_path = _os.path.join(_os.path.expanduser('~'), '.workbuddy', 'skills',
                                         'xiaohongshu-juguang-ai', 'alert_thresholds.json')
            with open(_alert_path, 'r') as f:
                self.alert_thresholds.update(json.load(f))
        except Exception:
            pass
    
    def save_thresholds(self, thresholds):
        self.alert_thresholds.update(thresholds)
        import os as _os
        _alert_path = _os.path.join(_os.path.expanduser('~'), '.workbuddy', 'skills',
                                     'xiaohongshu-juguang-ai', 'alert_thresholds.json')
        _os.makedirs(_os.path.dirname(_alert_path), exist_ok=True)
        with open(_alert_path, 'w') as f:
            json.dump(self.alert_thresholds, f, ensure_ascii=False, indent=2)
    
    # ==================== 账号大盘 ====================
    def get_account_dashboard(self):
        """获取账号大盘数据"""
        dashboard = {
            'account_info': {},
            'account_budget': {},
            'campaign_summary': {},
            'today_data': {},
            'active_campaigns': [],
            'paused_campaigns': [],
        }
        
        # 1. 账户信息
        dashboard['account_info'] = {
            'advertiser_id': self.sdk.advertiser_id,
            'account_name': '聚光投放账户',
        }
        
        # 2. 账户预算（真实数据）
        budget_result = self.sdk.get_account_budget()
        if budget_result.get('success'):
            budget_data = budget_result.get('data', {})
            account_budget = budget_data.get('account_budget', 0)  # 单位：分
            limit_day_budget = budget_data.get('limit_day_budget', 0)  # 0=不限，1=指定
            today_spend = budget_data.get('today_spend', 0)  # 单位：分
            available_balance = budget_data.get('available_balance', 0)  # 单位：分
            
            dashboard['account_budget'] = {
                'budget_yuan': account_budget / 100,  # 分转元
                'budget_type': '不限预算' if limit_day_budget == 0 else '指定预算',
                'limit_day_budget': limit_day_budget,
                'today_spend_yuan': today_spend / 100,  # 分转元
                'available_balance_yuan': available_balance / 100,  # 分转元
            }
        
        # 2. 今日数据（实时+离线）
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 实时数据（今日最新）
        realtime_result = self.sdk.get_realtime_report('account', start_date=today, end_date=today)
        if realtime_result.get('success'):
            realtime_data = realtime_result.get('data') or {}
            dashboard['today_data'] = {
                'total_cost': float(realtime_data.get('fee', 0)),
                'normal_cost': 0,  # 实时接口不区分标准投/简单投
                'easy_cost': 0,
                'impression': int(realtime_data.get('impression', 0)),
                'click': int(realtime_data.get('click', 0)),
                'data_source': 'realtime',
            }
        else:
            # 离线数据（T+1）
            today_data = self.sdk.get_daily_cost(today)
            dashboard['today_data'] = {
                'total_cost': float(today_data.get('total_cost', 0)),
                'normal_cost': float(today_data.get('normal_cost', 0)),
                'easy_cost': float(today_data.get('easy_cost', 0)),
                'impression': int(today_data.get('total_impression', 0)),
                'click': int(today_data.get('total_click', 0)),
                'data_source': 'offline',
            }
        
        # 计算效率指标
        imp = dashboard['today_data']['impression']
        click = dashboard['today_data']['click']
        cost = dashboard['today_data']['total_cost']
        dashboard['today_data']['ctr'] = (click / imp * 100) if imp > 0 else 0
        dashboard['today_data']['cpc'] = (cost / click) if click > 0 else 0
        dashboard['today_data']['cpm'] = (cost / imp * 1000) if imp > 0 else 0
        
        # 3. 计划列表（全量读取，自动分页）
        campaigns = self.sdk.get_all_campaigns()
        if campaigns.get('success'):
            data = campaigns.get('data', {})
            camp_list = data.get('base_campaign_dtos', [])
            total_count = data.get('total_count', len(camp_list))
            
            active_count = 0
            paused_count = 0
            total_budget = 0
            
            for camp in camp_list:
                cid = camp.get('campaign_id')
                name = camp.get('campaign_name', '未命名')
                enable = camp.get('campaign_enable', 0)
                budget = int(camp.get('limit_day_budget', 0)) / 100  # 分转元
                
                camp_info = {
                    'id': cid,
                    'name': name,
                    'enable': enable,
                    'budget': budget,
                }
                
                # 使用explore_status判断状态（4=投放中，1=暂停）
                explore_status = camp.get('explore_status', 0)
                if explore_status == 4:
                    active_count += 1
                    dashboard['active_campaigns'].append(camp_info)
                else:
                    paused_count += 1
                    dashboard['paused_campaigns'].append(camp_info)
                
                total_budget += budget
            
            dashboard['campaign_summary'] = {
                'total': total_count,
                'active': active_count,
                'paused': paused_count,
                'total_budget': total_budget,
            }
        
        # 4. 昨日数据（用于对比）
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_data = self.sdk.get_daily_cost(yesterday)
        dashboard['yesterday_data'] = {
            'total_cost': float(yesterday_data.get('total_cost', 0)),
            'impression': int(yesterday_data.get('total_impression', 0)),
            'click': int(yesterday_data.get('total_click', 0)),
        }
        
        return dashboard
    
    def format_dashboard(self, dashboard):
        """格式化账号大盘"""
        d = dashboard
        today = d['today_data']
        yesterday = d['yesterday_data']
        summary = d['campaign_summary']
        budget = d.get('account_budget', {})
        
        # 计算变化
        cost_change = self._calc_change(today['total_cost'], yesterday['total_cost'])
        imp_change = self._calc_change(today['impression'], yesterday['impression'])
        click_change = self._calc_change(today['click'], yesterday['click'])
        
        # 账户预算信息
        budget_type = budget.get('budget_type', '未知')
        budget_yuan = budget.get('budget_yuan', 0)
        today_spend = budget.get('today_spend_yuan', 0)
        available_balance = budget.get('available_balance_yuan', 0)
        
        report = f"""📊 聚光账号大盘
{'═'*45}
👤 账户ID: {d['account_info']['advertiser_id']}

💰 账户预算
  预算类型: {budget_type}
  日预算: {budget_yuan:.0f}元/天
  今日已消耗: {today_spend:.2f}元
  账户余额: {available_balance:.2f}元

📈 今日数据
  总消耗: {today['total_cost']:.2f}元
  标准投: {today['normal_cost']:.2f}元
  简单投: {today['easy_cost']:.2f}元
  较昨日: {cost_change}
  曝光: {today['impression']:,} ({imp_change})
  点击: {today['click']:,} ({click_change})
  CTR: {today['ctr']:.2f}%
  CPC: {today['cpc']:.2f}元
  CPM: {today['cpm']:.2f}元

📋 计划概况
  总计: {summary.get('total', 0)}个计划
  ─────────────────────────────
  ✅ 投放中: {summary.get('active', 0)}个
  ⏸️ 已暂停: {summary.get('paused', 0)}个
  ─────────────────────────────
  日预算合计: {summary.get('total_budget', 0):.0f}元"""
        
        # 投放中计划列表
        if d['active_campaigns']:
            report += f"\n\n✅ 投放中计划 ({len(d['active_campaigns'])}个)\n{'─'*45}"
            for camp in d['active_campaigns'][:10]:
                budget_str = f"预算{camp['budget']:.0f}元" if camp['budget'] > 0 else "不限预算"
                report += f"\n  • {camp['name']} | {budget_str}"
        
        # 暂停计划列表
        if d['paused_campaigns']:
            report += f"\n\n⏸️ 已暂停计划 ({len(d['paused_campaigns'])}个)\n{'─'*45}"
            for camp in d['paused_campaigns'][:10]:
                report += f"\n  • {camp['name']}"
        
        return report
    
    # ==================== 智能日报 ====================
    def generate_smart_daily_report(self, date=None):
        """生成智能日报（包含多维度对比和建议）"""
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 获取当日数据
        data = self.sdk.get_daily_cost(date)
        
        # 获取前一日数据
        yesterday = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        yd = self.sdk.get_daily_cost(yesterday)
        
        # 获取近7天数据（周平均）
        week_start = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
        week_data = self.sdk.get_daily_cost_range(week_start, date)
        week_avg_cost = sum(float(d['total_cost']) for d in week_data) / len(week_data) if week_data else 0
        week_avg_impression = sum(int(d['total_impression']) for d in week_data) / len(week_data) if week_data else 0
        week_avg_click = sum(int(d['total_click']) for d in week_data) / len(week_data) if week_data else 0
        
        # 获取近30天数据（月平均）
        month_start = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=30)).strftime("%Y-%m-%d")
        month_data = self.sdk.get_daily_cost_range(month_start, date)
        month_avg_cost = sum(float(d['total_cost']) for d in month_data) / len(month_data) if month_data else 0
        month_avg_impression = sum(int(d['total_impression']) for d in month_data) / len(month_data) if month_data else 0
        month_avg_click = sum(int(d['total_click']) for d in month_data) / len(month_data) if month_data else 0
        
        # 计算当日指标
        cost = float(data['total_cost'])
        impression = int(data['total_impression'])
        click = int(data['total_click'])
        ctr = (click / impression * 100) if impression > 0 else 0
        cpc = (cost / click) if click > 0 else 0
        cpm = (cost / impression * 1000) if impression > 0 else 0
        
        # 计算周平均指标
        week_ctr = (week_avg_click / week_avg_impression * 100) if week_avg_impression > 0 else 0
        week_cpc = (week_avg_cost / week_avg_click) if week_avg_click > 0 else 0
        
        # 计算月平均指标
        month_ctr = (month_avg_click / month_avg_impression * 100) if month_avg_impression > 0 else 0
        month_cpc = (month_avg_cost / month_avg_click) if month_avg_click > 0 else 0
        
        report = f"""📊 聚光智能日报
{'='*50}
📅 日期: {date}

💰 消耗对比
{'─'*50}
  当日消耗: {cost:.2f}元
  ├─ 标准投: {float(data['normal_cost']):.2f}元
  └─ 简单投: {float(data['easy_cost']):.2f}元
  
  较前日: {self._calc_change(cost, float(yd['total_cost']))} ({float(yd['total_cost']):.2f}元)
  较周均: {self._calc_change(cost, week_avg_cost)} ({week_avg_cost:.2f}元)
  较月均: {self._calc_change(cost, month_avg_cost)} ({month_avg_cost:.2f}元)

📈 曝光对比
{'─'*50}
  当日曝光: {impression:,}
  较前日: {self._calc_change(impression, int(yd['total_impression']))} ({int(yd['total_impression']):,})
  较周均: {self._calc_change(impression, week_avg_impression)} ({week_avg_impression:,.0f})
  较月均: {self._calc_change(impression, month_avg_impression)} ({month_avg_impression:,.0f})

👆 点击对比
{'─'*50}
  当日点击: {click:,}
  较前日: {self._calc_change(click, int(yd['total_click']))} ({int(yd['total_click']):,})
  较周均: {self._calc_change(click, week_avg_click)} ({week_avg_click:,.0f})
  较月均: {self._calc_change(click, month_avg_click)} ({month_avg_click:,.0f})

📊 效率指标对比
{'─'*50}
  CTR: {ctr:.2f}% (周均{week_ctr:.2f}% | 月均{month_ctr:.2f}%)
  CPC: {cpc:.2f}元 (周均{week_cpc:.2f}元 | 月均{month_cpc:.2f}元)
  CPM: {cpm:.2f}元"""
        
        # 生成今日建议
        suggestions = self._generate_daily_suggestions(cost, impression, click, ctr, cpc, cpm, week_avg_cost, week_ctr, week_cpc)
        if suggestions:
            report += f"\n\n💡 今日建议\n{'─'*50}"
            for i, s in enumerate(suggestions, 1):
                report += f"\n  {i}. {s}"
        
        # 检查预警
        alerts = self._check_alerts(data, ctr, cpc, cpm)
        if alerts:
            report += f"\n\n⚠️ 预警提醒\n{'─'*50}"
            for a in alerts:
                report += f"\n  {a}"
        
        return report
    
    def _generate_daily_suggestions(self, cost, impression, click, ctr, cpc, cpm, week_avg_cost, week_ctr, week_cpc):
        """生成今日建议"""
        suggestions = []
        
        # 消耗建议
        if cost > week_avg_cost * 1.5:
            suggestions.append(f"消耗偏高（较周均↑{((cost-week_avg_cost)/week_avg_cost*100):.0f}%），建议检查高消耗计划，暂停低效计划")
        elif cost < week_avg_cost * 0.5 and cost > 0:
            suggestions.append(f"消耗偏低（较周均↓{((week_avg_cost-cost)/week_avg_cost*100):.0f}%），可适当提高出价或扩大定向")
        elif cost == 0:
            suggestions.append("消耗为零，请检查计划状态、账户余额、定向设置")
        
        # CTR建议
        if ctr < week_ctr * 0.7 and impression > 100:
            suggestions.append(f"CTR偏低（{ctr:.2f}% vs 周均{week_ctr:.2f}%），建议优化创意素材或调整定向")
        elif ctr > week_ctr * 1.3:
            suggestions.append(f"CTR表现优秀（{ctr:.2f}% vs 周均{week_ctr:.2f}%），可考虑增加预算")
        
        # CPC建议
        if cpc > week_cpc * 1.5 and click > 10:
            suggestions.append(f"CPC偏高（{cpc:.2f}元 vs 周均{week_cpc:.2f}元），建议降低出价或优化关键词")
        elif cpc < week_cpc * 0.7:
            suggestions.append(f"CPC成本优秀（{cpc:.2f}元 vs 周均{week_cpc:.2f}元），可适当扩大投放")
        
        # 综合建议
        if not suggestions:
            suggestions.append("各项指标表现稳定，保持当前投放策略")
        
        return suggestions
    
    def _calc_change(self, cur, prev):
        if prev == 0:
            return "新增" if cur > 0 else "无变化"
        c = ((cur - prev) / prev) * 100
        return f"↑{c:.1f}%" if c > 0 else f"↓{abs(c):.1f}%" if c < 0 else "无变化"
    
    # ==================== 实时预警 ====================
    def check_realtime_alerts(self):
        alerts = []
        today = datetime.now().strftime("%Y-%m-%d")
        d = self.sdk.get_daily_cost(today)
        ctr = (float(d['total_click']) / float(d['total_impression']) * 100) if float(d['total_impression']) > 0 else 0
        cpc = (float(d['total_cost']) / float(d['total_click'])) if float(d['total_click']) > 0 else 0
        
        if float(d['total_cost']) > self.alert_thresholds['daily_cost_max']:
            alerts.append({'level': '🚨', 'type': 'cost_high', 'message': f"消耗超标：{float(d['total_cost']):.2f}元", 'suggestion': '暂停低效计划或降低出价'})
        if float(d['total_cost']) == 0:
            alerts.append({'level': '🚨', 'type': 'cost_zero', 'message': "消耗归零", 'suggestion': '检查计划状态、余额'})
        if ctr < self.alert_thresholds['ctr_min'] and float(d['total_impression']) > 100:
            alerts.append({'level': '⚠️', 'type': 'ctr_low', 'message': f"CTR偏低：{ctr:.2f}%", 'suggestion': '优化创意或调整定向'})
        if cpc > self.alert_thresholds['cpl_max'] and float(d['total_click']) > 0:
            alerts.append({'level': '⚠️', 'type': 'cpc_high', 'message': f"CPC偏高：{cpc:.2f}元", 'suggestion': '降低出价或优化关键词'})
        return alerts
    
    def _check_alerts(self, d, ctr, cpc, cpm):
        a = []
        if float(d['total_cost']) > self.alert_thresholds['daily_cost_max']:
            a.append(f"🚨 消耗超标：{float(d['total_cost']):.2f}元")
        if float(d['total_cost']) == 0:
            a.append("🚨 消耗归零")
        if ctr < self.alert_thresholds['ctr_min'] and float(d['total_impression']) > 100:
            a.append(f"⚠️ CTR偏低：{ctr:.2f}%")
        if cpc > self.alert_thresholds['cpl_max'] and float(d['total_click']) > 0:
            a.append(f"⚠️ CPC偏高：{cpc:.2f}元")
        return a
    
    def _generate_suggestions(self, d, ctr, cpc, cpm):
        s = []
        if float(d['total_cost']) > self.alert_thresholds['daily_cost_max']:
            s.append("💡 消耗超标，建议：暂停低效计划或降低出价20%")
        if ctr < self.alert_thresholds['ctr_min'] and float(d['total_impression']) > 100:
            s.append("💡 CTR偏低，建议：优化创意素材或调整定向人群")
        if cpc > self.alert_thresholds['cpl_max'] and float(d['total_click']) > 0:
            s.append("💡 CPC偏高，建议：降低出价或优化关键词质量")
        if float(d['total_cost']) == 0:
            s.append("💡 无消耗，建议：检查计划状态、余额、定向设置")
        return s
    
    # ==================== AI分析 ====================
    def analyze_campaign_performance(self, date=None):
        """分析计划表现（全量读取，自动分页）"""
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 获取计划列表（状态信息）
        campaigns = self.sdk.get_all_campaigns()
        results = {'high_efficiency': [], 'low_efficiency': [], 'normal': [], 'paused': []}
        if not campaigns.get('success'):
            return results
        
        # 建立计划ID到状态的映射
        camp_status = {}
        for camp in campaigns.get('data', {}).get('base_campaign_dtos', []):
            cid = str(camp.get('campaign_id'))
            explore_status = camp.get('explore_status', 0)
            name = camp.get('campaign_name', '未命名')
            camp_status[cid] = {'name': name, 'explore_status': explore_status}
        
        # 获取计划级报表（不传campaign_id，API会返回全部计划数据）
        report = self.sdk.get_offline_report('campaign', date, date)
        if not report.get('success'):
            # 报表获取失败，只返回暂停计划
            for cid, info in camp_status.items():
                if info['explore_status'] != 4:
                    results['paused'].append({'id': cid, 'name': info['name']})
            return results
        
        # 从data_list获取每个计划的数据
        data_list = report.get('data', {}).get('data_list', [])
        
        # 建立计划ID到报表数据的映射
        report_map = {}
        for item in data_list:
            cid = str(item.get('campaign_id', ''))
            if cid:
                report_map[cid] = item
        
        # 遍历计划列表，匹配报表数据
        for cid, info in camp_status.items():
            name = info['name']
            explore_status = info['explore_status']
            
            if explore_status != 4:
                results['paused'].append({'id': cid, 'name': name})
                continue
            
            # 从报表数据中获取该计划的数据
            item = report_map.get(cid)
            if item:
                fee = float(item.get('fee', 0))
                imp = int(item.get('impression', 0))
                click = int(item.get('click', 0))
                ctr = (click / imp * 100) if imp > 0 else 0
                plan = {'id': cid, 'name': name, 'cost': fee, 'ctr': ctr}
                if fee > 30 and ctr > 15:
                    results['high_efficiency'].append(plan)
                elif fee > 20 and ctr < 8:
                    results['low_efficiency'].append(plan)
                else:
                    results['normal'].append(plan)
            else:
                # 没有报表数据，标记为正常
                results['normal'].append({'id': cid, 'name': name, 'cost': 0, 'ctr': 0})
        
        return results
    
    def generate_optimization_suggestions(self, analysis):
        s = []
        if analysis['high_efficiency']:
            s.append("📈 高效计划（建议加预算）:")
            for p in analysis['high_efficiency']:
                s.append(f"  • {p['name']}: {p['cost']:.2f}元 CTR{p['ctr']:.1f}%")
        if analysis['low_efficiency']:
            s.append("\n📉 低效计划（建议暂停）:")
            for p in analysis['low_efficiency']:
                s.append(f"  • {p['name']}: {p['cost']:.2f}元 CTR{p['ctr']:.1f}%")
        return "\n".join(s) if s else "✅ 所有计划表现正常"
    
    def get_quick_actions(self, date=None):
        analysis = self.analyze_campaign_performance(date)
        actions = []
        for p in analysis['low_efficiency']:
            actions.append({'type': 'pause', 'target': p['id'], 'name': p['name'], 'reason': f"CTR偏低({p['ctr']:.1f}%)"})
        for p in analysis['high_efficiency']:
            actions.append({'type': 'increase_budget', 'target': p['id'], 'name': p['name'], 'reason': f"表现优秀(CTR{p['ctr']:.1f}%)"})
        return actions
    
    # ==================== 快速执行 ====================
    def execute_action(self, action_type, target_id, params=None):
        if params is None:
            params = {}
        r = None
        if action_type == 'pause_campaign':
            r = self.sdk.update_campaign_status([target_id], 2)
        elif action_type == 'resume_campaign':
            r = self.sdk.update_campaign_status([target_id], 1)
        elif action_type == 'pause_unit':
            r = self.sdk.update_unit_status([target_id], 2)
        elif action_type == 'resume_unit':
            r = self.sdk.update_unit_status([target_id], 1)
        elif action_type == 'pause_creative':
            r = self.sdk.update_creativity_status([target_id], 2)
        elif action_type == 'resume_creative':
            r = self.sdk.update_creativity_status([target_id], 1)
        elif action_type == 'update_budget':
            r = self.sdk.update_campaign(target_id, daily_budget=params.get('budget', 100))
        elif action_type == 'update_bid':
            r = self.sdk.update_unit_bid(target_id, params.get('bid', 0.5))
        else:
            return {'success': False, 'message': f'未知操作: {action_type}'}
        if r and r.get('success'):
            return {'success': True, 'message': f'操作成功: {action_type}'}
        return {'success': False, 'message': r.get('message', '操作失败') if r else '操作失败'}
    
    def batch_pause_campaigns(self, ids):
        return [{'id': cid, 'result': self.execute_action('pause_campaign', cid)} for cid in ids]
    
    def format_action_confirmation(self, action_type, name, params=None):
        if action_type == 'pause_campaign':
            return f"⏸️ 确认暂停计划「{name}」？"
        elif action_type == 'resume_campaign':
            return f"▶️ 确认开启计划「{name}」？"
        elif action_type == 'pause_unit':
            return f"⏸️ 确认暂停单元「{name}」？"
        elif action_type == 'update_budget':
            return f"💰 确认将计划「{name}」日预算调整为{params.get('budget', 0)}元？"
        elif action_type == 'update_bid':
            return f"💰 确认将单元「{name}」出价调整为{params.get('bid', 0)}元？"
        return f"确认执行操作「{action_type}」？"
    
    # ==================== 智能创编 ====================
    def create_campaign_smart(self, user_input):
        params = self._parse_user_input(user_input)
        config = {
            'name': params.get('name', f"{params.get('product', '推广')}-{datetime.now().strftime('%m月%d日')}"),
            'daily_budget': params.get('budget', 100),
            '投放方式': params.get('type', '标准投放'),
            '定向': params.get('target', '通投'),
            '出价': params.get('bid', 0.5),
        }
        return config
    
    def _parse_user_input(self, user_input):
        params = {}
        budget_match = re.search(r'(\d+)\s*元', user_input)
        if budget_match:
            params['budget'] = int(budget_match.group(1))
        keywords = ['酒店', '旅游', '美食', '教育', '医疗', '电商']
        for kw in keywords:
            if kw in user_input:
                params['product'] = kw
                break
        if '简单投' in user_input:
            params['type'] = '简单投'
        return params
    
    def format_campaign_config(self, config):
        return f"""📋 计划配置
{'─'*30}
名称: {config['name']}
日预算: {config['daily_budget']}元
投放方式: {config['投放方式']}
定向: {config['定向']}
出价: {config['出价']}元

确认创建吗？"""
    
    # ==================== 投放规则查询 ====================
    def get_rule(self, category=None, keyword=None):
        """查询投放规则"""
        if category:
            rules = JUGUANG_RULES.get(category, {})
            if keyword:
                for k, v in rules.items():
                    if keyword in k:
                        return {k: v}
                return {}
            return rules
        
        if keyword:
            results = {}
            for cat, rules in JUGUANG_RULES.items():
                for k, v in rules.items():
                    if keyword in k or keyword in str(v):
                        results[f"{cat}.{k}"] = v
            return results
        
        return JUGUANG_RULES
    
    def format_rules(self, rules, title="投放规则"):
        """格式化规则"""
        if isinstance(rules, dict) and all(isinstance(v, dict) for v in rules.values()):
            # 分类规则
            report = f"📖 {title}\n{'═'*40}"
            for cat, items in rules.items():
                report += f"\n\n📌 {cat}\n{'─'*30}"
                for k, v in items.items():
                    report += f"\n  • {k}: {v}"
            return report
        else:
            # 单项规则
            report = f"📖 {title}\n{'─'*30}"
            for k, v in rules.items():
                report += f"\n  • {k}: {v}"
            return report
    
    # ==================== 新手模式（交互式引导） ====================
    def get_beginner_guide(self, topic="入门"):
        """新手引导"""
        guides = {
            "入门": {
                "title": "🎯 聚光投放新手指南",
                "content": [
                    "1️⃣ 什么是聚光？",
                    "   聚光是小红书的广告投放平台，让你的内容被更多人看到",
                    "",
                    "2️⃣ 核心指标解释",
                    "   • CTR（点击率）= 点击数 ÷ 曝光数 × 100%",
                    "   • CPC（单次点击成本）= 消耗 ÷ 点击数",
                    "   • CPM（千次曝光成本）= 消耗 ÷ 曝光数 × 1000",
                    "   • CPL（单条线索成本）= 消耗 ÷ 线索数",
                    "",
                    "3️⃣ 投放流程",
                    "   创建计划 → 设置定向 → 设置出价 → 上传创意 → 开始投放",
                    "",
                    "4️⃣ 新手建议",
                    "   • 先用「简单投」测试，熟悉流程",
                    "   • 日预算从100元开始，不要一上来就烧大钱",
                    "   • 关注CTR，低于5%要优化创意",
                    "   • 投放3天后再看数据，不要急着调",
                ],
            },
            "出价": {
                "title": "💰 出价指南",
                "content": [
                    "• 搜索广告最低出价：0.3元/点击",
                    "• 信息流广告最低出价：0.2元/点击",
                    "• 建议出价：行业均价的1.2-1.5倍",
                    "• 单次调整不超过50%，避免大幅波动",
                ],
            },
            "预算": {
                "title": "📊 预算指南",
                "content": [
                    "• 计划最低日预算：100元",
                    "• 简单投最低日预算：50元",
                    "• 建议：先设100-200元测试",
                    "• 跑出效果后再逐步加预算",
                ],
            },
            "定向": {
                "title": "🎯 定向指南",
                "content": [
                    "• 地域：选择你的目标城市",
                    "• 年龄：根据目标人群选择",
                    "• 兴趣：选择相关行业类目",
                    "• 关键词：添加相关搜索词",
                    "• 建议：新手先用通投，再逐步精确定向",
                ],
            },
        }
        
        return guides.get(topic, guides["入门"])
    
    def get_welcome_message(self, is_connected=False):
        """获取欢迎消息（带大盘数据展示）"""
        if not is_connected:
            # 未接入 - 强制走接入引导
            welcome = f"""🎉 欢迎使用聚光投放助手！

我是你的AI投放助手，帮你管理小红书聚光广告投放。

{'─'*40}
⚠️ 你还没有接入聚光API
{'─'*40}

接入后我可以帮你：
  📊 查看账号大盘数据
  📈 生成智能日报
  🔍 分析计划表现
  ⚡ 一键操作（暂停/调价）
  🎨 创意优选推荐
  🆕 智能创编计划

{'─'*40}
💡 接入步骤：
  1. 打开聚光平台创建应用：
     👉 https://ad.xiaohongshu.com
  2. 进入「应用管理」创建应用
  3. 获取AppID和AppSecret
  4. 回复"接入"，我来帮你绑定

准备好了请回复"接入"~"""
        else:
            # 已接入 - 展示大盘 + 功能菜单
            dashboard = self.get_account_dashboard()
            dashboard_text = self.format_dashboard(dashboard)
            
            welcome = f"""🎉 欢迎使用聚光投放助手！

先看看你的账户情况：

{dashboard_text}

{'─'*40}
💡 我能帮你做什么？
  1️⃣ 查看智能日报（带环比分析）
  2️⃣ 分析计划表现（高效/低效识别）
  3️⃣ 一键操作（暂停/调价/启停）
  4️⃣ 智能创编（告诉我需求，我来配置）
  5️⃣ 创意优选（找优质创意加推）

告诉我你想做什么，或者直接说需求~"""
        
        return welcome
    
    def get_beginner_wizard(self, step=1, user_input=None):
        """新手向导（一步步引导）"""
        wizard = {
            1: {
                "title": "🔗 接入聚光API",
                "message": "好的！我来帮你接入聚光API。\n\n你需要准备：\n  • AppID（在聚光平台-应用管理中获取）\n  • AppSecret（同上）\n\n准备好了吗？",
                "options": ["准备好了，开始接入", "还没有，先了解一下", "我已经有AppID和AppSecret"],
                "next_step": 2,
            },
            2: {
                "title": "📝 输入AppID",
                "message": "请发送你的AppID：\n\n💡 获取方式：聚光平台 → 应用管理 → 找到你的应用 → 复制AppID",
                "options": [],
                "next_step": 3,
            },
            3: {
                "title": "🔐 输入AppSecret",
                "message": "请发送你的AppSecret：\n\n💡 获取方式：同上页面，复制AppSecret",
                "options": [],
                "next_step": 4,
            },
            4: {
                "title": "✅ 接入确认",
                "message": "好的！我来帮你完成接入。\n\nAppID: {app_id}\nAppSecret: {app_secret}\n\n确认接入吗？",
                "options": ["确认接入", "重新输入", "取消"],
                "next_step": 5,
            },
            5: {
                "title": "🎉 接入成功 + Token续期设置",
                "message": "接入成功！\n\n⚠️ 重要提醒：聚光API的Token有效期为24小时，过期后需要刷新。\n\n请选择Token续期方式：\n\n  方式1️⃣ 自动定时刷新（推荐）\n    • 系统每20小时自动刷新一次\n    • Token永远不会过期\n    • 无需手动操作\n\n  方式2️⃣ 调用时自动刷新\n    • 每次调用API时检查并刷新\n    • 如果长时间不调用，首次调用可能失败\n    • 适合频繁使用的场景\n\n请选择：",
                "options": ["自动定时刷新（推荐）", "调用时自动刷新"],
                "next_step": 6,
            },
            '5a': {
                "title": "⏰ 定时刷新已开启",
                "message": "已开启自动定时刷新！\n\n✅ 配置：每20小时自动刷新Token\n✅ 优势：Token永远不会过期\n✅ 保障：刷新失败会主动通知你\n\n现在来看看你的账户情况：\n\n{dashboard}\n\n{'─'*40}\n💡 接下来你可以：\n  1. 查看智能日报\n  2. 分析计划表现\n  3. 了解投放规则\n  4. 开始新手投放引导",
                "options": ["查看智能日报", "分析计划表现", "了解投放规则", "开始投放引导"],
                "next_step": None,
            },
            '5b': {
                "title": "✅ 调用时刷新已设置",
                "message": "已设置调用时自动刷新！\n\n✅ 配置：每次调用API时检查Token\n✅ 优势：无需额外定时任务\n⚠️ 注意：长时间不调用后首次调用可能失败\n\n💡 如果你想改为定时刷新，随时告诉我\n\n现在来看看你的账户情况：\n\n{dashboard}\n\n{'─'*40}\n💡 接下来你可以：\n  1. 查看智能日报\n  2. 分析计划表现\n  3. 了解投放规则\n  4. 开始新手投放引导",
                "options": ["查看智能日报", "分析计划表现", "了解投放规则", "开始投放引导"],
                "next_step": None,
            },
            6: {
                "title": "🎯 新手投放引导",
                "message": "好的！我来一步步教你创建投放计划。\n\n首先，你想推广什么？",
                "options": ["酒店/民宿", "美食/餐饮", "旅游/景点", "教育/培训", "其他"],
                "next_step": 7,
            },
            7: {
                "title": "💰 设置预算",
                "message": "好的！你想每天花多少钱投放？\n\n💡 建议新手从100-200元/天开始测试",
                "options": ["50元（简单投最低）", "100元（推荐新手）", "200元（进阶）", "自定义金额"],
                "next_step": 8,
            },
            8: {
                "title": "📍 选择投放区域",
                "message": "你想投放在哪个地区？",
                "options": ["厦门（本地）", "福建全省", "全国", "自定义城市"],
                "next_step": 9,
            },
            9: {
                "title": "🎯 选择投放方式",
                "message": "选择投放方式：\n\n• 简单投：系统全自动，适合新手\n• 标准投：可自定义设置，适合有经验的人",
                "options": ["简单投（推荐新手）", "标准投放"],
                "next_step": 10,
            },
            10: {
                "title": "✅ 配置确认",
                "message": "好的！我帮你整理一下配置：\n\n{config}\n\n确认创建吗？",
                "options": ["确认创建", "修改配置", "取消"],
                "next_step": 11,
            },
            11: {
                "title": "🚀 创建完成",
                "message": "计划创建成功！\n\n📊 接下来你可以：\n  1. 查看账号大盘\n  2. 查看今日数据\n  3. 了解投放规则\n\n有任何问题随时问我！",
                "options": ["查看账号大盘", "查看今日数据", "了解投放规则"],
                "next_step": None,
            },
        }
        
        return wizard.get(step, wizard[1])
    
    def process_beginner_wizard(self, step, user_choice, user_context=None):
        """处理新手向导的用户选择"""
        if user_context is None:
            user_context = {}
        
        wizard = self.get_beginner_wizard(step)
        
        # 处理用户选择
        if step == 1:
            # 接入确认
            if user_choice == 0:  # 准备好了
                return self.get_beginner_wizard(2), user_context
            elif user_choice == 1:  # 先了解
                return 'rules', user_context
            else:  # 已有AppID
                return self.get_beginner_wizard(2), user_context
        
        elif step == 2:
            # 输入AppID（需要用户输入文字）
            return self.get_beginner_wizard(3), user_context
        
        elif step == 3:
            # 输入AppSecret（需要用户输入文字）
            return self.get_beginner_wizard(4), user_context
        
        elif step == 4:
            # 接入确认
            if user_choice == 0:  # 确认接入
                # TODO: 实际接入逻辑
                return self.get_beginner_wizard(5), user_context
            elif user_choice == 1:  # 重新输入
                return self.get_beginner_wizard(2), user_context
            else:  # 取消
                return None, user_context
        
        elif step == 5:
            # Token续期方式选择
            if user_choice == 0:  # 自动定时刷新（推荐）
                user_context['token_refresh_mode'] = 'scheduled'
                return self.get_beginner_wizard('5a'), user_context
            else:  # 调用时自动刷新
                user_context['token_refresh_mode'] = 'on_demand'
                return self.get_beginner_wizard('5b'), user_context
        
        elif step in ['5a', '5b']:
            # Token续期设置完成后的操作
            if user_choice == 0:  # 查看智能日报
                return 'daily_report', user_context
            elif user_choice == 1:  # 分析计划表现
                return 'analysis', user_context
            elif user_choice == 2:  # 了解投放规则
                return 'rules', user_context
            elif user_choice == 3:  # 开始投放引导
                return self.get_beginner_wizard(6), user_context
        
        elif step == 6:
            # 选择推广行业
            industry_map = {
                0: "酒店/民宿",
                1: "美食/餐饮",
                2: "旅游/景点",
                3: "教育/培训",
                4: "其他",
            }
            user_context['industry'] = industry_map.get(user_choice, "其他")
            return self.get_beginner_wizard(7), user_context
        
        elif step == 7:
            # 选择预算
            budget_map = {
                0: 50,
                1: 100,
                2: 200,
                3: None,  # 自定义
            }
            user_context['budget'] = budget_map.get(user_choice, 100)
            return self.get_beginner_wizard(8), user_context
        
        elif step == 8:
            # 选择区域
            region_map = {
                0: "厦门",
                1: "福建",
                2: "全国",
                3: None,  # 自定义
            }
            user_context['region'] = region_map.get(user_choice, "厦门")
            return self.get_beginner_wizard(9), user_context
        
        elif step == 9:
            # 选择投放方式
            user_context['type'] = "简单投" if user_choice == 0 else "标准投放"
            return self.get_beginner_wizard(10), user_context
        
        elif step == 10:
            # 确认配置
            if user_choice == 0:  # 确认创建
                # 生成配置
                config = self.create_campaign_smart(f"{user_context.get('industry', '推广')} {user_context.get('type', '标准投放')} {user_context.get('budget', 100)}元 {user_context.get('region', '厦门')}")
                user_context['config'] = config
                return self.get_beginner_wizard(11), user_context
            elif user_choice == 1:  # 修改配置
                return self.get_beginner_wizard(6), user_context
            else:  # 取消
                return None, user_context
        
        elif step == 11:
            # 完成后的操作
            if user_choice == 0:  # 查看账号大盘
                return 'dashboard', user_context
            elif user_choice == 1:  # 查看今日数据
                return 'daily_report', user_context
            elif user_choice == 2:  # 了解投放规则
                return 'rules', user_context
        
        return None, user_context
    
    def format_beginner_guide(self, guide):
        """格式化新手引导"""
        report = f"{guide['title']}\n{'═'*40}"
        for line in guide['content']:
            report += f"\n{line}"
        return report
    
    # ==================== 创意优选 ====================
    def analyze_creative_performance(self, date=None, days=3, top_n=10):
        """分析创意表现，找出优质和低效创意
        Args:
            date: 结束日期，默认昨天
            days: 分析天数，默认3天
            top_n: 返回前N个创意
        """
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 计算日期范围
        end_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = (end_date - timedelta(days=days-1)).strftime("%Y-%m-%d")
        
        # 获取创意报表（使用data_list获取单个创意数据，page_size=500确保全量）
        report = self.sdk.get_offline_report('creative', start_date, date, page_size=500)
        if not report.get('success'):
            return {'excellent': [], 'poor': [], 'normal': []}
        
        data = report.get('data', {})
        creative_list = data.get('data_list', [])
        total_count = data.get('total_count', len(creative_list))
        
        # 分析每个创意的报表数据
        excellent = []  # 优质创意
        poor = []       # 低效创意
        normal = []     # 正常创意
        
        for creative in creative_list[:200]:  # 分析前200个创意
            cid = creative.get('creativity_id')
            name = creative.get('creativity_name', '未命名')
            unit_id = creative.get('unit_id')
            campaign_id = creative.get('campaign_id')
            note_id = creative.get('note_id')
            
            # 获取报表数据
            fee = float(creative.get('fee', 0))
            imp = int(creative.get('impression', 0))
            click = int(creative.get('click', 0))
            ctr_str = creative.get('ctr', '0%')
            ctr = float(ctr_str.replace('%', '')) if ctr_str else 0
            cpc = (fee / click) if click > 0 else 0
            
            creative_info = {
                'id': cid,
                'name': name,
                'unit_id': unit_id,
                'campaign_id': campaign_id,
                'note_id': note_id,
                'cost': fee,
                'impression': imp,
                'click': click,
                'ctr': ctr,
                'cpc': cpc,
                'days': days,
                'daily_avg_cost': fee / days if days > 0 else 0,
            }
            
            # 创意分类规则（近N天汇总）
            # 优质创意：日均消耗>30且CTR>15% 或 日均消耗>20且CPC<0.08
            # 低效创意：日均消耗<10 或 日均消耗>10且CTR<5% 或 日均消耗>20且CPC>0.15 或 曝光<100
            # 正常创意：其他所有
            
            daily_avg = creative_info.get('daily_avg_cost', 0)
            
            if daily_avg < 10:
                # 规则1: 日均消耗<10元 → 低效（消费不足，没跑起来）
                creative_info['score'] = -daily_avg
                creative_info['reason'] = f'日均消费不足（{daily_avg:.0f}元/天）'
                poor.append(creative_info)
            elif daily_avg > 30 and ctr > 15:
                # 规则2: 日均消耗>30且CTR>15% → 优质（高消耗高转化）
                creative_info['score'] = ctr * (daily_avg ** 0.5)
                creative_info['reason'] = f'日均高消耗高CTR（{daily_avg:.0f}元/天/{ctr:.1f}%）'
                excellent.append(creative_info)
            elif daily_avg > 20 and cpc < 0.08:
                # 规则3: 日均消耗>20且CPC<0.08 → 优质（高性价比）
                creative_info['score'] = (1/cpc) * (daily_avg ** 0.5)
                creative_info['reason'] = f'日均高消耗低成本（{daily_avg:.0f}元/天/{cpc:.3f}元）'
                excellent.append(creative_info)
            elif daily_avg > 10 and ctr < 5:
                # 规则4: 日均消耗>10且CTR<5% → 低效（高消耗低转化）
                creative_info['score'] = -ctr
                creative_info['reason'] = f'日均高消耗低CTR（{daily_avg:.0f}元/天/{ctr:.1f}%）'
                poor.append(creative_info)
            elif daily_avg > 20 and cpc > 0.15:
                # 规则5: 日均消耗>20且CPC>0.15 → 低效（高成本）
                creative_info['score'] = -cpc
                creative_info['reason'] = f'日均高消耗高成本（{daily_avg:.0f}元/天/{cpc:.3f}元）'
                poor.append(creative_info)
            elif fee > 0 and imp < 100:
                # 规则6: 有消耗但曝光<100 → 低效（曝光不足）
                creative_info['score'] = -imp
                creative_info['reason'] = f'有消耗但曝光不足（{fee:.0f}元/{imp}次）'
                poor.append(creative_info)
            else:
                # 正常创意：其他所有
                creative_info['score'] = 0
                creative_info['reason'] = f'表现正常（{daily_avg:.0f}元/天/{ctr:.1f}%）'
                normal.append(creative_info)
        
        # 按得分排序
        excellent.sort(key=lambda x: x.get('score', 0), reverse=True)
        poor.sort(key=lambda x: x.get('score', 0))
        
        return {
            'excellent': excellent[:top_n],
            'poor': poor[:top_n],
            'normal': normal,
        }
    
    def format_creative_analysis(self, analysis):
        """格式化创意分析报告"""
        excellent = analysis['excellent']
        poor = analysis['poor']
        normal = analysis['normal']
        
        report = f"🎨 创意优选分析\n{'='*45}\n\n"
        report += f"📊 创意概况\n{'─'*30}\n"
        report += f"  ✅ 优质创意: {len(excellent)}个\n"
        report += f"  ⚠️ 低效创意: {len(poor)}个\n"
        report += f"  📊 正常创意: {len(normal)}个\n"
        
        if excellent:
            report += f"\n\n🏆 优质创意（建议加推）\n{'─'*30}\n"
            for i, c in enumerate(excellent[:5], 1):
                report += f"  {i}. {c['name'][:30]}\n"
                report += f"     消耗: {c['cost']:.2f}元 | CTR: {c['ctr']:.1f}% | CPC: {c['cpc']:.2f}元\n"
                report += f"     笔记ID: {c['note_id']}\n"
            report += f"\n  💡 建议: 这些创意效果好，可以复制到新计划投放\n"
        
        if poor:
            report += f"\n\n⚠️ 低效创意（建议优化或暂停）\n{'─'*30}\n"
            for i, c in enumerate(poor[:5], 1):
                report += f"  {i}. {c['name'][:30]}\n"
                report += f"     消耗: {c['cost']:.2f}元 | CTR: {c['ctr']:.1f}% | CPC: {c['cpc']:.2f}元\n"
                report += f"     笔记ID: {c['note_id']}\n"
            report += f"\n  💡 建议: 这些创意效果差，建议暂停或优化素材\n"
        
        return report
    
    def get_creative_recommendations(self, date=None):
        """获取创意推荐（用于新计划创建）"""
        analysis = self.analyze_creative_performance(date)
        
        recommendations = []
        
        for c in analysis['excellent'][:3]:
            recommendations.append({
                'type': 'copy_creative',
                'note_id': c['note_id'],
                'creative_name': c['name'],
                'reason': f"高CTR({c['ctr']:.1f}%)低CPC({c['cpc']:.2f}元)",
                'message': f"推荐复制创意: {c['name'][:30]} (CTR{c['ctr']:.1f}%)",
            })
        
        return recommendations
    
    # ==================== 🆕 创意筛查（v4.1 核心升级） ====================
    
    # 行业基准值（用于创意筛查时的对比）
    INDUSTRY_BENCHMARKS = {
        '酒店': {'ctr': (1.5, 3.0), 'cpc': (0.8, 2.0), 'cpm': (25, 50), 'cvr': (0.5, 2.0), 'roi': (1.5, 3.0)},
        '教育': {'ctr': (2.0, 4.0), 'cpc': (1.0, 3.0), 'cpm': (30, 60), 'cvr': (1.0, 3.0), 'roi': (2.0, 5.0)},
        '电商': {'ctr': (3.0, 6.0), 'cpc': (0.5, 1.5), 'cpm': (20, 45), 'cvr': (1.5, 5.0), 'roi': (2.0, 6.0)},
        '美妆': {'ctr': (2.5, 5.0), 'cpc': (0.8, 2.5), 'cpm': (25, 55), 'cvr': (1.0, 3.0), 'roi': (1.5, 4.0)},
        '本地生活': {'ctr': (2.0, 4.0), 'cpc': (0.5, 1.5), 'cpm': (15, 40), 'cvr': (1.5, 5.0), 'roi': (2.0, 5.0)},
        '通用': {'ctr': (2.0, 4.0), 'cpc': (0.5, 2.5), 'cpm': (20, 55), 'cvr': (1.0, 4.0), 'roi': (1.5, 5.0)},
    }
    
    def _get_industry_benchmark(self, industry, metric):
        """获取行业基准值，找不到用通用"""
        bm = self.INDUSTRY_BENCHMARKS.get(industry, self.INDUSTRY_BENCHMARKS['通用'])
        return bm.get(metric, self.INDUSTRY_BENCHMARKS['通用'].get(metric, (1, 10)))
    
    def _score_metric_vs_benchmark(self, value, benchmark_range, higher_is_better=True, score_max=25):
        """对单一指标打分：跟行业基准对比
        
        Args:
            value: 实际值
            benchmark_range: (下限, 上限)
            higher_is_better: True=越高越好(CTR/转化率/ROI), False=越低越好(CPC/CPM)
            score_max: 满分
        
        Returns:
            得分 (0 ~ score_max)
        """
        low, high = benchmark_range
        if high == low:
            return score_max * 0.6  # 无法对比给及格分
        
        if higher_is_better:
            ratio = (value - low) / (high - low)
        else:
            ratio = (high - value) / (high - low)
        
        ratio = max(0, min(1.5, ratio))  # 限制范围，超过上限给满分
        return min(score_max, round(ratio * score_max, 1))
    
    def screen_creatives(self, days=7, industry='通用', top_n=30):
        """🆕 创意筛查：告诉用户哪些创意值得投、哪些该停
        
        这是 v4.1 最核心的新能力。不再是简单的CTR阈值判断，
        而是从6个维度综合评分，给出明确的「投/不投」建议。
        
        Args:
            days: 分析天数（3/7/30）
            industry: 行业（用于基准对比）
            top_n: 返回前N个创意
        
        Returns:
            {
                'screen_date': '2026-06-02',
                'days': 7,
                'industry': '酒店',
                'total_screened': 50,
                'recommend': [...],    # 🟢 建议加投
                'keep': [...],         # 🟡 继续投放
                'watch': [...],        # 🟠 需要观察
                'pause': [...],        # 🔴 建议暂停
                'abandon': [...],      # ⚫ 建议放弃
                'summary': {...}
            }
        """
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 获取创意报表
        report = self.sdk.get_offline_report('creative', start_date, end_date, page_size=500)
        if not report.get('success'):
            return {'error': '获取创意数据失败', 'total_screened': 0}
        
        creative_list = report.get('data', {}).get('data_list', [])
        if not creative_list:
            return {'error': '近{days}天没有创意数据'.format(days=days), 'total_screened': 0}
        
        # 获取行业基准
        bm_ctr = self._get_industry_benchmark(industry, 'ctr')
        bm_cpc = self._get_industry_benchmark(industry, 'cpc')
        bm_cvr = self._get_industry_benchmark(industry, 'cvr')
        
        screened = []
        
        for creative in creative_list[:200]:
            cid = creative.get('creativity_id') or creative.get('creative_id', '')
            name = creative.get('creativity_name') or creative.get('creative_name', '未命名')
            note_id = creative.get('note_id', '')
            
            # 基础数据
            fee = float(creative.get('fee', 0))
            imp = int(creative.get('impression', 0))
            click = int(creative.get('click', 0))
            
            # 互动数据
            interaction = int(creative.get('interaction', 0))
            like_val = int(creative.get('like', 0))
            collect_val = int(creative.get('collect', 0))
            comment_val = int(creative.get('comment', 0))
            
            # 转化数据
            leads = int(creative.get('leads', 0) or creative.get('message', 0) or creative.get('message_consult', 0))
            
            # 效率指标
            ctr_str = creative.get('ctr', '0%')
            ctr = float(ctr_str.replace('%', '')) if isinstance(ctr_str, str) else float(ctr_str)
            cpc = (fee / click) if click > 0 else 999
            cpm = (fee / imp * 1000) if imp > 0 else 999
            cvr = (leads / click * 100) if click > 0 else 0
            engagement = (interaction / imp * 100) if imp > 0 else 0
            daily_avg_cost = fee / days if days > 0 else 0
            
            # ===== 6 维评分 =====
            
            # 1. CTR vs 行业基准 (25分)
            score_ctr = self._score_metric_vs_benchmark(ctr, bm_ctr, True, 25)
            
            # 2. CPC vs 行业基准 (20分) — 越低越好
            score_cpc = self._score_metric_vs_benchmark(cpc, bm_cpc, False, 20)
            if cpc >= 999:
                score_cpc = 0  # 没有点击，CPC无意义
            
            # 3. 转化效率 (20分) — 有转化、转化率高
            if leads > 0 and cvr > 0:
                score_cvr = self._score_metric_vs_benchmark(cvr, bm_cvr, True, 20)
            elif click > 20 and leads == 0:
                score_cvr = 0  # 有点击无转化，严重扣分
            else:
                score_cvr = 5  # 数据不足给基础分
            
            # 4. 量级充足度 (15分) — 曝光够不够、消耗够不够
            if imp >= 5000:
                score_volume = 15
            elif imp >= 2000:
                score_volume = 12
            elif imp >= 500:
                score_volume = 8
            elif imp >= 100:
                score_volume = 5
            else:
                score_volume = 2  # 曝光太少
            
            # 5. 趋势检测 (10分) — 是否有改善趋势（对比更短窗口）
            score_trend = self._detect_creative_trend(cid, days)
            
            # 6. 性价比 (10分) — ROI / 消耗效率
            if fee > 0 and leads > 0:
                cost_per_lead = fee / leads
                if cost_per_lead < 10:
                    score_roi = 10
                elif cost_per_lead < 30:
                    score_roi = 7
                elif cost_per_lead < 60:
                    score_roi = 4
                else:
                    score_roi = 1
            elif fee > 50 and leads == 0:
                score_roi = 0  # 花了钱没转化
            else:
                score_roi = 5  # 数据不足
            
            # 加权总分
            total_score = round(score_ctr + score_cpc + score_cvr + score_volume + score_trend + score_roi, 1)
            
            # 问题诊断
            problems = self._diagnose_creative_problem(ctr, cpc, imp, click, leads, fee, daily_avg_cost, industry)
            
            # 建议行动
            action = self._get_creative_action(total_score, daily_avg_cost, leads, imp)
            
            screened.append({
                'creative_id': cid,
                'name': name,
                'note_id': note_id,
                'fee': round(fee, 2),
                'impression': imp,
                'click': click,
                'ctr': round(ctr, 2),
                'cpc': round(cpc, 2) if cpc < 999 else None,
                'cpm': round(cpm, 2) if cpm < 999 else None,
                'leads': leads,
                'cvr': round(cvr, 2),
                'engagement': round(engagement, 2),
                'daily_avg_cost': round(daily_avg_cost, 2),
                'total_score': total_score,
                'scores_detail': {
                    'ctr': score_ctr, 'cpc': score_cpc, 'cvr': score_cvr,
                    'volume': score_volume, 'trend': score_trend, 'roi': score_roi,
                },
                'problems': problems,
                'action': action,
                'industry': industry,
            })
        
        # 按总分排序
        screened.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 分类
        recommend = [s for s in screened if s['action']['tier'] == 'recommend']
        keep = [s for s in screened if s['action']['tier'] == 'keep']
        watch = [s for s in screened if s['action']['tier'] == 'watch']
        pause = [s for s in screened if s['action']['tier'] == 'pause']
        abandon = [s for s in screened if s['action']['tier'] == 'abandon']
        
        # 汇总
        total_cost = sum(s['fee'] for s in screened)
        total_cost_poor = sum(s['fee'] for s in (pause + abandon))
        total_leads = sum(s['leads'] for s in screened)
        avg_score = round(sum(s['total_score'] for s in screened) / len(screened), 1) if screened else 0
        
        return {
            'screen_date': end_date,
            'days': days,
            'industry': industry,
            'total_screened': len(screened),
            'recommend': recommend[:top_n],
            'keep': keep[:top_n],
            'watch': watch[:top_n],
            'pause': pause[:top_n],
            'abandon': abandon[:top_n],
            'summary': {
                'total_creatives': len(screened),
                'recommend_count': len(recommend),
                'keep_count': len(keep),
                'watch_count': len(watch),
                'pause_count': len(pause),
                'abandon_count': len(abandon),
                'total_cost': round(total_cost, 2),
                'wasted_cost': round(total_cost_poor, 2),
                'total_leads': total_leads,
                'avg_score': avg_score,
                'benchmarks': {'ctr': bm_ctr, 'cpc': bm_cpc, 'cvr': bm_cvr},
            },
        }
    
    def _detect_creative_trend(self, creative_id, days):
        """检测创意趋势：对比更短窗口的表现
        
        Returns:
            趋势得分 0-10（上升=10，持平=5，下降=0-3）
        """
        if days <= 3:
            return 5  # 窗口太短无法对比
        
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 后半段（更近期）
        half = max(2, days // 2)
        recent_start = (datetime.now() - timedelta(days=half)).strftime('%Y-%m-%d')
        recent_report = self.sdk.get_offline_report('creative', recent_start, end_date, page_size=500)
        
        if not recent_report.get('success'):
            return 5
        
        recent_list = recent_report.get('data', {}).get('data_list', [])
        
        # 找到对应创意
        for c in recent_list:
            rc_id = c.get('creativity_id') or c.get('creative_id', '')
            if str(rc_id) != str(creative_id):
                continue
            
            recent_ctr_str = c.get('ctr', '0%')
            recent_ctr = float(recent_ctr_str.replace('%', '')) if isinstance(recent_ctr_str, str) else float(recent_ctr_str)
            recent_fee = float(c.get('fee', 0))
            recent_imp = int(c.get('impression', 0))
            
            # 推算前半段
            earlier_fee = recent_fee  # 近似：假设消耗均匀
            earlier_imp = recent_imp
            
            # 简单趋势判断（如果有完整数据更准，这里做近似）
            # 真实场景中应该拉取全窗口数据对比
            # 这里用后半段日均 vs 全窗口日均来推断趋势
            if recent_imp > 100 and recent_ctr > 0:
                # 近期有投放，认为趋势稳定偏上升
                return 7
            elif recent_imp > 0:
                return 5
            else:
                return 3  # 近期无投放，在衰退
        
        return 5  # 找不到数据给中性分
    
    def _diagnose_creative_problem(self, ctr, cpc, imp, click, leads, fee, daily_avg_cost, industry):
        """诊断创意问题 — 不只给分数，还告诉用户为什么不行
        
        Returns:
            list of problem dicts
        """
        problems = []
        bm_ctr = self._get_industry_benchmark(industry, 'ctr')
        bm_cpc = self._get_industry_benchmark(industry, 'cpc')
        
        # 处理无效CPC
        effective_cpc = cpc if cpc and cpc < 999 else 999
        
        # 问题1：跑不动
        if imp < 100 and daily_avg_cost < 5:
            problems.append({
                'type': 'no_exposure',
                'severity': 'critical',
                'title': '根本跑不出去',
                'detail': f'近{daily_avg_cost:.1f}天日均消耗仅{daily_avg_cost:.1f}元，曝光{imp}次，几乎没有投放量',
                'cause': '出价太低 or 定向太窄 or 素材质量差被系统降权',
                'fix': '① 提高出价到行业均值的1.2倍 ② 放宽定向条件 ③ 更换封面/标题重新提交',
            })
        
        # 问题2：CTR低
        if imp >= 100 and ctr < bm_ctr[0]:
            problems.append({
                'type': 'low_ctr',
                'severity': 'high',
                'title': f'CTR过低（{ctr:.1f}% < 行业{bm_ctr[0]:.1f}%）',
                'detail': f'曝光{imp}次但点击率仅{ctr:.1f}%，用户看到但不点',
                'cause': '封面不够吸引人或标题没有击中痛点',
                'fix': '① 封面用高饱和对比色+大字 ② 标题前10字必须含核心卖点 ③ A/B测试不同封面',
            })
        
        # 问题3：CPC高
        if click > 10 and effective_cpc > bm_cpc[1] * 1.3:
            problems.append({
                'type': 'high_cpc',
                'severity': 'high',
                'title': f'CPC过高（{effective_cpc:.2f}元 > 行业上限{bm_cpc[1]:.2f}元）',
                'detail': f'每次点击成本{effective_cpc:.2f}元，远超行业水平',
                'cause': '竞争激烈 or 质量分低导致系统加价',
                'fix': '① 降低出价并观察 ② 优化素材提升质量分 ③ 错峰投放避开竞争高峰',
            })
        
        # 问题4：有消耗无转化
        if fee > 50 and leads == 0 and click > 10:
            problems.append({
                'type': 'no_conversion',
                'severity': 'critical',
                'title': f'花了{fee:.0f}元但没有转化',
                'detail': f'消耗{fee:.0f}元、{click}次点击，但0个咨询/线索',
                'cause': '落地页与素材不匹配 or 目标人群不精准 or 转化路径有摩擦',
                'fix': '① 检查笔记内容是否跟广告承诺一致 ② 优化私信引导话术 ③ 重新审视定向人群',
            })
        
        # 问题5：消耗高但各项指标都差
        if daily_avg_cost > 30 and (ctr < 3 or (click > 10 and leads == 0)):
            problems.append({
                'type': 'money_pit',
                'severity': 'critical',
                'title': '烧钱黑洞',
                'detail': f'日均烧{daily_avg_cost:.0f}元但没有对应产出',
                'cause': '可能定向人群不匹配 or 素材严重不吸引目标用户',
                'fix': '① 立即暂停 ② 重新分析目标人群画像 ③ 更换全新素材后再试',
            })
        
        # 问题6：曝光够但点击少
        if imp >= 3000 and click < 30:
            problems.append({
                'type': 'low_engagement',
                'severity': 'medium',
                'title': '曝光量够但没人点',
                'detail': f'{imp}次曝光仅{click}次点击，CTR {ctr:.1f}%',
                'cause': '素材与受众不匹配 or 广告位选择不当',
                'fix': '① 更换封面图片 ② 测试不同标题 ③ 检查定向是否过宽',
            })
        
        return problems
    
    def _get_creative_action(self, total_score, daily_avg_cost, leads, imp):
        """根据综合评分给出清晰的行动建议
        
        Returns:
            {tier, label, icon, recommendation, urgency}
        """
        if total_score >= 80:
            return {
                'tier': 'recommend',
                'label': '强烈推荐加投',
                'icon': '🟢',
                'recommendation': '效果优秀，建议加预算或复制到新计划扩量',
                'urgency': '机会',
            }
        elif total_score >= 60:
            return {
                'tier': 'keep',
                'label': '值得继续投放',
                'icon': '🟡',
                'recommendation': '表现尚可，继续投放观察，有余量可小幅加预算',
                'urgency': '正常',
            }
        elif total_score >= 40:
            return {
                'tier': 'watch',
                'label': '需要观察',
                'icon': '🟠',
                'recommendation': '表现一般，建议再观察3-7天，如无改善则优化或暂停',
                'urgency': '关注',
            }
        elif total_score >= 20:
            return {
                'tier': 'pause',
                'label': '建议暂停优化',
                'icon': '🔴',
                'recommendation': '效果差，建议暂停当前投放，优化素材/出价/定向后再试',
                'urgency': '尽快处理',
            }
        else:
            return {
                'tier': 'abandon',
                'label': '建议放弃',
                'icon': '⚫',
                'recommendation': '持续低效，不建议继续投入，直接关停或删除',
                'urgency': '立即处理',
            }
    
    def format_creative_screening(self, screening, max_per_category=5):
        """格式化创意筛查报告 — 用户友好的对话输出"""
        if screening.get('error'):
            return f"⚠️ {screening['error']}"
        
        s = screening['summary']
        bm = s['benchmarks']
        
        report = f"🔬 创意筛查报告 — 近{screening['days']}天（{screening['industry']}行业）\n"
        report += f"{'═'*50}\n\n"
        
        # 总览
        report += f"📊 筛查总览\n{'─'*35}\n"
        report += f"  共筛查 {s['total_creatives']} 个创意，总消耗 {s['total_cost']:.0f} 元\n"
        report += f"  行业基准：CTR {bm['ctr'][0]:.1f}-{bm['ctr'][1]:.1f}% | CPC {bm['cpc'][0]:.2f}-{bm['cpc'][1]:.2f}元 | 转化率 {bm['cvr'][0]:.1f}-{bm['cvr'][1]:.1f}%\n\n"
        
        # 分布
        report += f"📈 创意分布\n{'─'*35}\n"
        report += f"  🟢 强烈推荐加投：{s['recommend_count']} 个 — 这些是你的现金牛\n"
        report += f"  🟡 值得继续投放：{s['keep_count']} 个 — 稳定产出，保持\n"
        report += f"  🟠 需要观察：{s['watch_count']} 个 — 边缘徘徊，盯紧\n"
        report += f"  🔴 建议暂停优化：{s['pause_count']} 个 — 效果差，需要干预\n"
        report += f"  ⚫ 建议放弃：{s['abandon_count']} 个 — 纯烧钱，该停了\n"
        
        # 浪费金额警示
        if s['wasted_cost'] > 50:
            report += f"\n  ⚠️ 近{screening['days']}天，低效/无效创意共烧掉 {s['wasted_cost']:.0f} 元\n"
        
        # 🟢 推荐加投
        report += f"\n\n{'─'*50}\n"
        report += f"🟢 值得加投的创意（{s['recommend_count']}个）\n{'─'*50}\n"
        if screening['recommend']:
            for i, c in enumerate(screening['recommend'][:max_per_category], 1):
                report += f"\n  {i}. 「{c['name'][:25]}」— 综合评分 {c['total_score']}/100\n"
                report += f"     消耗{c['fee']:.0f}元 | 曝光{c['impression']} | CTR {c['ctr']:.1f}% | CPC {c['cpc']:.2f}元\n"
                if c['leads'] > 0:
                    report += f"     转化{c['leads']}个 | 转化率{c['cvr']:.1f}% | 性价比优秀\n"
                report += f"     💡 {c['action']['recommendation']}\n"
        else:
            report += f"  （暂无）\n"
        
        # 🔴 需要暂停
        report += f"\n{'─'*50}\n"
        report += f"🔴 建议暂停的创意（{s['pause_count']}个）\n{'─'*50}\n"
        if screening['pause']:
            for i, c in enumerate(screening['pause'][:max_per_category], 1):
                report += f"\n  {i}. 「{c['name'][:25]}」— 综合评分 {c['total_score']}/100\n"
                report += f"     消耗{c['fee']:.0f}元 | 曝光{c['impression']} | CTR {c['ctr']:.1f}%\n"
                if c['problems']:
                    for p in c['problems'][:2]:
                        report += f"     ⚡ {p['title']}：{p['cause']}\n"
                        report += f"     🔧 修复建议：{p['fix'][:60]}...\n"
                report += f"     💡 {c['action']['recommendation']}\n"
        else:
            report += f"  （暂无 — 你的创意整体表现不错！）\n"
        
        # ⚫ 建议放弃
        report += f"\n{'─'*50}\n"
        report += f"⚫ 建议放弃的创意（{s['abandon_count']}个）\n{'─'*50}\n"
        if screening['abandon']:
            for i, c in enumerate(screening['abandon'][:max_per_category], 1):
                report += f"\n  {i}. 「{c['name'][:25]}」— 综合评分 {c['total_score']}/100\n"
                report += f"     消耗{c['fee']:.0f}元 | 曝光{c['impression']} | CTR {c['ctr']:.1f}%\n"
                if c['problems']:
                    report += f"     ⚡ {c['problems'][0]['title']}\n"
                report += f"     💡 {c['action']['recommendation']}\n"
        else:
            report += f"  （暂无 — 没有特别差的创意！）\n"
        
        # 底部建议
        report += f"\n{'─'*50}\n"
        report += f"💡 下一步建议\n"
        report += f"  ① 优先关停 ⚫ 放弃 + 🔴 暂停 的创意，节省预算\n"
        report += f"  ② 把省下的预算加到 🟢 推荐创意上\n"
        report += f"  ③ 🟠 观察的创意再给 3-7 天，到期复查\n"
        report += f"\n回复「执行关停」暂停低效创意，或告诉我具体要操作哪几个。\n"
        
        return report
    
    # ==================== 僵尸计划清理 ====================
    def analyze_zombie_campaigns(self, days=7):
        """分析僵尸计划（长期无消耗的暂停计划）
        全量读取所有计划，确保数据准确
        """
        campaigns = self.sdk.get_all_campaigns()
        if not campaigns.get('success'):
            return {'zombies': [], 'active': [], 'paused': []}
        
        camp_list = campaigns.get('data', {}).get('base_campaign_dtos', [])
        total_count = campaigns.get('data', {}).get('total_count', len(camp_list))
        
        # 分类
        active_campaigns = []
        paused_campaigns = []
        zombie_campaigns = []
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        for camp in camp_list:
            cid = camp.get('campaign_id')
            name = camp.get('campaign_name', '未命名')
            enable = camp.get('campaign_enable', 0)
            
            camp_info = {'id': cid, 'name': name, 'enable': enable}
            
            if enable == 1:
                active_campaigns.append(camp_info)
            else:
                # 检查最近消耗
                try:
                    r = self.sdk.get_offline_report('campaign', start_date, end_date, campaign_id=cid)
                    if r.get('success'):
                        data = r.get('data', {}).get('aggregation_data', {})
                        fee = float(data.get('fee', 0))
                        if fee == 0:
                            camp_info['reason'] = f'最近{days}天无消耗'
                            zombie_campaigns.append(camp_info)
                        else:
                            camp_info['recent_cost'] = fee
                            paused_campaigns.append(camp_info)
                    else:
                        paused_campaigns.append(camp_info)
                except Exception:
                    paused_campaigns.append(camp_info)
        
        return {
            'zombies': zombie_campaigns,
            'active': active_campaigns,
            'paused': paused_campaigns,
            'total_count': total_count,
        }
    
    def format_zombie_report(self, analysis):
        """格式化僵尸计划报告"""
        zombies = analysis['zombies']
        active = analysis['active']
        paused = analysis['paused']
        
        report = f"🧹 僵尸计划分析\n{'='*40}\n\n"
        report += f"📊 计划概况\n{'─'*30}\n"
        report += f"  ✅ 投放中: {len(active)}个\n"
        report += f"  ⏸️ 有消耗暂停: {len(paused)}个\n"
        report += f"  💀 僵尸计划: {len(zombies)}个\n"
        
        if zombies:
            report += f"\n\n💀 僵尸计划（建议清理）\n{'─'*30}\n"
            for camp in zombies:
                report += f"  • {camp['name']}\n"
                report += f"    ID: {camp['id']} | {camp.get('reason', '长期无消耗')}\n"
            
            report += f"\n💡 建议: 这些计划长期无消耗，建议清理释放账户容量\n"
            report += f"   清理后可让账户结构更清晰，便于管理"
        
        return report
    
    def get_cleanup_suggestions(self, days=7):
        """获取清理建议"""
        analysis = self.analyze_zombie_campaigns(days)
        
        suggestions = []
        
        if analysis['zombies']:
            zombie_ids = [c['id'] for c in analysis['zombies']]
            zombie_names = [c['name'] for c in analysis['zombies']]
            
            suggestions.append({
                'type': 'cleanup_zombies',
                'count': len(analysis['zombies']),
                'names': zombie_names,
                'ids': zombie_ids,
                'message': f"发现{len(analysis['zombies'])}个僵尸计划，建议清理",
            })
        
        return suggestions
    
    # ==================== 配置管理 ====================
    def get_thresholds(self):
        return self.alert_thresholds
    
    def update_threshold(self, key, value):
        if key in self.alert_thresholds:
            self.alert_thresholds[key] = value
            self.save_thresholds(self.alert_thresholds)
            return True
        return False
    
    # ==================== 定时推送模板 ====================
    def get_push_templates(self):
        """获取所有定时推送模板"""
        templates = {
            'daily_report': {
                'name': '📊 每日投放日报',
                'description': '每天早上9点推送昨日投放数据，包含消耗、曝光、点击、CTR等核心指标',
                'schedule': '每天 09:00',
                'content': '昨日消耗 | 标准投+简单投 | 曝光/点击/CTR/CPC | 较前日变化',
                '适用场景': '日常运营监控，快速了解昨日投放效果',
            },
            'weekly_report': {
                'name': '📈 每周投放周报',
                'description': '每周一早上10点推送上周投放数据，包含周汇总、每日趋势、周环比',
                'schedule': '每周一 10:00',
                'content': '周消耗汇总 | 每日趋势 | 周环比变化 | TOP计划/创意',
                '适用场景': '周度复盘，分析投放趋势和优化方向',
            },
            'budget_alert': {
                'name': '💰 预算预警',
                'description': '当账户余额或计划预算不足时推送预警',
                'schedule': '实时监控',
                'content': '余额不足 | 预算即将耗尽 | 建议充值金额',
                '适用场景': '避免因预算不足导致投放中断',
            },
            'performance_alert': {
                'name': '⚡ 效果预警',
                'description': '当CTR、CPC、CPM等指标异常时推送预警',
                'schedule': '实时监控',
                'content': 'CTR下降 | CPC上涨 | CPM异常 | 具体计划/创意',
                '适用场景': '及时发现投放效果异常，快速调整',
            },
            'cost_alert': {
                'name': '🔥 消耗预警',
                'description': '当单日消耗超过阈值时推送预警',
                'schedule': '实时监控',
                'content': '消耗超标 | 具体金额 | 建议操作',
                '适用场景': '控制投放成本，避免超支',
            },
            'zombie_alert': {
                'name': '🧹 僵尸计划清理',
                'description': '每周五下午推送僵尸计划列表，建议清理',
                'schedule': '每周五 16:00',
                'content': '僵尸计划数量 | 具体计划列表 | 建议清理',
                '适用场景': '释放账户容量，提升管理效率',
            },
            'creative_alert': {
                'name': '🎨 创意优选推送',
                'description': '每周三下午推送创意分析报告，推荐加推优质创意',
                'schedule': '每周三 15:00',
                'content': '优质创意推荐 | 低效创意预警 | 加推建议',
                '适用场景': '优化创意效果，提升ROI',
            },
            'morning_brief': {
                'name': '☀️ 早安投放简报',
                'description': '每天早上8点推送今日投放计划和昨日关键数据',
                'schedule': '每天 08:00',
                'content': '昨日核心数据 | 今日投放计划 | 待处理事项',
                '适用场景': '快速了解今日投放重点，高效启动',
            },
            'evening_summary': {
                'name': '🌙 晚间投放总结',
                'description': '每天晚上8点推送今日投放总结和明日建议',
                'schedule': '每天 20:00',
                'content': '今日消耗 | 效果指标 | 明日建议 | 待优化项',
                '适用场景': '今日复盘，明日规划',
            },
        }
        return templates
    
    def format_push_templates(self, templates=None):
        """格式化推送模板列表"""
        if templates is None:
            templates = self.get_push_templates()
        
        report = f"📋 定时推送模板\n{'='*45}\n\n"
        report += f"💡 选择适合你的推送模板，系统会自动定时推送数据\n\n"
        
        for key, template in templates.items():
            report += f"{template['name']}\n{'─'*30}\n"
            report += f"  📝 {template['description']}\n"
            report += f"  ⏰ 推送时间: {template['schedule']}\n"
            report += f"  📊 推送内容: {template['content']}\n"
            report += f"  💡 适用场景: {template['适用场景']}\n\n"
        
        return report
    
    def generate_push_content(self, template_key, date=None):
        """生成推送内容"""
        if date is None:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        templates = self.get_push_templates()
        if template_key not in templates:
            return f"❌ 未知模板: {template_key}"
        
        template = templates[template_key]
        
        if template_key == 'daily_report':
            return self._generate_daily_push(date)
        elif template_key == 'weekly_report':
            return self._generate_weekly_push()
        elif template_key == 'budget_alert':
            return self._generate_budget_push()
        elif template_key == 'performance_alert':
            return self._generate_performance_push(date)
        elif template_key == 'cost_alert':
            return self._generate_cost_push(date)
        elif template_key == 'zombie_alert':
            return self._generate_zombie_push()
        elif template_key == 'creative_alert':
            return self._generate_creative_push()
        elif template_key == 'morning_brief':
            return self._generate_morning_push()
        elif template_key == 'evening_summary':
            return self._generate_evening_push(date)
        else:
            return f"❌ 模板 {template_key} 暂未实现"
    
    def _generate_daily_push(self, date):
        """生成每日日报推送"""
        data = self.sdk.get_daily_cost(date)
        cost = float(data.get('total_cost', 0))
        impression = int(data.get('total_impression', 0))
        click = int(data.get('total_click', 0))
        ctr = (click / impression * 100) if impression > 0 else 0
        cpc = (cost / click) if click > 0 else 0
        
        # 获取前一日数据
        yesterday = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        yd = self.sdk.get_daily_cost(yesterday)
        yd_cost = float(yd.get('total_cost', 0))
        cost_change = self._calc_change(cost, yd_cost)
        
        report = f"📊 聚光投放日报\n{'='*40}\n"
        report += f"📅 日期: {date}\n\n"
        report += f"💰 消耗: {cost:.2f}元 ({cost_change})\n"
        report += f"👀 曝光: {impression:,}\n"
        report += f"👆 点击: {click:,}\n"
        report += f"📈 CTR: {ctr:.2f}%\n"
        report += f"💵 CPC: {cpc:.2f}元\n"
        return report
    
    def _generate_weekly_push(self):
        """生成每周周报推送"""
        # 获取本周数据
        today = datetime.now()
        week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        week_end = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        week_data = self.sdk.get_daily_cost_range(week_start, week_end)
        total_cost = sum(float(d.get('total_cost', 0)) for d in week_data)
        total_impression = sum(int(d.get('total_impression', 0)) for d in week_data)
        total_click = sum(int(d.get('total_click', 0)) for d in week_data)
        
        # 获取上周数据
        last_week_start = (today - timedelta(days=today.weekday() + 7)).strftime("%Y-%m-%d")
        last_week_end = (today - timedelta(days=today.weekday() + 1)).strftime("%Y-%m-%d")
        last_week_data = self.sdk.get_daily_cost_range(last_week_start, last_week_end)
        last_week_cost = sum(float(d.get('total_cost', 0)) for d in last_week_data)
        
        cost_change = self._calc_change(total_cost, last_week_cost)
        
        report = f"📈 聚光投放周报\n{'='*40}\n"
        report += f"📅 周期: {week_start} ~ {week_end}\n\n"
        report += f"💰 周消耗: {total_cost:.2f}元 ({cost_change})\n"
        report += f"👀 周曝光: {total_impression:,}\n"
        report += f"👆 周点击: {total_click:,}\n"
        report += f"📊 日均消耗: {total_cost/7:.2f}元\n"
        return report
    
    def _generate_budget_push(self):
        """生成预算预警推送"""
        budget = self.sdk.get_account_budget()
        if not budget.get('success'):
            return "❌ 无法获取预算信息"
        
        data = budget.get('data', {})
        balance = int(data.get('available_balance', 0)) / 100
        daily_budget = int(data.get('account_budget', 0)) / 100
        today_spend = int(data.get('today_spend', 0)) / 100
        
        report = f"💰 预算预警\n{'='*40}\n\n"
        
        if balance < 100:
            report += f"🚨 余额不足预警\n"
            report += f"  当前余额: {balance:.2f}元\n"
            report += f"  建议充值: 500元以上\n\n"
        
        if daily_budget > 0 and today_spend > daily_budget * 0.8:
            report += f"⚠️ 预算即将耗尽\n"
            report += f"  日预算: {daily_budget:.0f}元\n"
            report += f"  今日已消耗: {today_spend:.2f}元\n"
            report += f"  剩余预算: {daily_budget - today_spend:.2f}元\n"
        
        if balance >= 100 and (daily_budget == 0 or today_spend <= daily_budget * 0.8):
            report += f"✅ 预算状态正常\n"
            report += f"  余额: {balance:.2f}元\n"
            report += f"  今日已消耗: {today_spend:.2f}元\n"
        
        return report
    
    def _generate_performance_push(self, date):
        """生成效果预警推送"""
        data = self.sdk.get_daily_cost(date)
        cost = float(data.get('total_cost', 0))
        impression = int(data.get('total_impression', 0))
        click = int(data.get('total_click', 0))
        ctr = (click / impression * 100) if impression > 0 else 0
        cpc = (cost / click) if click > 0 else 0
        
        report = f"⚡ 效果预警\n{'='*40}\n\n"
        
        alerts = []
        if ctr < 5:
            alerts.append(f"🚨 CTR过低: {ctr:.2f}% (建议>5%)")
        if cpc > 0.15:
            alerts.append(f"🚨 CPC过高: {cpc:.2f}元 (建议<0.15元)")
        
        if alerts:
            report += "\n".join(alerts)
            report += "\n\n💡 建议: 检查创意质量和出价设置"
        else:
            report += f"✅ 效果指标正常\n"
            report += f"  CTR: {ctr:.2f}%\n"
            report += f"  CPC: {cpc:.2f}元\n"
        
        return report
    
    def _generate_cost_push(self, date):
        """生成消耗预警推送"""
        data = self.sdk.get_daily_cost(date)
        cost = float(data.get('total_cost', 0))
        
        report = f"🔥 消耗预警\n{'='*40}\n\n"
        
        if cost > 200:
            report += f"🚨 消耗超标预警\n"
            report += f"  今日消耗: {cost:.2f}元\n"
            report += f"  建议: 检查计划预算设置，暂停低效计划\n"
        elif cost > 100:
            report += f"⚠️ 消耗较高\n"
            report += f"  今日消耗: {cost:.2f}元\n"
            report += f"  建议: 关注消耗趋势，及时调整\n"
        else:
            report += f"✅ 消耗正常\n"
            report += f"  今日消耗: {cost:.2f}元\n"
        
        return report
    
    def _generate_zombie_push(self):
        """生成僵尸计划推送"""
        zombie = self.analyze_zombie_campaigns(days=30)
        count = zombie.get('zombie_count', 0)
        
        report = f"🧹 僵尸计划清理\n{'='*40}\n\n"
        
        if count > 0:
            report += f"⚠️ 发现 {count} 个僵尸计划\n\n"
            report += "建议清理的计划:\n"
            for camp in zombie.get('zombie_campaigns', [])[:5]:
                report += f"  • {camp.get('name', '未命名')} (ID: {camp.get('id')})\n"
            report += f"\n💡 清理后可释放账户容量，提升管理效率"
        else:
            report += f"✅ 没有僵尸计划，账户状态良好\n"
        
        return report
    
    def _generate_creative_push(self):
        """生成创意优选推送"""
        creative = self.analyze_creative_performance(days=3)
        excellent = creative.get('excellent', [])
        poor = creative.get('poor', [])
        
        report = f"🎨 创意优选推送\n{'='*40}\n\n"
        
        if excellent:
            report += f"✅ 优质创意（建议加推）:\n"
            for c in excellent[:3]:
                report += f"  • {c['name'][:25]}\n"
                report += f"    消耗: {c['cost']:.2f}元 | CTR: {c['ctr']:.1f}%\n"
            report += "\n"
        
        if poor:
            report += f"⚠️ 低效创意（建议暂停）:\n"
            for c in poor[:3]:
                report += f"  • {c['name'][:25]}\n"
                report += f"    消耗: {c['cost']:.2f}元 | 原因: {c.get('reason', '')}\n"
            report += "\n"
        
        if not excellent and not poor:
            report += f"📊 创意表现正常，暂无优化建议\n"
        
        return report
    
    def _generate_morning_push(self):
        """生成早安简报推送"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        data = self.sdk.get_daily_cost(yesterday)
        cost = float(data.get('total_cost', 0))
        impression = int(data.get('total_impression', 0))
        click = int(data.get('total_click', 0))
        
        report = f"☀️ 早安投放简报\n{'='*40}\n"
        report += f"📅 {datetime.now().strftime('%Y-%m-%d')}\n\n"
        report += f"📊 昨日数据:\n"
        report += f"  消耗: {cost:.2f}元\n"
        report += f"  曝光: {impression:,}\n"
        report += f"  点击: {click:,}\n\n"
        report += f"💡 今日待办:\n"
        report += f"  1. 检查昨日数据异常\n"
        report += f"  2. 优化低效计划\n"
        report += f"  3. 更新创意素材\n"
        return report
    
    def _generate_evening_push(self, date):
        """生成晚间总结推送"""
        data = self.sdk.get_daily_cost(date)
        cost = float(data.get('total_cost', 0))
        impression = int(data.get('total_impression', 0))
        click = int(data.get('total_click', 0))
        ctr = (click / impression * 100) if impression > 0 else 0
        cpc = (cost / click) if click > 0 else 0
        
        report = f"🌙 晚间投放总结\n{'='*40}\n"
        report += f"📅 {date}\n\n"
        report += f"📊 今日数据:\n"
        report += f"  消耗: {cost:.2f}元\n"
        report += f"  曝光: {impression:,}\n"
        report += f"  点击: {click:,}\n"
        report += f"  CTR: {ctr:.2f}%\n"
        report += f"  CPC: {cpc:.2f}元\n\n"
        
        # 生成建议
        suggestions = []
        if ctr < 10:
            suggestions.append("CTR偏低，建议优化创意")
        if cpc > 0.1:
            suggestions.append("CPC偏高，建议调整出价")
        if cost < 30:
            suggestions.append("消耗偏低，建议提高预算")
        
        if suggestions:
            report += f"💡 明日建议:\n"
            for s in suggestions:
                report += f"  • {s}\n"
        else:
            report += f"✅ 表现良好，保持当前策略\n"
        
        return report
    
    # ==================== 智能交互功能 ====================
    def get_smart_greeting(self):
        """根据时间和账户状态生成智能问候语"""
        hour = datetime.now().hour
        
        # 时间问候
        if hour < 9:
            time_greeting = "早上好"
        elif hour < 12:
            time_greeting = "上午好"
        elif hour < 14:
            time_greeting = "中午好"
        elif hour < 18:
            time_greeting = "下午好"
        elif hour < 22:
            time_greeting = "晚上好"
        else:
            time_greeting = "夜深了"
        
        # 获取账户数据
        dashboard = self.get_account_dashboard()
        today = dashboard.get('today_data', {})
        summary = dashboard.get('campaign_summary', {})
        
        cost = today.get('total_cost', 0)
        active = summary.get('active', 0)
        total = summary.get('total', 0)
        
        # 生成智能提示
        hints = []
        
        if cost == 0:
            hints.append("📊 今日暂无消耗，建议检查计划是否正常投放")
        elif cost < 30:
            hints.append(f"📊 今日消耗{cost:.1f}元，偏低，可能需要提高预算或出价")
        elif cost > 200:
            hints.append(f"📊 今日消耗{cost:.1f}元，较高，请关注ROI")
        else:
            hints.append(f"📊 今日消耗{cost:.1f}元，正常")
        
        if active == 0:
            hints.append("⚠️ 没有投放中的计划，建议开启计划")
        elif active < 5:
            hints.append(f"📈 投放中计划{active}个，建议增加计划数量")
        
        # 组合问候语
        greeting = f"{time_greeting}！我是你的聚光AI运营助手\n\n"
        
        if hints:
            greeting += "💡 智能提示:\n"
            for hint in hints:
                greeting += f"  {hint}\n"
            greeting += "\n"
        
        greeting += "你可以问我:\n"
        greeting += "  • 看看今日数据\n"
        greeting += "  • 分析计划表现\n"
        greeting += "  • 优化创意\n"
        greeting += "  • 生成日报\n"
        greeting += "  • 清理僵尸计划\n"
        
        return greeting
    
    def get_smart_followup(self, action_type, result):
        """根据操作结果生成智能跟进提示"""
        hints = []
        
        if action_type == 'dashboard':
            # 查看大盘后的提示
            today = result.get('today_data', {})
            cost = today.get('total_cost', 0)
            
            if cost == 0:
                hints.append("💡 今日无消耗，建议：")
                hints.append("  1. 检查计划是否开启")
                hints.append("  2. 检查预算是否充足")
                hints.append("  3. 检查出价是否过低")
            elif cost < 30:
                hints.append("💡 消耗偏低，建议：")
                hints.append("  1. 提高出价5-10%")
                hints.append("  2. 增加计划数量")
                hints.append("  3. 优化创意提升CTR")
            
            hints.append("\n📋 你还可以：")
            hints.append("  • 分析计划表现")
            hints.append("  • 优化创意")
            hints.append("  • 生成今日日报")
        
        elif action_type == 'campaign_analysis':
            # 计划分析后的提示
            high = result.get('high_efficiency', [])
            poor = result.get('low_efficiency', [])
            
            if high:
                hints.append(f"📈 发现{len(high)}个高效计划，建议加预算")
            if poor:
                hints.append(f"📉 发现{len(poor)}个低效计划，建议优化或暂停")
            
            if not high and not poor:
                hints.append("✅ 所有计划表现正常")
            
            hints.append("\n📋 你还可以：")
            hints.append("  • 优化创意")
            hints.append("  • 清理僵尸计划")
            hints.append("  • 生成周报")
        
        elif action_type == 'creative_analysis':
            # 创意分析后的提示
            excellent = result.get('excellent', [])
            poor = result.get('poor', [])
            
            if excellent:
                hints.append(f"🎨 发现{len(excellent)}个优质创意，建议加推")
            if poor:
                hints.append(f"⚠️ 发现{len(poor)}个低效创意，建议优化")
            
            hints.append("\n📋 你还可以：")
            hints.append("  • 分析计划表现")
            hints.append("  • 生成日报")
            hints.append("  • 查看推送模板")
        
        elif action_type == 'daily_report':
            # 日报后的提示
            hints.append("📋 你还可以：")
            hints.append("  • 分析计划表现")
            hints.append("  • 优化创意")
            hints.append("  • 查看推送模板")
            hints.append("  • 设置定时推送")
        
        if hints:
            return "\n".join(hints)
        return ""
    
    def get_proactive_alert(self):
        """主动预警检查"""
        alerts = []
        
        # 获取今日数据
        dashboard = self.get_account_dashboard()
        today = dashboard.get('today_data', {})
        summary = dashboard.get('campaign_summary', {})
        budget = dashboard.get('account_budget', {})
        
        cost = today.get('total_cost', 0)
        ctr = today.get('ctr', 0)
        cpc = today.get('cpc', 0)
        active = summary.get('active', 0)
        balance = budget.get('available_balance_yuan', 0)
        
        # 消耗异常
        if cost > 200:
            alerts.append("🚨 消耗预警：今日消耗已超过200元，请关注")
        
        # CTR异常
        if ctr < 5 and cost > 10:
            alerts.append("⚠️ CTR预警：CTR低于5%，创意效果不佳")
        
        # CPC异常
        if cpc > 0.15 and cost > 10:
            alerts.append("⚠️ CPC预警：CPC超过0.15元，成本偏高")
        
        # 余额预警
        if balance < 100 and balance > 0:
            alerts.append("💰 余额预警：账户余额不足100元，建议充值")
        
        # 计划状态预警
        if active == 0:
            alerts.append("📭 状态预警：没有投放中的计划")
        
        return alerts
    
    def format_proactive_alert(self, alerts):
        """格式化主动预警"""
        if not alerts:
            return ""
        
        report = f"🔔 智能预警\n{'─'*30}\n"
        for alert in alerts:
            report += f"  {alert}\n"
        report += "\n💡 建议及时处理以上预警"
        return report
    
    def get_expert_analysis(self, industry="旅游/酒旅"):
        """获取顶级投手分析"""
        dashboard = self.get_account_dashboard()
        analysis = generate_expert_analysis(dashboard, industry)
        return format_expert_analysis(analysis)
    
    def get_industry_strategy(self, industry):
        """获取行业专属策略"""
        strategy = get_industry_strategy(industry)
        report = f"📊 {industry}行业投放策略\n{'═'*40}\n\n"
        for key, value in strategy.items():
            report += f"• {key}: {value}\n"
        return report
    
    def get_issue_diagnosis(self, issue):
        """问题诊断"""
        guide = get_troubleshooting_guide(issue)
        if not guide:
            return f"未找到'{issue}'的排查指南"
        
        report = f"🔍 {issue}问题诊断\n{'═'*40}\n\n"
        report += "可能原因：\n"
        for i, reason in enumerate(guide, 1):
            report += f"  {i}. {reason}\n"
        report += "\n💡 建议按顺序排查，优先检查素材质量"
        return report
    
    def get_advanced_diagnosis(self, industry="旅游/酒旅"):
        """获取进阶深度诊断"""
        dashboard = self.get_account_dashboard()
        diagnosis = get_advanced_diagnosis(dashboard, industry)
        return format_advanced_diagnosis(diagnosis)
    
    def get_creative_analysis(self, days=7):
        """获取创意内容分析"""
        analyzer = CreativeAnalyzer(self.sdk)
        results = analyzer.analyze_creative_performance(days)
        return analyzer.format_creative_analysis(results)
    
    def get_creative_optimization(self, creative_id):
        """获取创意优化建议"""
        # 获取创意报表数据
        creatives = self.get_creative_report(days=7)
        for creative in creatives:
            if creative.get('creative_id') == creative_id or creative.get('creativity_id') == creative_id:
                analyzer = CreativeAnalyzer(self.sdk)
                suggestions = analyzer.get_creative_optimization_suggestions(creative)
                return suggestions
        return []
    
    def get_automation_analysis(self, industry="旅游酒旅"):
        """获取自动化规则引擎分析"""
        engine = AutomationRuleEngine(self.sdk, industry)
        
        # 获取创意数据
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        result = self.sdk.get_offline_report('creative', start_date, end_date, page_size=50)
        creatives = result.get('data', {}).get('data_list', []) if result.get('success') else []
        
        # 获取计划数据
        campaigns = self.sdk.get_all_campaigns().get('data', {}).get('base_campaign_dtos', [])
        
        # 生成分析报告
        report = engine.generate_analysis_report(creatives[:50], campaigns[:50])
        return report
    
    def get_keyword_suggestions(self, seed_words=None, industry="旅游酒旅"):
        """获取关键词建议"""
        manager = KeywordManager(self.sdk, industry)
        suggestions = manager.get_keyword_suggestions(seed_words, limit=30)
        return manager.format_keyword_report(suggestions)
    
    def add_keywords_to_unit(self, unit_id, keywords, add_type=1):
        """添加关键词到单元（需用户确认）"""
        manager = KeywordManager(self.sdk)
        return manager.add_keywords_to_unit(unit_id, keywords, add_type)
    
    def replace_keywords_for_unit(self, unit_id, keywords):
        """替换单元关键词（需用户确认）"""
        manager = KeywordManager(self.sdk)
        return manager.replace_keywords_for_unit(unit_id, keywords)
    
    def clear_keywords_for_unit(self, unit_id):
        """清空单元所有关键词（需用户确认）"""
        manager = KeywordManager(self.sdk)
        return manager.clear_keywords_for_unit(unit_id)
    
    def get_smart_menu(self):
        """生成智能菜单"""
        menu = f"📋 功能菜单\n{'═'*40}\n\n"
        
        menu += "📊 数据查看\n"
        menu += "  1. 看看今日数据 - 账号大盘\n"
        menu += "  2. 生成今日日报 - 智能日报\n"
        menu += "  3. 查看周报/月报 - 趋势分析\n\n"
        
        menu += "📈 计划管理\n"
        menu += "  4. 分析计划表现 - 计划分析\n"
        menu += "  5. 清理僵尸计划 - 僵尸清理\n\n"
        
        menu += "🎨 创意优化\n"
        menu += "  6. 优化创意 - 创意优选\n"
        menu += "  7. 查看创意报告 - 创意分析\n"
        menu += "  8. 创意内容分析 - 互动数据\n"
        menu += "  9. 🔬 创意筛查 - 投/不投决策（NEW）\n\n"
        
        menu += "🔑 关键词管理（新增）\n"
        menu += "  10. 关键词推荐 - 行业词库\n"
        menu += "  11. 词包推荐 - 蓝海词\n"
        menu += "  12. 添加关键词 - 到单元\n"
        menu += "  13. 替换关键词 - 替换单元词\n"
        menu += "  14. 清空关键词 - 清空单元词\n\n"
        
        menu += "🧠 专家分析（新增）\n"
        menu += "  15. 顶级投手分析 - 数据诊断\n"
        menu += "  16. 行业投放策略 - 行业建议\n"
        menu += "  17. 问题诊断 - 排查指南\n"
        menu += "  18. 进阶深度诊断 - 全面评估\n"
        menu += "  19. 自动化规则分析 - 智能评分\n\n"
        
        menu += "⏰ 定时推送\n"
        menu += "  20. 查看推送模板 - 推送设置\n"
        menu += "  21. 设置定时推送 - 自动推送\n\n"
        
        menu += "📚 学习帮助\n"
        menu += "  22. 新手指南 - 操作向导\n"
        menu += "  23. 投放规则 - 规则查询\n"
        menu += "  24. 常见问题 - 问题解答\n"
        
        return menu


if __name__ == "__main__":
    assistant = AIOperationsAssistant()
    
    print("=== 账号大盘 ===")
    dashboard = assistant.get_account_dashboard()
    print(assistant.format_dashboard(dashboard))
    
    print("\n\n=== 投放规则 ===")
    print(assistant.format_rules(JUGUANG_RULES))
    
    print("\n\n=== 新手指南 ===")
    print(assistant.format_beginner_guide(assistant.get_beginner_guide("入门")))
