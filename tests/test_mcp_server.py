"""In-process MCP tests: real MCP protocol over memory streams, mocked TAQA HTTP API."""

import json

import httpx
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

import taqa_mcp_server
from conftest import SAMPLE_RESPONSE

TOOL_NAME = "get_water_electricity_bill_list"

pytestmark = pytest.mark.anyio


@pytest.fixture
def fake_api(monkeypatch):
    """Route the server's httpx calls to an in-memory handler and record requests."""
    state = {"requests": [], "status": 200, "body": SAMPLE_RESPONSE}

    def handler(request: httpx.Request) -> httpx.Response:
        state["requests"].append(request)
        return httpx.Response(state["status"], json=state["body"])

    real_client = httpx.AsyncClient

    def client_factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(taqa_mcp_server.httpx, "AsyncClient", client_factory)
    return state


async def _call(arguments: dict):
    async with create_connected_server_and_client_session(
        taqa_mcp_server.mcp._mcp_server
    ) as client:
        return await client.call_tool(TOOL_NAME, arguments)


async def test_server_lists_bill_tool():
    async with create_connected_server_and_client_session(
        taqa_mcp_server.mcp._mcp_server
    ) as client:
        tools = (await client.list_tools()).tools

    tool = next((t for t in tools if t.name == TOOL_NAME), None)
    assert tool is not None, f"{TOOL_NAME} not registered"
    props = tool.inputSchema["properties"]
    for field in (
        "trade_license_numbers",
        "account_id",
        "premise_id",
        "emirates_id_numbers",
        "identity_type",
        "show_all_accounts",
        "show_total_outstanding",
        "show_grand_total_outstanding",
    ):
        assert field in props


async def test_tool_returns_api_response(fake_api):
    result = await _call({"trade_license_numbers": ["CN-1094694"]})

    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["GrandTotalOutStanding"] == "974.83"
    assert data["TradeLicenseBalances"][0]["TradeLicenseNumber"] == "CN-1094694"
    assert len(data["WaterElectricityBillList"]) == 1


async def test_tool_sends_expected_request_payload(fake_api):
    await _call(
        {
            "trade_license_numbers": ["CN-1234567"],
            "account_id": "0519951948",
            "premise_id": "5704993656",
            "show_all_accounts": False,
        }
    )

    assert len(fake_api["requests"]) == 1
    request = fake_api["requests"][0]
    assert request.method == "POST"
    assert str(request.url) == taqa_mcp_server.API_URL

    body = json.loads(request.content)
    req = body["MyBusinessGetWaterElectricityBillListRequest"]
    assert req == {
        "AccountID": "0519951948",
        "EmiratesIDNumbers": [],
        "IdentityType": "TID",
        "PremiseID": "5704993656",
        "TradeLicenseNumbers": ["CN-1234567"],
        "ShowAllAccounts": "false",
        "ShowTotalOutStanding": "true",
        "ShowGrandTotalOutStanding": "true",
    }
    assert set(body["UserAuthentication"]) == {"Username", "Password"}


async def test_tool_uses_defaults_when_no_arguments(fake_api):
    await _call({})

    req = json.loads(fake_api["requests"][0].content)[
        "MyBusinessGetWaterElectricityBillListRequest"
    ]
    assert req["TradeLicenseNumbers"] == ["CN-1094694"]
    assert req["IdentityType"] == "TID"
    assert req["ShowAllAccounts"] == "true"


async def test_tool_reports_error_on_http_failure(fake_api):
    fake_api["status"] = 500
    fake_api["body"] = {"error": "boom"}

    result = await _call({"trade_license_numbers": ["CN-1094694"]})

    assert result.isError
    assert "500" in result.content[0].text
