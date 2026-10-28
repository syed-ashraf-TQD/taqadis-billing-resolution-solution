import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_path = Path(__file__).resolve().parent / "taqa_mcp_server.py"
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        cwd=str(server_path.parent),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            result = await session.call_tool(
                "get_water_electricity_bill_list",
                {
                    "trade_license_numbers": ["CN-1094694"],
                    "show_all_accounts": True,
                    "show_total_outstanding": True,
                    "show_grand_total_outstanding": True,
                },
            )

            payload = None
            if getattr(result, "content", None):
                first = result.content[0]
                if hasattr(first, "text"):
                    payload = json.loads(first.text)

            if payload is None:
                payload = result.model_dump()

            print("\nTAQA API response:")
            print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
