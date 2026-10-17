
from services.uptime_kuma_services import get_uptime_kuma_report


def main():
    report = get_uptime_kuma_report()

    print("\n===== UPTIME KUMA REPORT =====")
    print(
        "Checked at:",
        report["checked_at"].strftime("%d/%m/%Y %H:%M:%S %Z"),
    )
    print("Total Services:", report["total_services"])

    for status, total in report["counts"].items():
        print(f"{status}: {total}")

    print("Total Counted:", sum(report["counts"].values()))


if __name__ == "__main__":
    main()
