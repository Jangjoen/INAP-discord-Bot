import asyncio
import logging

import discord
from discord.ext import commands

from config import DISCORD_TOKEN, ensure_hanes_env
from services.hanes_bridge import get_latest_run_summary, run_hanes_monitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot berhasil login sebagai {bot.user}")
    print("Siap Berjalan.")


async def load_cogs():
    """Load all cogs from cogs folder"""
    try:
        await bot.load_extension("cogs.zabbix_cogs")
        logger.info("Zabbix cogs loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Zabbix cogs: {e}")


@bot.command(name="hanes")
async def hanes(ctx, mode: str = "run"):
    mode = (mode or "run").lower()
    ensure_hanes_env()

    if mode in {"run", "refresh", "check"}:
        await ctx.send("Mengeksekusi monitoring Hanes... ini mungkin memerlukan beberapa detik.")
        try:
            result = await asyncio.to_thread(run_hanes_monitor)
            summary_text = get_latest_run_summary()
            exit_code = result.get("exit_code", 0)
            if summary_text:
                await ctx.send(summary_text)
            await ctx.send(f"Monitoring selesai. Exit code: {exit_code}")
        except Exception as exc:
            await ctx.send(f"Monitoring Hanes gagal: {exc}")
        return

    if mode in {"last", "summary", "status"}:
        summary_text = get_latest_run_summary()
        if summary_text:
            await ctx.send(summary_text)
        else:
            await ctx.send("Belum ada hasil monitoring Hanes yang tersimpan.")
        return

    await ctx.send("Format perintah: !hanes run | !hanes last | !hanes status")


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("pong")


if __name__ == "__main__":
    async def main():
        async with bot:
            await load_cogs()
            await bot.start(DISCORD_TOKEN)
    
    asyncio.run(main())