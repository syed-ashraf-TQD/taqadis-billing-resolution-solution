"""End-to-end tests: launch taqa_mcp_server.py as a real stdio MCP subprocess."""

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from conftest import SAMPLE_RESPONSE

TOOL_NAME = "get_water_electricity_bill_list"

pytestmark = pytest.mark.anyio


@pytest.fixture
def fake_taqa_url():
    """Local HTTP server that mimics the TAQA endpoint."""
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            received.append(json.loads(self.rfile.read(length)))
            body = json.dumps(SAMPLE_RESPONSE).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/gateway", received
    finally:
        server.shutdown()


def _server_params(project_root, api_url=None):
    env = dict(os.environ)
    if api_url:
        env["TAQA_API_URL"] = api_url
    return StdioServerParameters(
        command=sys.executable,
        args=[str(project_root / "taqa_mcp_server.py")],
        cwd=str(project_root),
        env=env,
    )


async def test_stdio_server_initializes_and_lists_tools(project_root):
    async with stdio_client(_server_params(project_root)) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            assert init.serverInfo.name == "taqa-bills"
            tools = await session.list_tools()

    assert TOOL_NAME in [t.name for t in tools.tools]


async def test_stdio_server_calls_api_end_to_end(project_root, fake_taqa_url):
    url, received = fake_taqa_url

    async with stdio_client(_server_params(project_root, url)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                TOOL_NAME, {"trade_license_numbers": ["CN-1094694"]}
            )

    assert not result.isError
    data = json.loads(result.content[0].text)
    assert data["GrandTotalOutStanding"] == SAMPLE_RESPONSE["GrandTotalOutStanding"]
    assert received[0]["MyBusinessGetWaterElectricityBillListRequest"][
        "TradeLicenseNumbers"
    ] == ["CN-1094694"]
