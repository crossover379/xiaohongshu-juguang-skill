"""
创意内容分析模块 v1.0
基于投放数据+互动数据+封面图片进行创意优化分析
"""

import json
import os
import requests
from datetime import datetime, timedelta
from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK


class CreativeAnalyzer:
    """创意内容分析器"""
    
    def __init__(self, sdk=None):
        self.sdk = sdk or XiaohongshuJuguangSDK()
    
    def get_creative_report(self, days=7, page_size=100):
        """获取创意报表数据"""
        end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        all_creatives = []
        page = 1
        
        while True:
            result = self.sdk.get_offline_report(
                'creative', start_date, end_date, 
                page=page, page_size=page_size
            )
            
            if not result.get('success'):
                break
            
            data_list = result.get('data', {}).get('data_list', [])
            if not data_list:
                break
            
            all_creatives.extend(data_list)
            
            # 检查是否还有更多数据
            total = result.get('data', {}).get('total_count', 0)
            if len(all_creatives) >= total:
                break
            
            page += 1
        
        return all_creatives
    
    def analyze_creative_performance(self, days=7):
        """分析创意表现"""
        creatives = self.get_creative_report(days)
        
        if not creatives:
            return {'excellent': [], 'good': [], 'normal': [], 'poor': [], 'dead': []}
        
        results = {
            'excellent': [],  # 优质创意
            'good': [],       # 良好创意
            'normal': [],     # 正常创意
            'poor': [],       # 低效创意
            'dead': [],       # 僵尸创意
        }
        
        for creative in creatives:
            # 提取关键数据
            creative_id = creative.get('creative_id') or creative.get('creativity_id', '')
            creative_name = creative.get('creative_name') or creative.get('creativity_name', '未命名')
            note_id = creative.get('note_id', '')
            image_url = creative.get('creative_image') or creative.get('creativity_image', '')
            
            # 互动数据
            impression = int(creative.get('impression', 0))
            click = int(creative.get('click', 0))
            like = int(creative.get('like', 0))
            collect = int(creative.get('collect', 0))
            comment = int(creative.get('comment', 0))
            share = int(creative.get('share', 0))
            follow = int(creative.get('follow', 0))
            interaction = int(creative.get('interaction', 0))
            pic_save = int(creative.get('pic_save', 0))
            screenshot = int(creative.get('screenshot', 0))
            
            # 转化数据
            message = int(creative.get('message', 0))
            message_consult = int(creative.get('message_consult', 0))
            initiative_message = int(creative.get('initiative_message', 0))
            leads = int(creative.get('leads', 0))
            valid_leads = int(creative.get('valid_leads', 0))
            
            # 效率指标
            fee = float(creative.get('fee', 0))
            ctr = float(creative.get('ctr', '0%').replace('%', ''))
            cpc = float(creative.get('acp', 0))
            cpm = float(creative.get('cpm', 0))
            
            # 计算互动率
            engagement_rate = (interaction / impression * 100) if impression > 0 else 0
            
            # 计算转化率
            conversion_rate = (leads / click * 100) if click > 0 else 0
            
            # 分类
            if fee == 0 and impression == 0:
                results['dead'].append({
                    'creative_id': creative_id,
                    'creative_name': creative_name,
                    'note_id': note_id,
                    'image_url': image_url,
                    'fee': fee,
                    'impression': impression,
                    'click': click,
                    'status': '僵尸创意',
                })
            elif ctr < 2.0 or engagement_rate < 1.0:
                results['poor'].append({
                    'creative_id': creative_id,
                    'creative_name': creative_name,
                    'note_id': note_id,
                    'image_url': image_url,
                    'fee': fee,
                    'impression': impression,
                    'click': click,
                    'ctr': ctr,
                    'engagement_rate': engagement_rate,
                    'like': like,
                    'collect': collect,
                    'comment': comment,
                    'status': '低效创意',
                })
            elif ctr >= 5.0 and engagement_rate >= 3.0 and leads > 0:
                results['excellent'].append({
                    'creative_id': creative_id,
                    'creative_name': creative_name,
                    'note_id': note_id,
                    'image_url': image_url,
                    'fee': fee,
                    'impression': impression,
                    'click': click,
                    'ctr': ctr,
                    'engagement_rate': engagement_rate,
                    'like': like,
                    'collect': collect,
                    'comment': comment,
                    'leads': leads,
                    'conversion_rate': conversion_rate,
                    'status': '优质创意',
                })
            elif ctr >= 3.0 and engagement_rate >= 2.0:
                results['good'].append({
                    'creative_id': creative_id,
                    'creative_name': creative_name,
                    'note_id': note_id,
                    'image_url': image_url,
                    'fee': fee,
                    'impression': impression,
                    'click': click,
                    'ctr': ctr,
                    'engagement_rate': engagement_rate,
                    'like': like,
                    'collect': collect,
                    'comment': comment,
                    'leads': leads,
                    'status': '良好创意',
                })
            else:
                results['normal'].append({
                    'creative_id': creative_id,
                    'creative_name': creative_name,
                    'note_id': note_id,
                    'image_url': image_url,
                    'fee': fee,
                    'impression': impression,
                    'click': click,
                    'ctr': ctr,
                    'engagement_rate': engagement_rate,
                    'like': like,
                    'collect': collect,
                    'comment': comment,
                    'leads': leads,
                    'status': '正常创意',
                })
        
        return results
    
    def format_creative_analysis(self, results):
        """格式化创意分析结果"""
        report = f"🎨 创意内容分析\n{'═'*45}\n\n"
        
        # 统计
        excellent_count = len(results.get('excellent', []))
        good_count = len(results.get('good', []))
        normal_count = len(results.get('normal', []))
        poor_count = len(results.get('poor', []))
        dead_count = len(results.get('dead', []))
        
        report += f"📊 创意分布\n"
        report += f"  ✅ 优质创意: {excellent_count}个\n"
        report += f"  👍 良好创意: {good_count}个\n"
        report += f"  ➖ 正常创意: {normal_count}个\n"
        report += f"  ⚠️ 低效创意: {poor_count}个\n"
        report += f"  💀 僵尸创意: {dead_count}个\n\n"
        
        # 优质创意详情
        if results.get('excellent'):
            report += f"{'─'*40}\n"
            report += f"✅ 优质创意（建议加推）\n\n"
            for i, creative in enumerate(results['excellent'][:5], 1):
                report += f"  {i}. {creative['creative_name'][:30]}...\n"
                report += f"     CTR: {creative['ctr']:.1f}% | 互动率: {creative['engagement_rate']:.1f}%\n"
                report += f"     点赞: {creative['like']} | 收藏: {creative['collect']} | 评论: {creative['comment']}\n"
                report += f"     线索: {creative['leads']} | 转化率: {creative['conversion_rate']:.1f}%\n\n"
        
        # 低效创意详情
        if results.get('poor'):
            report += f"{'─'*40}\n"
            report += f"⚠️ 低效创意（建议优化）\n\n"
            for i, creative in enumerate(results['poor'][:5], 1):
                report += f"  {i}. {creative['creative_name'][:30]}...\n"
                report += f"     CTR: {creative['ctr']:.1f}% | 互动率: {creative['engagement_rate']:.1f}%\n"
                report += f"     问题: "
                if creative['ctr'] < 2.0:
                    report += "CTR低（封面/标题问题）"
                if creative['engagement_rate'] < 1.0:
                    report += "互动率低（内容问题）"
                report += "\n\n"
        
        # 僵尸创意
        if results.get('dead'):
            report += f"{'─'*40}\n"
            report += f"💀 僵尸创意（建议清理）\n\n"
            for i, creative in enumerate(results['dead'][:5], 1):
                report += f"  {i}. {creative['creative_name'][:30]}...\n"
                report += f"     曝光: {creative['impression']} | 点击: {creative['click']}\n\n"
        
        return report
    
    def get_creative_optimization_suggestions(self, creative_data):
        """获取创意优化建议"""
        suggestions = []
        
        # 提取数据
        ctr = float(creative_data.get('ctr', '0%').replace('%', ''))
        engagement_rate = (creative_data.get('interaction', 0) / creative_data.get('impression', 1) * 100) if creative_data.get('impression', 0) > 0 else 0
        like = int(creative_data.get('like', 0))
        collect = int(creative_data.get('collect', 0))
        comment = int(creative_data.get('comment', 0))
        leads = int(creative_data.get('leads', 0))
        
        # CTR分析
        if ctr < 2.0:
            suggestions.append({
                'type': 'CTR优化',
                'level': '⚠️',
                'issue': f'CTR {ctr:.1f}%，低于2%',
                'suggestion': '封面和标题问题：\n1. 封面需要高饱和对比色+醒目大字\n2. 标题前10字必须包含核心关键词\n3. 封面要直击用户痛点',
                'priority': '高',
            })
        elif ctr >= 5.0:
            suggestions.append({
                'type': 'CTR优秀',
                'level': '✅',
                'issue': f'CTR {ctr:.1f}%，表现优秀',
                'suggestion': '封面和标题效果好，可以作为模板复制到其他创意',
                'priority': '低',
            })
        
        # 互动率分析
        if engagement_rate < 1.0:
            suggestions.append({
                'type': '互动率优化',
                'level': '⚠️',
                'issue': f'互动率 {engagement_rate:.1f}%，低于1%',
                'suggestion': '内容问题：\n1. 正文要真实体验→解决痛点→购买理由\n2. 评论区置顶引导转化\n3. 互动率低说明内容没有引发用户共鸣',
                'priority': '高',
            })
        
        # 互动数据综合分析
        if like > 0 and collect > 0 and comment > 0:
            # 计算互动比例
            total_interaction = like + collect + comment
            like_ratio = like / total_interaction * 100
            collect_ratio = collect / total_interaction * 100
            comment_ratio = comment / total_interaction * 100
            
            if collect_ratio < 10:
                suggestions.append({
                    'type': '收藏率低',
                    'level': '💡',
                    'issue': f'收藏占比 {collect_ratio:.1f}%，偏低',
                    'suggestion': '收藏低说明内容实用性不够：\n1. 增加干货内容、攻略、教程\n2. 让用户觉得"以后用得上"\n3. 添加收藏引导语',
                    'priority': '中',
                })
            
            if comment_ratio < 5:
                suggestions.append({
                    'type': '评论率低',
                    'level': '💡',
                    'issue': f'评论占比 {comment_ratio:.1f}%，偏低',
                    'suggestion': '评论低说明互动性不够：\n1. 在正文末尾提问引导评论\n2. 设置争议性话题引发讨论\n3. 及时回复用户评论',
                    'priority': '中',
                })
        
        # 转化分析
        if leads == 0 and creative_data.get('click', 0) > 100:
            suggestions.append({
                'type': '转化优化',
                'level': '⚠️',
                'issue': '有点击无转化',
                'suggestion': '转化问题：\n1. 检查落地页与素材的关联性\n2. 优化转化入口和引导话术\n3. 检查私信回复是否及时',
                'priority': '高',
            })
        
        return suggestions


if __name__ == "__main__":
    analyzer = CreativeAnalyzer()
    
    print("=== 创意内容分析 ===\n")
    results = analyzer.analyze_creative_performance(days=7)
    print(analyzer.format_creative_analysis(results))
