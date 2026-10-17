import os
from dotenv import load_dotenv
from uptime_kuma_api import UptimeKumaApi

load_dotenv()

URL = os.getenv("UPTIME_KUMA_URL")
USERNAME = os.getenv("UPTIME_KUMA_USERNAME")
PASSWORD = os.getenv("UPTIME_KUMA_PASSWORD")


def main():
    if not all([URL, USERNAME, PASSWORD]):
        raise ValueError(
            "UPTIME_KUMA_URL, USERNAME, atau PASSWORD belum diatur."
        )

    with UptimeKumaApi(URL) as api:
        login_result = api.login(USERNAME, PASSWORD)
        print("LOGIN:", "BERHASIL" if login_result else "GAGAL")

        monitors = api.get_monitors()
        print("TOTAL MONITORS:", len(monitors))

        print("\n===== CONTOH DATA MONITOR =====")

        for monitor in monitors[:5]:
            monitor_id = monitor.get("id")
            name = monitor.get("name", "Unknown")

            print(f"\nNama: {name}")
            print("ID:", monitor_id)
            print("Active:", monitor.get("active"))
            print("Force Inactive:", monitor.get("forceInactive"))

            if monitor_id is not None:
                try:
                    status = api.get_monitor_status(monitor_id)
                    print("Status:", status)
                    print("Status Name:", getattr(status, "name", str(status)))
                except Exception as e:
                    print("Status Error:", e)

        print("\n===== SELESAI =====")


if __name__ == "__main__":
    main()