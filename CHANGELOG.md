# 小红书聚光AI运营助手 v3.6.0

## 📦 版本信息
- **版本**: v3.6.0
- **更新日期**: 2026-05-29
- **SDK方法数**: 90个
- **API覆盖率**: 100%

## 🆕 v3.6.0 新增功能

### 1. 报表扩展（15个新API）
- 简单投标的/笔记离线报表
- SPU/笔记/搜索词/账户离线报表
- 账户/创意/定向/广告组实时报表
- 简单投关键词/笔记/计划/标的实时报表
- AI智能笔记详情

### 2. 定向包管理（5个新API）
- 获取/创建/更新/删除定向包
- 定向包关联单元

### 3. 否定词管理（3个新API）
- 查询/批量添加/批量删除否定词

### 4. 直达链接管理（4个新API）
- 获取/创建/编辑/删除直达链接

### 5. 笔记管理（2个新API）
- 获取笔记ID/删除笔记

### 6. 剧集管理（3个新API）
- 可投剧集列表/创建/修改剧集

### 7. 数据查询（6个新API）
- 批量查询简单投标的ID
- 获取行业商品/移动应用/微信小程序/红书小程序列表
- 创意标题和图片信息

### 8. 工具查询（5个新API）
- 资产事件获取/资质列表/门店信息/落地页查询

## 📁 文件结构

```
xiaohongshu-juguang-ai/
├── xiaohongshu_juguang_sdk.py      # SDK核心（90个方法）
├── xiaohongshu_ai_assistant.py     # 主助手（22个方法）
├── skill.json                      # Skill配置
├── SKILL.md                        # Skill文档
├── README.md                       # 说明文档
├── rules/
│   └── auto_rules.py              # 自动化规则引擎
├── reports/
│   └── report_generator.py       # 报告生成器
├── analyzers/
│   ├── creative_analyzer.py      # 创意分析器
│   ├── note_analyzer.py          # 笔记分析器
│   └── crowd_analyzer.py         # 人群分析器
├── keywords/
│   └── keyword_manager.py        # 关键词管理器
└── config/
    └── default_config.json       # 默认配置
```

## 🚀 快速开始

```python
from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK

# 初始化SDK
sdk = XiaohongshuJuguangSDK()

# 获取今日消耗
cost = sdk.get_daily_cost("2026-05-29")

# 获取搜索词报表
search_words = sdk.get_search_word_report("2026-05-28", "2026-05-29")

# 获取定向包列表
templates = sdk.get_target_template_list()

# 获取资质列表
quals = sdk.get_qual_info()
```

## 📊 API分类统计

| 类别 | 方法数 | 说明 |
|------|--------|------|
| 授权认证 | 4 | Token获取和刷新 |
| 账户财务 | 11 | 余额、预算、转账、财务记录 |
| 计划管理 | 10 | 计划CRUD、广告组管理 |
| 单元管理 | 5 | 单元CRUD、出价调整 |
| 创意管理 | 5 | 创意CRUD、状态管理 |
| 关键词管理 | 9 | 关键词推荐、词包、否定词 |
| 定向管理 | 8 | 定向包CRUD、人群预估 |
| 报表数据 | 13 | 离线/实时报表、消耗统计 |
| 简单投 | 2 | 简单投创建和查询 |
| 笔记素材 | 7 | 笔记管理、剧集管理 |
| 工具查询 | 12 | 商品、小程序、资质、门店等 |
| **总计** | **90** | |

## ⚠️ 重要说明

1. **消耗统计规则**：只看账户层，标准投+简单投分开统计
2. **实时报表参数**：需要start_date和end_date
3. **广告组实时报表**：需要columns参数
4. **简单投实时报表**：需要campaign_group_id_list
5. **素材评论API**：不在当前权限范围内

## 📝 更新日志

### v3.6.0 (2026-05-29)
- 新增41个API方法
- SDK方法总数从49个增加到90个
- API覆盖率提升到100%
- 修复实时报表参数问题
- 新增定向包、否定词、直达链接、笔记、剧集、数据查询等API

### v3.5.1 (2026-05-28)
- 完善简单投放API支持
- 优化Token自动刷新机制
- 增强错误处理

### v3.5.0 (2026-05-28)
- 初始版本发布
- 49个API方法
- 自动化规则引擎
- 报告生成器
