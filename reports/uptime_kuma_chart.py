
from io import BytesIO

from datetime import datetime
from zoneinfo import ZoneInfo

SERVER_TZ = ZoneInfo("Asia/Bangkok")

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


BACKGROUND = "#0D1117"
PANEL = "#15191E"
TEXT = "#F0F3F6"
MUTED = "#A5B4C8"
LINE = "#343A40"

COLORS = {
    "UP": "#5BDA82",
    "DOWN": "#DC3545",
    "MAINTENANCE": "#1742DB",
    "PAUSE": "#6C7577",
}



def format_history_time(value) -> str:
    if not value:
        return "-"

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)



def generate_uptime_kuma_chart(report: dict) -> BytesIO:
    counts = report["counts"]
    history = report.get("history", [])[:12]

    checked_at = report["checked_at"].strftime(
        "%d/%m/%Y %H:%M:%S %Z"
    )

    # ==========================================
    # LAYOUT UTAMA
    # ==========================================
    width = 14
    height = 11.8
    dpi = 160

    fig, ax = plt.subplots(
        figsize=(width, height),
        dpi=dpi,
    )

    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.axis("off")

    # Panel utama
    outer_panel = FancyBboxPatch(
        (0.12, 0.12),
        width - 0.24,
        height - 0.24,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        facecolor=BACKGROUND,
        edgecolor="#24364B",
        linewidth=1.2,
    )
    ax.add_patch(outer_panel)

    # ==========================================
    # HEADER
    # ==========================================
    ax.text(
        0.55, 10.75,
        "UPTIME KUMA | INAP",
        fontsize=22,
        fontweight="bold",
        color=TEXT,
        va="center",
    )

    ax.text(
        13.45, 10.75,
        f"Checked at: {checked_at}",
        fontsize=8.5,
        color=MUTED,
        ha="right",
        va="center",
    )

    # ==========================================
    # STATISTIK
    # ==========================================
    metrics = [
        ("Up", counts["UP"], COLORS["UP"]),
        ("Down", counts["DOWN"], COLORS["DOWN"]),
        (
            "Maintenance",
            counts["MAINTENANCE"],
            COLORS["MAINTENANCE"],
        ),
        ("Pause", counts["PAUSE"], COLORS["PAUSE"]),
    ]

    positions = [1.8, 4.9, 8.0, 11.1]

    for (label, value, color), x in zip(
        metrics, positions
    ):
        ax.text(
            x, 9.35,
            label,
            fontsize=23,
            color=TEXT,
            fontweight="700",
            ha="center",
            va="center",
        )

        ax.text(
            x, 8.35,
            f"{value:,}",
            fontsize=32,
            color=color,
            fontweight="bold",
            ha="center",
            va="center",
        )

    # ==========================================
    # PANEL HISTORY
    # ==========================================
    panel_left = 0.30
    panel_bottom = 0.30
    panel_width = 13.40
    panel_top = 7.35
    panel_height = panel_top - panel_bottom

    table_panel = FancyBboxPatch(
        (panel_left, panel_bottom),
        panel_width,
        panel_height,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        facecolor=PANEL,
        edgecolor=PANEL,
        linewidth=0,
    )
    ax.add_patch(table_panel)

    ax.text(
        0.70, 6.95,
        "HISTORY",
        fontsize=15,
        fontweight="bold",
        color=TEXT,
        va="center",
    )

    # ==========================================
    # HEADER KOLOM
    # ==========================================
    columns = [
        ("NAME", 0.70),
        ("STATUS", 5.25),
        ("DATETIME", 7.10),
        ("MESSAGE", 9.65),
    ]

    header_y = 6.30

    for label, x in columns:
        ax.text(
            x, header_y,
            label,
            fontsize=9.5,
            fontweight="bold",
            color=MUTED,
            va="center",
        )

    header_line_y = 5.95

    ax.plot(
        [0.60, 13.40],
        [header_line_y, header_line_y],
        color=LINE,
        linewidth=0.8,
    )

    # ==========================================
    # BARIS HISTORY
    # ==========================================
    row_start_y = 5.55
    row_gap = 0.43

    badge_height = 0.26
    badge_width = 0.85

    for index, item in enumerate(history):
        y = row_start_y - index * row_gap

        name = str(
            item.get("monitor_name", "Unknown")
        )
        status = str(
            item.get("status", "UNKNOWN")
        ).upper()
        timestamp = format_history_time(item.get("time"))
        message = str(
            item.get("message") or "Tidak ada pesan"
        )

        # Batasi teks agar tidak masuk ke kolom lain.
        if len(name) > 36:
            name = name[:33] + "..."

        if len(timestamp) > 23:
            timestamp = timestamp[:23]

        if len(message) > 40:
            message = message[:37] + "..."

        # Nama monitor
        ax.text(
            0.70, y,
            name,
            fontsize=8.5,
            color=TEXT,
            va="center",
        )

        # Badge status
        status_color = COLORS.get(status, MUTED)

        if status not in ("UP", "DOWN"):
            badge_width = 1.30
        else:
            badge_width = 0.75

        badge = FancyBboxPatch(
            (5.25, y - badge_height / 2),
            badge_width,
            badge_height,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=status_color,
            edgecolor=status_color,
            linewidth=0,
        )
        ax.add_patch(badge)

        ax.text(
            5.25 + badge_width / 2,
            y,
            status,
            ha="center",
            va="center",
            fontsize=9,
            color="white" if status == "DOWN" else "black",
            fontweight="bold",
        )

        # Waktu
        ax.text(
            7.10, y,
            timestamp,
            fontsize=8,
            color=MUTED,
            va="center",
        )

        # Pesan
        ax.text(
            9.65, y,
            message,
            fontsize=8.5,
            color=TEXT,
            va="center",
        )

        # Garis pemisah antarbaris
        separator_y = y - row_gap / 2

        ax.plot(
            [0.60, 13.40],
            [separator_y, separator_y],
            color=LINE,
            linewidth=0.45,
        )

    # ==========================================
    # EXPORT KE MEMORY
    # ==========================================
    fig.subplots_adjust(
        left=0,
        right=1,
        top=1,
        bottom=0,
    )

    image_buffer = BytesIO()

    fig.savefig(
        image_buffer,
        format="png",
        dpi=dpi,
        facecolor=BACKGROUND,
        pad_inches=0,
    )

    plt.close(fig)
    image_buffer.seek(0)

    return image_buffer
