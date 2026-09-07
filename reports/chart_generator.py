import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# REPORT COLOUR PALLETE
BACKGROUND_COLOR = "#18191D"
GRAPH_COLOR = "#26A726"
TEXT_COLOR = "#E8E9EA"
MUTED_COLOR = "#A5A8AD"
GRID_COLOR = "#4A4D52"

def generate_metric_chart(
    history: list,
    title: str,
    output_path: str,
) -> None:
    """
    generate a monitoring chart dari zabbix historical data.

    history format:
    [
        {
            "timestamp": 1787580729,
            "value": 6.44
        },
        ...
    ]
    """

    if not history:
        raise ValueError(f"ga ada historical data buat {title}.")

    # Convert Unix timestamp -> datetime
    timestamps = [
        datetime.fromtimestamp(point["timestamp"])
        for point in history
    ]

    values = [
        point["value"]
        for point in history
    ]

    # CREATE FIGURE
    fig, ax = plt.subplots(
        figsize=(10, 3),
        dpi=150
    )

    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    #PLOT LINE
    ax.plot(
        timestamps,
        values,
        color=GRAPH_COLOR,
        linewidth=0.8,
    )

    #FILL BELOW GRAPH
    ax.fill_between(
        timestamps,
        values,
        0,
        color=GRAPH_COLOR,
        alpha=0.18,
    )

    #Y AXIS
    ax.set_ylim(0, 100)
    # ax.set_ylabel(
    #     "IN %",
    #     color=TEXT_COLOR,
    #     fontsize=9,
    # )

    # TITLE
    ax.set_title(
        title,
        loc="left",
        color=TEXT_COLOR,
        fontsize=12,
        fontweight="bold",
        pad=10,
    )


    # X AXIS FORMAT

    ax.xaxis.set_major_formatter (
        mdates.DateFormatter("%m-%d %H:%M")
    )

    ax.xaxis.set_major_locator(
        mdates.AutoDateLocator()
    )

    # TICK COLORS
    ax.tick_params (
        axis="x",
        colors=TEXT_COLOR,
        labelsize=8,
    )

    ax.tick_params (
        axis="y",
        colors=TEXT_COLOR,
        labelsize=8,
    )

    # GRID 
    ax.grid (
        True,
        axis="both",
        color=GRID_COLOR,
        alpha=0.35,
        linewidth=0.6,
    )

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


    #REMOVE BORDER TAK GUNA 
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)

    # Layout
    fig.tight_layout()

    # Save
    fig.savefig(
        output_path,
        facecolor=BACKGROUND_COLOR,
        bbox_inches="tight",
    )

    plt.close(fig)