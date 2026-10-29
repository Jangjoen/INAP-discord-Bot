import asyncio
import inspect
import io
import logging
import shlex
import threading

import aiohttp
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, MAIN2_WEBHOOK_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.reporting_enabled = True


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

    try:
        await bot.load_extension("cogs.kafka_cogs")
        logger.info("Kafka cogs loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Kafka cogs: {e}")

    try:
        await bot.load_extension("cogs.uptime_cogs")
        logger.info("Uptime cogs loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Uptime cogs: {e}")


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("pong")


@bot.command(name="reporting")
async def reporting_command(ctx, state: str = "status"):
    """Enable or disable scheduled reports: !reporting <on|off|status>"""
    state = state.lower()
    if state == "on":
        ctx.bot.reporting_enabled = True
        await ctx.send("Laporan terjadwal diaktifkan.")
    elif state == "off":
        ctx.bot.reporting_enabled = False
        await ctx.send(
            "Laporan terjadwal dinonaktifkan. Laporan yang sedang berjalan "
            "akan diselesaikan."
        )
    elif state == "status":
        status = "aktif" if ctx.bot.reporting_enabled else "nonaktif"
        await ctx.send(f"Laporan terjadwal saat ini {status}.")
    else:
        await ctx.send("Penggunaan: `!reporting <on|off|status>`")


class CliContext:
    def __init__(self, bot):
        self.bot = bot

    async def send(self, content=None, *, embed=None, file=None):
        if content is not None:
            print(content)

        if file is not None:
            if not MAIN2_WEBHOOK_URL:
                raise RuntimeError("MAIN2_WEBHOOK_URL belum dikonfigurasi")

            file.fp.seek(0)
            attachment = discord.File(
                io.BytesIO(file.fp.read()),
                filename=file.filename,
            )
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                    MAIN2_WEBHOOK_URL,
                    session=session,
                )
                try:
                    await webhook.send(content=content, file=attachment)
                finally:
                    attachment.close()
            print("Image report berhasil dikirim ke Discord.")

        if embed is not None:
            if embed.title:
                print(f"\n{embed.title}")
            if embed.description:
                print(embed.description)
            for field in embed.fields:
                print(f"\n{field.name}\n{field.value}")
            if embed.footer.text:
                print(embed.footer.text)


def convert_cli_arguments(command, arguments):
    parameters = list(command.clean_params.values())
    if len(arguments) > len(parameters):
        raise ValueError(f"Terlalu banyak argumen untuk perintah '{command.name}'.")

    converted = []
    for argument, parameter in zip(arguments, parameters):
        if parameter.annotation is int:
            try:
                argument = int(argument)
            except ValueError as error:
                raise ValueError(
                    f"Argumen '{parameter.name}' harus berupa angka."
                ) from error
        elif parameter.annotation not in (str, inspect.Parameter.empty):
            raise TypeError(
                f"Tipe argumen '{parameter.name}' belum didukung di CLI."
            )
        converted.append(argument)

    return converted


def queue_cli_input(loop, input_queue):
    while True:
        try:
            line = input("bot> ")
        except EOFError:
            loop.call_soon_threadsafe(input_queue.put_nowait, None)
            return

        try:
            loop.call_soon_threadsafe(input_queue.put_nowait, line)
        except RuntimeError:
            return


async def run_cli_commands():
    loop = asyncio.get_running_loop()
    input_queue = asyncio.Queue()
    threading.Thread(
        target=queue_cli_input,
        args=(loop, input_queue),
        daemon=True,
    ).start()

    print("CLI aktif. Ketik 'help' untuk daftar command atau 'exit' untuk keluar.")
    ctx = CliContext(bot)

    while True:
        line = await input_queue.get()
        if line is None:
            return

        try:
            parts = shlex.split(line)
        except ValueError as error:
            print(f"Input tidak valid: {error}")
            continue

        if not parts:
            continue

        name = parts[0].lstrip("!")
        arguments = parts[1:]

        if name in ("exit", "quit"):
            await bot.close()
            return

        if name == "help":
            if arguments:
                command = bot.get_command(arguments[0].lstrip("!"))
                if command is None:
                    print(f"Command tidak dikenal: {arguments[0]}")
                else:
                    print(command.help or command.brief or f"Command: {command.name}")
            else:
                command_names = sorted(
                    command.name
                    for command in bot.commands
                    if command.name != "help"
                )
                print("Command tersedia: " + ", ".join(command_names))
                print("Jalankan 'help <command>' untuk detail.")
            continue

        command = bot.get_command(name)
        if command is None:
            print(f"Command tidak dikenal: {name}. Ketik 'help' untuk daftar.")
            continue

        try:
            converted_arguments = convert_cli_arguments(command, arguments)
            await command(ctx, *converted_arguments)
        except Exception as error:
            logger.exception("CLI command '%s' gagal", name)
            print(f"Gagal menjalankan '{name}': {error}")


if __name__ == "__main__":
    async def main():
        async with bot:
            await load_cogs()
            cli_task = asyncio.create_task(run_cli_commands())
            try:
                await bot.start(DISCORD_TOKEN)
            finally:
                cli_task.cancel()
                await asyncio.gather(cli_task, return_exceptions=True)

    asyncio.run(main())