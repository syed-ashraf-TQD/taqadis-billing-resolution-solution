import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SAMPLE_RESPONSE = {
    "TradeLicenseBalances": [
        {"TotalOutStanding": "974.83", "TradeLicenseNumber": "CN-1094694"}
    ],
    "EmiratesIDBalances": [],
    "GrandTotalOutStanding": "974.83",
    "WaterElectricityBillList": [
        {
            "AccountID": "0519951948",
            "AccountInfo": "COMRC   ",
            "AccountStatus": "Active",
            "BillDueDate": "2026-10-16 00:00:00",
            "BillID": "051984502101",
            "CurrentBalance": "974.83",
            "EID": None,
            "TradeLicense": "CN-1094694",
            "PlotNumber": "C10",
            "PremiseAddress": "ME9-C10 Flat 204 (ME9-C10)",
            "PremiseID": "5704993656",
            "SectorCommunityCode": "ME9",
            "ZoneDistrictCode": "ME9-C10",
        }
    ],
    "Fault": None,
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT
