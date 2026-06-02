#!/usr/bin/env python3
"""
小红书聚光SDK增强模块 v1.0
在现有SDK基础上增加：重试机制、批量请求、缓存、导出功能
"""

import sys, os as _sys_os
_scripts_dir = _sys_os.path.dirname(_sys_os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import json
import time
import os
from datetime import datetime, timedelta
from functools import lru_cache


class SDKEnhancer:
    """SDK增强器 - 包装现有SDK，增加高级功能"""
    
    def __init__(self, sdk):
        self.sdk = sdk
        self.cache = {}
        self.cache_ttl = 300  # 5分钟缓存
    
    # ==================== 重试机制 ====================
    def _request_with_retry(self, method, max_retries=3, delay=2):
        """带重试的请求封装"""
        for attempt in range(max_retries):
            try:
                result = method()
                return result
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
                    continue
                return {"success": False, "message": f"重试{max_retries}次后失败: {str(e)}"}
    
    # ==================== 缓存 ====================
    def _get_cached(self, key):
        """获取缓存数据"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return data
        return None
    
    def _set_cached(self, key, data):
        """设置缓存"""
        self.cache[key] = (data, time.time())
    
    def get_daily_cost_cached(self, date):
        """带缓存的每日消耗查询"""
        cache_key = f"daily_cost_{date}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        result = self.sdk.get_daily_cost(date)
        self._set_cached(cache_key, result)
        return result
    
    # ==================== 并行拉取优化 ====================
    def get_month_data_fast(self, year=None, month=None):
        """快速拉取月度数据（优化版）"""
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 检查哪些天已经缓存
        all_dates = []
        current = start
        while current <= end:
            all_dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
        
        # 拉取未缓存的数据
        results = []
        for date in all_dates:
            data = self.get_daily_cost_cached(date)
            results.append(data)
        
        return results
    
    # ==================== 数据导出 ====================
    def export_to_csv(self, data, filename):
        """导出数据到CSV"""
        import csv
        
        if not data:
            return
        
        # 获取字段名
        if isinstance(data[0], dict):
            fields = list(data[0].keys())
        else:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
        
        return filename
    
    def export_report_to_csv(self, daily_data, filename):
        """导出报告数据到CSV"""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['日期', '标准投消耗', '简单投消耗', '总消耗', 
                           '标准投曝光', '简单投曝光', '总曝光',
                           '标准投点击', '简单投点击', '总点击', 'CTR'])
            
            for d in daily_data:
                total_click = d.get('normal_click', 0) + d.get('easy_click', 0)
                total_imp = d.get('normal_impression', 0) + d.get('easy_impression', 0)
                ctr = (total_click / total_imp * 100) if total_imp > 0 else 0
                
                writer.writerow([
                    d.get('date', ''),
                    d.get('normal_cost', 0),
                    d.get('easy_cost', 0),
                    d.get('total_cost', 0),
                    d.get('normal_impression', 0),
                    d.get('easy_impression', 0),
                    total_imp,
                    d.get('normal_click', 0),
                    d.get('easy_click', 0),
                    total_click,
                    f"{ctr:.2f}%"
                ])
        
        return filename
    
    # ==================== 数据分析 ====================
    def analyze_weekday_pattern(self, daily_data):
        """分析星期几的消耗模式"""
        weekday_data = {}
        for d in daily_data:
            dt = datetime.strptime(d['date'], '%Y-%m-%d')
            weekday = dt.weekday()  # 0=周一, 6=周日
            if weekday not in weekday_data:
                weekday_data[weekday] = []
            weekday_data[weekday].append(d['total_cost'])
        
        # 计算每个星期几的平均消耗
        weekday_avg = {}
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        for wd, costs in weekday_data.items():
            weekday_avg[weekday_names[wd]] = {
                'avg_cost': sum(costs) / len(costs),
                'days': len(costs),
                'total': sum(costs)
            }
        
        return weekday_avg
    
    def detect_anomalies(self, daily_data, threshold=2):
        """检测消耗异常（基于标准差）"""
        costs = [d['total_cost'] for d in daily_data if d['total_cost'] > 0]
        if len(costs) < 3:
            return []
        
        avg = sum(costs) / len(costs)
        variance = sum((x - avg) ** 2 for x in costs) / len(costs)
        std_dev = variance ** 0.5
        
        anomalies = []
        for d in daily_data:
            if d['total_cost'] > 0:
                z_score = (d['total_cost'] - avg) / std_dev if std_dev > 0 else 0
                if abs(z_score) > threshold:
                    anomalies.append({
                        'date': d['date'],
                        'cost': d['total_cost'],
                        'z_score': round(z_score, 2),
                        'type': 'high' if z_score > 0 else 'low'
                    })
        
        return anomalies
    
    # ==================== 格式化输出 ====================
    def format_cost(self, cost):
        """格式化金额显示"""
        if cost >= 10000:
            return f"{cost/10000:.2f}万"
        elif cost >= 1000:
            return f"{cost/1000:.2f}千"
        else:
            return f"{cost:.2f}"
    
    def format_number(self, num):
        """格式化数字显示"""
        if num >= 10000:
            return f"{num/10000:.1f}万"
        elif num >= 1000:
            return f"{num/1000:.1f}千"
        else:
            return str(num)
    
    def generate_summary_text(self, summary):
        """生成文字摘要"""
        total_cost = summary['total']['fee']
        total_imp = summary['total']['impression']
        total_click = summary['total']['click']
        ctr = (total_click / total_imp * 100) if total_imp > 0 else 0
        
        lines = [
            f"📊 今日数据摘要",
            f"💰 总消耗: {self.format_cost(total_cost)}元",
            f"📈 总曝光: {self.format_number(total_imp)}",
            f"👆 总点击: {self.format_number(total_click)}",
            f"📊 CTR: {ctr:.2f}%",
        ]
        
        if summary['normal'].get('message', 0) > 0:
            lines.append(f"💬 私信: {summary['normal']['message']}条")
        if summary['normal'].get('add_wechat_count', 0) > 0:
            lines.append(f"📱 加微: {summary['normal']['add_wechat_count']}人")
        
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
    
    sdk = XiaohongshuJuguangSDK()
    enhancer = SDKEnhancer(sdk)
    
    # 测试缓存功能
    print("=== 测试缓存 ===")
    r1 = enhancer.get_daily_cost_cached("2026-05-27")
    print(f"第一次查询: {r1['total_cost']:.2f}元")
    
    r2 = enhancer.get_daily_cost_cached("2026-05-27")
    print(f"第二次查询(缓存): {r2['total_cost']:.2f}元")
    
    # 测试异常检测
    print("\n=== 测试异常检测 ===")
    week_data = []
    for i in range(7):
        d = (datetime.now() - timedelta(days=i+1)).strftime("%Y-%m-%d")
        data = enhancer.get_daily_cost_cached(d)
        week_data.append(data)
    
    anomalies = enhancer.detect_anomalies(week_data)
    if anomalies:
        print(f"发现{len(anomalies)}个异常:")
        for a in anomalies:
            print(f"  {a['date']}: {a['cost']:.2f}元 ({a['type']})")
    else:
        print("无异常")
