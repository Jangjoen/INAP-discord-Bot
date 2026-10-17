import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from uptime_kuma_api import UptimeKumaApi

load_dotenv()

UPTIME_KUMA_URL = os.getenv("UPTIME_KUMA_URL")
UPTIME_KUMA_USERNAME = os.getenv("UPTIME_KUMA_USERNAME")
UPTIME_KUMA_PASSWORD = os.getenv("UPTIME_KUMA_PASSWORD")

SERVER_TZ = ZoneInfo("Asia/Bangkok")



from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SERVER_TZ = ZoneInfo("Asia/Bangkok")



from datetime import datetime
from zoneinfo import ZoneInfo

SERVER_TZ = ZoneInfo("Asia/Bangkok")


def normalize_history_time(value):
    if not value:
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).strip())
        except (ValueError, TypeError):
            return None

    # Waktu dari API berupa string tanpa timezone.
    # Perlakukan sebagai waktu UTC lalu konversikan ke Bangkok.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))

    return dt.astimezone(SERVER_TZ)




def get_uptime_kuma_report() -> dict:
    if not all([
        UPTIME_KUMA_URL,
        UPTIME_KUMA_USERNAME,
        UPTIME_KUMA_PASSWORD,
    ]):
        raise ValueError("Konfigurasi Uptime Kuma belum lengkap.")

    counts = {
        "UP": 0,
        "DOWN": 0,
        "MAINTENANCE": 0,
        "UNKNOWN": 0,
        "PAUSE": 0,
    }

    with UptimeKumaApi(UPTIME_KUMA_URL) as api:
        api.login(
            UPTIME_KUMA_USERNAME,
            UPTIME_KUMA_PASSWORD,
        )

        # Ambil daftar monitor satu kali.
        monitors = api.get_monitors()

        monitor_names = {
            monitor["id"]: monitor.get("name", "Unknown")
            for monitor in monitors
        }

        # Hitung status monitor.
        for monitor in monitors:
            monitor_id = monitor["id"]

            if (
                not monitor.get("active", True)
                or monitor.get("forceInactive", False)
            ):
                counts["PAUSE"] += 1
                continue

            if monitor.get("maintenance", False) is True:
                counts["MAINTENANCE"] += 1
                continue

            try:
                beats = api.get_monitor_beats(monitor_id, 1)

                if not beats:
                    counts["UNKNOWN"] += 1
                    continue

                latest = max(
                    beats,
                    key=lambda beat: beat.get("time") or "",
                )

                status = latest.get("status")
                status_name = getattr(
                    status, "name", str(status)
                ).upper()

                if status_name in ("UP", "DOWN"):
                    counts[status_name] += 1
                else:
                    counts["UNKNOWN"] += 1

            except Exception as exc:
                print(
                    f"[UPTIME KUMA][ERROR] "
                    f"Monitor {monitor_id}: {exc}"
                )
                counts["UNKNOWN"] += 1

        # Ambil history sekali.
       
       
        
        history = []

        try:
            important_heartbeats = api.get_important_heartbeats()

            for monitor_id, beats in important_heartbeats.items():
                try:
                    monitor_id = int(monitor_id)
                except (TypeError, ValueError):
                    continue

                monitor_name = monitor_names.get(
                    monitor_id, "Unknown"
                )

                for beat in beats or []:
                    status = beat.get("status")
                    status_name = getattr(
                        status, "name", str(status)
                    ).upper()

                    if status_name not in ("UP", "DOWN"):
                        continue

                    beat_time = normalize_history_time(
                        beat.get("time")
                    )

                    if beat_time is None:
                        continue

                    history.append({
                        "monitor_name": monitor_name,
                        "status": status_name,
                        "time": beat_time,
                        "message": (
                            beat.get("msg") or "Tidak ada pesan"
                        ),
                    })

        except Exception as exc:
            print(f"[UPTIME KUMA][HISTORY][ERROR] {exc}")

        history.sort(
            key=lambda item: item["time"],
            reverse=True,
        )

        history = history[:12]

        print(
            f"[UPTIME KUMA] History berhasil diambil: "
            f"{len(history)} kejadian"
        )




    return {
        "checked_at": datetime.now(SERVER_TZ),
        "total_services": len(monitors),
        "counts": counts,
        "history": history,
    }
