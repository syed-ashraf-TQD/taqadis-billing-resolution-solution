"""Live smoke test against the real TAQA API. Opt-in: set TAQA_LIVE_TESTS=1."""

import json
import os
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.skipif(
        os.getenv("TAQA_LIVE_TESTS") != "1",
        reason="Live TAQA API test disabled; set TAQA_LIVE_TESTS=1 to enable",
    ),
]


async def test_live_bill_list_for_trade_license(project_root):
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(project_root / "taqa_mcp_server.py")],
        cwd=str(project_root),
    )
    trade_license = os.getenv("TAQA_TEST_TRADE_LICENSE", "CN-1094694")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_water_electricity_bill_list",
                {"trade_license_numbers": [trade_license]},
            )

    assert not result.isError, result.content[0].text
    data = json.loads(result.content[0].text)
    assert "WaterElectricityBillList" in data
    assert "GrandTotalOutStanding" in data
    assert any(
        b["TradeLicenseNumber"] == trade_license for b in data["TradeLicenseBalances"]
    )
