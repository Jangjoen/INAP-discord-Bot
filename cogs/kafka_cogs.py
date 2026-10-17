import logging
from datetime import datetime
from pathlib import Path

import aiohttp
import discord
from discord.ext import commands

from config import KAFKA_WEBHOOK_URL
from services.kafka_services_report import send_kafka_report

logger = logging.getLogger(__name__)
KAFKA_REPORT_STATE_PATH = (
	Path(__file__).resolve().parents[1]
	/ "reports"
	/ "output"
	/ ".kafka_report_scheduler_state"
)


def load_last_kafka_report_slot():
	try:
		value = KAFKA_REPORT_STATE_PATH.read_text(encoding="ascii").strip()
		return datetime.fromisoformat(value)
	except FileNotFoundError:
		return None
	except ValueError:
		logger.warning("Invalid Kafka report state; treating slot as unreported")
		return None


def save_last_kafka_report_slot(slot: datetime) -> None:
	KAFKA_REPORT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
	temporary_path = KAFKA_REPORT_STATE_PATH.with_suffix(".tmp")
	temporary_path.write_text(
		slot.isoformat(timespec="minutes"),
		encoding="ascii",
	)
	temporary_path.replace(KAFKA_REPORT_STATE_PATH)


class KafkaCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def is_scheduled_report_due(self, slot: datetime) -> bool:
		last_reported_slot = load_last_kafka_report_slot()
		return (
			last_reported_slot is None
			or slot > last_reported_slot
		)

	async def _send_report(self) -> None:
		if not KAFKA_WEBHOOK_URL:
			raise RuntimeError("KAFKA_WEBHOOK_URL belum dikonfigurasi")

		async with aiohttp.ClientSession() as session:
			webhook = discord.Webhook.from_url(
				KAFKA_WEBHOOK_URL,
				session=session,
			)
			await send_kafka_report(webhook)

		logger.info("Kafka consumer report selesai dikirim")

	async def send_scheduled_report(self, slot: datetime) -> bool:
		if not self.is_scheduled_report_due(slot):
			return True

		await self._send_report()
		save_last_kafka_report_slot(slot)
		return True

	@commands.command(name="kafka")
	async def kafka_report(self, ctx):
		await ctx.send("Sedang mengambil laporan Kafka...")

		try:
			await self._send_report()
			await ctx.send("Laporan Kafka berhasil dikirim.")
		except Exception as error:
			logger.exception("Gagal mengirim Kafka report")
			await ctx.send(f"Gagal mengambil laporan Kafka: `{error}`")


async def setup(bot):
	await bot.add_cog(KafkaCog(bot))
