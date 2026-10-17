import logging
from datetime import datetime
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands

from config import UPTIME_KUMA_WEBHOOK_URL
from services.uptime_kuma_report_services import (
    send_uptime_kuma_report,
)

logger = logging.getLogger(__name__)
UPTIME_KUMA_REPORT_STATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "output"
    / ".uptime_kuma_report_scheduler_state"
)


def load_last_uptime_kuma_report_slot():
    try:
        value = UPTIME_KUMA_REPORT_STATE_PATH.read_text(encoding="ascii").strip()
        return datetime.fromisoformat(value)
    except FileNotFoundError:
        return None
    except ValueError:
        logger.warning("Invalid Uptime Kuma report state; treating slot as unreported")
        return None


def save_last_uptime_kuma_report_slot(slot: datetime) -> None:
    UPTIME_KUMA_REPORT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = UPTIME_KUMA_REPORT_STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        slot.isoformat(timespec="minutes"),
        encoding="ascii",
    )
    temporary_path.replace(UPTIME_KUMA_REPORT_STATE_PATH)


class UptimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_scheduled_report_due(self, slot: datetime) -> bool:
        last_reported_slot = load_last_uptime_kuma_report_slot()
        return (
            last_reported_slot is None
            or slot > last_reported_slot
        )

    async def _send_report(self):
        if not UPTIME_KUMA_WEBHOOK_URL:
            raise RuntimeError("UPTIME_KUMA_WEBHOOK_URL belum dikonfigurasi")

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                UPTIME_KUMA_WEBHOOK_URL,
                session=session,
            )
            await send_uptime_kuma_report(webhook)

    async def send_scheduled_report(self, slot: datetime) -> bool:
        if not self.is_scheduled_report_due(slot):
            return True

        await self._send_report()
        save_last_uptime_kuma_report_slot(slot)
        logger.info("Uptime Kuma report selesai dikirim")
        return True

    @commands.command(name="uptime")
    async def uptime_report(self, ctx):
        await ctx.send("Sedang mengambil laporan Uptime Kuma...")

        try:
            await self._send_report()
            await ctx.send("Laporan Uptime Kuma berhasil dikirim.")

        except Exception as error:
            await ctx.send(
                f"Gagal mengambil laporan Uptime Kuma: `{error}`"
            )


async def setup(bot):
    await bot.add_cog(UptimeCog(bot))
