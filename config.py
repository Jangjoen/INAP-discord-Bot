from dotenv import load_dotenv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=False)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
HANES_USERNAME = os.getenv("HANES_USERNAME", "").strip()
HANES_PASSWORD = os.getenv("HANES_PASSWORD", "").strip()

# Zabbix Configuration
ZABBIX_URL = os.getenv("ZABBIX_URL", "http://localhost:8080/api_jsonrpc.php").strip()
ZABBIX_AUTH = os.getenv("ZABBIX_AUTH", "").strip()


# WEBHOOK
TEST_WEBHOOK_URL = os.getenv(
    "TEST_WEBHOOK_URL"
)

MAIN2_WEBHOOK_URL = os.getenv(
    "MAIN2_WEBHOOK_URL"
)

MAIN_WEBHOOK_URL = os.getenv(
    "MAIN_WEBHOOK_URL"
)

# Zabbix Host Mapping
HOST_MAP = {
    "36": "10535",
    "37": "10544",
    "41": "10536",
    "42": "10537",
    "43": "10538",
    "44": "10539",
    "45": "10540",
    "46": "10541",
    "47": "10542",
    "48": "10543",
    "zabbix": "10084",
    "35": "10545",
    "61": "10546",
    "57": "10547",
    "58": "10548",
    "59": "10549",
}

DISK_HOST_MAP = {
    "36": "10535",
    "37": "10544",
    "41": "10536",
    "42": "10537",
    "43": "10538",
    "44": "10539",
    "45": "10540",
    "46": "10541",
    "47": "10542",
    "48": "10543",
    "zabbix": "10084"
}

ITEMIDS_DISK_MAP = {
    "36": "44334",
    "37": "45609",
    "41": "44928",
    "42": "44984",
    "43": "45051",
    "44": "45122",
    "45": "45192",
    "46": "45272",
    "47": "45355",
    "48": "45417",
    "zabbix": "44015"
}

ITEMIDS_CPU_MAP = {
    "36": "44258",
    "37": "45465",
    "41": "44382",
    "42": "44449",
    "43": "44516",
    "44": "44583",
    "45": "44650",
    "46": "44717",
    "47": "44784",
    "48": "44851",
    "zabbix": "42269",
    "35": "45532",
    "61": "48916",
    "57": "51374",
    "58": "51626",
    "59": "51769",
}

ITEMIDS_MEMORY_MAP = {
    "36": "44259",
    "37": "45466",
    "41": "44383",
    "42": "44450",
    "43": "44517",
    "44": "44584",
    "45": "44651",
    "46": "44718",
    "47": "44785",
    "48": "44852",
    "zabbix": "42270",
    "35": "45533",
    "61": "48917",
    "57": "51375",
    "58": "51627",
    "59": "51770",
}


def ensure_hanes_env() -> None:
    if HANES_USERNAME:
        os.environ["HANES_USERNAME"] = HANES_USERNAME
    if HANES_PASSWORD:
        os.environ["HANES_PASSWORD"] = HANES_PASSWORD
    if DISCORD_WEBHOOK_URL:
        os.environ["DISCORD_WEBHOOK_URL"] = DISCORD_WEBHOOK_URL


# ========================================================
# REPORT STATUS THRESHOLD
# ========================================================

CPU_WARNING_THRESHOLD = 75.0
CPU_CRITICAL_THRESHOLD = 90.0

MEMORY_WARNING_THRESHOLD = 75.0
MEMORY_CRITICAL_THRESHOLD = 90.0

DISK_WARNING_THRESHOLD = 70.0
DISK_CRITICAL_THRESHOLD = 90.0        

REPORT_CHANNEL_ID = int(
    os.getenv(
        "REPORT_CHANNEL_ID",
        "0",
    )
)