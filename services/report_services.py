from io import BytesIO

from config import HOST_MAP
from services.zabbix_service import get_vm_report_data
from reports.report_generator import generate_vm_report


def generate_vm_report_image(
    kode: str,
    hours: int = 2,
) -> dict:
    """
    Ambil data Zabbix dan generate image report untuk 1 VM.
    """

    if kode not in HOST_MAP:
        raise ValueError(
            f"VM '{kode}' tidak ditemukan di HOST_MAP"
        )

    # =========================
    # AMBIL DATA ZABBIX
    # =========================

    report = get_vm_report_data(
        kode,
        hours=hours,
    )

    # =========================
    # GENERATE IMAGE
    # =========================

    image = generate_vm_report(
        report=report,
    )

    return {
        "kode": kode,
        "report": report,
        "image": image,
    }


def generate_all_vm_reports(
    hours: int = 2,
) -> list[dict]:
    """
    Generate report untuk seluruh VM di HOST_MAP.
    """

    generated_reports = []

    for kode in HOST_MAP:

        try:
            print(
                f"[REPORT] generating vm {kode}...."
            )

            result = generate_vm_report_image(
                kode=kode,
                hours=hours,
            )

            generated_reports.append(
                result
            )

            print(
                f"[REPORT] VM {kode} selesai"
            )

        except Exception as e:

            print(
                f"[REPORT][ERROR]"
                f"VM {kode}: {e}"
            )

    return generated_reports


def build_report_summary(
    reports: list[dict],
) -> str:
    """
    Menghitung status keseluruhan setiap VM.
    """

    healthy = 0
    unavailable = 0
    warning_items = []
    critical_items = []

    for item in reports:

        report = item["report"]
        kode = item.get("kode", report.get("kode", "Unknown"))

        statuses = []

        for metric, label in [
            ("cpu", "CPU"),
            ("memory", "Memory"),
            ("disk", "Disk"),
        ]:

            data = report.get(metric)

            if not data:
                continue

            status = data.get("status")

            if status is not None:
                normalized_status = status.lower()
                statuses.append(normalized_status)

                current = data.get("current")
                percentage = (
                    f"{current:.0f}%"
                    if current is not None
                    else "N/A"
                )
                item_text = f"- {label} INAP {kode} - {percentage}"

                if normalized_status == "warning":
                    warning_items.append(item_text)
                elif normalized_status == "critical":
                    critical_items.append(item_text)

        # =========================
        # STATUS VM
        # =========================

        if not statuses:

            unavailable += 1

        elif "critical" in statuses:

            continue

        elif "warning" in statuses:

            continue

        else:

            healthy += 1

    warning_list = "\n".join(warning_items) or "-"
    critical_list = "\n".join(critical_items) or "-"

    return (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "SUMMARY\n\n"
        f"🟢 Healthy     : {healthy}\n\n"
        f"🟡 Warning     : {len(warning_items)}\n"
        f"{warning_list}\n\n"
        f"🔴 Critical    : {len(critical_items)}\n"
        f"{critical_list}\n\n"
        f"⚪ N/A         : {unavailable}"
    )