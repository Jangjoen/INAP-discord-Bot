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
    warning = 0
    critical = 0
    unavailable = 0

    for item in reports:

        report = item["report"]

        statuses = []

        for metric in [
            "cpu",
            "memory",
            "disk",
        ]:

            data = report.get(metric)

            if not data:
                continue

            status = data.get("status")

            if status is not None:
                statuses.append(
                    status.lower()
                )

        # =========================
        # STATUS VM
        # =========================

        if not statuses:

            unavailable += 1

        elif "critical" in statuses:

            critical += 1

        elif "warning" in statuses:

            warning += 1

        else:

            healthy += 1

    return (
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "SUMMARY\n\n"
        f"🟢 Healthy     : {healthy}\n"
        f"🟡 Warning     : {warning}\n"
        f"🔴 Critical    : {critical}\n"
        f"⚪ N/A         : {unavailable}"
    )