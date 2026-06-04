#!/usr/bin/env python3
"""
聚光AI投手 - 自我完善系统 v1.0

核心理念：
1. 记录用户反馈和错误，避免重复犯错
2. 基于数据验证反馈的正确性
3. 保护用户隐私，不泄露个人信息
4. 持续进化，越来越好

设计原则：
- 数据不会骗人：所有决策基于实际数据验证
- 有立场但开放：坚持正确的数据，但接受合理的反馈
- 隐私第一：用户个人信息永远不泄露
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class SelfLearningSystem:
    """自我完善系统 - 让AI投手持续进化"""
    
    def __init__(self, data_dir: str = None):
        """初始化自我完善系统
        
        Args:
            data_dir: 数据存储目录，默认为脚本同级目录下的learning_data
        """
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'learning_data')
        
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 用户反馈记录
        self.feedback_file = os.path.join(data_dir, 'user_feedback.json')
        self.feedback_history = self._load_json(self.feedback_file, [])
        
        # 错误记录
        self.error_file = os.path.join(data_dir, 'error_log.json')
        self.error_history = self._load_json(self.error_file, [])
        
        # 学习笔记
        self.learning_file = os.path.join(data_dir, 'learning_notes.json')
        self.learning_notes = self._load_json(self.learning_file, [])
        
        # 最佳实践
        self.best_practices_file = os.path.join(data_dir, 'best_practices.json')
        self.best_practices = self._load_json(self.best_practices_file, {})
        
        # 隐私保护配置
        self.privacy_config = {
            'fields_to_mask': [
                'advertiser_id', 'app_id', 'app_secret', 'access_token',
                'refresh_token', 'phone', 'email', 'name', 'address',
                'id_card', 'bank_account', 'ip_address'
            ],
            'mask_char': '*',
            'mask_length': 4
        }
    
    def _load_json(self, file_path: str, default: Any = None) -> Any:
        """加载JSON文件"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
        return default if default is not None else {}
    
    def _save_json(self, file_path: str, data: Any):
        """保存JSON文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文件失败 {file_path}: {e}")
    
    # ==================== 隐私保护 ====================
    
    def mask_sensitive_data(self, data: Dict) -> Dict:
        """遮盖敏感数据，保护用户隐私
        
        Args:
            data: 包含敏感信息的字典
            
        Returns:
            遮盖后的字典
        """
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        for key, value in data.items():
            # 检查是否是敏感字段
            if any(sensitive in key.lower() for sensitive in self.privacy_config['fields_to_mask']):
                if isinstance(value, str) and len(value) > self.privacy_config['mask_length']:
                    # 保留前2位和后2位，中间用*替代
                    mask_len = len(value) - 4
                    masked_data[key] = value[:2] + self.privacy_config['mask_char'] * mask_len + value[-2:]
                else:
                    masked_data[key] = self.privacy_config['mask_char'] * self.privacy_config['mask_length']
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                masked_data[key] = self.mask_sensitive_data(value)
            elif isinstance(value, list):
                # 处理列表
                masked_data[key] = [
                    self.mask_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data
    
    def sanitize_for_logging(self, data: Any) -> Any:
        """清理数据用于日志记录，确保不泄露敏感信息
        
        Args:
            data: 要清理的数据
            
        Returns:
            清理后的数据
        """
        if isinstance(data, dict):
            return self.mask_sensitive_data(data)
        elif isinstance(data, str):
            # 检查字符串是否包含敏感信息
            for sensitive in self.privacy_config['fields_to_mask']:
                if sensitive in data.lower():
                    return f"[包含敏感信息已隐藏]"
            return data
        return data
    
    # ==================== 反馈记录 ====================
    
    def record_feedback(self, feedback_type: str, content: str, 
                       context: Dict = None, is_valid: bool = None):
        """记录用户反馈
        
        Args:
            feedback_type: 反馈类型（bug/feature/improvement/question）
            content: 反馈内容
            context: 上下文信息（会被隐私处理）
            is_valid: 反馈是否有效（None=待验证，True=有效，False=无效）
        """
        feedback = {
            'id': f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'type': feedback_type,
            'content': content,
            'context': self.sanitize_for_logging(context) if context else None,
            'is_valid': is_valid,
            'status': 'pending' if is_valid is None else ('valid' if is_valid else 'invalid'),
            'applied': False
        }
        
        self.feedback_history.append(feedback)
        self._save_json(self.feedback_file, self.feedback_history)
        
        return feedback['id']
    
    def validate_feedback(self, feedback_id: str, is_valid: bool, reason: str = None):
        """验证用户反馈
        
        Args:
            feedback_id: 反馈ID
            is_valid: 是否有效
            reason: 验证原因
        """
        for feedback in self.feedback_history:
            if feedback['id'] == feedback_id:
                feedback['is_valid'] = is_valid
                feedback['status'] = 'valid' if is_valid else 'invalid'
                feedback['validation_reason'] = reason
                feedback['validation_time'] = datetime.now().isoformat()
                break
        
        self._save_json(self.feedback_file, self.feedback_history)
    
    def get_pending_feedback(self) -> List[Dict]:
        """获取待验证的反馈"""
        return [f for f in self.feedback_history if f['status'] == 'pending']
    
    def get_valid_feedback(self) -> List[Dict]:
        """获取已验证的有效反馈"""
        return [f for f in self.feedback_history if f['status'] == 'valid']
    
    # ==================== 错误记录 ====================
    
    def record_error(self, error_type: str, error_message: str, 
                    context: Dict = None, solution: str = None):
        """记录错误
        
        Args:
            error_type: 错误类型（api/validation/logic/unknown）
            error_message: 错误信息
            context: 上下文信息（会被隐私处理）
            solution: 解决方案
        """
        error = {
            'id': f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message,
            'context': self.sanitize_for_logging(context) if context else None,
            'solution': solution,
            'resolved': solution is not None
        }
        
        self.error_history.append(error)
        self._save_json(self.error_file, self.error_history)
        
        return error['id']
    
    def add_error_solution(self, error_id: str, solution: str):
        """为错误添加解决方案"""
        for error in self.error_history:
            if error['id'] == error_id:
                error['solution'] = solution
                error['resolved'] = True
                error['resolved_time'] = datetime.now().isoformat()
                break
        
        self._save_json(self.error_file, self.error_history)
    
    def get_unresolved_errors(self) -> List[Dict]:
        """获取未解决的错误"""
        return [e for e in self.error_history if not e['resolved']]
    
    def get_error_solutions(self, error_type: str = None) -> List[Dict]:
        """获取错误解决方案"""
        errors = self.error_history
        if error_type:
            errors = [e for e in errors if e['type'] == error_type]
        return [e for e in errors if e['resolved']]
    
    # ==================== 学习笔记 ====================
    
    def add_learning_note(self, category: str, content: str, 
                         source: str = None, importance: int = 5):
        """添加学习笔记
        
        Args:
            category: 分类（api/user_behavior/best_practice/mistake）
            content: 笔记内容
            source: 来源（用户反馈/文档/实践）
            importance: 重要性（1-10）
        """
        note = {
            'id': f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'content': content,
            'source': source,
            'importance': importance,
            'times_applied': 0,
            'last_applied': None
        }
        
        self.learning_notes.append(note)
        self._save_json(self.learning_file, self.learning_notes)
        
        return note['id']
    
    def get_learning_notes(self, category: str = None, 
                          min_importance: int = None) -> List[Dict]:
        """获取学习笔记"""
        notes = self.learning_notes
        if category:
            notes = [n for n in notes if n['category'] == category]
        if min_importance:
            notes = [n for n in notes if n['importance'] >= min_importance]
        return sorted(notes, key=lambda x: x['importance'], reverse=True)
    
    def apply_learning_note(self, note_id: str):
        """标记学习笔记已应用"""
        for note in self.learning_notes:
            if note['id'] == note_id:
                note['times_applied'] += 1
                note['last_applied'] = datetime.now().isoformat()
                break
        
        self._save_json(self.learning_file, self.learning_notes)
    
    # ==================== 最佳实践 ====================
    
    def add_best_practice(self, category: str, title: str, 
                         content: str, data_source: str = None):
        """添加最佳实践
        
        Args:
            category: 分类（bidding/creative/targeting/budget）
            title: 标题
            content: 内容
            data_source: 数据来源（实际验证/行业标准/用户反馈）
        """
        if category not in self.best_practices:
            self.best_practices[category] = []
        
        practice = {
            'id': f"bp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'title': title,
            'content': content,
            'data_source': data_source,
            'confidence': 0.5,  # 初始置信度
            'times_verified': 0,
            'last_verified': None
        }
        
        self.best_practices[category].append(practice)
        self._save_json(self.best_practices_file, self.best_practices)
        
        return practice['id']
    
    def verify_best_practice(self, category: str, practice_id: str, 
                            is_correct: bool, data: Dict = None):
        """验证最佳实践
        
        Args:
            category: 分类
            practice_id: 实践ID
            is_correct: 是否正确
            data: 验证数据
        """
        if category in self.best_practices:
            for practice in self.best_practices[category]:
                if practice['id'] == practice_id:
                    practice['times_verified'] += 1
                    practice['last_verified'] = datetime.now().isoformat()
                    
                    # 更新置信度
                    if is_correct:
                        practice['confidence'] = min(1.0, practice['confidence'] + 0.1)
                    else:
                        practice['confidence'] = max(0.0, practice['confidence'] - 0.2)
                    
                    if data:
                        practice['verification_data'] = self.sanitize_for_logging(data)
                    break
        
        self._save_json(self.best_practices_file, self.best_practices)
    
    def get_best_practices(self, category: str = None, 
                          min_confidence: float = None) -> List[Dict]:
        """获取最佳实践"""
        if category:
            practices = self.best_practices.get(category, [])
        else:
            practices = []
            for cat_practices in self.best_practices.values():
                practices.extend(cat_practices)
        
        if min_confidence:
            practices = [p for p in practices if p['confidence'] >= min_confidence]
        
        return sorted(practices, key=lambda x: x['confidence'], reverse=True)
    
    # ==================== 智能建议 ====================
    
    def get_suggestions(self, context: str) -> List[str]:
        """基于学习历史获取智能建议
        
        Args:
            context: 当前上下文（如"出价调整"、"创意优化"等）
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 1. 从学习笔记中查找相关建议
        for note in self.learning_notes:
            if context in note['content'] or context in note['category']:
                suggestions.append(f"📚 学习笔记：{note['content']}")
        
        # 2. 从最佳实践中查找相关建议
        for category, practices in self.best_practices.items():
            if context in category:
                for practice in practices:
                    if practice['confidence'] >= 0.7:
                        suggestions.append(f"✅ 最佳实践：{practice['title']} - {practice['content']}")
        
        # 3. 从错误记录中查找避免的错误
        for error in self.error_history:
            if error['resolved'] and (context in error['message'] or context in error.get('solution', '')):
                suggestions.append(f"⚠️ 避免错误：{error['message']} → 解决方案：{error['solution']}")
        
        return suggestions[:5]  # 最多返回5条建议
    
    def should_avoid(self, action: str) -> Optional[str]:
        """检查某个操作是否应该避免
        
        Args:
            action: 要执行的操作
            
        Returns:
            如果应该避免，返回原因；否则返回None
        """
        # 检查是否有相关的无效反馈
        for feedback in self.feedback_history:
            if feedback['status'] == 'invalid' and action in feedback['content']:
                return f"用户反馈此操作无效：{feedback['content']}"
        
        # 检查是否有相关的错误记录
        for error in self.error_history:
            if action in error['message'] and not error['resolved']:
                return f"历史上出现过错误：{error['message']}"
        
        return None
    
    # ==================== 统计分析 ====================
    
    def get_statistics(self) -> Dict:
        """获取学习系统统计信息"""
        stats = {
            'total_feedback': len(self.feedback_history),
            'valid_feedback': len([f for f in self.feedback_history if f['status'] == 'valid']),
            'invalid_feedback': len([f for f in self.feedback_history if f['status'] == 'invalid']),
            'pending_feedback': len([f for f in self.feedback_history if f['status'] == 'pending']),
            'total_errors': len(self.error_history),
            'resolved_errors': len([e for e in self.error_history if e['resolved']]),
            'unresolved_errors': len([e for e in self.error_history if not e['resolved']]),
            'total_learning_notes': len(self.learning_notes),
            'total_best_practices': sum(len(p) for p in self.best_practices.values()),
            'categories': list(self.best_practices.keys())
        }
        
        # 计算学习效率
        if stats['total_feedback'] > 0:
            stats['feedback_accuracy'] = stats['valid_feedback'] / stats['total_feedback']
        else:
            stats['feedback_accuracy'] = 0
        
        if stats['total_errors'] > 0:
            stats['error_resolution_rate'] = stats['resolved_errors'] / stats['total_errors']
        else:
            stats['error_resolution_rate'] = 0
        
        return stats
    
    def export_report(self) -> str:
        """导出学习报告"""
        stats = self.get_statistics()
        
        report = f"""
# 聚光AI投手 - 自我完善系统报告

## 📊 统计概览
- 总反馈数：{stats['total_feedback']}
  - 有效反馈：{stats['valid_feedback']}
  - 无效反馈：{stats['invalid_feedback']}
  - 待验证：{stats['pending_feedback']}
- 反馈准确率：{stats['feedback_accuracy']:.1%}

## 🐛 错误记录
- 总错误数：{stats['total_errors']}
- 已解决：{stats['resolved_errors']}
- 未解决：{stats['unresolved_errors']}
- 错误解决率：{stats['error_resolution_rate']:.1%}

## 📚 学习笔记
- 总笔记数：{stats['total_learning_notes']}

## ✅ 最佳实践
- 总实践数：{stats['total_best_practices']}
- 分类：{', '.join(stats['categories'])}

## 🔒 隐私保护
- 敏感字段已遮盖：{len(self.privacy_config['fields_to_mask'])} 个
- 所有日志和报告均经过隐私处理
"""
        
        return report
    
    # ==================== 账户画像学习 ====================
    
    def learn_from_daily_review(self, review_data: Dict):
        """🔥 从每日复盘学习用户账户特征
        
        每次拉数据复盘时调用，积累3-7天后AI就能掌握你的账户规律。
        
        Args:
            review_data: {
                'date': '2026-06-04',
                'total_cost': 58.05,
                'impression': 4968,
                'click': 956,
                'ctr': 19.2,
                'cpc': 0.06,
                'campaigns': [
                    {'id': 1, 'name': '计划A', 'placement': 2, 'cost': 20, 'imp': 500, 'click': 80, 'ctr': 16, 'convert': 3},
                    ...
                ],
                'channels': {
                    '搜索': {'cost': 35, 'imp': 2000, 'click': 400, 'ctr': 20, 'convert': 5, 'cpa': 7.0},
                    '信息流': {'cost': 23, 'imp': 2968, 'click': 556, 'ctr': 18.7, 'convert': 2, 'cpa': 11.5}
                }
            }
        """
        self.add_learning_note(
            'daily_review', 
            f'日期{review_data.get("date")}: 消耗{review_data.get("total_cost", 0)}元, CTR{review_data.get("ctr", 0):.1f}%, CPC{review_data.get("cpc", 0):.2f}元',
            '自动复盘',
            7
        )
        
        # 记录分渠道数据
        channels = review_data.get('channels', {})
        for channel_name, channel_data in channels.items():
            self._update_channel_profile(channel_name, channel_data)
        
        # 记录各个计划的表现
        for campaign in review_data.get('campaigns', []):
            self._update_campaign_profile(campaign)
    
    def _update_channel_profile(self, channel_name: str, channel_data: Dict):
        """更新渠道画像"""
        if 'channel_profiles' not in self.best_practices:
            self.best_practices['channel_profiles'] = []
        
        # 看是否有已存在的渠道记录
        existing = None
        for p in self.best_practices['channel_profiles']:
            if p['title'] == channel_name:
                existing = p
                break
        
        if existing:
            # 滑动平均更新
            n = existing.get('sample_count', 1)
            existing['ctr'] = (existing.get('ctr', 0) * n + channel_data.get('ctr', 0)) / (n + 1)
            existing['cpc'] = (existing.get('cpc', 0) * n + (channel_data.get('cost', 0) / max(channel_data.get('click', 1), 1))) / (n + 1)
            existing['cpa'] = (existing.get('cpa', 0) * n + (channel_data.get('cost', 0) / max(channel_data.get('convert', 1), 1))) / (n + 1)
            existing['sample_count'] = n + 1
            existing['confidence'] = min(1.0, 0.3 + n * 0.1)  # 数据越多越可信
            existing['last_updated'] = datetime.now().isoformat()
        else:
            self.best_practices['channel_profiles'].append({
                'id': f"cp_{channel_name}_{datetime.now().strftime('%Y%m%d')}",
                'timestamp': datetime.now().isoformat(),
                'title': channel_name,
                'ctr': channel_data.get('ctr', 0),
                'cpc': channel_data.get('cost', 0) / max(channel_data.get('click', 1), 1),
                'cpa': channel_data.get('cost', 0) / max(channel_data.get('convert', 1), 1),
                'sample_count': 1,
                'confidence': 0.3,
                'last_updated': datetime.now().isoformat(),
                'content': f'{channel_name}渠道：CTR {channel_data.get("ctr", 0):.1f}%, 当前CPA {channel_data.get("cost", 0) / max(channel_data.get("convert", 1), 1):.2f}元'
            })
        
        self._save_json(self.best_practices_file, self.best_practices)
    
    def _update_campaign_profile(self, campaign: Dict):
        """更新计划画像"""
        if 'campaign_profiles' not in self.best_practices:
            self.best_practices['campaign_profiles'] = []
        
        cid = str(campaign.get('id', ''))
        existing = None
        for p in self.best_practices['campaign_profiles']:
            if p['title'] == cid:
                existing = p
                break
        
        if existing:
            n = existing.get('sample_count', 1)
            existing['ctr'] = (existing.get('ctr', 0) * n + campaign.get('ctr', 0)) / (n + 1)
            existing['sample_count'] = n + 1
            existing['confidence'] = min(1.0, 0.3 + n * 0.1)
            existing['last_updated'] = datetime.now().isoformat()
        else:
            self.best_practices['campaign_profiles'].append({
                'id': f"camp_{cid}",
                'timestamp': datetime.now().isoformat(),
                'title': cid,
                'name': campaign.get('name', ''),
                'ctr': campaign.get('ctr', 0),
                'convert': campaign.get('convert', 0),
                'cost': campaign.get('cost', 0),
                'placement': campaign.get('placement', 0),
                'sample_count': 1,
                'confidence': 0.3,
                'last_updated': datetime.now().isoformat()
            })
        
        self._save_json(self.best_practices_file, self.best_practices)
    
    def get_channel_profile(self, channel_name: str = None) -> Optional[Dict]:
        """获取渠道画像（积累数据后会越来越准）"""
        profiles = self.best_practices.get('channel_profiles', [])
        if channel_name:
            for p in profiles:
                if p['title'] == channel_name:
                    return p
            return None
        return profiles
    
    def get_account_snapshot(self) -> Dict:
        """获取账户快照 — 基于多日学习总结用户投放特征"""
        profiles = self.best_practices.get('channel_profiles', [])
        campaign_profiles = self.best_practices.get('campaign_profiles', [])
        
        snapshot = {
            'days_learned': max((p.get('sample_count', 0) for p in profiles), default=0),
            'channels': {},
            'top_campaigns': [],
            'readiness': '冷启动'  # 默认
        }
        
        for p in profiles:
            snapshot['channels'][p['title']] = {
                'avg_ctr': round(p.get('ctr', 0), 1),
                'avg_cpc': round(p.get('cpc', 0), 2),
                'avg_cpa': round(p.get('cpa', 0), 2),
                'confidence': p.get('confidence', 0),
                'samples': p.get('sample_count', 0)
            }
        
        # 最佳计划 top 3
        sorted_campaigns = sorted(campaign_profiles, key=lambda x: x.get('ctr', 0), reverse=True)
        for c in sorted_campaigns[:3]:
            snapshot['top_campaigns'].append({
                'id': c.get('title', ''),
                'name': c.get('name', ''),
                'avg_ctr': round(c.get('ctr', 0), 1)
            })
        
        # 判断学习阶段
        total_samples = sum(p.get('sample_count', 0) for p in profiles)
        if total_samples >= 7:
            snapshot['readiness'] = '成熟 — 模型对你的账户已经很了解'
        elif total_samples >= 3:
            snapshot['readiness'] = '学习期 — 再积累几天会越来越准'
        else:
            snapshot['readiness'] = '冷启动 — 刚认识你的账户，多复盘几次就好了'
        
        return snapshot


# 全局实例
_learning_system = None


def get_learning_system() -> SelfLearningSystem:
    """获取全局学习系统实例"""
    global _learning_system
    if _learning_system is None:
        _learning_system = SelfLearningSystem()
    return _learning_system


# ==================== 便捷函数 ====================

def record_user_feedback(feedback_type: str, content: str, context: Dict = None):
    """记录用户反馈的便捷函数"""
    return get_learning_system().record_feedback(feedback_type, content, context)


def record_error(error_type: str, error_message: str, context: Dict = None, solution: str = None):
    """记录错误的便捷函数"""
    return get_learning_system().record_error(error_type, error_message, context, solution)


def get_smart_suggestions(context: str) -> List[str]:
    """获取智能建议的便捷函数"""
    return get_learning_system().get_suggestions(context)


def should_avoid_action(action: str) -> Optional[str]:
    """检查操作是否应该避免的便捷函数"""
    return get_learning_system().should_avoid(action)


def mask_sensitive_data(data: Dict) -> Dict:
    """遮盖敏感数据的便捷函数"""
    return get_learning_system().mask_sensitive_data(data)


if __name__ == "__main__":
    # 测试自我完善系统
    system = SelfLearningSystem()
    
    # 记录一些测试数据
    system.record_feedback('improvement', '实时数据获取太难用', {'feature': 'realtime_data'})
    system.record_feedback('improvement', '出价修改方法藏太深', {'feature': 'bid_update'})
    
    system.record_error('api', 'API返回超时', {'endpoint': '/data/report/realtime'}, '增加重试机制')
    
    system.add_learning_note('user_behavior', '用户希望一键获取开口数据', '用户反馈', 8)
    system.add_learning_note('api_knowledge', 'msg_chat_user_cnt=进线用户数, initiative_message=主动消息数', '官方API文档', 8)
    
    # 模拟3天账户学习数据（演示真实数据驱动出价建议）
    system.learn_from_daily_review({
        'date': '2026-06-01',
        'total_cost': 150,
        'channels': {
            '搜索': {'cost': 100, 'click': 200, 'ctr': 18, 'convert': 8, 'cpa': 12.5},
            '信息流': {'cost': 50, 'click': 300, 'ctr': 15, 'convert': 3, 'cpa': 16.7}
        }
    })
    system.learn_from_daily_review({
        'date': '2026-06-02',
        'total_cost': 180,
        'channels': {
            '搜索': {'cost': 120, 'click': 250, 'ctr': 19, 'convert': 10, 'cpa': 12.0},
            '信息流': {'cost': 60, 'click': 350, 'ctr': 16, 'convert': 4, 'cpa': 15.0}
        }
    })
    system.learn_from_daily_review({
        'date': '2026-06-03',
        'total_cost': 200,
        'channels': {
            '搜索': {'cost': 140, 'click': 280, 'ctr': 20, 'convert': 12, 'cpa': 11.7},
            '信息流': {'cost': 60, 'click': 320, 'ctr': 14, 'convert': 5, 'cpa': 12.0}
        }
    })
    
    print("搜索渠道画像:", system.get_channel_profile('搜索'))
    print("信息流渠道画像:", system.get_channel_profile('信息流'))
    print("账户快照:", system.get_account_snapshot())
    
    # 输出报告
    print(system.export_report())
    
    # 测试隐私保护
    test_data = {
        'advertiser_id': '1234567890',
        'app_secret': 'abcdef123456',
        'campaign_name': '测试计划',
        'data': {
            'access_token': 'token_123456789',
            'cost': 100.50
        }
    }
    
    print("\n隐私保护测试：")
    print("原始数据：", test_data)
    print("遮盖后：", system.mask_sensitive_data(test_data))
