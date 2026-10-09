import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
import logging
from pathlib import Path
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
    get_zabbix_events_after,
)
from services.report_services import (
    generate_all_vm_reports,
    build_report_summary,
)
from config import REPORT_CHANNEL_ID

logger = logging.getLogger(__name__)

REPORT_RETRY_SECONDS = 60
ALERT_POLL_SECONDS = 30
REPORT_STATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "output"
    / ".report_scheduler_state"
)
ALERT_STATE_PATH = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "output"
    / ".alert_event_state"
)


def get_report_slot(now: datetime) -> datetime:
    slot = now.replace(minute=0, second=0, microsecond=0)
    if slot.hour % 2 == 0:
        slot -= timedelta(hours=1)
    return slot


def load_last_report_slot():
    try:
        value = REPORT_STATE_PATH.read_text(encoding="ascii").strip()
        return datetime.fromisoformat(value)
    except FileNotFoundError:
        return None
    except ValueError:
        logger.warning("Invalid report scheduler state; treating slot as unreported")
        return None


def save_last_report_slot(slot: datetime) -> None:
    REPORT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = REPORT_STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        slot.isoformat(timespec="minutes"),
        encoding="ascii",
    )
    temporary_path.replace(REPORT_STATE_PATH)


def load_alert_event_id():
    try:
        return int(ALERT_STATE_PATH.read_text(encoding="ascii").strip())
    except FileNotFoundError:
        return None
    except ValueError:
        logger.warning("Invalid alert event state; will establish a new baseline")
        return None


def save_alert_event_id(eventid: int) -> None:
    ALERT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = ALERT_STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(str(eventid), encoding="ascii")
    temporary_path.replace(ALERT_STATE_PATH)


def split_discord_message(text: str, limit: int = 2000) -> list[str]:
    """Split text into Discord-safe chunks without breaking normal lines."""
    if not text:
        return []

    body_limit = max(1, limit - 64)
    chunks = []
    current_lines = []
    current_length = 0

    for line in text.splitlines():
        line_parts = [line[index:index + body_limit] for index in range(0, len(line), body_limit)] or [""]

        for part in line_parts:
            part_length = len(part) + (1 if current_lines else 0)

            if current_lines and current_length + part_length > body_limit:
                chunks.append("\n".join(current_lines))
                current_lines = []
                current_length = 0

            current_lines.append(part)
            current_length += len(part) + (1 if len(current_lines) > 1 else 0)

    if current_lines:
        chunks.append("\n".join(current_lines))

    if len(chunks) <= 1:
        return chunks

    total = len(chunks)
    return [
        chunk
        for index, chunk in enumerate(chunks, start=1)
    ]



class ZabbixCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.report_scheduler_task = asyncio.create_task(
            self.report_scheduler()
        )
        self.problem_alert_task = asyncio.create_task(
            self.problem_alert_monitor()
        )

    def cog_unload(self):
        self.report_scheduler_task.cancel()
        self.problem_alert_task.cancel()
    
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
            return False

        async with aiohttp.ClientSession() as session:

            # WEBHOOK TARGET
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
                reports,
                hours=2,
            )

            for summary_part in split_discord_message(summary):
                await webhook.send(summary_part)

        logger.info(
            "VM report selesai dikirim: %d VM",
            len(reports),
        )
        return True


    async def report_scheduler(self):

        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            now = datetime.now()
            current_slot = get_report_slot(now)
            last_reported_slot = load_last_report_slot()

            if (
                last_reported_slot is None
                or current_slot > last_reported_slot
            ):
                successful = False

                try:
                    logger.info(
                        "Automatic VM report started for slot %s",
                        current_slot.strftime("%d/%m/%Y %H:%M"),
                    )
                    successful = await self.send_vm_reports()

                    if successful:
                        save_last_report_slot(current_slot)
                    else:
                        logger.warning(
                            "Report slot %s belum terkirim; akan dicoba lagi.",
                            current_slot.strftime("%d/%m/%Y %H:%M"),
                        )

                except Exception:
                    successful = False
                    logger.exception(
                        "Automatic VM report failed; will retry"
                    )

                if not successful:
                    await asyncio.sleep(REPORT_RETRY_SECONDS)
                    continue

                continue

            next_slot = current_slot + timedelta(hours=2)
            wait_seconds = max(
                1,
                (next_slot - datetime.now()).total_seconds(),
            )
            logger.info(
                "Next automatic report: %s",
                next_slot.strftime("%d/%m/%Y %H:%M:%S"),
            )
            await asyncio.sleep(wait_seconds)


    async def send_problem_alert(self, event: dict) -> None:
        if not MAIN2_WEBHOOK_URL:
            raise RuntimeError("MAIN2_WEBHOOK_URL belum dikonfigurasi")

        severity_labels = {
            0: "Not classified",
            1: "Information",
            2: "Warning",
            3: "Average",
            4: "High",
            5: "Disaster",
        }
        severity_colors = {
            0: discord.Color.light_grey(),
            1: discord.Color.blue(),
            2: discord.Color.gold(),
            3: discord.Color.orange(),
            4: discord.Color.red(),
            5: discord.Color.dark_red(),
        }
        severity = event["severity"]
        hosts = ", ".join(event["hosts"]) or "Unknown"
        timestamp = datetime.fromtimestamp(event["clock"])

        embed = discord.Embed(
            title="🚨 Zabbix Problem Baru",
            description=event["name"],
            color=severity_colors.get(severity, discord.Color.red()),
            timestamp=timestamp,
        )
        embed.add_field(name="Host", value=hosts, inline=False)
        embed.add_field(
            name="Severity",
            value=severity_labels.get(severity, "Unknown"),
            inline=True,
        )
        embed.add_field(name="Event ID", value=str(event["eventid"]), inline=True)

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                MAIN2_WEBHOOK_URL,
                session=session,
            )
            await webhook.send(embed=embed)


    async def problem_alert_monitor(self):
        await self.bot.wait_until_ready()
        last_event_id = load_alert_event_id()

        while not self.bot.is_closed():
            try:
                events = await asyncio.to_thread(
                    get_zabbix_events_after,
                    last_event_id,
                )

                if last_event_id is None:
                    if events:
                        last_event_id = max(
                            event["eventid"] for event in events
                        )
                        save_alert_event_id(last_event_id)
                        logger.info(
                            "Zabbix alert monitor baseline set to event %s",
                            last_event_id,
                        )
                else:
                    for event in events:
                        if event["value"] == 1:
                            await self.send_problem_alert(event)
                            logger.info(
                                "Sent Zabbix problem alert for event %s",
                                event["eventid"],
                            )

                        last_event_id = event["eventid"]
                        save_alert_event_id(last_event_id)

            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "Zabbix problem alert check failed; will retry"
                )

            await asyncio.sleep(ALERT_POLL_SECONDS)

async def setup(bot):
    """Load ZabbixCog into the bot"""
    await bot.add_cog(ZabbixCog(bot))
