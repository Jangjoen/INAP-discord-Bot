import discord
from config import discord_token
from discord.ext import commands
from playwright.sync_api import sync_playwright
from io import BytesIO
from inap_api import get_inap_status 

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

class InapCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def status(self, ctx):
        data = get_inap_status()
        if "error" in data:
            await ctx.send(f"API error: {data['error']} - {data['message']}")
        else:
            # contoh: ambil jumlah impacted site dari JSON
            impacted = data.get("impacted_sites", "tidak ada field impacted_sites")
            embed = discord.Embed(title="INAP Dashboard Status")
            embed.add_field(name="Impacted Sites", value=impacted)
            await ctx.send(embed=embed)

def capture_inap(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        buffer = page.screenshot(full_page=True)
        browser.close()
        return buffer

@bot.command()
async def screenshot(ctx):
    image_bytes = capture_inap("https://10.62.7.36:8950/ui/#./inap-two/map2/event")
    await ctx.send(file=discord.File(BytesIO(image_bytes), filename="inap.png"))

bot.run("DISCORD_TOKEN")
