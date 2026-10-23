
"""HandaaS 品牌汽车区域销量情况 MCP 服务。"""

import json
import os
import sys
from hashlib import md5
from typing import Any, Literal
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


load_dotenv()

mcp = FastMCP(
    "品牌汽车区域销量情况",
    instructions='先检索汽车品牌取得 manufacturerId，再查询品牌详情、区域销量与门店布局、在售车型、车型销量、车款和经销商。',
    dependencies=["python-dotenv", "requests"],
)

GATEWAY_BASE_URL = "https://console.handaas.com/api/v1/integrator/call_api"
DEFAULT_TIMEOUT_SECONDS = 30.0

PRODUCT_IDS = {'brand_search': '6a7b19688c8d379dd486bcca', 'brand_detail': '6a7b1f3fdfa4a2f37b1914a8', 'market_analysis': '6a7bd578dfa4a2f37b191623', 'on_sale_models': '6a7bd6498c8d379dd486bfc7', 'model_sales': '6a7bda718c8d379dd486c01a', 'car_trims': '6a7be332dfa4a2f37b19173c', 'dealers': '6a7c26548c8d379dd486c364'}

READ_ONLY_TOOL = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)


def _request_timeout() -> float:
    raw = os.environ.get("HANDAAS_REQUEST_TIMEOUT", "")
    try:
        value = float(raw) if raw else DEFAULT_TIMEOUT_SECONDS
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    return value if value > 0 else DEFAULT_TIMEOUT_SECONDS


def _credential(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("your_"):
        return None
    return value


def _compact_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def _build_signature(call_params: dict[str, str], secret_key: str) -> str:
    plain = "".join(str(call_params[key]) for key in sorted(call_params))
    return md5(f"{plain}{secret_key}".encode("utf-8")).hexdigest()


def call_api(product_id: str, params: dict[str, Any]) -> Any:
    """调用 HandaaS Integrator Gateway并返回业务 data。"""
    integrator_id = _credential("INTEGRATOR_ID")
    secret_id = _credential("SECRET_ID")
    secret_key = _credential("SECRET_KEY")
    if not integrator_id:
        return {"error": "INTEGRATOR_ID 未配置"}
    if not secret_id:
        return {"error": "SECRET_ID 未配置"}
    if not secret_key:
        return {"error": "SECRET_KEY 未配置"}
    if not product_id:
        return {"error": "Product ID 不能为空"}

    call_params = {
        "product_id": product_id,
        "secret_id": secret_id,
        "params": json.dumps(
            _compact_params(params), ensure_ascii=False, separators=(",", ":")
        ),
    }
    call_params["signature"] = _build_signature(call_params, secret_key)
    url = f"{GATEWAY_BASE_URL}/{quote(integrator_id, safe='')}"
    try:
        response = requests.post(url, data=call_params, timeout=_request_timeout())
    except requests.RequestException:
        return {"error": "HandaaS 网关请求失败，请稍后重试"}
    if response.status_code != 200:
        return {
            "error": "HandaaS 网关返回非成功状态",
            "statusCode": response.status_code,
        }
    try:
        payload = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        return {"error": "HandaaS 网关返回了无法解析的响应"}
    if not isinstance(payload, dict):
        return {"error": "HandaaS 网关返回格式异常"}
    if "data" in payload:
        return payload["data"]
    error = payload.get("msgCN") or payload.get("message") or "HandaaS 网关未返回 data"
    if str(payload.get("code")) == "10001" or error == "查询数据为空":
        return {"total": 0, "resultList": []}
    result = {"error": error}
    if payload.get("code") is not None:
        result["code"] = payload["code"]
    return result


def _unwrap_backend_data(result: Any) -> Any:
    """兼容 Product API直接返回业务 data或保留内部 stat/data 外层。"""
    if not isinstance(result, dict) or "error" in result:
        return result
    if "stat" not in result:
        return result
    if result.get("stat") != 1:
        return {
            "error": result.get("msg") or "上游数据接口返回失败",
            "code": result.get("err"),
        }
    return result.get("data")


def _pagination_error(page_index: int, page_size: int, maximum: int = 10) -> dict[str, Any] | None:
    if page_index < 1:
        return {"error": "pageIndex 必须大于等于 1", "parameter": "pageIndex"}
    if page_size < 1 or page_size > maximum:
        return {"error": f"pageSize 必须在 1 到 {maximum} 之间", "parameter": "pageSize"}
    return None


def _normalize_paged(result: Any) -> Any:
    result = _unwrap_backend_data(result)
    if not isinstance(result, dict) or "error" in result:
        return result
    if isinstance(result.get("resultList"), list):
        records = result["resultList"]
        total = result.get("total", len(records))
        return {"total": total, "resultList": records}
    if isinstance(result.get("dataList"), list):
        records = result["dataList"]
        total = result.get("dataTotal", result.get("dataCount", len(records)))
        return {"total": total, "resultList": records}
    return result


def _normalize_single(result: Any) -> Any:
    result = _unwrap_backend_data(result)
    if not isinstance(result, dict) or "error" in result:
        return result
    if set(result) == {"total", "resultList"} and isinstance(result.get("resultList"), list):
        return result
    if not result:
        return {"total": 0, "resultList": []}
    return {"total": 1, "resultList": [result]}


def _number_range_error(
    minimum: int | float | None,
    maximum: int | float | None,
    minimum_name: str,
    maximum_name: str,
) -> dict[str, Any] | None:
    if minimum is not None and maximum is not None and minimum > maximum:
        return {
            "error": f"{minimum_name} 不能大于 {maximum_name}",
            "parameter": minimum_name,
        }
    return None


def _date_range_error(
    start: str | None,
    end: str | None,
    start_name: str,
    end_name: str,
) -> dict[str, Any] | None:
    if start and end and start > end:
        return {
            "error": f"{start_name} 不能晚于 {end_name}",
            "parameter": start_name,
        }
    return None

@mcp.tool(
    title="汽车品牌检索",
    description=(
        "用于发现汽车品牌并取得后续查询所需的 manufacturerId。可按品牌关键词、厂商总公司、"
        "所属国、年销量区间（单位：万辆）和新款上市日期筛选。pageIndex 从 1 开始，"
        "pageSize 最大 10；返回 total 与 resultList。"
    ),
    annotations=READ_ONLY_TOOL,
)
def vehicle_brand_search(
    keyword: str | None = None,
    manufacturerCompany: str | None = None,
    brandCountry: str | None = None,
    annualSalesVolumeMin: int | None = None,
    annualSalesVolumeMax: int | None = None,
    newModelLaunchTimeMin: str | None = None,
    newModelLaunchTimeMax: str | None = None,
    pageIndex: int = 1,
    pageSize: int = 10,
) -> dict[str, Any]:
    """按品牌、总公司、国别、销量和上市时间分页检索汽车品牌。"""
    if error := _pagination_error(pageIndex, pageSize, maximum=10): return error
    if error := _number_range_error(annualSalesVolumeMin, annualSalesVolumeMax, "annualSalesVolumeMin", "annualSalesVolumeMax"): return error
    if error := _date_range_error(newModelLaunchTimeMin, newModelLaunchTimeMax, "newModelLaunchTimeMin", "newModelLaunchTimeMax"): return error
    return _normalize_paged(call_api(PRODUCT_IDS["brand_search"], locals()))


@mcp.tool(
    title="汽车品牌详情查询",
    description=(
        "按 manufacturerId 查询品牌厂商、所属公司、价格区间、热销车型、历史销量、"
        "在售规模和门店概况。manufacturerId 必须来自 vehicle_brand_search；返回 total 与 resultList。"
    ),
    annotations=READ_ONLY_TOOL,
)
def vehicle_brand_detail(manufacturerId: str) -> dict[str, Any]:
    """按品牌厂商 ID查询品牌、制造商、历史销量和在售规模。"""
    return _normalize_single(call_api(PRODUCT_IDS["brand_detail"], {"manufacturerId": manufacturerId}))


@mcp.tool(
    title="品牌汽车区域销量与门店分布",
    description=(
        "分析品牌汽车在各区域的门店数量、月销量、销量占比、商圈数量和周边客流。"
        "不传 province 时按省份汇总，传省份短名（如广东）时按该省城市汇总；manufacturerId 来自品牌检索。"
    ),
    annotations=READ_ONLY_TOOL,
)
def vehicle_brand_market_analysis(manufacturerId: str, province: str | None = None) -> dict[str, Any]:
    """按品牌厂商 ID返回全国或指定省份的门店经营布局。"""
    return _normalize_single(call_api(PRODUCT_IDS["market_analysis"], {"manufacturerId": manufacturerId, "province": province}))


@mcp.tool(
    title="品牌在售车型查询",
    description=(
        "按 manufacturerId 分页查询在售车型名称、车型级别、价格区间和车款数量，"
        "并取得 carModelId 供车型销量查询。pageSize 最大 10；返回 total 与 resultList。"
    ),
    annotations=READ_ONLY_TOOL,
)
def vehicle_on_sale_model_list(manufacturerId: str, pageIndex: int = 1, pageSize: int = 10) -> dict[str, Any]:
    """按品牌厂商 ID分页返回在售车型、级别、价格和车款数量。"""
    if error := _pagination_error(pageIndex, pageSize, maximum=10): return error
    return _normalize_paged(call_api(PRODUCT_IDS["on_sale_models"], locals()))


@mcp.tool(
    title="品牌内车型近十二月销量",
    description=(
        "查询某车型最近 12 个月的销量和品牌内排名。manufacturerId 来自品牌检索，"
        "carModelId 来自在售车型结果；不传 carModelId 时自动查询该品牌销量最高的车型。"
    ),
    annotations=READ_ONLY_TOOL,
)
def vehicle_model_sales_ranking(manufacturerId: str, carModelId: str | None = None) -> dict[str, Any]:
    """返回指定车型或品牌热销车型最近12个月销量与品牌内排名。"""
    return _normalize_single(call_api(PRODUCT_IDS["model_sales"], {"manufacturerId": manufacturerId, "carId": carModelId}))


@mcp.tool(
    title="品牌车款明细查询",
    description=(
        "按 manufacturerId、上市日期、能源类型、车型类别和指导价区间分页查询具体车款、"
        "配置与上月销量。carType 和 secondCarType 互斥，价格单位为元，pageSize 最大 10。"
    ),
    annotations=READ_ONLY_TOOL,
)
def vehicle_car_trim_list(
    manufacturerId: str,
    launchTimeMin: str | None = None,
    launchTimeMax: str | None = None,
    powerEnergyType: str | None = None,
    carType: str | None = None,
    secondCarType: str | None = None,
    carPriceMin: float | None = None,
    carPriceMax: float | None = None,
    pageIndex: int = 1,
    pageSize: int = 10,
) -> dict[str, Any]:
    """按品牌、上市时间、能源、车型和价格区间分页查询车款。"""
    if error := _pagination_error(pageIndex, pageSize, maximum=10): return error
    if carType and secondCarType: return {"error": "carType 与 secondCarType 不能同时提供", "parameter": "carType"}
    if error := _date_range_error(launchTimeMin, launchTimeMax, "launchTimeMin", "launchTimeMax"): return error
    if error := _number_range_error(carPriceMin, carPriceMax, "carPriceMin", "carPriceMax"): return error
    return _normalize_paged(call_api(PRODUCT_IDS["car_trims"], locals()))


@mcp.tool(
    title="汽车品牌区域经销商查询",
    description=(
        "按 manufacturerId 查询指定省、市、区县的品牌经销商，可筛选经销类型、年营业额和商圈类型。"
        "返回门店主体、地址、商圈和客流等信息，支持分页并返回 total 与 resultList。"
    ),
    annotations=READ_ONLY_TOOL,
)
def vehicle_dealer_list(
    manufacturerId: str,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    dealerType: str | None = None,
    annualTurnoverRange: str | None = None,
    businessDistrictType: str | None = None,
    pageIndex: int = 1,
    pageSize: int = 10,
) -> dict[str, Any]:
    """按品牌、经销商类型、营业额、商圈和地区分页查询经销商。"""
    if error := _pagination_error(pageIndex, pageSize, maximum=10): return error
    params = locals(); params["annual_turnover_range"] = params.pop("annualTurnoverRange")
    return _normalize_paged(call_api(PRODUCT_IDS["dealers"], params))


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    transport = arguments[0] if arguments else "stdio"
    if transport not in {"stdio", "sse", "streamable-http"}:
        print("启动方式必须是 stdio、sse 或 streamable-http", file=sys.stderr)
        return 2
    mcp.run(transport=transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
