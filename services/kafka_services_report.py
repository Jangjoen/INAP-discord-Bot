import discord
from services.kafka_services import get_kafka_consumer_report


async def send_kafka_report(webhook):
    report = await __import__("asyncio").to_thread(
        get_kafka_consumer_report
    )

    screenshot = report["screenshot"]

    try:
        # 1. Kirim screenshot Consumers page
        screenshot.seek(0)

        await webhook.send(
            file=discord.File(
                screenshot,
                filename="kafka_consumers.png",
            )
        )

        # 2. Kirim ringkasan setelah screenshot
        checked_at = report["checked_at"].strftime(
            "%d/%m/%Y %H:%M:%S %Z"
        )

        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━",
            "KAFKA CONSUMERS GROUP REPORT",
            f"Checked at: {checked_at}",
            f"Total Consumer Groups: {len(report['groups'])}",
            "",
            "HIGHEST MESSAGES BEHIND",
            "",
        ]

        for rank, group in enumerate(report["top5"], start=1):
            lines.extend([
                f"{rank}. {group['group_id']}",
                f"   Messages Behind: "
                f"**{group['messages_behind']:,}**",
                f"   State: {group['state']}",
                "",
            ])

        await webhook.send("\n".join(lines).rstrip())

    finally:
        screenshot.close()
