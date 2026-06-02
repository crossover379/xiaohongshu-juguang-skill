"""
关键词管理模块 v1.0
基于聚光API的关键词推荐、分析、优化
"""

import sys, os as _sys_os
_scripts_dir = _sys_os.path.dirname(_sys_os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

import json
import os
from datetime import datetime, timedelta
from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK


# ==================== 行业关键词库 ====================
INDUSTRY_KEYWORDS = {
    "旅游酒旅": {
        "核心词": ["酒店", "民宿", "住宿", "度假", "旅游", "旅行"],
        "长尾词": ["厦门酒店", "海景酒店", "亲子酒店", "度假酒店", "网红民宿"],
        "场景词": ["周末出游", "节假日旅行", "情侣度假", "家庭出游", "闺蜜旅行"],
        "痛点词": ["酒店攻略", "住宿推荐", "性价比酒店", "特价酒店", "酒店测评"],
    },
    "本地生活": {
        "核心词": ["美食", "餐厅", "外卖", "团购", "优惠", "探店"],
        "长尾词": ["厦门美食", "网红餐厅", "必吃榜", "美食攻略", "探店打卡"],
        "场景词": ["周末聚餐", "约会餐厅", "家庭聚餐", "朋友聚会", "生日派对"],
        "痛点词": ["美食推荐", "餐厅测评", "性价比美食", "隐藏美食", "地道美食"],
    },
    "电商零售": {
        "核心词": ["好物", "推荐", "必买", "种草", "测评", "开箱"],
        "长尾词": ["好物推荐", "必买清单", "种草好物", "真实测评", "开箱分享"],
        "场景词": ["换季必备", "节日礼物", "自用好物", "回购推荐", "新品首发"],
        "痛点词": ["避坑指南", "踩雷分享", "真假对比", "性价比推荐", "平价替代"],
    },
    "美妆护肤": {
        "核心词": ["护肤", "美妆", "化妆", "护肤", "美白", "防晒"],
        "长尾词": ["护肤步骤", "化妆教程", "美白方法", "防晒推荐", "护肤心得"],
        "场景词": ["日常护肤", "约会妆容", "职场妆容", "学生党护肤", "换季护肤"],
        "痛点词": ["护肤误区", "成分分析", "敏感肌护肤", "痘痘肌护肤", "抗衰老"],
    },
    "知识教育": {
        "核心词": ["学习", "教程", "课程", "考试", "技能", "提升"],
        "长尾词": ["学习方法", "教程分享", "课程推荐", "考试攻略", "技能提升"],
        "场景词": ["自学教程", "备考经验", "职场技能", "兴趣学习", "考证攻略"],
        "痛点词": ["学习规划", "时间管理", "学习效率", "考试技巧", "避坑指南"],
    },
}


class KeywordManager:
    """关键词管理器"""
    
    def __init__(self, sdk=None, industry="旅游酒旅"):
        self.sdk = sdk or XiaohongshuJuguangSDK()
        self.industry = industry
        self.keyword_library = INDUSTRY_KEYWORDS.get(industry, INDUSTRY_KEYWORDS["旅游酒旅"])
    
    def get_keyword_suggestions(self, seed_words=None, limit=20):
        """获取关键词建议"""
        suggestions = []
        
        # 1. 从词包推荐获取
        word_bag_result = self.sdk.get_word_bag_list()
        if word_bag_result.get('success'):
            word_bags = word_bag_result.get('data', {}).get('word_tag_dto_list', [])
            for bag in word_bags:
                bag_name = bag.get('name', '')
                # 筛选行业相关词包
                if any(kw in bag_name for kw in ['旅游', '出行', '酒店', '民宿', '本地']):
                    for word in bag.get('word_list', []):
                        keyword = word.get('keyword', '')
                        monthpv = word.get('monthpv', 0)
                        bid = word.get('bid', 0) / 100  # 转换为元
                        competition = word.get('competition_level', '')
                        reasons = word.get('recommend_reason', [])
                        
                        suggestions.append({
                            'keyword': keyword,
                            'source': '词包推荐',
                            'monthpv': monthpv,
                            'bid': bid,
                            'competition': competition,
                            'reasons': reasons,
                            'bag_name': bag_name,
                        })
        
        # 2. 从推荐关键词获取（以词推词）
        if seed_words:
            for seed in seed_words:
                recommend_result = self.sdk.keyword_recommend(seed)
                if recommend_result.get('success'):
                    data = recommend_result.get('data', {})
                    word_list = data.get('word_list', [])
                    for kw in word_list:
                        if isinstance(kw, dict):
                            keyword = kw.get('keyword', '')
                            monthpv = kw.get('monthpv', 0)
                            competition = kw.get('competition_level', '')
                            
                            suggestions.append({
                                'keyword': keyword,
                                'source': f'以词推词({seed})',
                                'monthpv': monthpv,
                                'competition': competition,
                            })
        
        # 3. 从行业关键词库获取
        for category, keywords in self.keyword_library.items():
            for kw in keywords:
                if not any(s['keyword'] == kw for s in suggestions):
                    suggestions.append({
                        'keyword': kw,
                        'source': f'行业库-{category}',
                        'category': category,
                    })
        
        # 去重
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s['keyword'] not in seen:
                seen.add(s['keyword'])
                unique_suggestions.append(s)
        
        return unique_suggestions[:limit]
    
    def analyze_keyword_performance(self, keyword_data):
        """分析关键词表现"""
        analysis = {
            'keyword': keyword_data.get('keyword', ''),
            'impression': int(keyword_data.get('impression', 0)),
            'click': int(keyword_data.get('click', 0)),
            'fee': float(keyword_data.get('fee', 0)),
            'leads': int(keyword_data.get('leads', 0)),
        }
        
        # 计算指标
        if analysis['impression'] > 0:
            analysis['ctr'] = analysis['click'] / analysis['impression'] * 100
        else:
            analysis['ctr'] = 0
        
        if analysis['click'] > 0:
            analysis['cpc'] = analysis['fee'] / analysis['click']
        else:
            analysis['cpc'] = 0
        
        if analysis['leads'] > 0:
            analysis['cpa'] = analysis['fee'] / analysis['leads']
        else:
            analysis['cpa'] = float('inf')
        
        # 评估
        if analysis['ctr'] >= 5.0 and analysis['cpa'] != float('inf') and analysis['cpa'] < 50:
            analysis['level'] = '优质关键词'
            analysis['suggestion'] = '建议加大投放'
        elif analysis['ctr'] >= 3.0:
            analysis['level'] = '良好关键词'
            analysis['suggestion'] = '保持当前投放'
        elif analysis['ctr'] < 2.0:
            analysis['level'] = '低效关键词'
            analysis['suggestion'] = '建议优化或暂停'
        else:
            analysis['level'] = '普通关键词'
            analysis['suggestion'] = '继续观察'
        
        return analysis
    
    def format_keyword_report(self, suggestions, limit=20):
        """格式化关键词报告"""
        report = f"🔑 关键词推荐报告\n{'═'*45}\n\n"
        
        # 按来源分组
        sources = {}
        for s in suggestions:
            source = s.get('source', '未知')
            if source not in sources:
                sources[source] = []
            sources[source].append(s)
        
        # 词包推荐
        if '词包推荐' in sources:
            report += f"📦 词包推荐（{len(sources['词包推荐'])}个）\n{'─'*40}\n"
            for s in sources['词包推荐'][:10]:
                report += f"  • {s['keyword']}\n"
                if s.get('monthpv'):
                    report += f"    月搜索量: {s['monthpv']:,} | 出价: {s.get('bid', 0):.2f}元 | 竞争: {s.get('competition', '')}\n"
                if s.get('reasons'):
                    report += f"    推荐原因: {', '.join(s['reasons'])}\n"
            report += "\n"
        
        # 以词推词
        word_recommend_sources = {k: v for k, v in sources.items() if k.startswith('以词推词')}
        if word_recommend_sources:
            report += f"🔍 以词推词\n{'─'*40}\n"
            for source, words in word_recommend_sources.items():
                seed = source.replace('以词推词(', '').replace(')', '')
                report += f"\n  种子词: {seed}\n"
                for s in words[:5]:
                    report += f"    • {s['keyword']}"
                    if s.get('cover_num'):
                        report += f" - 覆盖人数: {s['cover_num']:,}"
                    if s.get('reasons'):
                        report += f" - {', '.join(s['reasons'])}"
                    report += "\n"
            report += "\n"
        
        # 行业库
        industry_sources = {k: v for k, v in sources.items() if k.startswith('行业库')}
        if industry_sources:
            report += f"📚 行业关键词库\n{'─'*40}\n"
            for source, words in industry_sources.items():
                category = source.replace('行业库-', '')
                report += f"\n  {category}:\n"
                for s in words[:5]:
                    report += f"    • {s['keyword']}\n"
            report += "\n"
        
        return report
    
    def get_keyword_optimization_suggestions(self, current_keywords):
        """获取关键词优化建议"""
        suggestions = []
        
        for kw_data in current_keywords:
            analysis = self.analyze_keyword_performance(kw_data)
            
            if analysis['level'] == '低效关键词':
                suggestions.append({
                    'keyword': analysis['keyword'],
                    'issue': f"CTR {analysis['ctr']:.1f}%，低于2%",
                    'suggestion': '建议优化匹配方式或暂停',
                    'priority': '高',
                })
            elif analysis['level'] == '优质关键词':
                suggestions.append({
                    'keyword': analysis['keyword'],
                    'issue': f"CTR {analysis['ctr']:.1f}%，表现优秀",
                    'suggestion': '建议加大投放，提高出价',
                    'priority': '中',
                })
        
        return suggestions
    
    def check_keyword_in_thesaurus(self, keywords):
        """检查关键词是否在词库中"""
        if isinstance(keywords, str):
            keywords = [keywords]
        
        result = self.sdk.get_keyword_match(keywords)
        if result.get('success'):
            match_infos = result.get('data', {}).get('match_infos', [])
            return {info['keyword']: info['in_thesaurus'] for info in match_infos}
        return {}
    
    def add_keywords_to_unit(self, unit_id, keywords, add_type=1):
        """添加关键词到单元
        add_type: 0=替换（删除已有词再添加） 1=追加（不删除已有词）
        """
        keyword_with_bid = []
        for kw in keywords:
            if isinstance(kw, str):
                keyword_with_bid.append({
                    "keyword": kw,
                    "bid": 0,  # 使用默认出价
                    "phrase_match_type": 0,  # 广泛匹配
                })
            elif isinstance(kw, dict):
                keyword_with_bid.append({
                    "keyword": kw.get('keyword', ''),
                    "bid": kw.get('bid', 0),
                    "phrase_match_type": kw.get('phrase_match_type', 0),
                })
        
        result = self.sdk.add_unit_keyword(
            unit_id=unit_id,
            keyword_with_bid=keyword_with_bid,
            add_type=add_type,
        )
        
        return result
    
    def replace_keywords_for_unit(self, unit_id, keywords):
        """替换单元关键词（清空后添加）"""
        return self.add_keywords_to_unit(unit_id, keywords, add_type=0)
    
    def clear_keywords_for_unit(self, unit_id):
        """清空单元所有关键词"""
        return self.add_keywords_to_unit(unit_id, [], add_type=0)


if __name__ == "__main__":
    manager = KeywordManager(industry="旅游酒旅")
    
    print("=== 关键词推荐 ===\n")
    suggestions = manager.get_keyword_suggestions(
        seed_words=["酒店", "民宿", "厦门旅游"],
        limit=30
    )
    print(manager.format_keyword_report(suggestions))
