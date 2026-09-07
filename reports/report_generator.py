import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import io 
from io import BytesIO


# ============================================================
# COLOR PALETTE
# ============================================================

BACKGROUND_COLOR = "#18191D"
GRAPH_BACKGROUND = "#242528"

GRAPH_COLOR = "#238B23"
TEXT_COLOR = "#E8E9EA"
MUTED_COLOR = "#A5A8AD"
GRID_COLOR = "#4A4D52"

HEADER_COLOR = "#60777C"

HEALTHY_COLOR = "#3FB950"
WARNING_COLOR = "#D29922"
CRITICAL_COLOR = "#F85149"


#  # ASSETS
# ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# def find_asset(name: str) -> Path:
#     """
#     Find an asset by filename without requiring a specific extension.
#     """

#     matches = list(ASSETS_DIR.glob(f"{name}.*"))

#     if not matches:
#         raise FileNotFoundError(
#             f"Asset tidak ditemukan: {ASSETS_DIR / name}"
#         )

#     return matches[0]

# METRIC_ICONS = {
#     "CPU": "desktop-icon 3",
#     "Memory": "memory-icon 3",
#     "Disk": "disk-icon 3",
# }

# def add_metric_icon(
#     ax,
#     metric_name: str,
#     x: float,
#     y: float,
#     zoom: float = 0.05,
# ):
#     asset_name = METRIC_ICONS.get(metric_name)

#     if not asset_name:
#         return

#     try:
#         asset_path = find_asset(asset_name)

#         image = mpimg.imread(asset_path)

#         icon = OffsetImage(
#             image,
#             zoom=0.35,
#         )

#         annotation = AnnotationBbox(
#             icon,
#             (x, y),
#             xycoords="axes fraction",
#             frameon=False,
#             box_alignment=(0.5, 0.5),
#             pad=0,
#         )

#         ax.add_artist(annotation)

#     except FileNotFoundError as e:
#         print(f"[WARNING] {e}")

# ============================================================
# STATUS
# ============================================================

def get_status_color(status: str) -> str:
    status_upper = status.upper()

    if "CRITICAL" in status_upper or "SEKARAT" in status_upper:
        return CRITICAL_COLOR

    if "WARNING" in status_upper or "PERINGATAN" in status_upper:
        return WARNING_COLOR

    return HEALTHY_COLOR


def get_status_text(status: str) -> str:
    status_upper = status.upper()

    if "CRITICAL" in status_upper or "SEKARAT" in status_upper:
        return "CRITICAL!"

    if "WARNING" in status_upper or "PERINGATAN" in status_upper:
        return "WARNING!"

    return "HEALTHY"


# ============================================================
# GRAPH
# ============================================================

def draw_metric_chart(
    ax,
    history: list,
    title: str,
):
    if not history:
        ax.text(
            0.5,
            0.5,
            "No data",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color=MUTED_COLOR,
        )
        return

    timestamps = [
        datetime.fromtimestamp(point["timestamp"])
        for point in history
    ]

    values = [
        point["value"]
        for point in history
    ]

    # Background
    ax.set_facecolor(GRAPH_BACKGROUND)

    # Main line
    ax.plot(
        timestamps,
        values,
        color=GRAPH_COLOR,
        linewidth=1.2,
        zorder=3,
    )

    # Filled area
    ax.fill_between(
        timestamps,
        values,
        0,
        color=GRAPH_COLOR,
        alpha=0.18,
        zorder=1,
    )

    # Y axis
    ax.set_ylim(0, 110)
    ax.margins(x=0.025)

    # Title
    ax.set_title(
        title,
        loc="left",
        color=TEXT_COLOR,
        fontsize=11,
        fontweight="bold",
        pad=8,
    )

    # X axis
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%H:%M")
    )

    ax.xaxis.set_major_locator(
        mdates.AutoDateLocator()
    )

    # Ticks
    ax.tick_params(
        axis="x",
        colors=MUTED_COLOR,
        labelsize=8,
        width=0.5,
    )

    ax.tick_params(
        axis="y",
        colors=MUTED_COLOR,
        labelsize=8,
        width=0.5,
    )

    # Grid
    ax.grid(
        True,
        color=GRID_COLOR,
        alpha=0.30,
        linewidth=0.5,
        linestyle="--",
        zorder=0,
    )

    # Borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)

    ax.spines["left"].set_linewidth(0.5)
    ax.spines["bottom"].set_linewidth(0.5)

    # =========================
    # IMPORTANT POINTS
    # =========================

    top_count = 3

    top_indices = sorted(
        range(len(values)),
        key=lambda i: values[i],
        reverse=True
    )[:top_count]

    last_index = len(values) - 1

    important_indices = set(top_indices)
    important_indices.add(last_index)


    # =========================
    # FILTER
    # =========================

    VALUE_DIFF_THRESHOLD = 1.0
    TIME_DIFF_THRESHOLD = 300  # 5 menit


    # Kandidat diproses dari nilai tertinggi
    candidates = sorted(
        important_indices,
        key=lambda i: values[i],
        reverse=True,
    )

    display_indices = []


    for index in candidates:

        # Titik pertama pasti masuk
        if not display_indices:
            display_indices.append(index)
            continue

        should_skip = False

        for accepted_index in display_indices:

            value_difference = abs(
                values[index] - values[accepted_index]
            )

            time_difference = abs(
                (timestamps[index] - timestamps[accepted_index]).total_seconds()
            )

            # -----------------------------------------
            # 1. Nilai terlalu mirip
            # -----------------------------------------

            if value_difference <= VALUE_DIFF_THRESHOLD:
                should_skip = True
                break

            # -----------------------------------------
            # 2. Waktu terlalu dekat
            # -----------------------------------------

            if time_difference <= TIME_DIFF_THRESHOLD:
                should_skip = True
                break

        if not should_skip:
            display_indices.append(index)


    # Kembalikan urutan berdasarkan waktu
    display_indices.sort()


    # --------------------------------------------------------
    # Marker + Value
    # --------------------------------------------------------

    offsets = [
        (0, 9),
        (0, 18),
        (0, -9),
        (12, 9),
        (-12, 9),
    ]

    for i, index in enumerate(display_indices):

        x = timestamps[index]
        y = values[index]

        ax.scatter(
            x,
            y,
            s=24,
            facecolor=TEXT_COLOR,
            edgecolor=GRAPH_COLOR,
            linewidth=1.2,
            zorder=5,
        )

        dx, dy = offsets[i % len(offsets)]

        ax.annotate(
            f"{y:.2f}",
            xy=(x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=MUTED_COLOR,
            fontsize=8,
            fontweight="normal",
            zorder=6,
        )


# ============================================================
# REPORT GENERATOR
# ============================================================

def generate_vm_report(
    report: dict
    # output_path: str,
):
    checked_at_text = datetime.fromtimestamp(
            report["checked_at"]
        ).strftime("%d/%m/%Y %H:%M:%S")

    kode = report["kode"]

    cpu = report["cpu"]
    memory = report["memory"]
    disk = report["disk"]

    period_start = report["period"]["start"]
    period_end = report["period"]["end"]

    checked_at = report["checked_at"]

    # ========================================================
    # FIGURE
    # ========================================================

    fig = plt.figure(
        figsize=(16, 8),
        dpi=120,
        facecolor=BACKGROUND_COLOR,
    )

    fig.subplots_adjust(
        left=0.055,
        right=0.985,
        top=0.965,
        bottom=0.055,
    )

    grid = fig.add_gridspec(
        1,
        2,
        width_ratios=[3.6, 1.0],
        wspace=0.025,
    )
    
    # ========================================================
    # LEFT SIDE - GRAPHS
    # ========================================================

    graph_grid = grid[0, 0].subgridspec(
        3,
        1,
        hspace=0.37,
    )

    ax_cpu = fig.add_subplot(graph_grid[0])
    ax_memory = fig.add_subplot(graph_grid[1])
    ax_disk = fig.add_subplot(graph_grid[2])

    # ========================================================
    # CPU
    # ========================================================

    draw_metric_chart(
        ax_cpu,
        cpu["history"],
        "CPU UTILIZATION",
    )

    # ========================================================
    # MEMORY
    # ========================================================

    draw_metric_chart(
        ax_memory,
        memory["history"],
        "MEMORY UTILIZATION",
    )

    # ========================================================
    # DISK
    # ========================================================

    if disk["history"]:

        draw_metric_chart(
            ax_disk,
            disk["history"],
            "DISK UTILIZATION",
        )

    else:
        # Bersihkan area supaya tidak kotak putih
        ax_disk.set_facecolor(BACKGROUND_COLOR)
        ax_disk.set_xticks([])
        ax_disk.set_yticks([])

        for spine in ax_disk.spines.values():
            spine.set_visible(False)

        ax_disk.text(
            0.0,
            1.02,
            "DISK UTILIZATION",
            transform=ax_disk.transAxes,
            ha="left",
            va="bottom",
            color=TEXT_COLOR,
            fontsize=14,
            fontweight="bold",
        )

        ax_disk.text(
            0.5,
            0.5,
            "NO DATA AVAILABLE",
            transform=ax_disk.transAxes,
            ha="center",
            va="center",
            color=MUTED_COLOR,
            fontsize=18,
            fontweight="bold",
        )


    # ========================================================
    # RIGHT SIDE - SUMMARY
    # ========================================================

    ax_panel = fig.add_subplot(grid[0, 1])

    ax_panel.set_facecolor(BACKGROUND_COLOR)
    ax_panel.set_xlim(0, 1)
    ax_panel.set_ylim(0, 1)

    ax_panel.axis("off")

    # Header
    ax_panel.add_patch(
        plt.Rectangle(
            (0, 0.88),
            1,
            0.12,
            transform=ax_panel.transAxes,
            facecolor=HEADER_COLOR,
            edgecolor="none",
        )
    )

    ax_panel.text(
        0.08,
        0.94,
        f"INAP {kode}",
        transform=ax_panel.transAxes,
        ha="left",
        va="center",
        color=TEXT_COLOR,
        fontsize=20,
        fontweight="bold",
    )

    # ========================================================
    # DISK CHART
    # ========================================================

    # ax_disk = fig.add_subplot(grid[0, 0])

    # if disk["history"]:

    #     draw_metric_chart(
    #         ax_disk,
    #         disk["history"],
    #         "DISK UTILIZATION",
    #     )

    # else:

    #     ax_disk.set_facecolor(BACKGROUND_COLOR)

    #     ax_disk.set_xticks([])
    #     ax_disk.set_yticks([])

    #     for spine in ax_disk.spines.values():
    #         spine.set_visible(False)

    #     ax_disk.text(
    #         0.0,
    #         1.02,
    #         "DISK UTILIZATION",
    #         transform=ax_disk.transAxes,
    #         ha="left",
    #         va="bottom",
    #         color=TEXT_COLOR,
    #         fontsize=14,
    #         fontweight="bold",
    #     )

    # ========================================================
    # METRIC SUMMARY
    # ========================================================

    metrics = [
        ("CPU", cpu),
        ("Memory", memory),
        ("Disk", disk),
    ]

    y_positions = [0.80, 0.60, 0.40]

    for (name, data), y in zip(metrics, y_positions):

        # =========================
        # CEK DATA
        # =========================

        if data["current"] is None:

            value_text = "N/A"
            status_text = "NOT AVAILABLE"
            status_color = "#777777"

        else:

            value_text = f'{data["current"]:.2f} %'
            status_color = get_status_color(data["status"])
            status_text = get_status_text(data["status"])

        # ====================================================
        # METRIC NAME
        # ====================================================

        ax_panel.text(
            0.10,
            y,
            name,
            transform=ax_panel.transAxes,
            ha="left",
            va="center",
            color=TEXT_COLOR,
            fontsize=16,
            fontweight="normal",
        )

        # ====================================================
        # CURRENT VALUE
        # ====================================================

        ax_panel.text(
            0.10,
            y - 0.055,
            value_text,
            transform=ax_panel.transAxes,
            ha="left",
            va="center",
            color=TEXT_COLOR,
            fontsize=22,
            fontweight="bold",
        )

        # ====================================================
        # STATUS DOT
        # ====================================================

        ax_panel.scatter(
            0.135,
            y - 0.105,
            s=220,
            color=status_color,
            transform=ax_panel.transAxes,
            zorder=5,
        )

        # ====================================================
        # STATUS TEXT
        # ====================================================

        ax_panel.text(
            0.21,
            y - 0.108,
            status_text,
            transform=ax_panel.transAxes,
            ha="left",
            va="center",
            color=TEXT_COLOR,
            fontsize=10,
            fontweight="bold",
        )

    # ========================================================
    # DIVIDER
    # ========================================================

    ax_panel.plot(
        [0.08, 0.92],
        [0.24, 0.24],
        transform=ax_panel.transAxes,
        color=GRID_COLOR,
        linewidth=0.8,
    )

    # ========================================================
    # PERIOD
    # ========================================================

    if period_start and period_end:

        start_dt = datetime.fromtimestamp(period_start)
        end_dt = datetime.fromtimestamp(period_end)

        period_text = (
            f"{start_dt.strftime('%H:%M:%S')}"
            f" - "
            f"{end_dt.strftime('%H:%M:%S')}"
        )

    else:
        period_text = "-"

    ax_panel.text(
        0.10,
        0.195,
        "Report period :",
        transform=ax_panel.transAxes,
        ha="left",
        va="center",
        color=TEXT_COLOR,
        fontsize=12,
        fontweight="bold",
    )

    ax_panel.text(
        0.10,
        0.145,
        period_text,
        transform=ax_panel.transAxes,
        ha="left",
        va="center",
        color=MUTED_COLOR,
        fontsize=10,
    )

    # ========================================================
    # CHECKED AT
    # ========================================================

    ax_panel.text(
        0.10,
        0.085,
        "Checked at :",
        transform=ax_panel.transAxes,
        ha="left",
        va="center",
        color=TEXT_COLOR,
        fontsize=12,
        fontweight="bold",
    )

    ax_panel.text(
        0.10,
        0.035,
        checked_at_text,
        transform=ax_panel.transAxes,
        ha="left",
        va="center",
        color=MUTED_COLOR,
        fontsize=10,
    )

    # ========================================================
    # SAVE
    # ========================================================

    # fig.savefig(  
    #     output_path,
    #     facecolor=BACKGROUND_COLOR,
    #     bbox_inches="tight",
    #     pad_inches=0,
    # )

    # plt.close(fig) 

    buffer = BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=120,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    buffer.seek(0)

    return buffer