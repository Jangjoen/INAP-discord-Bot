
from datetime import datetime
from io import BytesIO

from playwright.sync_api import sync_playwright


KAFKA_UI_URL = (
    "http://10.62.7.48:18080/"
    "ui/clusters/bc-inap-kafka/consumer-groups"
)


def get_kafka_consumer_report() -> dict:
    """Mengambil screenshot dan data Consumer Groups."""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            page = browser.new_page(
                viewport={
                    "width": 1600,
                    "height": 1000,
                }
            )

            page.goto(
                KAFKA_UI_URL,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            rows = page.locator("table tbody tr")

            rows.first.wait_for(
                state="visible",
                timeout=15000,
            )

            groups = []

            for row in rows.all():
                cells = [
                    cell.strip()
                    for cell in row.locator("td").all_inner_texts()
                ]

                if len(cells) < 6:
                    continue

                group_id, members, topics, lag, coordinator, state = (
                    cells[:6]
                )

                groups.append({
                    "group_id": group_id,
                    "members": int(members),
                    "topics": int(topics),
                    "messages_behind": int(
                        lag.replace(",", "")
                    ),
                    "coordinator": int(coordinator),
                    "state": state,
                })

            if not groups:
                raise RuntimeError(
                    "Tidak ada Consumer Group yang berhasil dibaca."
                )

            # Catat waktu setelah data tabel berhasil dibaca.
            checked_at = datetime.now()

            screenshot = BytesIO(
                page.screenshot(
                    full_page=True,
                    animations="disabled",
                )
            )
            screenshot.seek(0)

            top5 = sorted(
                groups,
                key=lambda group: group["messages_behind"],
                reverse=True,
            )[:5]

            return {
                "checked_at": checked_at,
                "screenshot": screenshot,
                "groups": groups,
                "top5": top5,
            }

        finally:
            browser.close()
