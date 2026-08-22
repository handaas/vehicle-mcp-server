# 车辆：品牌汽车区域销量情况

[该MCP服务提供汽车品牌搜索、品牌详情、区域门店与销量、在售车型、车型销量、车款配置和经销商查询功能。](https://www.handaas.com/)


## 主要功能

- 🚘 汽车品牌及厂商搜索
- 📊 品牌区域门店和月销量分析
- 🚗 品牌在售车型查询
- 📈 车型最近12个月销量与排名
- 🧾 车款配置和上月销量查询
- 🏪 品牌区域经销商查询

## 环境要求

- Python 3.10+
- 依赖包：python-dotenv, requests, mcp

## 本地快速启动

### 1. 克隆项目
```bash
git clone https://github.com/handaas/vehicle-mcp-server
cd vehicle-mcp-server
```

### 2. 创建虚拟环境&安装依赖

```bash
python -m venv mcp_env && source mcp_env/bin/activate
pip install -r requirements.txt
```

### 3. 环境配置

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下环境变量：

```env
INTEGRATOR_ID=your_integrator_id
SECRET_ID=your_secret_id
SECRET_KEY=your_secret_key
HANDAAS_REQUEST_TIMEOUT=30
```

### 4. streamable-http启动服务

```bash
python server/mcp_server.py streamable-http
```

服务将在 `http://localhost:8000` 启动，MCP 地址为 `http://127.0.0.1:8000/mcp`。

#### 支持启动方式 stdio 或 sse 或 streamable-http

### 5. Cursor / Cherry Studio MCP配置

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

## STDIO版安装部署

### 设置Cursor / Cherry Studio MCP配置

```json
{
  "mcpServers": {
    "vehicle-mcp-server": {
      "command": "uv",
      "args": ["run", "mcp", "run", "{workdir}/server/mcp_server.py"],
      "env": {
        "PATH": "{workdir}/mcp_env/bin:$PATH",
        "PYTHONPATH": "{workdir}/mcp_env",
        "INTEGRATOR_ID": "your_integrator_id",
        "SECRET_ID": "your_secret_id",
        "SECRET_KEY": "your_secret_key"
      }
    }
  }
}
```

## 使用官方Remote服务

当前服务暂未开放官方 Remote 地址。请使用本地 `stdio`、`sse` 或 `streamable-http` 方式运行；官方 Remote 地址开放后将在本节补充配置。

### 注意：integrator_id、secret_id、secret_key及Remote token需要登录 https://www.handaas.com/ 进行注册开通平台获取


## 可用工具

### 1. vehicle_brand_search
**功能**: 汽车品牌搜索

**参数**:
按品牌名称、厂商总公司、所属国、年销量和新款上市时间搜索汽车品牌。

- `keyword` (可选): 品牌名称关键词
- `manufacturerCompany` (可选): 品牌厂商总公司
- `brandCountry` (可选): 品牌所属国
- `annualSalesVolumeMin` / `annualSalesVolumeMax` (可选): 年销量区间，单位为万辆
- `newModelLaunchTimeMin` / `newModelLaunchTimeMax` (可选): 新款上市日期区间，格式YYYY-MM-DD
- `pageIndex` (可选): 页码，从1开始
- `pageSize` (可选): 每页条数，最大10

**返回值**:
- `total`: 品牌总数
- `resultList`: 品牌结果列表
  - `manufacturerId`: 品牌厂商ID
  - `manufacturerName`: 品牌厂商名称
  - `manufacturerCompany`: 厂商总公司
  - `brandCountry`: 品牌所属国
  - `priceRange`: 价格区间
  - `hotSellingCarModelName`: 热销车型
  - `annualSalesVolume`: 年销量，单位为辆
  - `onSaleCarModelNum`: 在售车型数量
  - `onSaleCarTrimNum`: 在售车款数量

### 2. vehicle_brand_detail
**功能**: 汽车品牌详情查询

**参数**:
- `manufacturerId` (必需): 必须使用品牌搜索返回的品牌厂商ID

**返回值**:
- `total`: 命中数量
- `resultList`: 品牌详情列表
  - `manufacturerName`: 品牌厂商名称
  - `manufacturerCompany`: 厂商总公司
  - `manufacturerIntroduction`: 品牌厂商简介
  - `hotSellingCarModelList`: 热销车型列表
  - `nationalHistoricalSalesList`: 全国历史销量
  - `annualSalesVolume`: 年销量
  - `brandStoreNum`: 品牌门店数量
  - `brandMonthSales`: 品牌月销量
  - `all_car_model_dict`: 在售车型名称与ID映射

### 3. vehicle_brand_market_analysis
**功能**: 品牌汽车区域销量与门店分布查询

**参数**:
- `manufacturerId` (必需): 品牌厂商ID
- `province` (可选): 省份短名，例如广东；不传时按省份汇总，传入后按城市汇总

**返回值**:
- `total`: 命中数量
- `resultList`: 市场分析结果
  - `storeLayout`: 区域经营布局列表
    - `storeLocation`: 省份或城市
    - `storeNum`: 门店数量
    - `monthlySalesVolume`: 月销量
    - `percentage`: 销量占比
    - `businessDistrictNum`: 入驻商圈数量
    - `storeSurroundMonthlyTraffic`: 门店周边月均客流

### 4. vehicle_on_sale_model_list
**功能**: 品牌在售车型查询

**参数**:
- `manufacturerId` (必需): 品牌厂商ID
- `pageIndex` (可选): 页码，从1开始
- `pageSize` (可选): 每页条数，最大10

**返回值**:
- `total`: 在售车型总数
- `resultList`: 在售车型列表
  - `carModelId`: 车型ID
  - `carModelName`: 车型名称
  - `level`: 车型级别
  - `price`: 价格区间
  - `carTrimNum`: 车款数量

### 5. vehicle_model_sales_ranking
**功能**: 品牌内车型销量查询

**参数**:
- `manufacturerId` (必需): 品牌厂商ID
- `carModelId` (可选): 在售车型返回的车型ID；不传时查询品牌销量最高车型

**返回值**:
- `total`: 命中数量
- `resultList`: 车型销量详情
  - `carModelName`: 车型名称
  - `salesList`: 最近12个月销量
    - `month`: 月份
    - `rank`: 品牌内排名
    - `reg_value`: 销量，单位为辆

### 6. vehicle_car_trim_list
**功能**: 品牌车款明细查询

**参数**:
- `manufacturerId` (必需): 品牌厂商ID
- `launchTimeMin` / `launchTimeMax` (可选): 上市日期区间
- `powerEnergyType` (可选): 动力或能源类型
- `carType` / `secondCarType` (可选): 一级或二级车型分类，两者互斥
- `carPriceMin` / `carPriceMax` (可选): 价格区间，单位为元
- `pageIndex` (可选): 页码
- `pageSize` (可选): 每页条数，最大10

**返回值**:
- `total`: 车款总数
- `resultList`: 车款明细列表
  - `carModelId`: 车型ID
  - `carModelName`: 车型名称
  - `carTrimName`: 车款名称
  - `launchTime`: 上市时间
  - `powerEnergyType`: 动力或能源类型
  - `manufacturerGuidePrice`: 厂商指导价
  - `carSpecs`: 配置参数
  - `MonthSales`: 上月销量

### 7. vehicle_dealer_list
**功能**: 汽车品牌区域经销商查询

**参数**:
- `manufacturerId` (必需): 品牌厂商ID
- `province` / `city` / `district` (可选): 省市区筛选
- `dealerType` (可选): 经销类型
- `annualTurnoverRange` (可选): 年营业额区间
- `businessDistrictType` (可选): 商圈类型
- `pageIndex` (可选): 页码
- `pageSize` (可选): 每页条数，最大10

**返回值**:
- `total`: 经销商总数
- `resultList`: 经销商列表
  - `storeName`: 门店名称
  - `EnterpriseEntity`: 企业主体
  - `dealerType`: 经销类型
  - `Revenue`: 年营业额
  - `address`: 门店地址
  - `businessDistrict`: 所属商圈
  - `businessType`: 商圈类型
  - `monthFootTraffic`: 商圈客流量

## 使用注意事项

1. **品牌ID要求**: 后续查询必须先通过品牌搜索取得 `manufacturerId`。
2. **车型ID要求**: `carModelId` 来自在售车型查询结果。
3. **分页限制**: 车辆分页接口一页最多获取10条数据。
4. **互斥参数**: `carType` 与 `secondCarType` 不能同时提供。
5. **单位说明**: 品牌年销量筛选单位为万辆，车款价格筛选单位为元。

## 使用提问示例

### vehicle_brand_search (汽车品牌搜索)
1. 帮我搜索比亚迪汽车品牌
2. 查询年销量超过50万辆的汽车品牌
3. 搜索所属国为德国的汽车品牌

### vehicle_brand_detail (汽车品牌详情查询)
1. 查询比亚迪的品牌介绍和在售规模
2. 查看丰田的历史销量情况
3. 获取该品牌的热销车型列表

### vehicle_brand_market_analysis (品牌汽车区域销量与门店分布查询)
1. 分析比亚迪在广东各城市的门店和月销量
2. 查看丰田在全国各省的销售布局
3. 比较该品牌各区域的销量占比

### vehicle_on_sale_model_list (品牌在售车型查询)
1. 比亚迪目前有哪些在售车型
2. 查看丰田在售车型的价格区间
3. 获取该品牌在售车型和车型ID

### vehicle_model_sales_ranking (品牌内车型销量查询)
1. 查看这款车型最近12个月销量
2. 查询该车型在品牌内的销量排名
3. 不指定车型时查看品牌最畅销车型

### vehicle_car_trim_list (品牌车款明细查询)
1. 查询比亚迪在售车款和配置
2. 查看指导价20万到30万元的车款
3. 查询最近一年上市的车款及上月销量

### vehicle_dealer_list (汽车品牌区域经销商查询)
1. 查询比亚迪在深圳的经销商
2. 查看该品牌在广东的门店分布
3. 查询指定商圈类型内的品牌经销商

## 测试验证

```bash
python -m py_compile server/mcp_server.py
python -m unittest discover -s tests -v
```

当前服务包含 9 个离线单元测试。真实接口验证需在本地 `.env` 配置有效凭据后执行，测试输出不得提交真实业务响应或凭据。
