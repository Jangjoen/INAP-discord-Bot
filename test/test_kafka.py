
from services.kafka_services import get_kafka_consumer_report


def main():
    report = get_kafka_consumer_report()

    print("CHECKED AT:", report["checked_at"].strftime(
        "%d/%m/%Y %H:%M:%S %Z"
    ))

    print("TOTAL GROUPS:", len(report["groups"]))

    print("\n===== TOP 5 MESSAGES BEHIND =====")

    for rank, group in enumerate(report["top5"], start=1):
        print(
            f"{rank}. {group['group_id']} "
            f"| Lag: {group['messages_behind']:,} "
            f"| State: {group['state']}"
        )

    screenshot = report["screenshot"]
    screenshot.seek(0)

    with open("kafka_consumers_test.png", "wb") as file:
        file.write(screenshot.getvalue())

    screenshot.close()

    print("\nScreenshot saved: kafka_consumers_test.png")


if __name__ == "__main__":
    main()
