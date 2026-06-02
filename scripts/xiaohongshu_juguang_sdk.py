#!/usr/bin/env python3
# 小红书聚光API完整SDK v3.8.1
# 基于飞书文档v1.1规范重写：统一POST、Header传Token、无签名
import json
import time
import logging
import requests
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 错误码映射
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

# ==================== 金额单位转换工具 ====================

def fen_to_yuan(fen):
    """分转元 — 小红书聚光 API 所有金额字段返回单位均为分，必须先转元再展示。
    
    用法：
        balance = sdk_result.get('available_balance', 0)  # 原始分
        print(f"余额: {fen_to_yuan(balance)}元")           # → 余额: 100.00元
    
    唯一例外：query_balance 接口返回的已经是元，不需要调用此函数。
    """
    if fen is None or fen == 0:
        return 0.0
    return float(fen) / 100.0


def yuan_to_fen(yuan):
    """元转分 — 构造 API 请求参数时使用。
    
    用法：
        params = {'limit_day_budget': yuan_to_fen(200)}  # 200元 → 20000分
    """
    if yuan is None:
        return 0
    return int(float(yuan) * 100)


# ==================== SDK 类 ====================

class XiaohongshuJuguangSDK:
    def __init__(self, config_path=None):
        import os as _os
        if config_path is None:
            config_path = (
                _os.environ.get('XIAOHONGSHU_CONFIG_PATH') or
                _os.path.join(_os.path.expanduser('~'), '.workbuddy', 'skills',
                              'xiaohongshu-juguang-ai', 'xiaohongshu_config.json')
            )
        if not _os.path.exists(config_path):
            raise FileNotFoundError(
                f"配置文件不存在: {config_path}\n"
                f"请先创建配置文件，参考模板: xiaohongshu_config.example.json"
            )
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.app_id = self.config['app_id']
        self.app_secret = self.config['app_secret']
        self.redirect_uri = self.config['redirect_uri']
        self.api_base_url = self.config['api_base_url']
        self.token_file = self.config['token_file']
        
        self.token_data = self._load_token()
        self.access_token = self.token_data.get('access_token', '')
        self.refresh_token = self.token_data.get('refresh_token', '')
        self.expires_at = self.token_data.get('expires_at', 0)
        self.advertiser_id = self.token_data.get('advertiser_id', '')
    
    def _load_token(self):
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_token(self, token_data):
        with open(self.token_file, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)
        self.token_data = token_data
        self.access_token = token_data.get('access_token', '')
        self.refresh_token = token_data.get('refresh_token', '')
        self.expires_at = token_data.get('expires_at', 0)
        self.advertiser_id = token_data.get('advertiser_id', '')
    
    def _request(self, api_path, data=None):
        """统一请求封装 - 按文档规范：POST + Header传Token"""
        return self._request_url(f"{self.api_base_url}{api_path}", data)
    
    def _request_url(self, url, data=None):
        """直接URL请求封装，支持非jg前缀的接口（如finance）"""
        start_time = time.time()
        
        # 检查token是否过期，自动刷新
        if time.time() > self.expires_at - 300 and self.refresh_token:
            self.refresh_access_token()
        
        if data is None:
            data = {}
        
        headers = {
            "Content-Type": "application/json",
            "Access-Token": self.access_token,
            "Timestamp": str(int(time.time()))
        }
        
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            
            elapsed = time.time() - start_time
            
            if result.get('code') == 0:
                logger.info(f"API请求成功: {url}, 耗时: {elapsed:.2f}s")
                return {"success": True, "data": result.get('data', {})}
            else:
                error_code = result.get('code')
                error_msg = ERROR_CODES.get(error_code, result.get('msg', '未知错误'))
                logger.warning(f"API请求失败: {url}, 错误码: {error_code}, 错误信息: {error_msg}, 耗时: {elapsed:.2f}s")
                return {
                    "success": False, 
                    "code": error_code, 
                    "message": error_msg
                }
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"API请求异常: {url}, 错误: {str(e)}, 耗时: {elapsed:.2f}s")
            return {"success": False, "message": f"请求失败: {str(e)}"}
    
    # ==================== 授权认证 ====================
    def get_access_token_by_code(self, auth_code):
        """用授权码换access_token - POST /api/open/oauth2/access_token
        官方文档字段：app_id(long), secret(string), auth_code(string)
        注意：不需要grant_type，字段名是secret不是app_secret
        """
        url = f"https://adapi.xiaohongshu.com/api/open/oauth2/access_token"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": int(self.app_id),
            "secret": self.app_secret,
            "auth_code": auth_code
        }
        
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            
            if result.get('code') == 0:
                data = result['data']
                token_data = {
                    "access_token": data['access_token'],
                    "refresh_token": data['refresh_token'],
                    "expires_at": int(time.time()) + data.get('expires_in', 86400),
                    "advertiser_id": data.get('advertiser_id', ''),
                    "advertiser_name": data.get('advertiser_name', ''),
                    "auth_time": int(time.time())
                }
                self._save_token(token_data)
                return {"success": True, "data": token_data}
            else:
                return {"success": False, "code": result.get('code'), "message": result.get('msg', '获取token失败')}
        except Exception as e:
            return {"success": False, "message": f"请求失败: {str(e)}"}
    
    def refresh_access_token(self):
        """刷新access_token - POST /api/open/oauth2/refresh_token
        官方文档字段：app_id(long), secret(string), refresh_token(string)
        注意：不需要grant_type参数
        """
        url = f"https://adapi.xiaohongshu.com/api/open/oauth2/refresh_token"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": int(self.app_id),
            "secret": self.app_secret,
            "refresh_token": self.refresh_token
        }
        
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=15)
            resp.raise_for_status()
            result = resp.json()
            
            if result.get('code') == 0:
                rdata = result['data']
                token_data = {
                    "access_token": rdata['access_token'],
                    "refresh_token": rdata['refresh_token'],
                    "expires_at": int(time.time()) + rdata.get('expires_in', 86400),
                    "advertiser_id": rdata.get('advertiser_id', self.advertiser_id),
                    "advertiser_name": rdata.get('advertiser_name', self.token_data.get('advertiser_name', '')),
                    "refresh_time": int(time.time())
                }
                self._save_token(token_data)
                return {"success": True, "data": token_data}
            else:
                return {"success": False, "code": result.get('code'), "message": result.get('msg', '刷新token失败')}
        except Exception as e:
            return {"success": False, "message": f"请求失败: {str(e)}"}
    
    # ==================== 账户服务 ====================
    def query_balance(self, user_id, virtual_seller_id_list, advertiser_id=None):
        """代理商主子账号余额查询
        余额单位为元（非分），virtual_seller_id_list最多100个
        资金类型：0现金/1授信/2返货/3券/4赔付返货
        """
        data = {
            "user_id": user_id,
            "virtual_seller_id_list": virtual_seller_id_list
        }
        return self._request_url("https://adapi.xiaohongshu.com/api/open/finance/balance/query", data)

    def agent_transfer(self, user_id, from_virtual_seller_id, to_virtual_seller_id, amount, 
                       from_wallet_type=0, to_wallet_type=0, remark="", business_no=None):
        """代理商转账（仅限代理商/服务商）
        金额单位为元（保留两位小数）
        只支持主→子和子→主，子账户首次满2000后才能创编
        request_no强制64字符且全局唯一，自动生成
        QPS有分布式锁，建议串行调用
        """
        import uuid
        request_no = business_no or f"Partner_{uuid.uuid4().hex}"[:64]
        data = {
            "user_id": user_id,
            "from_wallet": {
                "virtual_seller_id": from_virtual_seller_id,
                "wallet_type": from_wallet_type
            },
            "to_wallet": {
                "virtual_seller_id": to_virtual_seller_id,
                "wallet_type": to_wallet_type
            },
            "business_no": request_no,
            "request_no": request_no,
            "amount": f"{float(amount):.2f}",
            "remark": remark
        }
        return self._request_url("https://adapi.xiaohongshu.com/api/open/finance/agent/transfer", data)

    def query_transfer_result(self, user_id, virtual_seller_id, request_no):
        """查询转账结果
        status: PROCESSING=处理中, SUCCESS=成功, FAIL=失败
        """
        data = {
            "user_id": user_id,
            "virtual_seller_id": virtual_seller_id,
            "request_no": request_no
        }
        return self._request_url("https://adapi.xiaohongshu.com/api/open/finance/transfer/result/query", data)

    def query_finance_record(self, user_id, virtual_seller_id, start_date, end_date, 
                              page_index=1, page_size=100, date_key=None, 
                              wallet_type_list=None, trade_type_list=None):
        """资金流水查询（仅限代理商/服务商，品牌方用获取账户流水接口）
        注意：对应Partner平台资金流水，非聚光等其他平台账户流水
        金额单位为元，消耗+转出消耗流水在次日6:00之后
        direction: 1=收入, -1=支出
        date_key: 1=按投放日期, 2=按扣费日期
        trade_type: 1充值/2入账/3消费扣款/4退款/5转账/6出款/11订单支付/12订单退款
        """
        data = {
            "user_id": user_id,
            "virtual_seller_id": virtual_seller_id,
            "business_type": "AD_EFFECT",
            "start_date": start_date,
            "end_date": end_date,
            "page_index": page_index,
            "page_size": page_size
        }
        if date_key is not None:
            data["date_key"] = date_key
        if wallet_type_list is not None:
            data["wallet_type_list"] = wallet_type_list
        if trade_type_list is not None:
            data["trade_type_list"] = trade_type_list
        return self._request_url("https://adapi.xiaohongshu.com/api/open/finance/transaction/record/query", data)

    def get_account_budget(self, advertiser_id=None):
        """获取账户日预算余额（自动转换分→元）"""
        aid = int(advertiser_id or self.advertiser_id)
        result = self._request("/account/budget/info", {"advertiser_id": aid})
        return self._convert_budget_to_yuan(result)

    def get_account_budget_detail(self, advertiser_id=None):
        """获取账户日预算余额详情（自动转换分→元）"""
        aid = int(advertiser_id or self.advertiser_id)
        result = self._request("/account/budget/info", {"advertiser_id": aid})
        return self._convert_budget_to_yuan(result)

    def _convert_budget_to_yuan(self, result):
        """将预算接口返回的金额从分转换为元"""
        if not result.get('success'):
            return result
        data = result.get('data', {})
        fen_fields = [
            'cash_balance', 'return_balance', 'freeze_balance',
            'today_spend', 'total_balance', 'credit_balance',
            'available_balance', 'compensate_return_balance',
            'account_budget'
        ]
        for field in fen_fields:
            if field in data and data[field] is not None:
                data[field] = round(data[field] / 100, 2)
        result['data'] = data
        return result

    def get_account_order_info(self, start_date, end_date, advertiser_id=None, page=1, page_size=50, 
                               account_types=None, data_type=None):
        """获取账户流水（品牌方用此接口，代理商用finance/transaction/record/query）
        注意：此接口数据包括聚光/乘风/千帆/lite所有竞价广告流水
        金额单位为分，order_amount负数表示支出
        account_types: 0现金/1常规返货/2授信/6赔付返货，不传默认[0,1,2,6]
        服务商用户需传type=2
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {
            "advertiser_id": aid,
            "start_time": start_date,
            "end_time": end_date,
            "page": page,
            "page_size": page_size
        }
        if account_types is not None:
            data["account_types"] = account_types
        if data_type is not None:
            data["type"] = data_type
        return self._request("/account/order/info", data)
    
    def update_account_budget(self, budget_yuan, limit_day_budget=1, smart_switch=0, advertiser_id=None):
        """修改账户日预算
        budget_yuan: 预算金额（元），自动转换为分
        limit_day_budget: 0=不限预算 1=指定预算
        smart_switch: 0=关闭节假日上浮 1=开启
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {
            "advertiser_id": aid,
            "limit_day_budget": limit_day_budget
        }
        if limit_day_budget == 1:
            data["account_budget"] = int(budget_yuan * 100)  # 元转分
            data["smart_switch"] = smart_switch
        return self._request("/account/budget/update", data)
    
    def get_campaign_order_info(self, start_date, end_date, advertiser_id=None, page=1, page_size=50):
        """获取计划流水（消耗明细）
        返回金额单位为分，campaign_day_budget=-1表示不限预算
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/account/ad/order/info", {
            "advertiser_id": aid, "start_time": start_date, "end_time": end_date,
            "page": page, "page_size": page_size
        })
    
    # ==================== 推广计划 ====================
    def cascade_modify(self, modify_type, mod_cascade_info_list, advertiser_id=None):
        """新创编编辑接口（统一入口，修改计划/单元/创意）
        modify_type: 1=编辑计划 2=编辑单元 3=编辑创意
        ⚠️ 目前只支持产品种草营销诉求
        ⚠️ 预算金额单位为分
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {
            "advertiser_id": aid,
            "modify_type": modify_type,
            "mod_cascade_info_list": mod_cascade_info_list
        }
        return self._request("/cascade/modify", data)

    def cascade_create(self, create_type, create_cascade_info_list, advertiser_id=None):
        """新创编创建接口（创建计划/单元/创意）
        create_type: 1=创建三层 2=已有计划下创建单元+创意 3=已有单元下创建创意
        ⚠️ create_type=2只支持手动出价计划；2/3需有完整计划单元创意
        ⚠️ 一次最多新建20个创意
        ⚠️ 预算/出价金额单位为分

        create_cascade_info_list 格式示例（create_type=1）：
        [{
            "campaign": {
                "campaign_name": "计划名称",
                "marketing_target": 4,  # 4=产品种草 9=客资收集 13=种草直达
                "placement": 1,  # 1=信息流 2=搜索 4=全站 7=视频流
                "promotion_target": 1,  # 1=笔记 9=落地页
                "optimize_objective": 0,  # 0=点击量 1=互动量
                "deep_optimize_objective": -1,
                "bidding_strategy": 2,  # 2=手动出价 3=最大转化 7=稳定成本
                "pacing_mode": 1,  # 1=匀速 2=加速
                "search_flag": 0,  # 0=关闭 1=开启
                "limit_day_budget": 1,  # 0=不限 1=指定预算
                "origin_campaign_day_budget": 10000,  # 预算金额(分)
                "time_type": 0,  # 0=长期投放 1=设置起止日期
                "time_period_type": 0,  # 0=不限 1=指定时段
                "time_period": {  # TimePeriodDTO, 7天×24小时
                    "mon": "111111111111111111111111",
                    "tues": "111111111111111111111111",
                    "wed": "111111111111111111111111",
                    "thur": "111111111111111111111111",
                    "fri": "111111111111111111111111",
                    "sat": "111111111111111111111111",
                    "sun": "111111111111111111111111"
                },
                "explore_state": 0,
                "horse_race": 0
            },
            "unit_with_creative_list": [{
                "unit": {
                    "unit_name": "单元名称",
                    "target_type": 2,  # 2=智能定向 3=高级定向
                    "event_bid": 100,  # 出价(分)
                    "target_info": {  # CreateTargetInfo
                        "target_gender": "all",
                        "target_city_type": 0,
                        "target_city": "中国",
                        "target_area_code": "1",  # -1=全部, 多个用#分隔
                        "target_age": "all",
                        "target_device": "all",
                        "target_device_price": "all",
                        "target_generalization_switch": 0,
                        "search_target_city_intent": 0,
                        "intelligent_expansion": 0
                    }
                },
                "creativity_list": [{
                    "creativity_name": "创意名称",
                    "note_id": "笔记ID",
                    "conversion_type": 0,  # 0=无组件 3=私信组件
                    "note_source_type": 1,
                    "mask_gen": 2,  # 1=开启自动优化封面 2=不开启
                    "title_gen": 2  # 1=开启自动优化标题 2=不开启
                }]
            }]
        }]
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {
            "advertiser_id": aid,
            "create_type": create_type,
            "create_cascade_info_list": create_cascade_info_list
        }
        return self._request("/cascade/create", data)

    def quick_create_campaign(self, campaign_name, note_id, unit_name=None, creativity_name=None,
                              marketing_target=4, placement=1, bidding_strategy=2,
                              daily_budget_yuan=100, bid_yuan=1,
                              area_code="-1", target_gender="all",
                              conversion_type=0, optimize_objective=0,
                              carrier_type=None, campaign_group_id=None,
                              search_flag=0, bar_content=None,
                              component_conv_num_is_show=None):
        """快捷创建计划（产品种草/客资收集常用配置）

        Args:
            campaign_name: 计划名称
            note_id: 笔记ID
            unit_name: 单元名称（默认=计划名称+单元）
            creativity_name: 创意名称（默认=计划名称+创意）
            marketing_target: 4=产品种草 9=客资收集 13=种草直达
            placement: 1=信息流 2=搜索 4=全站 7=视频流
            bidding_strategy: 2=手动出价 3=最大转化 7=稳定成本
            daily_budget_yuan: 日预算（元），内部自动转分
            bid_yuan: 出价（元），内部自动转分
            area_code: 地域编码，-1=全部
            target_gender: 性别定向，all/0/1
            conversion_type: 组件类型
                产品种草: 0=无组件
                客资收集: 3=私信 10=留资 20=落地页 78=私信表单同投
            optimize_objective: 优化目标
                产品种草: 0=点击 1=互动
                客资收集: 3=表单提交 5=私信进线 13=私信开口 50=留资 78=线索流资
            carrier_type: 投放载体（客资收集必传: 1=私信 2=落地页 3=私信+落地页）
            campaign_group_id: 广告组ID
            search_flag: 搜索快投 0=关闭 1=开启
            bar_content: 引导文案（客资收集私信组件可选，最多6字）
            component_conv_num_is_show: 展示已转化人数（客资收集私信组件可选）

        Returns:
            {success, campaign_id, unit_id, creativity_id} 或错误信息
        """
        all_day = "111111111111111111111111"
        daily_budget = int(daily_budget_yuan * 100)
        bid = int(bid_yuan * 100)

        campaign = {
            "campaign_name": campaign_name,
            "marketing_target": marketing_target,
            "placement": placement,
            "promotion_target": 1,
            "optimize_objective": optimize_objective,
            "deep_optimize_objective": -1,
            "bidding_strategy": bidding_strategy,
            "pacing_mode": 1,
            "search_flag": search_flag,
            "limit_day_budget": 1,
            "origin_campaign_day_budget": daily_budget,
            "time_type": 0,
            "time_period_type": 0,
            "time_period": {
                "mon": all_day, "tues": all_day, "wed": all_day,
                "thur": all_day, "fri": all_day, "sat": all_day, "sun": all_day
            },
            "explore_state": 0,
            "horse_race": 0
        }
        if carrier_type:
            campaign["carrier_type"] = carrier_type
        if campaign_group_id:
            campaign["campaign_group_id"] = campaign_group_id

        unit = {
            "unit_name": unit_name or f"{campaign_name}_单元",
            "target_type": 2,
            "event_bid": bid,
            "target_info": {
                "target_gender": target_gender,
                "target_city_type": 0,
                "target_city": "中国",
                "target_area_code": str(area_code),
                "target_age": "all",
                "target_device": "all",
                "target_device_price": "all",
                "target_generalization_switch": 0,
                "search_target_city_intent": 0,
                "intelligent_expansion": 0
            }
        }

        creative = {
            "creativity_name": creativity_name or f"{campaign_name}_创意",
            "note_id": str(note_id),
            "conversion_type": conversion_type,
            "note_source_type": 1,
            "mask_gen": 2,
            "title_gen": 2
        }
        # 客资收集私信组件需要的额外参数
        if conversion_type == 3:  # 私信组件
            creative["conversion_component_types"] = [0]
            if bar_content:
                creative["bar_content"] = bar_content
            if component_conv_num_is_show is not None:
                creative["component_conv_num_is_show"] = component_conv_num_is_show

        result = self.cascade_create(1, [{
            "campaign": campaign,
            "unit_with_creative_list": [{
                "unit": unit,
                "creativity_list": [creative]
            }]
        }])

        if result.get("success"):
            info = result["data"]["info_list"][0]
            return {
                "success": True,
                "campaign_id": info["campaign"]["campaign_id"],
                "unit_id": info["unit_with_creative_list"][0]["unit"]["unit_id"],
                "creativity_id": info["unit_with_creative_list"][0]["creativity_list"][0]["creativity_id"]
            }
        return result

    def get_top_creatives(self, days=30, top_n=5, min_fee=1.0, min_ctr=10.0, filter_existing_notes=True):
        """获取优质笔记（按消耗和CTR筛选，同一笔记多计划投放会汇总）

        Args:
            days: 统计天数（默认30天）
            top_n: 返回前N个笔记
            min_fee: 最低消耗阈值（元）
            min_ctr: 最低CTR阈值（%）
            filter_existing_notes: 是否只返回笔记列表中存在的笔记

        Returns:
            [{note_id, fee, click, impression, ctr, convert, score, creativity_count}, ...]
        """
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days+1)).strftime('%Y-%m-%d')
        
        r = self.get_offline_report('creative', start_date, end_date)
        if not r.get('success'):
            return []
        
        data_list = r.get('data', {}).get('data_list', [])
        
        # 获取现有笔记ID列表
        existing_note_ids = set()
        if filter_existing_notes:
            note_r = self.get_note_list()
            if note_r.get('success'):
                existing_note_ids = set(n['note_id'] for n in note_r['data'].get('notes', []))
        
        # 按note_id汇总数据
        note_stats = defaultdict(lambda: {'fee': 0, 'click': 0, 'impression': 0, 'convert': 0, 'creativity_count': 0})
        
        for c in data_list:
            note_id = c.get('note_id', '')
            
            # 过滤掉已删除的笔记
            if filter_existing_notes and note_id not in existing_note_ids:
                continue
            
            fee = float(c.get('fee', 0))
            click = int(c.get('click', 0))
            impression = int(c.get('impression', 0))
            convert = int(c.get('convert_cnt', 0))
            
            note_stats[note_id]['fee'] += fee
            note_stats[note_id]['click'] += click
            note_stats[note_id]['impression'] += impression
            note_stats[note_id]['convert'] += convert
            note_stats[note_id]['creativity_count'] += 1
        
        # 计算评分和CTR
        notes = []
        for note_id, stats in note_stats.items():
            fee = stats['fee']
            click = stats['click']
            impression = stats['impression']
            convert = stats['convert']
            ctr = (click / impression * 100) if impression > 0 else 0
            
            # 计算综合评分
            score = 0
            if fee >= min_fee:
                score += 40  # 有消耗
            if click > 0:
                score += min(click / 10, 20)  # 点击量
            if ctr >= min_ctr:
                score += 25  # CTR达标
            if convert > 0:
                score += 30  # 有转化
            
            notes.append({
                'note_id': note_id,
                'fee': round(fee, 2),
                'click': click,
                'impression': impression,
                'ctr': round(ctr, 2),
                'convert': convert,
                'score': score,
                'creativity_count': stats['creativity_count']
            })
        
        # 按评分排序
        notes.sort(key=lambda x: x['score'], reverse=True)
        return notes[:top_n]

    def create_campaign_with_creatives(self, campaign_name, note_ids, unit_name=None,
                                        marketing_target=9, placement=4, bidding_strategy=7,
                                        daily_budget_yuan=100, bid_yuan=1.0,
                                        carrier_type=1, optimize_objective=13,
                                        conversion_type=3, bar_content="立即咨询",
                                        component_conv_num_is_show=True,
                                        target_gender="all", area_code="-1",
                                        search_flag=0, keywords=None, industry_keyword=None):
        """创建计划（支持多个创意）

        Args:
            campaign_name: 计划名称
            note_ids: 笔记ID列表（至少5个）
            unit_name: 单元名称
            marketing_target: 4=产品种草 9=客资收集
            placement: 1=信息流 2=搜索 4=全站 7=视频流
            bidding_strategy: 2=手动出价 3=最大转化 7=稳定成本
            daily_budget_yuan: 日预算（元）
            bid_yuan: 出价（元）
            carrier_type: 1=私信 2=落地页 3=私信+落地页
            optimize_objective: 3=表单提交 5=私信进线 13=私信开口 50=留资 78=线索流资
            conversion_type: 3=私信 10=留资 20=落地页 78=私信表单同投
            bar_content: 引导文案
            component_conv_num_is_show: 展示已转化人数
            target_gender: 性别定向
            area_code: 地域编码
            search_flag: 搜索快投
            keywords: 关键词列表 [{keyword, bid, phrase_match_type}]，bid单位分
            industry_keyword: 行业关键词（如"酒店"、"旅游"），用于自动获取推荐关键词

        Returns:
            {success, campaign_id, unit_id, creativity_ids: [...]} 或错误信息
        """
        all_day = "111111111111111111111111"
        daily_budget = int(daily_budget_yuan * 100)
        bid = int(bid_yuan * 100)

        # 构建创意列表
        creativity_list = []
        for i, note_id in enumerate(note_ids):
            creative = {
                "creativity_name": f"{campaign_name}_创意{i+1}",
                "note_id": str(note_id),
                "conversion_type": conversion_type,
                "note_source_type": 1,
                "mask_gen": 2,
                "title_gen": 2
            }
            if conversion_type == 3:  # 私信组件
                creative["conversion_component_types"] = [0]
                if bar_content:
                    creative["bar_content"] = bar_content
                if component_conv_num_is_show is not None:
                    creative["component_conv_num_is_show"] = component_conv_num_is_show
            creativity_list.append(creative)

        campaign = {
            "campaign_name": campaign_name,
            "marketing_target": marketing_target,
            "placement": placement,
            "promotion_target": 1,
            "optimize_objective": optimize_objective,
            "deep_optimize_objective": -1,
            "bidding_strategy": bidding_strategy,
            "pacing_mode": 1,
            "search_flag": search_flag,
            "limit_day_budget": 1,
            "origin_campaign_day_budget": daily_budget,
            "time_type": 0,
            "time_period_type": 0,
            "time_period": {
                "mon": all_day, "tues": all_day, "wed": all_day,
                "thur": all_day, "fri": all_day, "sat": all_day, "sun": all_day
            },
            "explore_state": 0,
            "horse_race": 0
        }
        if carrier_type:
            campaign["carrier_type"] = carrier_type

        unit = {
            "unit_name": unit_name or f"{campaign_name}_单元",
            "target_type": 2,
            "event_bid": bid,
            "target_info": {
                "target_gender": target_gender,
                "target_city_type": 0,
                "target_city": "中国",
                "target_area_code": str(area_code),
                "target_age": "all",
                "target_device": "all",
                "target_device_price": "all",
                "target_generalization_switch": 0,
                "search_target_city_intent": 0,
                "intelligent_expansion": 0
            }
        }

        # 如果没有提供关键词，但提供了行业关键词，自动获取推荐关键词
        if not keywords and industry_keyword:
            try:
                r = self.keyword_recommend(industry_keyword)
                if r.get('success'):
                    word_list = r['data'].get('word_list', [])[:5]
                    keywords = [{
                        'keyword': k.get('keyword', ''),
                        'bid': int(k.get('bid', 200)),  # 转换为分
                        'phrase_match_type': 0  # 广泛匹配
                    } for k in word_list if k.get('keyword')]
            except Exception as e:
                pass  # 获取关键词失败不影响创建计划
        
        result = self.cascade_create(1, [{
            "campaign": campaign,
            "unit_with_creative_list": [{
                "unit": unit,
                "creativity_list": creativity_list
            }]
        }])

        if result.get("success"):
            info = result["data"]["info_list"][0]
            unit_info = info["unit_with_creative_list"][0]
            campaign_id = info["campaign"]["campaign_id"]
            unit_id = unit_info["unit"]["unit_id"]
            creativity_ids = [c["creativity_id"] for c in unit_info["creativity_list"]]
            
            # 添加关键词
            if keywords:
                keyword_result = self.add_unit_keyword(unit_id, keywords)
                if not keyword_result.get('success'):
                    return {
                        "success": True,
                        "campaign_id": campaign_id,
                        "unit_id": unit_id,
                        "creativity_ids": creativity_ids,
                        "keyword_warning": f"关键词添加失败: {keyword_result.get('message', '')}"
                    }
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "unit_id": unit_id,
                "creativity_ids": creativity_ids
            }
        return result

    def get_campaign_list(self, advertiser_id=None, campaign_ids=None, start_time=None, expire_time=None,
                           status=None, update_start_date=None, update_end_date=None,
                           page_index=1, page_size=20):
        """查询计划列表（单页）
        campaign_ids: 最多20个
        status: 1=有效 2=暂停 3=已删除 4=计划预算不足 5=现金余额不足 6=所有未删除 7=账户日预算不足 8=暂停阶段
        start_time/expire_time: 创建时间查询范围
        update_start_date/update_end_date: 更新时间查询范围
        返回：data.page.total_count=总计划数, data.base_campaign_dtos=计划列表
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {"advertiser_id": aid, "page": {"page_index": page_index, "page_size": page_size}}
        if campaign_ids: data["campaign_ids"] = campaign_ids
        if start_time: data["start_time"] = start_time
        if expire_time: data["expire_time"] = expire_time
        if status is not None: data["status"] = status
        if update_start_date: data["update_start_date"] = update_start_date
        if update_end_date: data["update_end_date"] = update_end_date
        return self._request("/campaign/list", data)
    
    def get_all_campaigns(self, advertiser_id=None):
        """获取全量计划（自动分页）
        返回所有计划列表，确保全量读取
        返回格式：{success, data: [...], total_count}
        """
        aid = int(advertiser_id or self.advertiser_id)
        all_campaigns = []
        page_index = 1
        page_size = 100  # 最大每页数量
        
        while True:
            result = self.get_campaign_list(
                advertiser_id=aid,
                page_index=page_index,
                page_size=page_size
            )
            
            if not result.get('success'):
                break
            
            data = result.get('data', {})
            campaigns = data.get('base_campaign_dtos', [])
            page_info = data.get('page', {})
            total_count = page_info.get('total_count', 0)
            
            all_campaigns.extend(campaigns)
            
            # 如果已经获取所有计划，或者返回数量小于每页数量，停止
            if len(all_campaigns) >= total_count or len(campaigns) < page_size:
                break
            
            page_index += 1
        
        return {
            'success': True,
            'data': all_campaigns,
            'total_count': len(all_campaigns)
        }

    def get_all_units(self, advertiser_id=None):
        """获取全量单元（自动分页）
        返回所有单元列表，确保全量读取
        返回格式：{success, data: [...], total_count}
        """
        aid = int(advertiser_id or self.advertiser_id)
        all_units = []
        page_index = 1
        page_size = 100  # 最大每页数量
        
        while True:
            result = self.get_unit_list(
                advertiser_id=aid,
                page_index=page_index,
                page_size=page_size
            )
            
            if not result.get('success'):
                break
            
            data = result.get('data', {})
            units = data.get('unit_infos', [])
            total_count = data.get('total_count', 0)
            
            all_units.extend(units)
            
            # 如果已经获取所有单元，或者返回数量小于每页数量，停止
            if len(all_units) >= total_count or len(units) < page_size:
                break
            
            page_index += 1
        
        return {
            'success': True,
            'data': all_units,
            'total_count': len(all_units)
        }

    def get_all_creatives(self, status=2, advertiser_id=None):
        """获取全量创意（自动分页）
        返回所有创意列表，确保全量读取
        返回格式：{success, data: [...], total_count}
        """
        aid = int(advertiser_id or self.advertiser_id)
        all_creatives = []
        page_index = 1
        page_size = 100  # 最大每页数量
        
        while True:
            result = self.search_creativity(
                status=status,
                advertiser_id=aid,
                page_index=page_index,
                page_size=page_size
            )
            
            if not result.get('success'):
                break
            
            data = result.get('data', {})
            creatives = data.get('creativity_dtos', [])
            page_info = data.get('page', {})
            total_count = page_info.get('total_count', 0)
            
            all_creatives.extend(creatives)
            
            # 如果已经获取所有创意，或者返回数量小于每页数量，停止
            if len(all_creatives) >= total_count or len(creatives) < page_size:
                break
            
            page_index += 1
        
        return {
            'success': True,
            'data': all_creatives,
            'total_count': len(all_creatives)
        }

    def get_all_notes(self, note_type=1, advertiser_id=None):
        """获取全量笔记（自动分页）
        返回所有笔记列表，确保全量读取
        返回格式：{success, data: [...], total_count}
        """
        aid = int(advertiser_id or self.advertiser_id)
        all_notes = []
        page = 1
        page_size = 100  # 最大每页数量
        
        while True:
            result = self.get_note_list(
                note_type=note_type,
                advertiser_id=aid,
                page=page,
                page_size=page_size
            )
            
            if not result.get('success'):
                break
            
            data = result.get('data', {})
            notes = data.get('notes', [])
            total_count = data.get('total_count', len(notes))
            
            all_notes.extend(notes)
            
            # 如果已经获取所有笔记，或者返回数量小于每页数量，停止
            if len(all_notes) >= total_count or len(notes) < page_size:
                break
            
            page += 1
        
        return {
            'success': True,
            'data': all_notes,
            'total_count': len(all_notes)
        }

    def update_campaign(self, campaign_id, advertiser_id=None, **kwargs):
        """编辑计划
        campaign_name: 计划名称（不能重复）
        limit_day_budget: 预算类型
        campaign_day_budget: 预算金额（单位分）
        smart_switch: 节假日上浮 0=关闭 1=开启
        time_type: 0=长期投放 1=设置起止时间
        start_time/expire_time: 推广开始/结束时间
        time_period_type: 0=全时段 1=自定义
        time_period: TimePeriodDTO
        pacing_mode: 1=匀速 2=加速
        ⚠️ bidding_strategy不支持更新
        search_flag: 搜索快投（仅客资收集支持）
        search_bid_ratio: 搜索快投出价系数，默认1.0
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {"advertiser_id": aid, "campaign_id": campaign_id}
        data.update(kwargs)
        return self._request("/campaign/update", data)

    def update_campaign_status(self, campaign_ids, action_type, advertiser_id=None):
        """修改计划状态
        action_type: 1=开启 2=暂停 3=删除
        campaign_ids: 最多20个
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/campaign/status/update", {
            "advertiser_id": aid, "campaign_ids": campaign_ids, "action_type": action_type
        })
    
    def create_campaign_group(self, campaign_group_name, limit_day_budget=0, origin_group_day_budget=None, advertiser_id=None):
        """创建广告组
        campaign_group_name: 广告组名称，最多50字符
        limit_day_budget: 是否限制预算 0=不限制 1=限制
        origin_group_day_budget: ⚠️ 日预算金额（单位分），最小值10000（100元），最大值99999900，limit_day_budget=1时必填
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {"advertiser_id": aid, "campaign_group_name": campaign_group_name, "limit_day_budget": limit_day_budget}
        if origin_group_day_budget is not None:
            data["origin_group_day_budget"] = origin_group_day_budget
        return self._request("/campaign/group/create", data)
    
    def delete_campaign_group(self, groups, advertiser_id=None):
        """删除广告组
        groups: 广告组数组，结构为[{"campaign_group_id": 广告组ID, "state": 0}] ⚠️ state必须固定传0
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/campaign/group/delete", {"advertiser_id": aid, "groups": groups})
    
    def update_campaign_group(self, groups, advertiser_id=None):
        """更新广告组
        groups: 广告组数组，每个元素结构：
        {
            "campaign_group_id": 广告组ID（必填）,
            "enable": 可选 启停状态 0=下线 1=上线,
            "campaign_group_name": 可选 广告组名称 最多50字符,
            "limit_day_budget": 可选 是否限制预算 0=不限制 1=限制,
            "origin_group_day_budget": 可选 日预算金额 单位分 最小10000（100元）最大99999900 limit_day_budget=1时必填
        }
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/campaign/group/update", {"advertiser_id": aid, "groups": groups})
    
    def list_campaign_group(self, ids=None, name=None, page_num=1, page_size=20, advertiser_id=None):
        """查询广告组列表
        ⚠️ 该接口仅支持查询未删除的广告组
        ⚠️ ids和name参数互斥，不能同时传值
        ids: 可选 广告组ID数组
        name: 可选 广告组名称
        page_num: 页码 默认1
        page_size: 页大小 默认20
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {"advertiser_id": aid, "page_num": page_num, "page_size": page_size}
        if ids is not None:
            data["ids"] = ids
        if name is not None:
            data["name"] = name
        return self._request("/campaign/group/base/list", data)

    # ==================== 简单投模块 ====================
    def create_ube_semi_auto(self, base_config, target_config, creativity_config, advertiser_id=None):
        """新建简单投
        ⚠️ 当前仅支持应用唤起营销诉求
        base_config: 计划基础配置，结构见接口文档UbeSemiBaseConfigDTO
        target_config: 定向配置，结构见接口文档UbeSemiTargetConfigDTO
        creativity_config: 创意配置，结构见接口文档UbeSemiCreativityConfigDTO
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {
            "advertiser_id": aid,
            "base_config": base_config,
            "target_config": target_config,
            "creativity_config": creativity_config
        }
        return self._request("/ube/semi/auto/create", data)

    def get_note_list(self, note_type=1, page=1, page_size=20, advertiser_id=None):
        """获取笔记列表（2026-05-28验证通过）
        note_type: 笔记类型，1=已确认可用
        返回格式：{success, data: {notes: [...], total_count}}
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/note/list", {
            "advertiser_id": aid, "note_type": note_type,
            "page": page, "page_size": page_size
        })

    # ==================== 推广单元 ====================
    def add_unit_keyword(self, unit_id, keyword_with_bid, add_type=1, phrase_match_type_upgrade=-1, advertiser_id=None):
        """修改单元关键词
        add_type: 0=替换（删除已有词再添加） 1=追加（不删除已有词）
        keyword_with_bid: [{"keyword": "xxx", "bid": 0, "phrase_match_type": 0/1}]
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/unit/keyword/add", {
            "advertiser_id": aid, "unit_id": unit_id, "add_type": add_type,
            "phrase_match_type_upgrade": phrase_match_type_upgrade,
            "keyword_with_bid": keyword_with_bid
        })

    def update_unit(self, unit_id, advertiser_id=None, **kwargs):
        """编辑单元
        event_bid: 出价/目标成本（单位分），自动控制不需要传
        note_ids: 笔记id列表
        target_type: 1=通投 2=智能定向 3=高级定向
        target_config: 定向配置
        keyword_with_bid: 关键词列表
        keyword_gen_type: -1=无意义 0=手动 1=智能拓词 2=手动+智能
        spu_note_info: spu&笔记标的信息（不支持修改）
        landing_page_url: 自研落地页URL（不支持修改）
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {"advertiser_id": aid, "unit_id": unit_id}
        data.update(kwargs)
        return self._request("/unit/update", data)

    def get_unit_list(self, page_index=1, page_size=20, advertiser_id=None, **kwargs):
        """查询单元列表（2026-05-28验证通过）
        page_index/page_size: 分页参数
        ⚠️ 接口参数为pageIndex/pageSize（驼峰命名），非page/page_size
        campaign_id: 可选，按计划筛选
        unit_ids: 可选，按单元ID筛选
        注意：返回字段是id和name，不是unit_id和unit_name
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {"advertiser_id": aid, "pageIndex": str(page_index), "pageSize": str(page_size)}
        data.update(kwargs)
        result = self._request("/unit/list", data)
        # 兼容字段名：将id/name转换为unit_id/unit_name
        if result.get('success'):
            for unit in result.get('data', {}).get('unit_infos', []):
                if 'id' in unit and 'unit_id' not in unit:
                    unit['unit_id'] = unit['id']
                if 'name' in unit and 'unit_name' not in unit:
                    unit['unit_name'] = unit['name']
        return result

    def update_unit_status(self, unit_ids, status, advertiser_id=None):
        """修改单元状态（2026-05-28验证通过）
        unit_ids: 单元ID数组，最多20个
        status: 1=开启 2=暂停 3=删除
        ⚠️ 参数为status（不是action_type），路径为/unit/update/status
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/unit/update/status", {
            "advertiser_id": aid, "unit_ids": unit_ids, "status": status
        })

    def update_unit_bid(self, event_bid_list, advertiser_id=None):
        """修改单元出价（批量）
        event_bid_list: [{"unit_id": long, "event_bid": int(单位分)}]，最多100个
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/unit/batch/update/bid", {
            "advertiser_id": aid, "event_bid_list": event_bid_list
        })

    # ==================== 创意管理 ====================
    def search_creativity(self, status=2, page_index=1, page_size=20, advertiser_id=None, **kwargs):
        """查询创意列表
        status: 创意状态枚举 1=已删除 2=所有未删除 3=暂停 4=单元暂停 5=计划暂停 8=有效 9=商品异常 10=单元未开始 11=单元已结束 12=暂停时段 13=计划预算不足 14=现金不足 16=账户日预算不足
        page_index: 页码 默认1
        page_size: 每页行数 默认20
        其他可选筛选参数：
        campaign_id: 计划ID
        unit_id: 单元ID
        creativity_ids: 创意ID数组 最多20个 ⚠️传了会忽略其他所有筛选字段
        start_time/end_time: 创意创建时间筛选 格式yyyy-MM-dd 必须同时传/不传
        note_id: 笔记ID 仅creativity_ids为空时有效
        update_start_date/update_end_date: 创意更新时间筛选 格式yyyy-MM-dd 必须同时传/不传
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {
            "advertiser_id": aid,
            "status": status,
            "page": {"page_index": page_index, "page_size": page_size}
        }
        data.update(kwargs)
        return self._request("/creativity/search", data)
    
    def update_creativity_status(self, creativity_ids, action_type, advertiser_id=None):
        """批量修改创意状态
        creativity_ids: 创意ID数组，最多20个
        action_type: 1=开启，2=暂停，3=删除
        ⚠️ 接口路径为/creativitystatus/update（status直接连写，无斜杠）
        """
        aid = int(advertiser_id or self.advertiser_id)
        return self._request("/creativitystatus/update", {
            "advertiser_id": aid, "creativity_ids": creativity_ids, "action_type": action_type
        })
    
    def update_creativity(self, creativity_id, advertiser_id=None, **kwargs):
        """编辑创意
        creativity_name: 创意名称
        click_urls: 点击链接数组
        expo_urls: 曝光链接数组
        mask_perfer: 封面优选开关 0=关闭 1=开启
        title_mask_perfer: 标题优选开关 0=关闭 1=开启
        jump_url: 跳转链接
        bar_content: 文案内容
        item_id: 商品ID
        h5_infos: 前链H5信息
        conversion_component_type: 转化组件类型数组 [0=营销组件,1=评论区组件]
        comment: 评论区文案
        h5_material_info: 程序化创意素材
        poi_id: POI ID
        poi_jump_type: POI跳转类型
        monitor_company: 监测公司
        monitor_params: 监测参数
        ad_biz_item_id: 广告侧绑定商品ID
        app_comp_icon: 唤端场景商品主图
        fall_back_jump_url: 唤端兜底链接
        primary_title: 主标题（最多11字符）
        ios_download_link: iOS兜底下载链接（仅应用唤起专属）
        android_download_link: Android兜底下载链接（仅应用唤起专属）
        """
        aid = int(advertiser_id or self.advertiser_id)
        data = {"advertiser_id": aid, "creativity_id": creativity_id}
        data.update(kwargs)
        return self._request("/creativity/update", data)
    
    # ==================== 数据报表 ====================
    def get_offline_report(self, report_type, start_date, end_date, time_unit="SUMMARY", 
                           page=1, page_size=200, advertiser_id=None, **kwargs):
        """获取离线报表（普通投放）
        report_type: account/campaign/unit/creative/keyword/search_word/note/crowd/spu
        
        返回结构：
        {
            "success": True,
            "data": {
                "aggregation_data": {...},  # 汇总数据
                "data_list": [...],          # 明细数据（创意/计划/单元等）
                "total_count": 112           # 总数
            }
        }
        
        ⚠️ 注意：消耗字段是'fee'（单位：元），不是'cost'
        """
        aid = advertiser_id or self.advertiser_id
        data = {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date,
            "time_unit": time_unit, "page": page, "page_size": page_size
        }
        data.update(kwargs)
        return self._request(f"/data/report/offline/{report_type}", data)
    
    def get_easy_promotion_report(self, start_date, end_date, time_unit="SUMMARY",
                                   page=1, page_size=200, advertiser_id=None):
        """获取简单投报表"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/offline/easy/promotion/base", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date,
            "time_unit": time_unit, "page": page, "page_size": page_size
        })
    
    def get_realtime_report(self, report_type, advertiser_id=None, **kwargs):
        """获取实时报表
        report_type: account/campaign/unit/creative/keyword/target/group
        """
        aid = advertiser_id or self.advertiser_id
        data = {"advertiser_id": aid}
        data.update(kwargs)
        return self._request(f"/data/report/realtime/{report_type}", data)
    
    def get_daily_cost(self, date, advertiser_id=None):
        """获取指定日期的完整消耗（仅看账户层，规则已锁死）
        
        🚫 规则锁死（严禁修改，违反者出数据事故）：
        1. 消耗统计只看账户层（account），禁止用计划/单元/创意层级
           - 原因：下层可能因权限返回空数据，账户层是唯一准确源
        2. 标准投放：/data/report/offline/account → aggregation_data.fee（单位元）
        3. 简单投：  /data/report/offline/easy/promotion/base → aggregation_data.fee（单位元）
        4. 总消耗 = 标准投放.fee + 简单投.fee
        5. fee字段已经是元，不需要除以100
        6. 禁止用delivery_type参数区分，简单投有独立接口路径
        7. 禁止用campaign/unit/creative报表的消耗数据做汇总
        
        返回结构：
        {
            "date": "2026-05-27",
            "normal_cost": 45.57,    # 标准投放消耗（元）
            "normal_impression": 3837,
            "normal_click": 719,
            "easy_cost": 12.48,       # 简单投消耗（元）
            "easy_impression": 1131,
            "easy_click": 237,
            "total_cost": 58.05,      # 总消耗（元）
            "total_impression": 4968,
            "total_click": 956
        }
        """
        aid = advertiser_id or self.advertiser_id
        result = {
            "date": date,
            "normal_cost": 0, "normal_impression": 0, "normal_click": 0,
            "easy_cost": 0, "easy_impression": 0, "easy_click": 0,
        }
        
        # 判断是否为今天（实时报表支持今天，离线报表T+1）
        today = datetime.now().strftime("%Y-%m-%d")
        is_today = (date == today)
        
        if is_today:
            # 今日数据：使用实时报表
            # 实时报表数据结构：data直接包含字段，非aggregation_data
            realtime = self.get_realtime_report("account", advertiser_id=aid, start_date=date, end_date=date)
            if realtime['success']:
                realtime_data = realtime.get('data', {})
                result['normal_cost'] = float(realtime_data.get('fee', 0))
                result['normal_impression'] = int(realtime_data.get('impression', 0))
                result['normal_click'] = int(realtime_data.get('click', 0))
        else:
            # 历史数据：使用离线报表
            # 标准投放
            normal = self.get_offline_report("account", date, date, advertiser_id=aid)
            if normal['success']:
                agg = normal['data'].get('aggregation_data', {})
                result['normal_cost'] = float(agg.get('fee', 0))
                result['normal_impression'] = int(agg.get('impression', 0))
                result['normal_click'] = int(agg.get('click', 0))
            
            # 简单投（独立接口，非delivery_type参数）
            easy = self.get_easy_promotion_report(date, date, advertiser_id=aid)
            if easy['success']:
                agg = easy['data'].get('aggregation_data', {})
                result['easy_cost'] = float(agg.get('fee', 0))
                result['easy_impression'] = int(agg.get('impression', 0))
                result['easy_click'] = int(agg.get('click', 0))
        
        result['total_cost'] = result['normal_cost'] + result['easy_cost']
        result['total_impression'] = result['normal_impression'] + result['easy_impression']
        result['total_click'] = result['normal_click'] + result['easy_click']
        
        return result
    
    def get_daily_cost_range(self, start_date, end_date, advertiser_id=None):
        """获取日期范围内的每日消耗汇总
        返回按日期排序的每日消耗列表
        """
        aid = advertiser_id or self.advertiser_id
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        results = []
        current = start
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            daily = self.get_daily_cost(date_str, advertiser_id=aid)
            results.append(daily)
            current += timedelta(days=1)
        
        return results
    
    def get_yesterday_full_cost(self, advertiser_id=None):
        """获取昨日完整消耗（兼容旧接口，内部调用get_daily_cost）"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return self.get_daily_cost(yesterday, advertiser_id=advertiser_id)
    
    def get_yesterday_creative_report(self, advertiser_id=None):
        """获取昨日创意层级报表"""
        aid = advertiser_id or self.advertiser_id
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return self.get_offline_report("creative", yesterday, yesterday, advertiser_id=aid)


    # ==================== 工具类接口 ====================
    def get_history_list(self, start_time, end_time, advertiser_id=None, page=1, page_size=20):
        """历史操作记录 - POST /history/list
        start_time: 开始时间，格式：2026-05-28
        end_time: 结束时间，格式：2026-05-28
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/history/list", {
            "advertiser_id": aid, "start_time": start_time, "end_time": end_time,
            "page": page, "page_size": page_size
        })
    
    def keyword_recommend(self, keyword, request_type="search", advertiser_id=None):
        """定向推词-以词推词 - POST /keyword/common/recommend
        request_type: search/note/session/industry
        注意：参数名是keyword，不是word或keyword_search_list（2026-05-29验证）
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/keyword/common/recommend", {"advertiser_id": aid, "keyword": keyword, "request_type": request_type})
    
    def get_industry_taxonomy(self, advertiser_id=None):
        """行业类目 - POST /keyword/industry/taxonomy"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/keyword/industry/taxonomy", {"advertiser_id": aid})
    
    def get_industry_taxonomy_attribute(self, taxonomy_id, advertiser_id=None):
        """行业类目属性 - POST /keyword/industry/taxonomy/attribute"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/keyword/industry/taxonomy/attribute", {"advertiser_id": aid, "taxonomy_id": taxonomy_id})
    
    def get_word_bag_list(self, advertiser_id=None):
        """词包推荐 - POST /keyword/word/bag/list"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/keyword/word/bag/list", {"advertiser_id": aid})
    
    def estimate_crowd(self, placement=1, target_type=1, advertiser_id=None):
        """人群预估 - POST /crowd/estimate
        placement: 1,2,3,4,7
        target_type: 1=通投, 2=智能定向, 3=高级定向
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/crowd/estimate", {
            "advertiser_id": aid, "placement": placement, "target_type": target_type
        })
    
    def get_keyword_match(self, keywords, advertiser_id=None):
        """获取关键词匹配词库信息 - POST /target/keyword/match
        注意：参数名是keywords（列表），不是word（2026-05-29验证）
        """
        aid = advertiser_id or self.advertiser_id
        if isinstance(keywords, str):
            keywords = [keywords]
        return self._request("/target/keyword/match", {"advertiser_id": aid, "keywords": keywords})
    
    def get_keyword_recommend(self, word, advertiser_id=None):
        """获取推荐关键词信息 - POST /target/keyword/recommend"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/target/keyword/recommend", {"advertiser_id": aid, "word": word})
    
    def get_available_target_info(self, marketing_target=1, advertiser_id=None):
        """获取定向信息 - POST /target/get_available_target_info
        marketing_target: 营销目标
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/target/get_available_target_info", {
            "advertiser_id": aid, "marketing_target": marketing_target
        })
    
    def check_name_dup(self, name, check_type, advertiser_id=None):
        """计划单元名称重复性校验 - POST /data/check/name/dup
        name: 名称字符串或名称列表，单次上限100个
        check_type: 1=计划, 2=单元
        返回: {name: is_dup} 映射
        """
        aid = advertiser_id or self.advertiser_id
        if isinstance(name, str):
            name = [name]
        return self._request("/data/check/name/dup", {"advertiser_id": aid, "name": name, "type": check_type})

    # ============================================================
    # v3.6.0 新增API - 报表扩展
    # ============================================================

    def get_easy_promotion_group_report(self, start_date, end_date, time_unit="SUMMARY",
                                        advertiser_id=None, page=1, page_size=50):
        """简单投标的离线报表 - POST /data/report/offline/easy/promotion/group"""
        aid = advertiser_id or self.advertiser_id
        data = {
            "advertiser_id": aid,
            "start_date": start_date,
            "end_date": end_date,
            "time_unit": time_unit,
            "page": page,
            "page_size": page_size
        }
        return self._request("/data/report/offline/easy/promotion/group", data)

    def get_easy_promotion_note_report(self, start_date, end_date, time_unit="SUMMARY",
                                       advertiser_id=None, page=1, page_size=50):
        """简单投笔记离线报表 - POST /data/report/offline/easy/promotion/note"""
        aid = advertiser_id or self.advertiser_id
        data = {
            "advertiser_id": aid,
            "start_date": start_date,
            "end_date": end_date,
            "time_unit": time_unit,
            "page": page,
            "page_size": page_size
        }
        return self._request("/data/report/offline/easy/promotion/note", data)

    def get_spu_report(self, start_date, end_date, time_unit="SUMMARY",
                       advertiser_id=None, page=1, page_size=50):
        """SPU层级离线报表 - POST /data/report/offline/spu"""
        aid = advertiser_id or self.advertiser_id
        data = {
            "advertiser_id": aid,
            "start_date": start_date,
            "end_date": end_date,
            "time_unit": time_unit,
            "page": page,
            "page_size": page_size
        }
        return self._request("/data/report/offline/spu", data)

    def get_note_report(self, start_date, end_date, time_unit="SUMMARY",
                        advertiser_id=None, page=1, page_size=50):
        """笔记层级离线报表 - POST /data/report/offline/note"""
        aid = advertiser_id or self.advertiser_id
        data = {
            "advertiser_id": aid,
            "start_date": start_date,
            "end_date": end_date,
            "time_unit": time_unit,
            "page": page,
            "page_size": page_size
        }
        return self._request("/data/report/offline/note", data)

    def get_search_word_report(self, start_date, end_date, time_unit="SUMMARY",
                               advertiser_id=None, page=1, page_size=50):
        """搜索词层级离线报表 - POST /data/report/offline/search/word"""
        aid = advertiser_id or self.advertiser_id
        data = {
            "advertiser_id": aid,
            "start_date": start_date,
            "end_date": end_date,
            "time_unit": time_unit,
            "page": page,
            "page_size": page_size
        }
        return self._request("/data/report/offline/search/word", data)

    def get_account_report(self, start_date, end_date, time_unit="SUMMARY",
                           advertiser_id=None, page=1, page_size=50):
        """账户层级离线报表 - POST /data/report/offline/account"""
        aid = advertiser_id or self.advertiser_id
        data = {
            "advertiser_id": aid,
            "start_date": start_date,
            "end_date": end_date,
            "time_unit": time_unit,
            "page": page,
            "page_size": page_size
        }
        return self._request("/data/report/offline/account", data)

    def get_realtime_account_report(self, start_date, end_date, advertiser_id=None):
        """账户层级实时报表 - POST /data/report/realtime/account"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/realtime/account", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date
        })

    def get_realtime_creativity_report(self, start_date, end_date, advertiser_id=None):
        """创意层级实时报表 - POST /data/report/realtime/creativity"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/realtime/creativity", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date
        })

    def get_realtime_target_report(self, start_date, end_date, advertiser_id=None):
        """定向层级实时报表 - POST /data/report/realtime/target"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/realtime/target", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date
        })

    def get_realtime_campaign_group_report(self, start_date, end_date, columns=None, advertiser_id=None):
        """广告组层级实时报表 - POST /data/report/realtime/campaign/group
        columns: 需要返回的字段列表，如 ["fee", "show_cnt", "click_cnt"]
        """
        aid = advertiser_id or self.advertiser_id
        data = {"advertiser_id": aid, "start_date": start_date, "end_date": end_date}
        if columns:
            data["columns"] = columns
        return self._request("/data/report/realtime/campaign/group", data)

    def get_realtime_ube_keyword_report(self, start_date, end_date, campaign_group_id_list, advertiser_id=None):
        """简单投关键词实时数据 - POST /data/report/realtime/ube/keyword
        campaign_group_id_list: 简单投广告组ID列表
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/realtime/ube/keyword", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date,
            "campaign_group_id_list": campaign_group_id_list
        })

    def get_realtime_ube_note_report(self, start_date, end_date, campaign_group_id_list, advertiser_id=None):
        """简单投笔记实时数据 - POST /data/report/realtime/ube/note
        campaign_group_id_list: 简单投广告组ID列表
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/realtime/ube/note", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date,
            "campaign_group_id_list": campaign_group_id_list
        })

    def get_realtime_ube_campaign_report(self, start_date, end_date, campaign_group_id_list, advertiser_id=None):
        """简单投计划实时数据 - POST /data/report/realtime/ube/campaign
        campaign_group_id_list: 简单投广告组ID列表
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/realtime/ube/campaign", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date,
            "campaign_group_id_list": campaign_group_id_list
        })

    def get_realtime_ube_group_report(self, start_date, end_date, campaign_group_id_list, advertiser_id=None):
        """简单投标的实时数据 - POST /data/report/realtime/ube/group
        campaign_group_id_list: 简单投广告组ID列表
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/realtime/ube/group", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date,
            "campaign_group_id_list": campaign_group_id_list
        })

    def get_realtime_aigc_report(self, start_date, end_date, filters, advertiser_id=None):
        """AI智能笔记详情 - POST /data/report/realtime/unit/aigc
        filters: 过滤条件列表，如 [{"field": "unit_id", "value": "xxx"}]
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/report/realtime/unit/aigc", {
            "advertiser_id": aid, "start_date": start_date, "end_date": end_date,
            "filters": filters
        })

    # ============================================================
    # v3.6.0 新增API - 定向包管理
    # ============================================================

    def get_target_template_list(self, page=1, page_size=20, advertiser_id=None):
        """获取定向包列表 - POST /target/template/query"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/target/template/query", {
            "advertiser_id": aid, "page": page, "page_size": page_size
        })

    def create_target_template(self, name, target_config, advertiser_id=None):
        """创建定向包 - POST /target/template/create
        target_config: 定向配置对象，包含人群、地域、兴趣等
        """
        aid = advertiser_id or self.advertiser_id
        data = {"advertiser_id": aid, "name": name}
        data.update(target_config)
        return self._request("/target/template/create", data)

    def update_target_template(self, template_id, name=None, target_config=None, advertiser_id=None):
        """更新定向包 - POST /target/template/update"""
        aid = advertiser_id or self.advertiser_id
        data = {"advertiser_id": aid, "template_id": template_id}
        if name:
            data["name"] = name
        if target_config:
            data.update(target_config)
        return self._request("/target/template/update", data)

    def delete_target_template(self, template_id, advertiser_id=None):
        """删除定向包 - POST /target/template/delete"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/target/template/delete", {
            "advertiser_id": aid, "template_id": template_id
        })

    def apply_target_template(self, template_id, unit_ids, advertiser_id=None):
        """定向包关联单元 - POST /target/template/apply"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/target/template/apply", {
            "advertiser_id": aid, "template_id": template_id, "unit_ids": unit_ids
        })

    # ============================================================
    # v3.6.0 新增API - 否定词管理
    # ============================================================

    def get_negative_keyword_list(self, unit_id, advertiser_id=None):
        """查询否定词列表 - POST /negative/keyword/list"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/negative/keyword/list", {
            "advertiser_id": aid, "unit_id": unit_id
        })

    def batch_add_negative_keywords(self, unit_id, keywords, advertiser_id=None):
        """批量添加否定词 - POST /negative/keyword/batch/add
        keywords: [{"keyword": "xxx", "match_type": 1}] 或 ["xxx"]（自动转为对象数组）
        """
        aid = advertiser_id or self.advertiser_id
        # 如果是简单字符串数组，转为对象数组
        if keywords and isinstance(keywords[0], str):
            keywords = [{"keyword": k, "match_type": 1} for k in keywords]
        return self._request("/negative/keyword/batch/add", {
            "advertiser_id": aid, "unit_id": unit_id, "keywords": keywords
        })

    def batch_delete_negative_keywords(self, unit_id, negative_keyword_ids, advertiser_id=None):
        """批量删除否定词 - POST /negative/keyword/batch/delete
        negative_keyword_ids: 否定词ID列表，如 [203203940]
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/negative/keyword/batch/delete", {
            "advertiser_id": aid, "unit_id": unit_id, "negative_keyword_ids": negative_keyword_ids
        })

    # ============================================================
    # v3.6.0 新增API - 直达链接管理
    # ============================================================

    def get_direct_link_list(self, page=1, page_size=20, advertiser_id=None):
        """获取直达链接列表 - POST /direct_link/list"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/direct_link/list", {
            "advertiser_id": aid, "page": page, "page_size": page_size
        })

    def create_direct_link(self, name, url, advertiser_id=None):
        """创建直达链接 - POST /direct_link/create"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/direct_link/create", {
            "advertiser_id": aid, "name": name, "url": url
        })

    def update_direct_link(self, link_id, name=None, url=None, advertiser_id=None):
        """编辑直达链接 - POST /direct_link/update"""
        aid = advertiser_id or self.advertiser_id
        data = {"advertiser_id": aid, "link_id": link_id}
        if name:
            data["name"] = name
        if url:
            data["url"] = url
        return self._request("/direct_link/update", data)

    def delete_direct_link(self, link_id, advertiser_id=None):
        """删除直达链接 - POST /direct_link/delete"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/direct_link/delete", {
            "advertiser_id": aid, "link_id": link_id
        })

    # ============================================================
    # v3.6.0 新增API - 笔记管理
    # ============================================================

    def get_note_id(self, note_url, advertiser_id=None):
        """获取笔记ID - POST /noteid/query"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/noteid/query", {
            "advertiser_id": aid, "note_url": note_url
        })

    def delete_note(self, note_id, advertiser_id=None):
        """删除笔记 - POST /note/delete"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/note/delete", {
            "advertiser_id": aid, "note_id": note_id
        })

    # ============================================================
    # v3.6.0 新增API - 剧集管理
    # ============================================================

    def get_episodes_list(self, page=1, page_size=20, advertiser_id=None):
        """可投剧集列表 - POST /data/episodes/list"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/episodes/list", {
            "advertiser_id": aid, "page": page, "page_size": page_size
        })

    def create_episode(self, name, cover_url, advertiser_id=None):
        """剧集创建 - POST /data/episodes/create"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/episodes/create", {
            "advertiser_id": aid, "name": name, "cover_url": cover_url
        })

    def update_episode(self, episode_id, name=None, cover_url=None, advertiser_id=None):
        """剧集修改 - POST /data/episodes/update"""
        aid = advertiser_id or self.advertiser_id
        data = {"advertiser_id": aid, "episode_id": episode_id}
        if name:
            data["name"] = name
        if cover_url:
            data["cover_url"] = cover_url
        return self._request("/data/episodes/update", data)

    # ============================================================
    # v3.6.0 新增API - 数据查询
    # ============================================================

    def query_ube_ids(self, uids, advertiser_id=None):
        """批量查询简单投标的ID - POST /ube/extra/query"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/ube/extra/query", {
            "advertiser_id": aid, "uids": uids
        })

    def search_product(self, keyword, page=1, page_size=20, advertiser_id=None):
        """获取行业商品列表 - POST /data/product/search"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/product/search", {
            "advertiser_id": aid, "keyword": keyword, "page": page, "page_size": page_size
        })

    def get_app_info(self, platform=1, page=1, page_size=20, advertiser_id=None):
        """获取移动应用列表 - POST /data/app/info
        platform: 平台类型
        """
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/app/info", {
            "advertiser_id": aid, "platform": platform, "page": page, "page_size": page_size
        })

    def get_wechat_mini_program_list(self, page=1, page_size=20, advertiser_id=None):
        """获取微信小程序/小游戏列表 - POST /app/industry_item/list"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/app/industry_item/list", {
            "advertiser_id": aid, "page": page, "page_size": page_size
        })

    def get_xhs_mini_program_list(self, page=1, page_size=20, advertiser_id=None):
        """获取红书小程序列表 - POST /query/mini_program"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/query/mini_program", {
            "advertiser_id": aid, "page": page, "page_size": page_size
        })

    # ============================================================
    # v3.6.0 新增API - 工具类
    # ============================================================

    def get_event_asset_info(self, advertiser_id=None):
        """资产事件获取 - POST /data/event/asset/info"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/event/asset/info", {"advertiser_id": aid})

    def get_qual_info(self, advertiser_id=None):
        """获取资质列表 - POST /data/qual/info"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/qual/info", {"advertiser_id": aid})

    def get_poi_list(self, page=1, page_size=20, advertiser_id=None):
        """门店信息列表 - POST /data/poi/list"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/data/poi/list", {
            "advertiser_id": aid, "page": page, "page_size": page_size
        })

    def get_landing_page_list(self, page=1, page_size=20, advertiser_id=None):
        """落地页表单查询 - POST /landing_page/list_landing_page"""
        aid = advertiser_id or self.advertiser_id
        return self._request("/landing_page/list_landing_page", {
            "advertiser_id": aid, "page": page, "page_size": page_size
        })

    def get_material_prefer_info(self, note_id, creativity_id=None, advertiser_id=None):
        """创意标题和图片信息 - POST /material/prefer/info
        ⚠️ 1qps限制，只在真正创编时调用
        note_id: 笔记ID（必传）
        creativity_id: 创意ID（编辑场景必传）
        返回: title_info_list(标题列表) + photo_info_list(封面列表)
        """
        aid = advertiser_id or self.advertiser_id
        material = {"note_id": str(note_id)}
        if creativity_id:
            material["creativity_id"] = int(creativity_id)
        return self._request("/material/prefer/info", {
            "advertiser_id": aid, "material_info_dtos": [material]
        })


if __name__ == "__main__":
    sdk = XiaohongshuJuguangSDK()
    print("SDK v3.8.1 初始化完成")
    print(f"access_token: {'存在' if sdk.access_token else '不存在'}")
    print(f"advertiser_id: {sdk.advertiser_id or '未绑定'}")
    if sdk.expires_at:
        print(f"token过期时间: {datetime.fromtimestamp(sdk.expires_at)}")
