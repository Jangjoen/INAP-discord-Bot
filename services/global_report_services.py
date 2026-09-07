from datetime import datetime

from config import HOST_MAP
from services.zabbix_service import get_hosts_snapshot
from services.zabbix_service import get_active_problems_with_hosts
from services.zabbix_service import (
    get_active_problems,
    get_monitored_hosts,
)
from services.report_services import build_report_summary

SEVERITY_EMOJI = {
    "0": "⚪",
    "1": "🔵",
    "2": "🟡",
    "3": "🟠",
    "4": "🔴",
    "5": "🔴",
}

def build_global_report_text(reports):
    """
    Membuat teks summary lengkap untuk Discord.
    """

    # ========================================================
    # VM SUMMARY
    # ========================================================

    vm_summary = build_report_summary(reports)

    # ========================================================
    # PERIOD
    # ========================================================

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

    # ========================================================
    # GLOBAL DATA
    # ========================================================

    cpu_values = []
    memory_values = []

    for item in reports:

        kode = item["kode"]
        report = item["report"]

        cpu = report["cpu"]["current"]
        memory = report["memory"]["current"]

        if cpu is not None:
            cpu_values.append(
                (kode, cpu)
            )

        if memory is not None:
            memory_values.append(
                (kode, memory)
            )

    cpu_values.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    memory_values.sort(
        key=lambda x: x[1],
        reverse=True,
    )

    # ========================================================
    # TOP CPU
    # ========================================================

    top_cpu_lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "TOP CPU",
        "",
    ]

    for i, (kode, value) in enumerate(
        cpu_values[:3],
        start=1,
    ):
        top_cpu_lines.append(
            f"{i}. INAP {kode} — {value:.2f}%"
        )

    # ========================================================
    # TOP MEMORY
    # ========================================================

    top_memory_lines = [
        "",
        "============",
        # "",
        "TOP MEMORY",
        "",
    ]

    for i, (kode, value) in enumerate(
        memory_values[:3],
        start=1,
    ):
        top_memory_lines.append(
            f"{i}. INAP {kode} — {value:.2f}%"
        )

    # ========================================================
    # ZABBIX
    # ========================================================

    monitored_hosts = get_monitored_hosts()
    total_hosts = len(HOST_MAP)
    monitored_count = len(monitored_hosts)

    zabbix_lines = [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "ZABBIX",
        "",
        "🟢 Server : Running",
        f"🖥️ Hosts  : {monitored_count}/{total_hosts} monitored",
    ]

    # ========================================================
    # ACTIVE PROBLEMS
    # ========================================================

    problems = get_active_problems()

    problems_text = format_active_problems(
        problems
    )

    # ========================================================
    # FINAL
    # ========================================================

    header = (
        "**SUMMARY REPORT**\n\n"
        f"Period: {period_start} - {period_end}\n"
        f"Checked at: {checked_at}\n"
    )

    return (
        header
        + vm_summary
        + "\n".join(top_cpu_lines)
        + "\n".join(top_memory_lines)
        + "\n".join(zabbix_lines)
        + "\n\n"
        + problems_text
    )

def build_global_summary(reports):
    """
    Membuat summary keseluruhan berdasarkan report VM
    yang sudah berhasil digenerate.

    reports:
        [
            (kode, image, report_data),
            ...
        ]
    """

    healthy = 0
    warning = 0
    critical = 0
    na = 0

    cpu_values = []
    memory_values = []

    for kode, image, report in reports:

        cpu = report["cpu"]
        memory = report["memory"]
        disk = report["disk"]

        statuses = []

        for metric in (cpu, memory, disk):
            if metric["current"] is not None:
                statuses.append(metric["status"])

        # =========================
        # VM OVERALL STATUS
        # =========================

        if not statuses:
            na += 1

        elif "critical" in statuses:
            critical += 1

        elif "warning" in statuses:
            warning += 1

        else:
            healthy += 1

        # =========================
        # TOP CPU
        # =========================

        if cpu["current"] is not None:
            cpu_values.append(
                (kode, cpu["current"])
            )

        # =========================
        # TOP MEMORY
        # =========================

        if memory["current"] is not None:
            memory_values.append(
                (kode, memory["current"])
            )

    # =========================
    # SORT TOP UTILIZATION
    # =========================

    cpu_values.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    memory_values.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    return {
        "summary": {
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "na": na,
        },

        "top_cpu": cpu_values[:3],

        "top_memory": memory_values[:3],

        "host_count": len(HOST_MAP),

        "zabbix_status": "Running",
    }

def format_global_summary(global_data):

    summary = global_data["summary"]

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "SUMMARY",
        "",
        f"🟢 Healthy     : {summary['healthy']}",
        f"🟡 Warning     : {summary['warning']}",
        f"🔴 Critical    : {summary['critical']}",
        f"⚪ N/A         : {summary['na']}",
    ]

    # =========================
    # TOP CPU
    # =========================

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "TOP CPU",
        "",
    ])

    for i, (kode, value) in enumerate(
        global_data["top_cpu"],
        start=1,
    ):
        lines.append(f"{i}. INAP {kode} — {value:.2f}%")

    # =========================
    # TOP MEMORY
    # =========================

    lines.extend([
        "",
        "",
        "",
        "",
        "TOP MEMORY",
        "",
    ])

    for i, (kode, value) in enumerate(
        global_data["top_memory"],
        start=1,
    ):
        lines.append(f"{i}. INAP {kode} — {value:.2f}%")

    # =========================
    # ZABBIX
    # =========================

    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━━━",
        "ZABBIX",
        "",
        f"🟢 Server : {global_data['zabbix_status']}",
        f"🖥️ Hosts  : {global_data['host_count']} monitored",
    ])

    return "\n".join(lines)

def format_active_problems(problems: list) -> str:

    if not problems:
        return (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "ACTIVE PROBLEMS\n\n"
            "🟢 No active problems"
        )

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "PROBLEMS",
        "",
    ]

    for problem in problems:

        name = problem.get(
            "name",
            "Unknown problem"
        )

        emoji = problem.get(
            "severity_emoji",
            "⚪"
        )

        duration = problem.get(
            "duration",
            "Unknown"
        )

        hosts = problem.get(
            "hosts",
            []
        )

        # ----------------------------------------------------
        # Problem name
        # ----------------------------------------------------

        lines.append(
            f"{emoji} {name}"
        )

        # ----------------------------------------------------
        # Hosts
        # ----------------------------------------------------

        seen_hosts = set()

        for host in hosts:

            if host in seen_hosts:
                continue

            seen_hosts.add(host)

            lines.append(
                f"   • {host}"
            )

        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        lines.append(
            f"Duration: {duration}"
        )

        lines.append("")

    return "\n".join(
        lines
    ).rstrip()