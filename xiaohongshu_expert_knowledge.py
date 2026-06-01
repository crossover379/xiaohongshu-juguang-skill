"""
小红书聚光顶级投手知识库 v1.0
基于2026星云5.0版训练专用知识库
"""

EXPERT_KNOWLEDGE = {
    "platform_logic": {
        "name": "平台底层逻辑",
        "rules": [
            "聚光是内容匹配引擎，非流量购买工具，内容质量分权重>出价",
            "搜索流量占比≥65%，推搜联动是唯一正确打法",
            "CES评分公式：推荐得分=(基础质量分×0.3)+(用户互动分×0.4)+(商业价值分×0.2)+(社交关系分×0.1)",
            "评论/转发权重=点赞×4",
            "投放上限由站内需求数决定，非预算多少",
            "新账户冷启动沙盒期3-7天，用质量换数量，不是用价格换质量",
            "素材月衰减率≈10%，3个月基本失效",
            "数据波动是常态，受平台流量、算法匹配、季节、节假日影响",
        ]
    },
    
    "budget_allocation": {
        "name": "预算分配黄金法则",
        "rules": [
            "通用比例：30%测试+70%放量",
            "新手单计划日预算：100-300元，总测试预算3000-8000元",
            "集中火力原则：2-3个计划消耗80%预算",
            "动态倾斜：实时向高ROI场域（搜索>信息流>视频流）和高转化计划转移预算",
        ]
    },
    
    "targeting_strategy": {
        "name": "定向策略（漏斗式递进）",
        "stages": {
            "测试期": "仅限定性别+年龄段，其余全放开，让系统充分跑量积累数据样本",
            "优化期": "根据转化数据筛选高转化人群特征，逐步收窄定向",
            "高级运用": "DMP人群包追投（加购未付、多次点击未转化、浏览过店铺未下单）",
        },
        "must_have": "排除已转化/已咨询客户，避免预算浪费"
    },
    
    "bidding_strategy": {
        "name": "出价策略",
        "important_note": "⚠️ 官方建议出价普遍虚高（比实际高30%-50%），实战中应参考同行实际出价，不要盲目跟官方建议",
        "stages": {
            "冷启动期": {
                "方式": "手动出价，参考同行实际出价（非官方建议），适当高5%-10%即可",
                "目标": "快速跑出数据，完成模型训练",
            },
            "放量期": {
                "方式": "oCPM智能出价，设置目标转化成本",
                "目标": "扩大流量规模，保持成本稳定",
            },
            "维稳期": {
                "方式": "混合出价（优质计划智能+测试计划手动）",
                "目标": "平衡消耗与ROI",
            },
            "收割期": {
                "方式": "搜索关键词精准出价",
                "目标": "最大化转化效率",
            },
        }
    },
    
    "keyword_strategy": {
        "name": "关键词攻防体系",
        "rules": [
            "品牌词防守：买断自有品牌词，防止竞品截流",
            "竞品词进攻：投竞品品牌/产品词，卡位搜索页前3",
            "长尾词收割：避开泛流量大词，锁定精准长尾需求",
            "关键词数量×10≈单关键词成本",
        ]
    },
    
    "content_standards": {
        "name": "内容素材核心标准",
        "hard_metrics": {
            "点击率": "图文≥2.5%，视频≥4%（发布后1小时数据决定笔记生死）",
            "停留时长": "目标用户平均30-60秒，<10秒直接淘汰",
            "转化指标": "私信开口率≥5%，商销CVR≥2%，表单提交率≥1%",
        },
        "golden_structure": {
            "封面": "高饱和对比色+醒目大字+真实场景+核心卖点",
            "标题": "前10字必须包含核心关键词+痛点/利益点",
            "正文": "真实体验→解决痛点→购买理由→自然引导转化",
            "评论区": "置顶评论引导转化，及时回复用户提问",
        },
        "lifecycle": [
            "标签化分类（行业/场景/卖点/转化效果）",
            "以旧带新：用已跑通的老素材数据带动新素材测试",
            "提前养新计划：不要等老计划完全衰退再替换",
            "多元组合：视频>图文>直播，视频素材点击率更高、转化成本更低",
        ]
    },
    
    "data_analysis": {
        "name": "数据分析与精准归因",
        "metric_mapping": {
            "种草": {
                "核心指标": "CTR、CPE",
                "问题定位": "CTR低→优化封面和标题；CPE高→优化正文和评论区",
            },
            "商销": {
                "核心指标": "CTR、CVR",
                "问题定位": "CVR低→检查落地页与素材的关联性，优化转化入口",
            },
            "留资": {
                "核心指标": "私信开口率、咨询成本",
                "问题定位": "开口率低→优化引导话术；成本高→优化定向和出价",
            },
        },
        "daily_check": "曝光量、点击量、点击率、互动率、转化率、CPC、CPE、ROI",
        "key_metrics": "笔记详情停留时长、场域分布（信息流/搜索/视频流）、关键词转化数据",
        "anomaly_rule": "单笔记CPM连续3天超阈值50%，立即暂停并优化",
    },
    
    "risk_control": {
        "name": "风险控制与合规",
        "rules": [
            "2026年强化AI+人工双重审核",
            "禁止使用'最'、'第一'、'绝对'等绝对化用语",
            "禁止跳转至微信个人号或未备案域名",
            "禁止虚构效果、过度美化、虚假宣传",
            "禁止使用医疗术语（非医疗行业）",
            "禁用第三方代充，建立素材备用库，定期抽查合规性",
        ]
    },
    
    "industry_specific": {
        "name": "分行业投放策略",
        "本地生活": {
            "核心转化目标": "团购核销、到店消费",
            "最佳投放时段": "11:00-14:00, 17:00-22:00",
            "推荐转化方式": "团购链接、私信预约",
            "素材特点": "真实探店、效果对比、价格优惠",
            "关键词策略": "地域+品类+需求（如'厦门思明区美甲'）",
        },
        "电商零售": {
            "核心转化目标": "商品下单、店铺关注",
            "最佳投放时段": "10:00-12:00, 19:00-24:00",
            "推荐转化方式": "商品卡片、店铺跳转",
            "素材特点": "产品测评、使用教程、穿搭展示",
            "关键词策略": "产品词+功效词+场景词（如'油痘肌粉底液'）",
        },
        "知识付费/教育": {
            "核心转化目标": "课程购买、免费试听",
            "最佳投放时段": "19:00-23:00",
            "推荐转化方式": "表单提交、私信领取资料",
            "素材特点": "干货分享、学员案例、讲师介绍",
            "关键词策略": "问题词+解决方案词（如'雅思听力怎么提高'）",
        },
        "旅游/酒旅": {
            "核心转化目标": "民宿预订、跟团咨询",
            "最佳投放时段": "19:00-24:00",
            "推荐转化方式": "私信咨询、预订链接",
            "素材特点": "风景实拍、住宿体验、行程攻略",
            "关键词策略": "目的地+品类+需求（如'泉州海边民宿'）",
        },
        "医疗健康": {
            "核心转化目标": "到院咨询、预约挂号",
            "最佳投放时段": "10:00-12:00, 14:00-18:00",
            "推荐转化方式": "表单预约、私信咨询",
            "素材特点": "医生科普、案例展示、环境介绍",
            "关键词策略": "症状词+医院词（如'厦门牙齿矫正医院'）",
        },
        "汽车/房产": {
            "核心转化目标": "到店试驾、看房预约",
            "最佳投放时段": "10:00-12:00, 14:00-18:00",
            "推荐转化方式": "表单预约、电话咨询",
            "素材特点": "产品解析、实景拍摄、用户口碑",
            "关键词策略": "品牌词+车型/户型词+地域词",
        },
    },
    
    "top_vs_normal": {
        "name": "顶级vs普通投手区别",
        "思维方式": "流量思维→内容思维：用什么内容吸引什么用户",
        "工作重点": "调参数→分析数据、优化素材、制定策略",
        "内容态度": "内容团队给什么就投什么→用投放数据反哺内容生产",
        "问题处理": "只会加预算或停计划→精准定位问题根源，给出可执行解决方案",
        "行业认知": "一套方法用遍所有行业→根据不同行业特点调整投放策略",
        "目标追求": "完成消耗目标→ROI最大化，提升整体营销效率",
    },
    
    "troubleshooting": {
        "name": "问题排查顺序",
        "order": "先看素材→再看定向→最后看出价",
        "common_issues": {
            "消耗低": [
                "素材质量分低，系统不愿给量",
                "出价过低（注意：官方建议出价虚高，应参考同行实际出价）",
                "定向过窄，覆盖人群不足",
                "冷启动期未过，模型未建立",
            ],
            "CTR低": [
                "封面不够吸引人",
                "标题没有痛点或利益点",
                "素材与定向人群不匹配",
                "素材老化，需要更新",
            ],
            "CPC高": [
                "竞争加剧，出价被动抬高",
                "素材质量分低，需要用高出价补偿",
                "定向过窄，系统匹配效率低",
            ],
            "转化成本高": [
                "素材与落地页不一致",
                "转化入口不清晰",
                "定向人群不精准",
                "出价过高，系统倾向于高价流量",
            ],
        }
    },
}


def get_industry_strategy(industry):
    """获取行业专属策略"""
    return EXPERT_KNOWLEDGE["industry_specific"].get(industry, EXPERT_KNOWLEDGE["industry_specific"]["旅游/酒旅"])


def get_troubleshooting_guide(issue):
    """获取问题排查指南"""
    return EXPERT_KNOWLEDGE["troubleshooting"]["common_issues"].get(issue, [])


def get_bidding_advice(stage):
    """获取出价建议"""
    return EXPERT_KNOWLEDGE["bidding_strategy"]["stages"].get(stage, {})


def get_content_standards():
    """获取内容素材标准"""
    return EXPERT_KNOWLEDGE["content_standards"]


def generate_expert_analysis(dashboard_data, industry="旅游/酒旅"):
    """基于数据生成专家分析"""
    analysis = []
    
    # 提取关键数据
    today = dashboard_data.get('today_data', {})
    summary = dashboard_data.get('campaign_summary', {})
    budget = dashboard_data.get('account_budget', {})
    
    cost = today.get('total_cost', 0)
    ctr = today.get('ctr', 0)
    cpc = today.get('cpc', 0)
    impressions = today.get('impression', 0)
    clicks = today.get('click', 0)
    active = summary.get('active', 0)
    balance = budget.get('available_balance_yuan', 0)
    daily_budget = budget.get('budget_yuan', 0)
    
    # 获取行业策略
    industry_strategy = get_industry_strategy(industry)
    
    # 1. 预算分析
    if daily_budget > 0:
        budget_usage = cost / daily_budget * 100
        if budget_usage < 30:
            analysis.append({
                "type": "预算利用不足",
                "level": "⚠️",
                "insight": f"今日消耗{cost:.1f}元，仅占日预算{budget_usage:.0f}%",
                "expert_advice": "根据'30%测试+70%放量'原则，当前消耗过低。可能原因：\n1. 素材质量分低，系统不愿给量\n2. 出价低于行业均价\n3. 冷启动期未过",
                "action": "检查素材CTR是否达标（图文≥2.5%，视频≥4%），如不达标优先优化素材",
            })
        elif budget_usage > 80:
            analysis.append({
                "type": "预算即将耗尽",
                "level": "🚨",
                "insight": f"今日消耗{cost:.1f}元，已占日预算{budget_usage:.0f}%",
                "expert_advice": "预算即将耗尽，系统会自动压低出价，导致流量质量下降",
                "action": "如ROI达标，建议提高预算；如ROI不达标，先优化素材再放量",
            })
    
    # 2. CTR分析
    if ctr > 0:
        if ctr < 2.5:
            analysis.append({
                "type": "点击率偏低",
                "level": "⚠️",
                "insight": f"CTR {ctr:.1f}%，低于行业标准（图文≥2.5%，视频≥4%）",
                "expert_advice": "CTR低的核心原因：\n1. 封面不够吸引人（高饱和对比色+醒目大字）\n2. 标题前10字没有核心关键词\n3. 素材与定向人群不匹配",
                "action": "优先优化封面和标题，发布后1小时数据决定笔记生死",
            })
        elif ctr > 5:
            analysis.append({
                "type": "点击率优秀",
                "level": "✅",
                "insight": f"CTR {ctr:.1f}%，高于行业标准",
                "expert_advice": "CTR表现优秀，说明素材吸引力强。建议：\n1. 适当提高预算放量\n2. 用此素材带动新素材测试",
                "action": "保持当前素材，观察转化数据",
            })
    
    # 3. CPC分析
    if cpc > 0.15:
        analysis.append({
            "type": "点击成本偏高",
            "level": "⚠️",
            "insight": f"CPC {cpc:.2f}元，高于实战均价",
            "expert_advice": "CPC高的原因：\n1. 出价过高（注意：官方建议出价虚高，应参考同行实际出价）\n2. 素材质量分低，需要用高出价补偿\n3. 定向过窄，系统匹配效率低",
            "action": "先优化素材提升质量分，再考虑降低出价",
        })
    
    # 4. 余额预警
    if balance < 200 and balance > 0:
        analysis.append({
            "type": "余额预警",
            "level": "💰",
            "insight": f"余额{balance:.0f}元，按当前消耗预计可用{balance/cost:.1f}天",
            "expert_advice": "余额不足会导致：\n1. 系统自动压低出价\n2. 流量质量下降\n3. 转化成本上升",
            "action": "尽快充值，保持账户余额充足",
        })
    
    # 5. 计划结构分析
    if active > 0:
        if active < 3:
            analysis.append({
                "type": "计划数量不足",
                "level": "⚠️",
                "insight": f"投放中计划{active}个，计划数量过少",
                "expert_advice": "根据'集中火力原则'，建议：\n1. 保持2-3个核心计划消耗80%预算\n2. 增加测试计划，用30%预算测试新素材",
                "action": "增加测试计划，保持计划结构健康",
            })
        elif active > 20:
            analysis.append({
                "type": "计划过于分散",
                "level": "⚠️",
                "insight": f"投放中计划{active}个，计划过于分散",
                "expert_advice": "计划过多会导致：\n1. 每个计划都拿不到足够数据\n2. 冷启动失败率高\n3. 预算分散，转化效率低",
                "action": "暂停低效计划，集中预算到2-3个核心计划",
            })
    
    # 6. 行业专属建议
    analysis.append({
        "type": f"{industry}行业建议",
        "level": "💡",
        "insight": f"基于{industry}行业最佳实践",
        "expert_advice": f"行业策略：\n1. 最佳投放时段：{industry_strategy['最佳投放时段']}\n2. 推荐转化方式：{industry_strategy['推荐转化方式']}\n3. 素材特点：{industry_strategy['素材特点']}\n4. 关键词策略：{industry_strategy['关键词策略']}",
        "action": f"根据{industry}行业特点调整投放策略",
    })
    
    return analysis


def format_expert_analysis(analysis):
    """格式化专家分析"""
    if not analysis:
        return "暂无分析结果"
    
    report = f"🧠 顶级投手分析\n{'═'*45}\n\n"
    
    for item in analysis:
        report += f"{item['level']} {item['type']}\n"
        report += f"{'─'*40}\n"
        report += f"📊 {item['insight']}\n\n"
        report += f"💡 专家解读：\n{item['expert_advice']}\n\n"
        report += f"🎯 建议操作：{item['action']}\n\n"
    
    return report


if __name__ == "__main__":
    # 测试专家分析
    test_dashboard = {
        'today_data': {
            'total_cost': 60.89,
            'ctr': 19.73,
            'cpc': 0.09,
            'impression': 3294,
            'click': 650,
        },
        'campaign_summary': {
            'active': 64,
            'paused': 10,
        },
        'account_budget': {
            'budget_yuan': 150,
            'available_balance_yuan': 220.12,
        }
    }
    
    analysis = generate_expert_analysis(test_dashboard, "旅游/酒旅")
    print(format_expert_analysis(analysis))
