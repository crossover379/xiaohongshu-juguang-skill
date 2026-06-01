---
name: xiaohongshu-juguang-ai
description: "小红书聚光AI运营助手 - 智能投放管理、数据分析、创意优化、新手引导。适用于小红书聚光广告投放的运营管理场景。"
version: 3.15.0
author: xueji
tags: [xiaohongshu, ad, juguang, ai, marketing, advertising]
---

# 小红书聚光AI运营助手

## Overview

小红书聚光平台AI运营助手，提供智能投放管理、数据分析、创意优化、新手引导等功能。支持自然语言交互，帮助运营人员高效管理聚光广告投放。

## When to Use

- 需要查看聚光账号大盘数据
- 需要生成智能日报（带环比分析）
- 需要分析计划表现（高效/低效识别）
- 需要一键操作（暂停/调价/启停）
- 需要智能创编计划（自然语言解析）
- 需要创意优选（找优质创意加推）
- 需要僵尸计划清理
- 需要新手引导（一步步教你投放）

## Features

### 📊 账号大盘
一站式查看账户信息、今日数据、计划概况。区分投放中/已暂停计划，展示消耗、曝光、点击、CTR等核心指标。

### 📈 智能日报
带环比分析（消耗、曝光、点击、CTR变化），支持自定义日期查询，自动计算CPC、CPM等衍生指标。

### 🔍 计划分析
识别高效/低效/暂停计划，基于数据自动生成优化建议。创意优选：找出优质创意推荐加推。

### ⚡ 快速执行
一键操作：暂停/调价/启停（需用户确认），批量操作：批量暂停低效计划，操作确认：格式化确认信息。

### 🆕 智能创编
自然语言解析："投酒店，日预算200" → 自动生成配置。支持产品/行业、预算、投放方式识别，用户确认后执行。

#### 智能创建计划完整流程

**第一步：数据分析**
1. 调用`get_top_creatives(days=30, top_n=5, min_fee=1.0, min_ctr=10.0)`获取优质创意
   - 自动过滤已删除笔记（filter_existing_notes=True）
   - 按消耗+CTR评分排序
   - 返回30天内有消耗且CTR>10%的笔记

**第二步：出价参考**
1. 调用`keyword_recommend(keyword)`获取关键词推荐
   - 返回搜索量、建议出价
   - 用于设置关键词和出价

**第三步：方案确认**
展示推荐方案：
- 计划名称：{行业}客资_{日期}_{投放方式}
- 投放位置：全站（默认）
- 优化目标：私信开口量（默认）
- 竞价策略：稳定成本（默认）
- 日预算：100元（默认）
- 出价：1.0元/条（默认）
- 笔记：优质创意笔记
- 关键词：行业相关词

**第四步：创建执行**
调用`create_campaign_with_creatives()`创建计划：
- note_ids: 优质创意笔记ID列表
- keywords: [{keyword, bid, phrase_match_type}]
- 返回计划ID、单元ID、创意IDs

#### 优质创意筛选规则
- 综合评分 = 消耗(40分) + 点击量(20分) + CTR>15%(25分) + 转化(30分)
- 消耗阈值：≥1元
- CTR阈值：≥10%
- 默认返回前5个优质创意
- 只返回笔记列表中存在的笔记（过滤已删除）

### 🧹 僵尸计划清理
识别长期无消耗的暂停计划，建议清理释放账户容量。

### 🎨 创意优选
分析全账户创意表现，找出优质创意推荐加推，低效创意建议暂停。

### 📖 投放规则
内置9大类聚光平台规则（官方文档+实战验证）：
- 出价规则：搜索最低0.3元，信息流最低0.2元
- 预算规则：计划最低100元，简单投最低50元
- API规则：3000次/分钟，无消耗门槛

### 🆕 新手模式
欢迎消息（未接入→引导回复"接入"+直接给链接；已接入→展示大盘+功能菜单）→ 11步交互式向导（接入API→展示大盘→选行业→设预算→选区域→选投放方式→确认配置→完成）

## File Structure

```
xiaohongshu-juguang-ai/
├── SKILL.md                            # 本说明文档
├── _meta.json                          # SkillHub元数据
├── xiaohongshu_juguang_sdk.py          # SDK核心（93个方法）
├── xiaohongshu_sdk_enhancer.py         # SDK增强器
├── xiaohongshu_reports.py              # 报表引擎
├── xiaohongshu_ai_assistant.py         # AI运营助手
├── xiaohongshu_automation_rules.py     # 自动化规则引擎
├── xiaohongshu_creative_analyzer.py    # 创意分析器
├── xiaohongshu_keyword_manager.py      # 关键词管理器
├── xiaohongshu_expert_knowledge.py     # 投手知识库
├── xiaohongshu_expert_knowledge_advanced.py # 高级投手知识库
├── xiaohongshu_config.json.template    # 配置文件模板
├── CHANGELOG.md                        # 版本更新日志
└── README.md                           # 项目说明
```

## Quick Start

### 1. 安装
将本Skill解压到 `~/.openclaw/workspace/skills/xiaohongshu-juguang-ai/`

### 2. 配置
编辑 `xiaohongshu_config.json`，填入你的聚光平台凭证：
```json
{
  "app_id": "你的AppID",
  "app_secret": "你的AppSecret",
  "advertiser_id": "你的广告主ID"
}
```

### 3. 使用
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

## 创建计划 API (cascade/create)

### 快捷创建
```python
from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
sdk = XiaohongshuJuguangSDK()

# 产品种草
result = sdk.quick_create_campaign(
    campaign_name="酒店种草计划",
    note_id="6a17b5e70000000006021696",
    marketing_target=4,  # 产品种草
    placement=1,  # 信息流
    daily_budget_yuan=100,
    bid_yuan=1
)

# 客资收集（私信）
result = sdk.quick_create_campaign(
    campaign_name="酒店客资计划",
    note_id="6a17b5e70000000006021696",
    marketing_target=9,  # 客资收集
    placement=1,
    carrier_type=1,  # 1=私信 2=落地页 3=私信+落地页
    optimize_objective=5,  # 5=私信进线 13=私信开口 50=留资
    conversion_type=3,  # 3=私信 10=留资 20=落地页 78=私信表单同投
    bidding_strategy=7,  # 稳定成本
    daily_budget_yuan=100,
    bid_yuan=5,
    bar_content="立即咨询",
    component_conv_num_is_show=True
)
# 返回: {success, campaign_id, unit_id, creativity_id}

# 多创意创建（推荐，至少5个创意）
result = sdk.create_campaign_with_creatives(
    campaign_name="酒店客资_5月29日_全站",
    note_ids=[
        "6a19313f00000000080259ee",  # 三亚艾迪逊
        "6a17b5e70000000006021696",  # 香港尼依格罗
        "6a153b1f0000000006022d9f",  # 厦门安达仕
        "6a14110f00000000070136e1",  # 重庆康莱德
        "6a0ecbab0000000008026f58"   # 巴厘岛W
    ],
    marketing_target=9,  # 客资收集
    placement=4,  # 全站
    daily_budget_yuan=100,
    bid_yuan=1.0
)
# 返回: {success, campaign_id, unit_id, creativity_ids: [...]}
```

### 完整创建参数
使用 `sdk.cascade_create(1, [cascade_info])` 调用，参数格式见SDK内docstring。

### 关键参数说明
| 字段 | 说明 | 可选值 |
|------|------|--------|
| marketing_target | 营销诉求 | 4=产品种草 9=客资收集 13=种草直达 |
| placement | 投放位置 | 1=信息流 2=搜索 4=全站 7=视频流 |
| bidding_strategy | 竞价策略 | 2=手动出价 3=最大转化 7=稳定成本 |
| time_period | 投放时段 | 7天×24小时对象，每个字段24位01串 |
| target_area_code | 地域编码 | -1=全部，多个用#分隔 |
| conversion_type | 组件类型 | 0=无组件 3=私信组件 |
| optimize_objective | 优化目标 | 0=点击量 1=互动量 |

### 注意事项
- ⚠️ 预算/出价金额单位为分，SDK快捷方法自动转换单位
- ⚠️ time_period必须是7天×24小时对象格式，不是字符串
- ⚠️ target_info必须用target_area_code/target_age等字段名
- ⚠️ 创意名称字段是creativity_name，不是creative_name
- ⚠️ conversion_type必传，0=无组件
- ⚠️ 一次最多新建20个创意

## Important Notes

1. **安全第一**：所有涉及修改、删除、新增投放设置的接口，均需用户确认后执行
2. **消耗统计**：必须分普通投放+简单投两套拉取后汇总，禁止用delivery_type参数区分
3. **数据时效**：离线报表T+1上午10点出数，实时报表5-10分钟延迟
4. **批量限制**：批量操作单次上限20个ID
5. **QPS限制**：普通接口10次/秒，报表5次/秒

## Changelog

### v3.15.0 (2026-05-30)
- 新增自动执行闭环模块（xiaohongshu_auto_executor.py）
- 新增规则引擎：支持复杂条件（and/or）、自动评估规则
- 新增自动执行：自动优化、试运行模式
- 新增策略管理：创建策略、应用策略、策略性能统计
- 新增执行历史：记录执行历史、统计成功率
- 测试通过：规则评估、自动优化、创建策略、执行历史、策略性能

### v3.14.0 (2026-05-30)
- 新增归因分析与创意A/B测试模块（xiaohongshu_attribution_ai.py）
- 新增数据驱动归因：基于贡献度归因、Shapley值归因
- 新增创意A/B测试：创建、启动、分析、结束测试
- 新增受众分析：受众细分、受众洞察
- 新增综合归因分析：数据驱动+Shapley+受众分析
- 测试通过：数据驱动归因、Shapley归因、受众分析、综合分析

### v3.13.0 (2026-05-30)
- 新增创意生成与异常检测模块（xiaohongshu_creative_ai.py）
- 新增创意生成功能：5种风格（痛点型/数据型/故事型/对比型/攻略型）
- 新增异常检测功能：Z-score方法检测消耗/曝光/点击/CTR异常
- 新增智能定向功能：基于行业推荐定向策略
- 新增综合分析功能：创意分析+异常检测+优化建议
- 测试通过：创意生成、智能定向、综合分析

### v3.12.0 (2026-05-29)
- 新增真正的AI模块（xiaohongshu_real_ai.py）
- 新增决策反馈循环：记录决策、记录结果、预测质量
- 新增多臂老虎机算法：UCB/ε-greedy/Thompson三种策略
- 新增智能出价策略：基于目标CPA/ROAS/历史表现
- 新增智能预算分配：基于表现/平均/探索策略
- 新增学习与优化：从历史决策中学习规律
- 测试通过：决策记录、老虎机、智能推荐

### v3.11.0 (2026-05-29)
- 新增高级分析模块（xiaohongshu_advanced_analytics.py）
- 新增预测分析功能：预测计划/关键词未来表现
- 新增A/B测试功能：创建、启动、分析、结束测试
- 新增归因分析功能：支持last_click/first_click/linear/time_decay模型
- 新增预算分配功能：performance/balanced/aggressive三种策略
- 测试通过：A/B测试、归因分析、预算分配、预算建议

### v3.10.0 (2026-05-29)
- 新增AI投手大脑模块（xiaohongshu_ai_brain.py）
- 新增自动学习功能：从历史数据中学习，发现投放规律
- 新增智能决策功能：分析数据并做出决策，获取智能推荐
- 新增预测功能：预测明天消耗、预测预算耗尽时间
- 新增创意生成功能：生成创意建议
- 测试通过：自动学习、规律发现、智能决策

### v3.9.0 (2026-05-29)
- 新增AI投手智能优化模块（xiaohongshu_smart_optimizer.py）
- 新增数据预警功能：支持消耗超标、CTR过低、CPC过高预警
- 新增智能投放功能：支持自动创建计划、自动优化计划
- 新增批量操作功能：支持批量暂停/启动/修改预算/修改出价
- 新增报表自动化功能：支持日报、周报自动生成
- 测试通过：数据预警、日报生成、周报生成

### v3.8.2 (2026-05-29)
- 全面测试通过，所有新增方法正常工作
- 修复get_all_notes方法参数错误
- 优化日志记录格式
- 更新SKILL.md文档

### v3.8.1 (2026-05-29)
- 修复Bug检测报告中发现的问题
- 新增get_all_units方法：自动分页获取全量单元
- 新增get_all_creatives方法：自动分页获取全量创意
- 新增get_all_notes方法：自动分页获取全量笔记
- 优化get_all_campaigns返回格式：统一为{success, data, total_count}
- 新增错误码映射：提供更详细的错误信息
- 新增日志记录：记录API请求耗时和结果
- 更新SKILL.md文档

### v3.8.0 (2026-05-29)
- 更新SKILL.md文档：版本号、方法数量、文件结构
- 优化智能创建计划流程：支持行业关键词自动推荐
- 修复单元列表字段兼容：id/name → unit_id/unit_name
- 优质创意筛选改为30天范围，按note_id汇总数据
- 全面排查32/35功能通过，3个失败接口为平台限制

### v3.7.0 (2026-05-29)
- 智能创建计划流程完善
- 新增get_top_creatives方法：按消耗+CTR评分筛选优质创意
- 新增create_campaign_with_creatives方法：支持多创意创建
- 新增keyword_recommend方法：获取行业关键词推荐
- 修复报表字段：消耗字段是fee（元），不是cost

### v3.6.0 (2026-05-29)
- 智能创建计划流程+多创意支持
- 新增行业关键词自动推荐
- 修复单元列表字段兼容

### v3.5.0 (2026-05-28)
- 从v2.5迭代至v3.5.1，完成全量功能开发与API修复
- 创意/计划报表API返回账户层数据而非单条数据→改用data_list字段
- get_campaign_list()只读单页→改用get_all_campaigns()全量读取
- 关键词匹配400错误→参数改keywords(列表格式)
- 以词推词→参数改keyword

### v2.6.0 (2026-05-29)
- 新增cascade/create创建计划API（完整参数格式文档）
- 新增quick_create_campaign快捷创建方法
- 修复TimePeriodDTO格式（7天×24小时对象）
- 修复CreateTargetInfo格式（target_area_code等字段）
- 修复创意名称字段（creativity_name）
- 修复check_name_dup（name参数支持列表）
- 修复get_material_prefer_info（使用material_info_dtos参数）
- 全面排查91个方法，14/15核心测试通过

### v2.5.1 (2026-05-28)
- 全面诊断修复，0个问题
- 账号大盘：计划总数、今日消耗、预算类型全部正常
- 计划分析：高效/低效/正常/暂停计数正确
- 创意优选：使用data_list获取单个创意数据，分类规则完善
- 僵尸计划：正常工作
- 新手向导：正常工作
- 投放规则：9条规则可用
- 智能日报：多维度对比和建议

### v2.5.0 (2026-05-28)
- 修复创意优选功能（使用data_list获取单个创意数据）
- 优化智能日报（增加多维度对比和建议）
- 完善创意分类规则（日均消耗<10元为低效）
- 修复SDK返回结构（保留data_list明细数据）

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
