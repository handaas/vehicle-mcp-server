
import asyncio
import importlib.util
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

SERVER_PATH = Path(__file__).parents[1] / "server" / "mcp_server.py"
SPEC = importlib.util.spec_from_file_location("vehicle_mcp_server", SERVER_PATH)
assert SPEC and SPEC.loader
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class ContractTests(TestCase):
    def test_registered_tools_and_annotations(self) -> None:
        tools = asyncio.run(server.mcp.list_tools())
        self.assertEqual(server.mcp.name, '车辆：品牌汽车区域销量情况')
        self.assertEqual({tool.name for tool in tools}, {'vehicle_model_sales_ranking', 'vehicle_dealer_list', 'vehicle_car_trim_list', 'vehicle_brand_search', 'vehicle_brand_detail', 'vehicle_brand_market_analysis', 'vehicle_on_sale_model_list'})
        for tool in tools:
            self.assertEqual(tool.outputSchema.get("type"), "object")
            self.assertTrue(tool.annotations.readOnlyHint)
            self.assertFalse(tool.annotations.destructiveHint)
            self.assertTrue(tool.annotations.idempotentHint)
            self.assertGreaterEqual(len(tool.description or ""), 50)
            self.assertTrue(tool.annotations.openWorldHint)

    def test_missing_credentials_blocks_http(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch.object(server.requests, "post") as post:
            result = server.call_api("product", {})
        self.assertEqual(result, {"error": "INTEGRATOR_ID 未配置"})
        post.assert_not_called()

    def test_backend_envelope_and_pagination_are_normalized(self) -> None:
        wrapped = {"stat": 1, "data": {"dataList": [{"id": 1}], "dataTotal": 3}}
        self.assertEqual(server._normalize_paged(wrapped), {"total": 3, "resultList": [{"id": 1}]})
        self.assertEqual(server._normalize_single({"stat": 1, "data": {"id": 1}}), {"total": 1, "resultList": [{"id": 1}]})
        self.assertEqual(server._normalize_single({"stat": 1, "data": {}}), {"total": 0, "resultList": []})

    def test_invalid_pagination_is_actionable(self) -> None:
        error = server._pagination_error(0, 10)
        self.assertEqual(error["parameter"], "pageIndex")
        error = server._pagination_error(1, 51)
        self.assertEqual(error["parameter"], "pageSize")

    def test_empty_business_response_is_normalized(self) -> None:
        response = Mock(status_code=200)
        response.json.return_value = {"code": "10001", "msgCN": "查询数据为空"}
        credentials = {"INTEGRATOR_ID": "integrator", "SECRET_ID": "secret-id", "SECRET_KEY": "secret-key"}
        with patch.dict(os.environ, credentials, clear=True), patch.object(server.requests, "post", return_value=response):
            result = server.call_api("product", {})
        self.assertEqual(result, {"total": 0, "resultList": []})


class RoutingTests(TestCase):
    def test_all_product_routes(self) -> None:
        cases = [
            (lambda: server.vehicle_brand_search(keyword="汽车"), "brand_search"),
            (lambda: server.vehicle_brand_detail("brand-1"), "brand_detail"),
            (lambda: server.vehicle_brand_market_analysis("brand-1"), "market_analysis"),
            (lambda: server.vehicle_on_sale_model_list("brand-1"), "on_sale_models"),
            (lambda: server.vehicle_model_sales_ranking("brand-1"), "model_sales"),
            (lambda: server.vehicle_car_trim_list("brand-1"), "car_trims"),
            (lambda: server.vehicle_dealer_list("brand-1"), "dealers"),
        ]
        for invoke, route in cases:
            with self.subTest(route=route), patch.object(server, "call_api", return_value={"dataList": [], "dataTotal": 0}) as call:
                invoke()
            self.assertEqual(call.call_args.args[0], server.PRODUCT_IDS[route])

    def test_wire_parameter_mappings(self) -> None:
        with patch.object(server, "call_api", return_value={}) as call:
            server.vehicle_model_sales_ranking("brand-1", "model-1")
        self.assertEqual(call.call_args.args[1], {"manufacturerId": "brand-1", "carId": "model-1"})

        with patch.object(server, "call_api", return_value={"dataList": []}) as call:
            server.vehicle_dealer_list("brand-1", annualTurnoverRange="5000万-1亿")
        self.assertEqual(call.call_args.args[1]["annual_turnover_range"], "5000万-1亿")
        self.assertNotIn("annualTurnoverRange", call.call_args.args[1])

    def test_invalid_trim_filters_are_rejected(self) -> None:
        with patch.object(server, "call_api") as call:
            result = server.vehicle_car_trim_list("brand-1", carType="SUV", secondCarType="紧凑型SUV")
        self.assertEqual(result["parameter"], "carType")
        call.assert_not_called()

    def test_vehicle_page_size_is_limited_to_product_contract(self) -> None:
        with patch.object(server, "call_api") as call:
            result = server.vehicle_brand_search(pageSize=11)
        self.assertEqual(result["parameter"], "pageSize")
        call.assert_not_called()
