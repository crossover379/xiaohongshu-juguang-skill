# 小红书聚光AI运营助手 v3.11.0

## 简介

小红书聚光平台AI运营助手，提供智能投放管理、数据分析、创意优化、智能决策等功能。支持自然语言交互，帮助运营人员高效管理聚光广告投放。

## 功能特性

- 📊 **数据分析**：账户数据、消耗数据、计划/单元/创意/笔记数据
- 📈 **报表自动化**：日报、周报自动生成，带环比分析
- 🔍 **智能分析**：优质创意筛选、关键词推荐、行业类目、人群预估
- ⚡ **投放管理**：计划创建、状态管理、单元管理、创意管理
- 🧠 **AI大脑**：自动学习、规律发现、智能决策、预测分析
- 📊 **高级分析**：A/B测试、归因分析、预算分配
- ⚡ **批量操作**：批量暂停/启动/修改预算/修改出价
- 🚨 **数据预警**：消耗超标、CTR过低、CPC过高预警
- 🎯 **智能投放**：自动创建计划、自动优化计划

## 安装

1. 将本Skill解压到 `~/.openclaw/workspace/skills/xiaohongshu-juguang-ai/`
2. 编辑 `xiaohongshu_config.json`，填入你的聚光平台凭证
3. 重启OpenClaw

## 配置

编辑 `xiaohongshu_config.json`：

```json
{
  "app_id": "你的AppID",
  "app_secret": "你的AppSecret",
  "advertiser_id": "你的广告主ID"
}
```

### 获取凭证

1. 打开聚光平台：https://ad.xiaohongshu.com
2. 进入「应用管理」创建应用
3. 获取AppID和AppSecret

## 使用示例

```python
from xiaohongshu_ai_assistant import AIOperationsAssistant

assistant = AIOperationsAssistant()

# 获取欢迎消息
welcome = assistant.get_welcome_message(is_connected=False)

# 获取账号大盘
dashboard = assistant.get_account_dashboard()
print(assistant.format_dashboard(dashboard))

# 获取智能日报
daily = assistant.generate_smart_daily_report()

# 分析计划表现
analysis = assistant.analyze_campaign_performance()
print(assistant.format_campaign_analysis(analysis))

# 创意优选
creative_analysis = assistant.analyze_creative_performance()
print(assistant.format_creative_analysis(creative_analysis))

# 新手向导
wizard = assistant.get_beginner_wizard(step=1)
next_wizard, context = assistant.process_beginner_wizard(step=1, user_choice=0)
```

## 注意事项

1. **安全第一**：所有涉及修改、删除、新增投放设置的接口，均需用户确认后执行
2. **消耗统计**：必须分普通投放+简单投两套拉取后汇总，禁止用delivery_type参数区分
3. **数据时效**：离线报表T+1上午10点出数，实时报表5-10分钟延迟
4. **批量限制**：批量操作单次上限20个ID
5. **QPS限制**：普通接口10次/秒，报表5次/秒

## 文件说明

| 文件 | 说明 |
|------|------|
| `SKILL.md` | Skill说明文档 |
| `_meta.json` | SkillHub元数据 |
| `xiaohongshu_juguang_sdk.py` | SDK核心（45个方法） |
| `xiaohongshu_sdk_enhancer.py` | SDK增强器 |
| `xiaohongshu_reports.py` | 报表引擎 |
| `xiaohongshu_ai_assistant.py` | AI运营助手（v2.4完整版） |
| `xiaohongshu_config.json` | 配置文件模板 |

## 更新日志

### v2.4.0 (2026-05-28)
- 新增账号大盘功能
- 新增投放规则库（9大类）
- 新增新手模式（11步交互式向导）
- 新增僵尸计划清理
- 新增创意优选功能
- 优化欢迎消息（未接入引导+直接给链接）

### v2.3.0 (2026-05-28)
- 新增智能创编（自然语言解析）

### v2.2.0 (2026-05-28)
- 新增快速执行（一键操作、批量操作）

### v2.1.0 (2026-05-28)
- 新增AI分析（计划表现分析、优化建议）

### v2.0.0 (2026-05-28)
- 新增智能日报（带环比分析）
- 新增实时预警（24h监控）

## 许可证

MIT License
