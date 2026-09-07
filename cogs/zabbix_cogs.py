import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import logging
from config import DISCORD_WEBHOOK_URL, TEST_WEBHOOK_URL, MAIN_WEBHOOK_URL, MAIN2_WEBHOOK_URL
import aiohttp
from services.global_report_services import build_global_report_text
from services.zabbix_service import (
    get_cpu_data,
    get_memory_data,
    get_disk_data,
    get_all_cpu_data,
    get_all_memory_data,
    get_all_disk_data,
    get_active_problems,
    get_recent_events,
)
from services.report_services import (
    generate_all_vm_reports,
    build_report_summary,
)
from config import REPORT_CHANNEL_ID

logger = logging.getLogger(__name__)


class ZabbixCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.report_scheduler_task = asyncio.create_task(
            self.report_scheduler()
        )

    def cog_unload(self):
        self.report_scheduler_task.cancel()
    
    @commands.command(name="cpu")
    async def cpu_command(self, ctx, kode: str = None):
        """Check CPU utilization for a specific host
        Usage: !cpu <kode>
        Example: !cpu 36
        """
        if not kode:
            embed = discord.Embed(
                title="❌ Missing Parameter",
                description="Usage: `!cpu <kode>`\nExample: `!cpu 36`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            data = get_cpu_data(kode)
            
            embed = discord.Embed(
                title="🖥️ CPU Utilization",
                color=discord.Color.blue()
            )
            embed.add_field(name="VM", value=f"`{data['kode']}`", inline=True)
            embed.add_field(name="Usage", value=f"**{data['value']:.2f}%**", inline=True)
            embed.add_field(name="Status", value=data['status'], inline=True)
            embed.add_field(name="Item", value=f"`{data['item_name']}`", inline=False)
            embed.set_footer(text=f"Checked at: {data['checked_at']}")
            
            await ctx.send(embed=embed)
            logger.info(f"CPU command executed for host {kode}")
            
        except ValueError as e:
            embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception(f"Error in CPU command for host {kode}")
    
    @commands.command(name="mem")
    async def memory_command(self, ctx, kode: str = None):
        """Check Memory utilization for a specific host
        Usage: !mem <kode>
        Example: !mem 36
        """
        if not kode:
            embed = discord.Embed(
                title="❌ Missing Parameter",
                description="Usage: `!mem <kode>`\nExample: `!mem 36`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            data = get_memory_data(kode)
            
            embed = discord.Embed(
                title="🧠 Memory Utilization",
                color=discord.Color.blue()
            )
            embed.add_field(name="VM", value=f"`{data['kode']}`", inline=True)
            embed.add_field(name="Usage", value=f"**{data['value']:.2f}%**", inline=True)
            embed.add_field(name="Status", value=data['status'], inline=True)
            embed.add_field(name="Item", value=f"`{data['item_name']}`", inline=False)
            embed.set_footer(text=f"Checked at: {data['checked_at']}")
            
            await ctx.send(embed=embed)
            logger.info(f"Memory command executed for host {kode}")
            
        except ValueError as e:
            embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception(f"Error in Memory command for host {kode}")
    
    @commands.command(name="disk")
    async def disk_command(self, ctx, kode: str = None):
        """Check Disk utilization for a specific host
        Usage: !disk <kode>
        Example: !disk 36
        """
        if not kode:
            embed = discord.Embed(
                title="❌ Missing Parameter",
                description="Usage: `!disk <kode>`\nExample: `!disk 36`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            data = get_disk_data(kode)
            
            embed = discord.Embed(
                title="💾 Disk Utilization",
                color=discord.Color.blue()
            )
            embed.add_field(name="VM", value=f"`{data['kode']}`", inline=True)
            embed.add_field(name="Usage", value=f"**{data['value']:.2f}%**", inline=True)
            embed.add_field(name="Status", value=data['status'], inline=True)
            embed.add_field(name="Item", value=f"`{data['item_name']}`", inline=False)
            embed.set_footer(text=f"Checked at: {data['checked_at']}")
            
            await ctx.send(embed=embed)
            logger.info(f"Disk command executed for host {kode}")
            
        except ValueError as e:
            embed = discord.Embed(
                title="❌ Error",
                description=str(e),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception(f"Error in Disk command for host {kode}")
    
    @commands.command(name="allcpu")
    async def all_cpu_command(self, ctx):
        """Check CPU utilization for all hosts"""
        try:
            data_list = get_all_cpu_data()
            
            embed = discord.Embed(
                title="🖥️ All INAP VM CPU Utilization",
                color=discord.Color.blue()
            )
            
            healthy = 0
            warning = 0
            critical = 0
            error = 0
            
            for data in data_list:
                if "error" in data:
                    error += 1
                    status_text = f"{data['status']}"
                else:
                    value = data['value']
                    if value >= 85:
                        critical += 1
                    elif value >= 70:
                        warning += 1
                    else:
                        healthy += 1
                    status_text = f"{data['status']} | {value:.2f}%"
                
                embed.add_field(name=f"Host {data['kode']}", value=status_text, inline=False)
            
            summary = f"🟢 Sehat: {healthy} | 🟡 Hati2: {warning} | 🔴 Sekarat: {critical}"
            if error > 0:
                summary += f" | ❌ Error: {error}"
            
            embed.description = summary
            embed.set_footer(text="All hosts summary")
            
            await ctx.send(embed=embed)
            logger.info("All CPU command executed")
            
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception("Error in All CPU command")
    
    @commands.command(name="allmem")
    async def all_memory_command(self, ctx):
        """Check Memory utilization for all hosts"""
        try:
            data_list = get_all_memory_data()
            
            embed = discord.Embed(
                title="🧠 All INAP VM Memory Utilization",
                color=discord.Color.blue()
            )
            
            healthy = 0
            warning = 0
            critical = 0
            error = 0
            
            for data in data_list:
                if "error" in data:
                    error += 1
                    status_text = f"{data['status']}"
                else:
                    value = data['value']
                    if value >= 90:
                        critical += 1
                    elif value >= 75:
                        warning += 1
                    else:
                        healthy += 1
                    status_text = f"{data['status']} | {value:.2f}%"
                
                embed.add_field(name=f"Host {data['kode']}", value=status_text, inline=False)
            
            summary = f"🟢 Sehat: {healthy} | 🟡 Hati2: {warning} | 🔴 Sekarat: {critical}"
            if error > 0:
                summary += f" | ❌ Error: {error}"
            
            embed.description = summary
            embed.set_footer(text="All hosts summary")
            
            await ctx.send(embed=embed)
            logger.info("All Memory command executed")
            
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception("Error in All Memory command")
    
    @commands.command(name="alldisk")
    async def all_disk_command(self, ctx):
        """Check Disk utilization for all hosts"""
        try:
            data_list = get_all_disk_data()
            
            embed = discord.Embed(
                title="💾 All INAP VM Disk Utilization",
                color=discord.Color.blue()
            )
            
            healthy = 0
            warning = 0
            critical = 0
            error = 0
            
            for data in data_list:
                if "error" in data:
                    error += 1
                    status_text = f"{data['status']}"
                else:
                    value = data['value']
                    if value >= 90:
                        critical += 1
                    elif value >= 85:
                        warning += 1
                    else:
                        healthy += 1
                    status_text = f"{data['status']} | {value:.2f}%"
                
                embed.add_field(name=f"Host {data['kode']}", value=status_text, inline=False)
            
            summary = f"🟢 Sehat: {healthy} | 🟡 Hati2: {warning} | 🔴 Sekarat: {critical}"
            if error > 0:
                summary += f" | ❌ Error: {error}"
            
            embed.description = summary
            embed.set_footer(text="All hosts summary")
            
            await ctx.send(embed=embed)
            logger.info("All Disk command executed")
            
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception("Error in All Disk command")

    # ------------------------------------
    # TESTING FOR SCHEDULER/ TAKE A SHOT FOR REPORT
    # ------------------------------------

    @commands.command(name="shot")
    async def snapshot_command(self, ctx):

        try:

            await ctx.send(
                "Membuat laporan Zabbix INAP..."
            )

            await self.send_vm_reports(
            )

            logger.info(
                "Manual VM report executed"
            )

        except Exception as e:

            await ctx.send(
                f"⚠️ Gagal membuat VM report:\n"
                f"`{e}`"
            )

            logger.exception(
                "Error in Shot command"
            )
    
    @commands.command(name="problems")
    async def problems_command(self, ctx, status: str = "all"):
        """Get problems from Zabbix - active, resolved, or all
        Usage: !problems [status]
        - !problems           → Show ALL problems (last 30 days)
        - !problems active    → Show only ACTIVE problems
        - !problems resolved  → Show only RESOLVED problems
        """
        status = (status or "all").lower()
        if status not in ["active", "resolved", "all"]:
            embed = discord.Embed(
                title="❌ Invalid Parameter",
                description="Usage: `!problems [active|resolved|all]`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            problems = get_active_problems(status=status)
            
            if not problems:
                embed = discord.Embed(
                    title="✅ No Problems Found",
                    description=f"Tidak ada {status} problems di Zabbix!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            # Filter by status if not "all"
            if status != "all":
                if status == "active":
                    problems = [p for p in problems if p.get("event_status") == "PROBLEM"]
                elif status == "resolved":
                    problems = [p for p in problems if p.get("event_status") == "RESOLVED"]
            
            if not problems:
                embed = discord.Embed(
                    title="✅ No Problems Found",
                    description=f"Tidak ada {status} problems di Zabbix!",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🚨 {status.upper()} Problems - Detailed List",
                color=discord.Color.red() if status != "resolved" else discord.Color.blue()
            )
            
            summary_count = {
                "Critical": 0, "Disaster": 0, "High": 0,
                "Average": 0, "Warning": 0, "Information": 0
            }
            
            for idx, problem in enumerate(problems[:20], 1):  # Limit to 20 for Discord embed limit
                severity = problem.get("severity", "Unknown")
                summary_count[severity] = summary_count.get(severity, 0) + 1
                
                emoji = problem.get("severity_emoji", "❓")
                hosts_text = ", ".join(problem.get("hosts", ["Unknown"])) or "Unknown"
                duration = problem.get("duration", "N/A")
                ack = problem.get("acknowledged", "No")
                clock = problem.get("clock", "N/A")
                tags_list = problem.get("tags", [])
                tags_text = " | ".join(tags_list[:3]) if tags_list else "No tags"
                event_status = problem.get("event_status", "UNKNOWN")
                
                # Format field name: Time | Host | Problem name | Status
                field_name = f"{clock} | {hosts_text} | {emoji} {severity}"
                
                # Format field value with details
                status_indicator = "🟢 RESOLVED" if event_status == "RESOLVED" else "🔴 ACTIVE"
                field_value = (
                    f"**{problem.get('name', 'Unknown')[:55]}**\n"
                    f"{status_indicator} | ⏱️ {duration} | ✓ {ack}\n"
                    f"🏷️ {tags_text}"
                )
                
                embed.add_field(name=field_name, value=field_value, inline=False)
            
            # Summary
            summary_text = " | ".join([f"{emoji} {count}" for emoji, count in [
                ("💥", summary_count["Disaster"]),
                ("🔴", summary_count["High"]),
                ("🟡", summary_count["Average"]),
                ("⚠️", summary_count["Warning"]),
                ("ℹ️", summary_count["Information"])
            ]])
            
            embed.description = f"Total: {len(problems)} {status} problems (last 30 days)\n{summary_text}"
            embed.set_footer(text=f"Updated at: {problems[0]['timestamp'] if problems else 'N/A'}")
            
            await ctx.send(embed=embed)
            logger.info(f"Problems command executed with status={status}")
            
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception("Error in Problems command")
            
            await ctx.send(embed=embed)
            logger.info("Problems command executed")
            
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception("Error in Problems command")
    
    @commands.command(name="alert")
    async def alert_command(self, ctx, limit: int = 15):
        """Get recent alerts/events from Zabbix
        Usage: !alert [limit]
        Example: !alert 10
        """
        if limit < 1 or limit > 50:
            limit = 15
        
        try:
            events = get_recent_events(limit=limit)
            
            if not events:
                embed = discord.Embed(
                    title="ℹ️ No Recent Events",
                    description="Belum ada event terbaru.",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"📢 Recent Alerts (Last {limit})",
                color=discord.Color.orange()
            )
            
            problem_count = 0
            resolved_count = 0
            
            for event in events:
                if "PROBLEM" in event.get("type", ""):
                    problem_count += 1
                else:
                    resolved_count += 1
                
                emoji = event.get("severity_emoji", "❓")
                event_type = event.get("type", "UNKNOWN")
                hosts_text = ", ".join(event.get("hosts", ["Unknown"])) or "Unknown"
                
                field_name = f"{emoji} {event_type} | {event.get('severity', 'Unknown')}"
                field_value = f"Hosts: {hosts_text}\nTime: `{event.get('clock', 'N/A')}`"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
            
            # Summary
            summary = f"🔴 Problems: {problem_count} | 🟢 Resolved: {resolved_count}"
            embed.description = summary
            embed.set_footer(text="Most recent events shown first")
            
            await ctx.send(embed=embed)
            logger.info("Alert command executed")
            
        except Exception as e:
            embed = discord.Embed(
                title="⚠️ Error",
                description=str(e),
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            logger.exception("Error in Alert command")


    # -------------------------------------------
    # REPORTING
    # -------------------------------------------

    async def send_vm_reports(self):
        """
        Generate seluruh VM report dan kirim melalui Discord webhook.
        """

        reports = await asyncio.to_thread(
            generate_all_vm_reports,
            hours=2,
        )

        if not reports:
            logger.warning(
                "Tidak ada report yang berhasil dibuat."
            )
            return

        async with aiohttp.ClientSession() as session:

            webhook = discord.Webhook.from_url(
                # TEST_WEBHOOK_URL,
                # MAIN_WEBHOOK_URL,
                MAIN2_WEBHOOK_URL,
                # DISCORD_WEBHOOK_URL,
                session=session,
            )

            # ====================================================
            # HEADER
            # ====================================================

            first_report = reports[0]["report"]

            period = first_report["period"]

            period_start = datetime.fromtimestamp(
                period["start"]
            ).strftime("%H:%M")

            period_end = datetime.fromtimestamp(
                period["end"]
            ).strftime("%H:%M")

            checked_at = datetime.fromtimestamp(
                first_report["checked_at"]
            ).strftime("%H:%M")

            await webhook.send(
                " ============== **ZABBIX INAP REPORT** ==============\n\n"
                f"Period: {period_start} - {period_end}\n"
                f"Checked at: {checked_at}"
            )

            # ====================================================
            # VM IMAGES
            # ====================================================

            for item in reports:

                kode = item["kode"]
                image = item["image"]

                image.seek(0)

                await webhook.send(
                    file=discord.File(
                        image,
                        filename=f"vm_{kode}_report.png",
                    )
                )

                image.close()

            # ====================================================
            # GLOBAL SUMMARY
            # ====================================================

            summary = build_global_report_text(
                reports
            )

            await webhook.send(
                summary
            )

        logger.info(
            "VM report selesai dikirim: %d VM",
            len(reports),
        )


    async def wait_until_next_report(self):
        """
        Menunggu jadwal report:

        01:00
        03:00
        05:00
        ...
        23:00
        """

        now = datetime.now()

        # Cari boundary ganjil berikutnya
        if now.hour % 2 == 0:
            next_hour = now.hour + 1
        else:
            next_hour = now.hour + 2

        if next_hour >= 24:

            next_run = (
                now.replace(
                    hour=1,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                + timedelta(days=1)
            )

        else:

            next_run = now.replace(
                hour=next_hour,
                minute=0,
                second=0,
                microsecond=0,
            )

        wait_seconds = (
            next_run - now
        ).total_seconds()

        logger.info(
            "Next automatic report: %s",
            next_run.strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
        )

        await asyncio.sleep(
            wait_seconds
        )


    async def report_scheduler(self):

        await self.bot.wait_until_ready()

        while not self.bot.is_closed():

            await self.wait_until_next_report()

            try:

                logger.info(
                    "Automatic VM report started"
                )

                await self.send_vm_reports()

            except Exception:

                logger.exception(
                    "Automatic VM report failed"
                )

async def setup(bot):
    """Load ZabbixCog into the bot"""
    await bot.add_cog(ZabbixCog(bot))
