
import asyncio
import discord

from services.uptime_kuma_services import get_uptime_kuma_report
from reports.uptime_kuma_chart import generate_uptime_kuma_chart


async def send_uptime_kuma_report(webhook):
    # Ambil data monitor dan history.
    report = await asyncio.to_thread(
        get_uptime_kuma_report
    )

    # Generate satu gambar berisi statistik + history.
    image_buffer = await asyncio.to_thread(
        generate_uptime_kuma_chart,
        report,
    )

    checked_at = report["checked_at"].strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    try:
        await webhook.send(
            content=(
                "**Uptime Kuma | INAP**\n"
                f"Service Monitoring · Checked at: {checked_at}"
            ),
            file=discord.File(
                image_buffer,
                filename="uptime_kuma_report.png",
            ),
        )
    finally:
        image_buffer.close()
