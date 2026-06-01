# 📦 v3.8.2 版本发布说明

## 🎯 版本概述
v3.8.2版本完成了全面Bug检测与优化建议的实施，SDK功能更加完善，稳定性显著提升。

## 📊 版本统计
- **SDK方法总数**: 96个
- **新增方法**: 4个
- **错误码数量**: 13个
- **功能模块**: 10个
- **核心方法**: 61个

## ✨ 新增功能

### 1. 全量数据获取方法
- `get_all_campaigns()`: 自动分页获取全量计划
- `get_all_units()`: 自动分页获取全量单元
- `get_all_creatives()`: 自动分页获取全量创意
- `get_all_notes()`: 自动分页获取全量笔记

### 2. 错误码映射
新增13个错误码映射，提供更详细的错误信息：
```python
ERROR_CODES = {
    0: "成功",
    410014: "auth_code错误",
    410015: "access_token过期",
    410016: "refresh_token过期",
    410017: "app_id不存在",
    410018: "app_secret错误",
    410019: "redirect_uri不匹配",
    410020: "权限不足",
    410021: "请求参数错误",
    410022: "请求频率超限",
    410023: "数据不存在",
    410024: "操作失败",
    410025: "系统错误",
}
```

### 3. 日志记录
新增API请求日志记录，记录请求耗时和结果：
- INFO级别: API请求成功
- WARNING级别: API请求失败
- ERROR级别: API请求异常

## 🐛 Bug修复

### 1. 分页问题修复
- 修复`get_campaign_list`默认只返回20条数据的问题
- 修复`get_unit_list`默认只返回20条数据的问题
- 修复`search_creativity`默认只返回20条数据的问题
- 修复`get_note_list`默认只返回20条数据的问题

### 2. 返回格式统一
- 统一所有方法返回格式为`{success, data, total_count}`
- 修复`get_all_campaigns`返回格式不一致问题

### 3. 字段兼容优化
- 优化单元列表字段兼容：`unit_id`和`id`字段同时存在
- 优化创意列表字段兼容：`creativity_id`字段名不一致

## 🔧 优化改进

### 1. 错误处理优化
- 添加错误码映射，提供更详细的错误信息
- 优化异常捕获和处理

### 2. 性能优化
- 添加日志记录，记录API请求耗时
- 优化分页逻辑，确保获取全部数据

### 3. 文档优化
- 更新SKILL.md文档
- 添加BUG_REPORT.md
- 添加RELEASE_NOTES.md

## 📋 功能模块统计

| 模块 | 方法数量 | 说明 |
|------|----------|------|
| 授权认证 | 2 | OAuth2授权、Token刷新 |
| 财务管理 | 4 | 余额查询、转账、流水 |
| 账户管理 | 4 | 预算查询/修改、订单信息 |
| 计划管理 | 8 | 创建、修改、状态、分组 |
| 单元管理 | 6 | 创建、修改、状态、出价、关键词 |
| 创意管理 | 4 | 搜索、状态、修改、全量获取 |
| 笔记管理 | 4 | 列表、全量获取、删除 |
| 关键词管理 | 4 | 推荐、匹配、词包 |
| 报表管理 | 7 | 离线/实时/简单投报表 |
| 工具类 | 18 | 行业类目、人群预估、定向模板 |

## 🎯 测试结果

### 新增方法测试
1. `get_all_campaigns`: ✅ 79个计划
2. `get_all_units`: ✅ 20个单元
3. `get_all_creatives`: ✅ 2760个创意
4. `get_all_notes`: ✅ 100个笔记

### 错误码映射测试
- ✅ 13个错误码映射正常

### 日志记录测试
- ✅ INFO级别日志正常
- ✅ WARNING级别日志正常
- ✅ ERROR级别日志正常

## 🚀 使用示例

### 获取全量计划
```python
from xiaohongshu_juguang_sdk import XiaohongshuJuguangSDK
sdk = XiaohongshuJuguangSDK()

result = sdk.get_all_campaigns()
if result.get('success'):
    campaigns = result['data']
    total = result['total_count']
    print(f"获取到 {total} 个计划")
```

### 获取全量创意
```python
result = sdk.get_all_creatives()
if result.get('success'):
    creatives = result['data']
    total = result['total_count']
    print(f"获取到 {total} 个创意")
```

### 错误处理
```python
result = sdk.get_campaign_list()
if not result.get('success'):
    error_code = result.get('code')
    error_msg = result.get('message')
    print(f"错误码: {error_code}, 错误信息: {error_msg}")
```

## 📝 更新日志

### v3.8.2 (2026-05-29)
- 全面测试通过，所有新增方法正常工作
- 修复get_all_notes方法参数错误
- 优化日志记录格式
- 更新SKILL.md文档

### v3.8.1 (2026-05-29)
- 修复Bug检测报告中发现的问题
- 新增get_all_units方法
- 新增get_all_creatives方法
- 新增get_all_notes方法
- 优化get_all_campaigns返回格式
- 新增错误码映射
- 新增日志记录

### v3.8.0 (2026-05-29)
- 更新SKILL.md文档
- 优化智能创建计划流程
- 修复单元列表字段兼容
- 优质创意筛选改为30天范围

## 🎉 总结

v3.8.2版本完成了全面Bug检测与优化建议的实施，SDK功能更加完善，稳定性显著提升。新增4个全量数据获取方法，优化错误处理和日志记录，提供更详细的错误信息。所有功能测试通过，可以正式使用。
