#!/usr/bin/env python3
"""
小红书聚光投放数据报告模块 v1.0
支持周报、月报、多维度对比分析。

所有数据来源：账户层（已锁死规则）
标准投放 + 简单投 = 总消耗
"""

import sys, os as _sys_os
_scripts_dir = _sys_os.path.dirname(_sys_os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import json
from datetime import datetime, timedelta


class ReportEngine:
    def __init__(self, sdk):
        self.sdk = sdk

    # ==================== 数据拉取 ====================
    def get_date_range_data(self, start_date, end_date):
        """拉取日期范围内每日消耗数据"""
        return self.sdk.get_daily_cost_range(start_date, end_date)

    def get_week_data(self, year=None, week=None):
        """获取指定周的数据（ISO周）"""
        if not year:
            year = datetime.now().year
        if not week:
            week = datetime.now().isocalendar()[1]
        
        # 计算周的起止日期
        jan4 = datetime(year, 1, 4)
        start_of_week = jan4 + timedelta(weeks=week-1, days=-jan4.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        start_str = start_of_week.strftime("%Y-%m-%d")
        end_str = end_of_week.strftime("%Y-%m-%d")
        
        data = self.get_date_range_data(start_str, end_str)
        return {
            "year": year, "week": week,
            "start_date": start_str, "end_date": end_str,
            "daily_data": data
        }

    def get_month_data(self, year=None, month=None):
        """获取指定月的数据"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        
        data = self.get_date_range_data(start_str, end_str)
        return {
            "year": year, "month": month,
            "start_date": start_str, "end_date": end_str,
            "daily_data": data
        }

    # ==================== 统计计算 ====================
    def calc_summary(self, daily_data):
        """计算汇总数据"""
        if not daily_data:
            return {}
        
        total_cost = sum(d["total_cost"] for d in daily_data)
        total_normal = sum(d["normal_cost"] for d in daily_data)
        total_easy = sum(d["easy_cost"] for d in daily_data)
        total_impression = sum(d["total_impression"] for d in daily_data)
        total_click = sum(d["total_click"] for d in daily_data)
        
        # 有效天数（有消耗的天）
        active_days = sum(1 for d in daily_data if d["total_cost"] > 0)
        
        # 平均日消耗
        avg_daily = total_cost / len(daily_data) if daily_data else 0
        avg_daily_active = total_cost / active_days if active_days > 0 else 0
        
        # CTR
        ctr = (total_click / total_impression * 100) if total_impression > 0 else 0
        
        # CPC
        cpc = (total_cost / total_click) if total_click > 0 else 0
        
        # CPM
        cpm = (total_cost / total_impression * 1000) if total_impression > 0 else 0
        
        # 简单投占比
        easy_pct = (total_easy / total_cost * 100) if total_cost > 0 else 0
        
        # 日消耗列表（用于趋势分析）
        daily_costs = [d["total_cost"] for d in daily_data]
        
        # 环比（与上一周期对比）
        comparison = None
        if len(daily_data) > 1:
            mid = len(daily_data) // 2
            first_half = daily_data[:mid]
            second_half = daily_data[mid:]
            first_cost = sum(d["total_cost"] for d in first_half)
            second_cost = sum(d["total_cost"] for d in second_half)
            if first_cost > 0:
                change_pct = ((second_cost - first_cost) / first_cost * 100)
            else:
                change_pct = 0
            comparison = {
                "first_half_cost": first_cost,
                "second_half_cost": second_cost,
                "change_pct": round(change_pct, 2)
            }
        
        return {
            "total_cost": round(total_cost, 2),
            "total_normal": round(total_normal, 2),
            "total_easy": round(total_easy, 2),
            "total_impression": total_impression,
            "total_click": total_click,
            "active_days": active_days,
            "total_days": len(daily_data),
            "avg_daily_cost": round(avg_daily, 2),
            "avg_daily_active_cost": round(avg_daily_active, 2),
            "ctr": round(ctr, 2),
            "cpc": round(cpc, 2),
            "cpm": round(cpm, 2),
            "easy_pct": round(easy_pct, 2),
            "daily_costs": daily_costs,
            "comparison": comparison
        }

    # ==================== 报告生成 ====================
    def generate_weekly_report(self, year=None, week=None):
        """生成周报"""
        week_data = self.get_week_data(year, week)
        summary = self.calc_summary(week_data["daily_data"])
        
        report = f"""
📊 小红书聚光投放周报
{'='*45}
📅 周期: {week_data['start_date']} ~ {week_data['end_date']} (第{week_data['week']}周)
{'─'*45}

💰 消耗概况
  总消耗: {summary['total_cost']:.2f}元
  标准投: {summary['total_normal']:.2f}元 ({100-summary['easy_pct']:.1f}%)
  简单投: {summary['total_easy']:.2f}元 ({summary['easy_pct']:.1f}%)
  日均消耗: {summary['avg_daily_cost']:.2f}元
  有效天数: {summary['active_days']}/{summary['total_days']}天

📈 曝光与点击
  总曝光: {summary['total_impression']:,}
  总点击: {summary['total_click']:,}
  CTR: {summary['ctr']:.2f}%
  CPC: {summary['cpc']:.2f}元
  CPM: {summary['cpm']:.2f}元

📅 每日消耗
"""
        for d in week_data["daily_data"]:
            bar = "█" * int(d["total_cost"] / 10) if d["total_cost"] > 0 else "·"
            report += f"  {d['date']}: {d['total_cost']:>8.2f}元 {bar}\n"
        
        if summary["comparison"]:
            comp = summary["comparison"]
            trend = "📈上升" if comp["change_pct"] > 0 else "📉下降" if comp["change_pct"] < 0 else "➡️持平"
            report += f"\n🔄 周内趋势: {trend} {abs(comp['change_pct']):.1f}%\n"
            report += f"   前半周: {comp['first_half_cost']:.2f}元 | 后半周: {comp['second_half_cost']:.2f}元\n"
        
        return report

    def generate_monthly_report(self, year=None, month=None):
        """生成月报"""
        month_data = self.get_month_data(year, month)
        summary = self.calc_summary(month_data["daily_data"])
        
        # 按周分组
        weeks = {}
        for d in month_data["daily_data"]:
            dt = datetime.strptime(d["date"], "%Y-%m-%d")
            week_num = dt.isocalendar()[1]
            weeks.setdefault(week_num, []).append(d)
        
        report = f"""
📊 小红书聚光投放月报
{'='*45}
📅 周期: {month_data['start_date']} ~ {month_data['end_date']}
{'─'*45}

💰 消耗概况
  总消耗: {summary['total_cost']:.2f}元
  标准投: {summary['total_normal']:.2f}元 ({100-summary['easy_pct']:.1f}%)
  简单投: {summary['total_easy']:.2f}元 ({summary['easy_pct']:.1f}%)
  日均消耗: {summary['avg_daily_cost']:.2f}元
  有效天数: {summary['active_days']}/{summary['total_days']}天

📈 曝光与点击
  总曝光: {summary['total_impression']:,}
  总点击: {summary['total_click']:,}
  CTR: {summary['ctr']:.2f}%
  CPC: {summary['cpc']:.2f}元
  CPM: {summary['cpm']:.2f}元

📅 每周汇总
"""
        for week_num in sorted(weeks.keys()):
            week_summary = self.calc_summary(weeks[week_num])
            report += f"  第{week_num}周: {week_summary['total_cost']:.2f}元 (日均{week_summary['avg_daily_cost']:.2f}元)\n"
        
        report += f"\n📅 每日消耗\n"
        for d in month_data["daily_data"]:
            bar = "█" * int(d["total_cost"] / 10) if d["total_cost"] > 0 else "·"
            report += f"  {d['date']}: {d['total_cost']:>8.2f}元 {bar}\n"
        
        return report

    def generate_comparison_report(self, period1_start, period1_end, period2_start, period2_end, label1="前期", label2="后期"):
        """生成对比分析报告"""
        data1 = self.get_date_range_data(period1_start, period1_end)
        data2 = self.get_date_range_data(period2_start, period2_end)
        
        s1 = self.calc_summary(data1)
        s2 = self.calc_summary(data2)
        
        def pct_change(old, new):
            if old > 0:
                return round((new - old) / old * 100, 2)
            return 0
        
        report = f"""
📊 小红书聚光投放对比分析
{'='*45}
📅 {label1}: {period1_start} ~ {period1_end}
📅 {label2}: {period2_start} ~ {period2_end}
{'─'*45}

💰 消耗对比
  {label1}: {s1['total_cost']:.2f}元
  {label2}: {s2['total_cost']:.2f}元
  变化: {pct_change(s1['total_cost'], s2['total_cost']):+.2f}%

📈 曝光对比
  {label1}: {s1['total_impression']:,}
  {label2}: {s2['total_impression']:,}
  变化: {pct_change(s1['total_impression'], s2['total_impression']):+.2f}%

👆 点击对比
  {label1}: {s1['total_click']:,}
  {label2}: {s2['total_click']:,}
  变化: {pct_change(s1['total_click'], s2['total_click']):+.2f}%

📊 CTR对比
  {label1}: {s1['ctr']:.2f}%
  {label2}: {s2['ctr']:.2f}%
  变化: {pct_change(s1['ctr'], s2['ctr']):+.2f}%

💰 CPC对比
  {label1}: {s1['cpc']:.2f}元
  {label2}: {s2['cpc']:.2f}元
  变化: {pct_change(s1['cpc'], s2['cpc']):+.2f}%

📋 结论
"""
        # 自动生成结论
        conclusions = []
        cost_change = pct_change(s1['total_cost'], s2['total_cost'])
        ctr_change = pct_change(s1['ctr'], s2['ctr'])
        cpc_change = pct_change(s1['cpc'], s2['cpc'])
        
        if cost_change > 20:
            conclusions.append(f"  ⚠️ 消耗增长{cost_change:.1f}%，需关注预算控制")
        elif cost_change < -20:
            conclusions.append(f"  📉 消耗下降{abs(cost_change):.1f}%，检查投放状态")
        
        if ctr_change > 10:
            conclusions.append(f"  ✅ CTR提升{ctr_change:.1f}%，素材效果改善")
        elif ctr_change < -10:
            conclusions.append(f"  ⚠️ CTR下降{abs(ctr_change):.1f}%，建议优化素材")
        
        if cpc_change > 15:
            conclusions.append(f"  ⚠️ CPC上涨{cpc_change:.1f}%，竞争加剧或出价过高")
        elif cpc_change < -15:
            conclusions.append(f"  ✅ CPC下降{abs(cpc_change):.1f}%，投放效率提升")
        
        if not conclusions:
            conclusions.append("  ✅ 各项指标波动在正常范围内")
        
        report += "\n".join(conclusions)
        return report

    def generate_daily_detail(self, date=None):
        """生成单日详细报告"""
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        data = self.sdk.get_daily_cost(date)
        
        report = f"""
📊 小红书聚光投放日报
{'='*45}
📅 日期: {date}
{'─'*45}

💰 消耗
  标准投: {data['normal_cost']:.2f}元
  简单投: {data['easy_cost']:.2f}元
  总消耗: {data['total_cost']:.2f}元

📈 曝光
  标准投: {data['normal_impression']:,}
  简单投: {data['easy_impression']:,}
  总曝光: {data['total_impression']:,}

👆 点击
  标准投: {data['normal_click']:,}
  简单投: {data['easy_click']:,}
  总点击: {data['total_click']:,}

📊 效率指标
  CTR: {(data['total_click']/data['total_impression']*100) if data['total_impression']>0 else 0:.2f}%
  CPC: {(data['total_cost']/data['total_click']) if data['total_click']>0 else 0:.2f}元
  CPM: {(data['total_cost']/data['total_impression']*1000) if data['total_impression']>0 else 0:.2f}元
"""
        return report


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
    
    sdk = XiaohongshuJuguangSDK()
    report = ReportEngine(sdk)
    
    # 生成5/27日报
    print(report.generate_daily_detail("2026-05-27"))
    
    # 生成上周周报
    print(report.generate_weekly_report(2026, 21))


# ==================== CSV导出 ====================
def export_daily_data_csv(daily_data, filename):
    """导出每日数据到CSV"""
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['日期', '标准投消耗', '简单投消耗', '总消耗', 
                       '标准投曝光', '简单投曝光', '总曝光',
                       '标准投点击', '简单投点击', '总点击', 'CTR', 'CPC', 'CPM'])
        
        for d in daily_data:
            total_click = d.get('normal_click', 0) + d.get('easy_click', 0)
            total_imp = d.get('normal_impression', 0) + d.get('easy_impression', 0)
            total_cost = d.get('total_cost', 0)
            ctr = (total_click / total_imp * 100) if total_imp > 0 else 0
            cpc = (total_cost / total_click) if total_click > 0 else 0
            cpm = (total_cost / total_imp * 1000) if total_imp > 0 else 0
            
            writer.writerow([
                d.get('date', ''),
                f"{d.get('normal_cost', 0):.2f}",
                f"{d.get('easy_cost', 0):.2f}",
                f"{total_cost:.2f}",
                d.get('normal_impression', 0),
                d.get('easy_impression', 0),
                total_imp,
                d.get('normal_click', 0),
                d.get('easy_click', 0),
                total_click,
                f"{ctr:.2f}%",
                f"{cpc:.2f}",
                f"{cpm:.2f}"
            ])
    
    return filename


# ==================== 数据分析 ====================
def analyze_daily_data(daily_data):
    """分析每日数据，生成统计摘要"""
    if not daily_data:
        return {}
    
    costs = [d.get('total_cost', 0) for d in daily_data]
    impressions = [d.get('total_impression', 0) for d in daily_data]
    clicks = [d.get('total_click', 0) for d in daily_data]
    
    active_days = sum(1 for c in costs if c > 0)
    total_cost = sum(costs)
    total_imp = sum(impressions)
    total_click = sum(clicks)
    
    # 计算统计指标
    avg_cost = total_cost / len(costs) if costs else 0
    avg_daily_active = total_cost / active_days if active_days > 0 else 0
    max_cost = max(costs) if costs else 0
    min_cost = min(c for c in costs if c > 0) if active_days > 0 else 0
    ctr = (total_click / total_imp * 100) if total_imp > 0 else 0
    cpc = (total_cost / total_click) if total_click > 0 else 0
    cpm = (total_cost / total_imp * 1000) if total_imp > 0 else 0
    
    # 标准差
    if len(costs) > 1:
        avg = sum(costs) / len(costs)
        variance = sum((x - avg) ** 2 for x in costs) / len(costs)
        std_dev = variance ** 0.5
    else:
        std_dev = 0
    
    return {
        'total_cost': round(total_cost, 2),
        'total_impression': total_imp,
        'total_click': total_click,
        'active_days': active_days,
        'total_days': len(daily_data),
        'avg_daily_cost': round(avg_cost, 2),
        'avg_daily_active_cost': round(avg_daily_active, 2),
        'max_cost': round(max_cost, 2),
        'min_cost': round(min_cost, 2),
        'cost_std_dev': round(std_dev, 2),
        'ctr': round(ctr, 2),
        'cpc': round(cpc, 2),
        'cpm': round(cpm, 2)
    }


def generate_analysis_report(daily_data, title="数据分析报告"):
    """生成数据分析报告"""
    stats = analyze_daily_data(daily_data)
    
    if not stats:
        return "无数据"
    
    report = f"""
📊 {title}
{'='*45}

💰 消耗统计
  总消耗: {stats['total_cost']:.2f}元
  日均消耗: {stats['avg_daily_cost']:.2f}元
  有效天均: {stats['avg_daily_active_cost']:.2f}元
  最高日消耗: {stats['max_cost']:.2f}元
  最低日消耗: {stats['min_cost']:.2f}元
  消耗波动: {stats['cost_std_dev']:.2f}元

📈 曝光与点击
  总曝光: {stats['total_impression']:,}
  总点击: {stats['total_click']:,}
  CTR: {stats['ctr']:.2f}%
  CPC: {stats['cpc']:.2f}元
  CPM: {stats['cpm']:.2f}元

📅 有效天数: {stats['active_days']}/{stats['total_days']}天
"""
    return report
