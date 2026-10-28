import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

API_URL = os.getenv(
    "TAQA_API_URL",
    "https://api.taqa.ae/gateway/ADDC_TAMM_WaterElectricityBill/1.0/MyBusinessGetWaterElectricityBillList",
)
DEFAULT_USERNAME = os.getenv("TAQA_USERNAME", "usrDED.prod")
DEFAULT_PASSWORD = os.getenv("TAQA_PASSWORD", "Iwe@_987a")

mcp = FastMCP("taqa-bills")


@mcp.tool()
async def get_water_electricity_bill_list(
    trade_license_numbers: list[str] | None = None,
    account_id: str = "",
    premise_id: str = "",
    emirates_id_numbers: list[str] | None = None,
    identity_type: str = "TID",
    show_all_accounts: bool = True,
    show_total_outstanding: bool = True,
    show_grand_total_outstanding: bool = True,
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
) -> dict[str, Any]:
    """Fetch water and electricity bill summaries for a TAQA trade license or account."""
    payload = {
        "MyBusinessGetWaterElectricityBillListRequest": {
            "AccountID": account_id,
            "EmiratesIDNumbers": emirates_id_numbers or [],
            "IdentityType": identity_type,
            "PremiseID": premise_id,
            "TradeLicenseNumbers": trade_license_numbers or ["CN-1094694"],
            "ShowAllAccounts": str(show_all_accounts).lower(),
            "ShowTotalOutStanding": str(show_total_outstanding).lower(),
            "ShowGrandTotalOutStanding": str(show_grand_total_outstanding).lower(),
        },
        "UserAuthentication": {
            "Username": username,
            "Password": password,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
