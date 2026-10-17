
from playwright.sync_api import sync_playwright

KAFKA_UI_URL = (
    "http://10.62.7.48:18080/"
    "ui/clusters/bc-inap-kafka/consumer-groups"
)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(
            KAFKA_UI_URL,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        page.locator("table").first.wait_for(
            state="visible",
            timeout=15000,
        )

        # Ambil header tabel
        headers = page.locator("table thead th").all_inner_texts()
        print("HEADERS:", headers)

        # Ambil seluruh baris tabel
        rows = page.locator("table tbody tr")
        print("JUMLAH BARIS:", rows.count())

        for row in rows.all():
            cells = [
                cell.strip()
                for cell in row.locator("td").all_inner_texts()
            ]

            if not cells:
                continue

            print(cells)

        browser.close()


if __name__ == "__main__":
    main()
