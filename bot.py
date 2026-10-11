import asyncio
import logging

import discord
from discord.ext import commands

from config import DISCORD_TOKEN

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


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("pong")


if __name__ == "__main__":
    async def main():
        async with bot:
            await load_cogs()
            await bot.start(DISCORD_TOKEN)
    
    asyncio.run(main())