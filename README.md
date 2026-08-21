# 车辆：品牌汽车区域销量情况

[该 MCP 服务围绕品牌汽车区域销量情况，提供汽车品牌发现、品牌详情、区域经营布局、车型与车款销量以及经销商查询能力。](https://www.handaas.com/)

> 所属板块：市场贸易

## 主要功能

- 汽车品牌多条件检索
- 品牌与制造商详情
- 品牌区域门店经营布局
- 在售车型和车型销量分析
- 车款配置与经销商

## 服务设计说明

- 服务以品牌汽车在不同区域的销量和渠道布局分析为核心，品牌、车型、车款和经销商信息用于补充销量研判上下文。
- 服务提供 7 个只读 Tool，单次 Tool 调用只访问一个 Product ID。
- 翻页结果统一收口为 `total` 与 `resultList`。
- 成功响应自动兼容 Gateway业务 data和内部 `stat/data` 两种形态。
- 请求超时可通过 `HANDAAS_REQUEST_TIMEOUT` 配置，默认30秒。

## 环境要求

- Python 3.10+
- 依赖：`mcp`、`python-dotenv`、`requests`

## 本地快速启动

```bash
cd vehicle-mcp-server
python3 -m venv mcp_env
source mcp_env/bin/activate
pip install -r requirements.txt
cp .env.example .env
python server/mcp_server.py streamable-http
```

服务默认地址：`http://127.0.0.1:8000/mcp`。支持 `stdio`、`sse` 和 `streamable-http`。

## 环境变量

```env
INTEGRATOR_ID=your_integrator_id
SECRET_ID=your_secret_id
SECRET_KEY=your_secret_key
HANDAAS_REQUEST_TIMEOUT=30
```

真实凭据只能保存在本地 `.env` 或部署密钥中。

## Cursor / Cherry Studio配置

```json
{
  "mcpServers": {
    "vehicle-mcp-server": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## 可用 Tool 与 Product ID

| MCP Tool | 使用场景 | Product ID | 关键输入 |
| --- | --- | --- | --- |
| `vehicle_brand_search` | 发现汽车品牌并取得 `manufacturerId` | `6a7b19688c8d379dd486bcca` | 品牌、厂商、国别、销量、上市日期、分页 |
| `vehicle_brand_detail` | 查询品牌厂商和历史销量概况 | `6a7b1f3fdfa4a2f37b1914a8` | `manufacturerId` |
| `vehicle_brand_market_analysis` | 分析区域门店、月销量和商圈布局 | `6a7bd578dfa4a2f37b191623` | `manufacturerId`、`province` |
| `vehicle_on_sale_model_list` | 查询品牌在售车型并取得 `carModelId` | `6a7bd6498c8d379dd486bfc7` | `manufacturerId`、分页 |
| `vehicle_model_sales_ranking` | 查询车型最近 12 个月销量和品牌内排名 | `6a7bda718c8d379dd486c01a` | `manufacturerId`、`carModelId` |
| `vehicle_car_trim_list` | 查询具体车款、配置和上月销量 | `6a7be332dfa4a2f37b19173c` | 品牌、日期、能源、车型、价格、分页 |
| `vehicle_dealer_list` | 查询品牌区域经销商和商圈信息 | `6a7c26548c8d379dd486c364` | 品牌、地区、类型、营业额、商圈、分页 |

## 推荐调用流程

1. 先用 `vehicle_brand_search` 确认品牌并取得 `manufacturerId`。
2. 使用品牌 ID 查询品牌详情和区域销量布局。
3. 需要车型分析时，先查在售车型取得 `carModelId`，再查询最近 12 个月销量。
4. 使用品牌 ID 继续查询车款配置或指定区域经销商。

## Tool 详细说明

### 1. vehicle_brand_search

**何时使用**：用户只提供品牌名、厂商名、所属国或销量范围时，用于定位汽车品牌。

**关键参数**：`keyword` 为品牌模糊词；年销量筛选单位为万辆；上市日期格式为 `YYYY-MM-DD`；`pageSize` 最大 10。

**返回说明**：返回品牌、厂商、所属国、价格区间、年销量和在售规模，并提供 `manufacturerId`。

### 2. vehicle_brand_detail

**何时使用**：需要品牌介绍、热销车型、历史销量、在售规模或门店概况时使用。

**关键参数**：`manufacturerId` 必须来自品牌检索结果。

**返回说明**：详情以 `total=1` 和单条 `resultList` 返回。

### 3. vehicle_brand_market_analysis

**何时使用**：比较品牌在不同省份或某省不同城市的门店与销量布局时使用。

**关键参数**：必填 `manufacturerId`；不传 `province` 时按省份汇总，传入“广东”等省份短名时按城市汇总。

**返回说明**：返回 `storeLayout`，包括门店数量、月销量、占比、商圈数量和周边月均客流。

### 4. vehicle_on_sale_model_list

**何时使用**：查看品牌当前在售车型、价格和车款数量，或为销量查询取得车型 ID 时使用。

**关键参数**：`manufacturerId` 来自品牌检索；支持分页。

**返回说明**：返回车型名称、级别、价格和 `carModelId`。

### 5. vehicle_model_sales_ranking

**何时使用**：查看某车型最近 12 个月销量和品牌内排名时使用。

**关键参数**：`manufacturerId` 必填；`carModelId` 来自在售车型结果，不传时查询该品牌销量最高的车型。

**返回说明**：返回车型名称以及最近 12 个月的月份、销量和排名。

### 6. vehicle_car_trim_list

**何时使用**：需要查询具体车款、能源类型、指导价、配置或上月销量时使用。

**关键参数**：价格单位为元；`carType` 与 `secondCarType` 不能同时提供；日期格式为 `YYYY-MM-DD`；支持分页。

**返回说明**：返回车型、车款、上市时间、能源类型、指导价、配置和上月销量。

### 7. vehicle_dealer_list

**何时使用**：需要查找某品牌在指定区域的经销商、运营主体和商圈信息时使用。

**关键参数**：`manufacturerId` 必填；可按省、市、区县、经销类型、年营业额和商圈类型筛选。

**返回说明**：返回门店名称、企业主体、地址、商圈、客流和周边房价等信息。

## 使用示例

### 示例一：品牌区域销量

> 分析比亚迪在广东省各城市的门店数量、月销量和销量占比。

先调用 `vehicle_brand_search(keyword="比亚迪")` 取得 `manufacturerId`，再调用：

```json
{
  "tool": "vehicle_brand_market_analysis",
  "arguments": {
    "manufacturerId": "从品牌检索结果取得",
    "province": "广东"
  }
}
```

### 示例二：车型销量趋势

> 查看比亚迪某款在售车型最近 12 个月销量和品牌内排名。

先查询品牌，再调用 `vehicle_on_sale_model_list` 取得 `carModelId`，最后调用：

```json
{
  "tool": "vehicle_model_sales_ranking",
  "arguments": {
    "manufacturerId": "从品牌检索结果取得",
    "carModelId": "从在售车型结果取得"
  }
}
```

### 示例三：区域经销商

> 查找比亚迪在深圳的经销商和所在商圈。

```json
{
  "tool": "vehicle_dealer_list",
  "arguments": {
    "manufacturerId": "从品牌检索结果取得",
    "province": "广东省",
    "city": "深圳市",
    "pageIndex": 1,
    "pageSize": 10
  }
}
```

## 使用注意事项

1. `manufacturerId` 来自汽车品牌检索结果。
2. `carModelId` 来自在售车型结果，在 Product API wire 层映射为 `carId`。
3. 一级车型 `carType` 与二级车型 `secondCarType` 不能同时提供。
4. 年销量筛选单位为万辆，车款价格筛选单位为元，返回销量单位以字段说明为准。

## 测试验证

```bash
python -m py_compile server/mcp_server.py
python -m unittest discover -s tests -v
```

单元测试使用 Mock 响应；真实验证通过本地 `.env` 调用 HandaaS Integrator Gateway。
