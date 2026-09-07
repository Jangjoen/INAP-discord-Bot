import requests
# from datetime import datetime
import datetime
import logging
from config import HOST_MAP, ZABBIX_AUTH, ZABBIX_URL, ITEMIDS_CPU_MAP, ITEMIDS_MEMORY_MAP, ITEMIDS_DISK_MAP, DISK_HOST_MAP
from config import (
    CPU_WARNING_THRESHOLD,
    CPU_CRITICAL_THRESHOLD,
    MEMORY_WARNING_THRESHOLD,
    MEMORY_CRITICAL_THRESHOLD,
    DISK_WARNING_THRESHOLD,
    DISK_CRITICAL_THRESHOLD,
)



logger = logging.getLogger(__name__)


def cpu_status(value):
    """Determine CPU status emoji based on utilization percentage"""
    if value >= 85:
        return "🔴 SEKARAT"
    if value >= 70:
        return "🟡 AWAS AJA"
    return "🟢 SEHAT"


def memory_status(value):
    """Determine Memory status emoji based on utilization percentage"""
    if value >= 90:
        return "🔴 SEKARAT"
    if value >= 80:
        return "🟡 AWAS AJA"
    return "🟢 SEHAT"


def disk_status(value):
    """Determine Disk status emoji based on utilization percentage"""
    if value >= 90:
        return "🔴 SEKARAT"
    if value >= 75:
        return "🟡 AWAS AJA"
    return "🟢 SEKARAT"


def get_host_item(hostid: str, search_name: str) -> dict:
    """Query Zabbix for a specific item on a host"""
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name", "value_type", "lastvalue"],
            "hostids": hostid,
            "search": {"name": search_name}
        },
        "auth": ZABBIX_AUTH,
        "id": 2
    }
    
    try:
        response = requests.post(ZABBIX_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data and len(data["result"]) > 0:
            return data["result"][0]
        return None
    except requests.exceptions.ConnectionError:
        logger.exception("Koneksi Zabbix gagal")
        raise Exception("⚠️ Koneksi monitoring terputus. Periksa VPN dan tunnel.")
    except requests.exceptions.Timeout:
        logger.exception("Timeout koneksi Zabbix")
        raise Exception("⚠️ Server monitoring tidak merespons dalam 10 detik.")
    except requests.exceptions.RequestException as e:
        logger.exception("Request Zabbix gagal")
        raise Exception("⚠️ Gagal menghubungi server monitoring.")
    except Exception as e:
        logger.exception("Error tidak terduga saat query Zabbix")
        raise Exception("⚠️ Error tidak terduga saat query Zabbix.")


def get_cpu_data(kode: str) -> dict:
    """Get CPU data for a specific host code"""
    hostid = HOST_MAP.get(kode)
    
    if not hostid:
        raise ValueError(f"Kode {kode} tidak ditemukan dalam mapping.")
    
    item = get_host_item(hostid, "CPU Utilization")
    
    if not item:
        raise ValueError(f"Data CPU untuk host {kode} tidak ditemukan.")
    
    value = float(item["lastvalue"])
    return {
        "kode": kode,
        "value": value,
        "status": cpu_status(value),
        "item_name": item["name"],
        "checked_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }


def get_memory_data(kode: str) -> dict:
    """Get Memory data for a specific host code"""
    hostid = HOST_MAP.get(kode)
    
    if not hostid:
        raise ValueError(f"Kode {kode} tidak ditemukan dalam mapping.")
    
    item = get_host_item(hostid, "Memory Utilization")
    
    if not item:
        raise ValueError(f"Data Memory untuk host {kode} tidak ditemukan.")
    
    value = float(item["lastvalue"])
    return {
        "kode": kode,
        "value": value,
        "status": memory_status(value),
        "item_name": item["name"],
        "checked_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }


def get_disk_data(kode: str) -> dict:
    """Get Disk data for a specific host code"""
    hostid = DISK_HOST_MAP.get(kode)
    
    if not hostid:
        raise ValueError(f"Kode {kode} tidak ditemukan dalam DISK_HOST_MAP.")
    
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name", "value_type", "lastvalue", "hostid"],
            "hostids": hostid,
            "search": {"name": "Space utilization"}
        },
        "auth": ZABBIX_AUTH,
        "id": 2
    }
    
    try:
        response = requests.post(ZABBIX_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data and len(data["result"]) > 0:
            # Filter untuk /data atau /data-first item
            target_item = next(
                (item for item in data["result"]
                 if item["name"] in ["/data: Space utilization", "/data-first: Space utilization"]),
                None
            )
            
            if target_item:
                value = float(target_item["lastvalue"])
                return {
                    "kode": kode,
                    "value": value,
                    "status": disk_status(value),
                    "item_name": target_item["name"],
                    "checked_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
            else:
                raise ValueError(f"Tidak ada item /data atau /data-first ditemukan untuk host {kode}.")
        else:
            raise ValueError(f"Data Disk untuk host {kode} tidak ditemukan.")
    except requests.exceptions.ConnectionError:
        logger.exception("Koneksi Zabbix gagal")
        raise Exception("⚠️ Koneksi monitoring terputus. Periksa VPN dan tunnel.")
    except requests.exceptions.Timeout:
        logger.exception("Timeout koneksi Zabbix")
        raise Exception("⚠️ Server monitoring tidak merespons dalam 10 detik.")
    except requests.exceptions.RequestException as e:
        logger.exception("Request Zabbix gagal")
        raise Exception("⚠️ Gagal menghubungi server monitoring.")
    except Exception as e:
        if "tidak ditemukan" in str(e) or "tidak ada" in str(e).lower():
            raise
        logger.exception("Error tidak terduga saat query Zabbix")
        raise Exception("⚠️ Error tidak terduka saat query Zabbix.")


def get_all_cpu_data() -> list:
    """Get CPU data for all hosts"""
    results = []
    for kode in HOST_MAP.keys():
        try:
            data = get_cpu_data(kode)
            results.append(data)
        except Exception as e:
            logger.warning(f"Failed to get CPU data for {kode}: {str(e)}")
            results.append({
                "kode": kode,
                "value": None,
                "status": "❌ ERROR",
                "error": str(e)
            })
    return results


def get_all_memory_data() -> list:
    """Get Memory data for all hosts"""
    results = []
    for kode in HOST_MAP.keys():
        try:
            data = get_memory_data(kode)
            results.append(data)
        except Exception as e:
            logger.warning(f"Failed to get Memory data for {kode}: {str(e)}")
            results.append({
                "kode": kode,
                "value": None,
                "status": "❌ ERROR",
                "error": str(e)
            })
    return results


def get_all_disk_data() -> list:
    """Get Disk data for all hosts"""
    results = []
    for kode in DISK_HOST_MAP.keys():
        try:
            data = get_disk_data(kode)
            results.append(data)
        except Exception as e:
            logger.warning(f"Failed to get Disk data for {kode}: {str(e)}")
            results.append({
                "kode": kode,
                "value": None,
                "status": "❌ ERROR",
                "error": str(e)
            })
    return results

# -------------------------------------------------

def get_item_history(itemid: str, hours: int, limit: int = 2) -> list:

    now = int(datetime.datetime.now().timestamp())
    time_from = now - (hours * 60 * 60)  # Convert hours to seconds

    item_payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid", "name", "value_type"],
            "itemids": [itemid],
        },
        "auth": ZABBIX_AUTH,
        "id": 2,
    }   

    try:
        response = requests.post(
            ZABBIX_URL,
            json=item_payload,
            timeout=10
        )
        response.raise_for_status()

        item_data = response.json()

        if "error" in item_data:
            raise Exception(item_data["error"].get("data", "Zabbix API error"))

        if not item_data:
            raise ValueError(f"Item dengan ID {itemid} tidak ditemukan di Zabbix.")

        value_type = int(item_data["result"][0]["value_type"])

        # History API expects the history type:
        # 0 = float
        # 3 = unsigned integer
        if value_type not in (0, 3): 
            raise ValueError(f"item {itemid} memiliki value_type {value_type} yang tidak didukung")
        
        # print("NOW:", now)
        # print("TIME FROM:", time_from)

        # print("NOW HUMAN:", datetime.datetime.fromtimestamp(now))
        # print("FROM HUMAN:", datetime.datetime.fromtimestamp(time_from))


        history_payload = {
            "jsonrpc": "2.0",
            "method": "history.get",
            "params": {
                "output": ["clock", "value"],
                "history": value_type,
                "itemids": [itemid],
                "sortfield": "clock",
                "sortorder": "ASC",
                "time_from": time_from,
                "time_till": now,
                "limit": 1000,
            },
            "auth": ZABBIX_AUTH,
            "id": 2,
        }

        response = requests.post(ZABBIX_URL, json=history_payload, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise Exception(data["error"].get("data", "Zabbix API error"))

        result = []

        raw_result = data.get("result", [])

        # print("\n===== ZABBIX HISTORY DEBUG =====")
        # print("Item ID:", itemid)
        # print("Value type:", value_type)
        # print("Result type:", type(raw_result))
        # print("Result sample:", repr(raw_result)[:3000])
        # print("================================\n")

        result = []

        for point in raw_result:
            # print("POINT TYPE:", type(point))
            # print("POINT:", repr(point))

            result.append({
                "timestamp": int(point["clock"]),
                "value": float(point["value"]),
            })

        return result

    except requests.exceptions.ConnectionError:
        logger.exception("Koneksi Zabbix gagal")
        raise Exception("⚠️ Koneksi monitoring terputus. Periksa VPN dan tunnel.")

    except requests.exceptions.Timeout:
        logger.exception("Timeout koneksi Zabbix")
        raise Exception("⚠️ Server monitoring tidak merespons dalam 10 detik.")

    except requests.exceptions.RequestException:
        logger.exception("Request Zabbix gagal")
        raise Exception("⚠️ Gagal menghubungi server monitoring.")

    except Exception as e:
        logger.exception("Error tidak terduga saat query Zabbix")
        raise Exception(f"⚠️ Error tidak terduga saat query Zabbix: {str(e)}")

def get_cpu_history(kode: str, hours: int = 2) -> list:
    """Get CPU history for a specific host code"""

    itemid = ITEMIDS_CPU_MAP.get(kode)
    
    if not itemid:
        raise ValueError(f"Kode {kode} tidak ditemukan dalam ITEMIDS_CPU_MAP.")
    
    return get_item_history(itemid, hours)

def get_memory_history(kode: str, hours: int = 2) -> list:
    """Get Memory history for a specific host code"""

    itemid = ITEMIDS_MEMORY_MAP.get(kode)
    
    if not itemid:
        raise ValueError(f"Kode {kode} tidak ditemukan dalam ITEMIDS_MEMORY_MAP.")
    
    return get_item_history(itemid, hours)

def get_disk_history(kode: str, hours: int = 2) -> list:
    """get Disk history for a specific host code"""

    itemid = ITEMIDS_DISK_MAP.get(kode)

    # if not itemid:
    #     raise ValueError(f"Kode {kode} tidak ditemukan dalam ITEMIDS_DISK_MAP.")

    if not itemid:
        return []

    return get_item_history(itemid, hours)

def get_vm_report_data(kode, hours=2):

    # CPU
    cpu = get_cpu_history(
        kode,
        hours=hours,
    )

    cpu_current = (
        cpu[-1]["value"]
        if cpu
        else None
    )

    # MEMORY
    memory = get_memory_history(
        kode,
        hours=hours,
    )

    memory_current = (
        memory[-1]["value"]
        if memory
        else None
    )

    # DISK  
    disk = get_disk_history(
        kode,
        hours=hours,
    )

    disk_current = (
        disk[-1]["value"]
        if disk
        else None
    )

    # REPORT PERIOD
    all_histories = [
        cpu,
        memory,
        disk,
    ]

    timestamps = [
        point["timestamp"]
        for history in all_histories
        for point in history
    ]

    if timestamps:
        period_start = min(timestamps)
        period_end = max(timestamps)
    else:
        period_start = None
        period_end = None

    # CHECKED AT
    import time

    checked_at = int(time.time())

    # STATUS
    cpu_status = get_metric_status(
        cpu_current,
        CPU_WARNING_THRESHOLD,
        CPU_CRITICAL_THRESHOLD,
    )

    memory_status = get_metric_status(
        memory_current,
        MEMORY_WARNING_THRESHOLD,
        MEMORY_CRITICAL_THRESHOLD,
    )

    disk_status = get_metric_status(
        disk_current,
        DISK_WARNING_THRESHOLD,
        DISK_CRITICAL_THRESHOLD,
    )

    return {
        "kode": kode,

        "cpu": {
            "current": cpu_current,
            "status": cpu_status,
            "history": cpu,
        },

        "memory": {
            "current": memory_current,
            "status": memory_status,
            "history": memory,
        },

        "disk": {
            "current": disk_current,
            "status": disk_status,
            "history": disk,
        },

        "period": {
            "start": period_start,
            "end": period_end,
        },

        "checked_at": checked_at,

    }

def get_metric_status(
    value,
    warning_threshold,
    critical_threshold,
):
    if value is None:
        return "unavailable"

    if value >= critical_threshold:
        return "critical"

    if value >= warning_threshold:
        return "warning"

    return "healthy"

SEVERITY_EMOJI = {
    "0": "⚪",
    "1": "🔵",
    "2": "🟡",
    "3": "🟠",
    "4": "🔴",
    "5": "🔴",
}

# from datetime import datetime

def format_problem_duration(clock) -> str:

    if not clock:
        return "Unknown"

    problem_time = datetime.datetime.fromtimestamp(int(clock))
    now = datetime.datetime.now()


    total_seconds = int(
        (now - problem_time).total_seconds()
    )

    if total_seconds < 0:
        return "Unknown"

    days, remainder = divmod(
        total_seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, _ = divmod(
        remainder,
        60,
    )

    if days > 0:
        return f"{days}d {hours}h {minutes}m"

    if hours > 0:
        return f"{hours}h {minutes}m"

    return f"{minutes}m"

def get_active_problems() -> list:
    """
    Mengambil semua problem aktif dari Zabbix
    beserta host dan durasinya.
    """

    payload = {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "output": [
                "eventid",
                "objectid",
                "clock",
                "name",
                "severity",
            ],
            "sortfield": "eventid",
            "sortorder": "DESC",
        },
        "auth": ZABBIX_AUTH,
        "id": 2,
    }

    try:

        response = requests.post(
            ZABBIX_URL,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise Exception(
                data["error"].get(
                    "data",
                    "Zabbix API error",
                )
            )

        problems = data.get("result", [])
            
        problems = [
            problem
            for problem in problems
            if "PostgreSQL:" not in problem.get("name", "")
        ]

        formatted_problems = []

        for problem in problems:

            trigger_id = problem.get("objectid")

            # ====================================================
            # HOST
            # ====================================================

            hosts = []

            if trigger_id:

                trigger_payload = {
                    "jsonrpc": "2.0",
                    "method": "trigger.get",
                    "params": {
                        "output": [
                            "triggerid",
                            "description",
                        ],
                        "triggerids": [
                            trigger_id
                        ],
                        "selectHosts": [
                            "hostid",
                            "host",
                            "name",
                        ],
                    },
                    "auth": ZABBIX_AUTH,
                    "id": 3,
                }

                trigger_response = requests.post(
                    ZABBIX_URL,
                    json=trigger_payload,
                    timeout=10,
                )

                trigger_response.raise_for_status()

                trigger_data = trigger_response.json()

                if "error" not in trigger_data:

                    trigger_result = trigger_data.get(
                        "result",
                        []
                    )

                    if trigger_result:

                        hosts = [
                            host.get("name")
                            or host.get("host")
                            for host in trigger_result[0].get(
                                "hosts",
                                []
                            )
                        ]

            # ====================================================
            # SEVERITY
            # ====================================================

            severity_code = str(
                problem.get(
                    "severity",
                    "0"
                )
            )

            severity_emoji = SEVERITY_EMOJI.get(
                severity_code,
                "⚪"
            )

            # ====================================================
            # DURATION
            # ====================================================

            duration = format_problem_duration(
                problem.get("clock")
            )

            # ====================================================
            # RESULT
            # ====================================================

            formatted_problems.append({
                "eventid": problem.get("eventid"),
                "objectid": problem.get("objectid"),

                "name": problem.get(
                    "name",
                    "Unknown problem"
                ),

                "severity_code": severity_code,
                "severity_emoji": severity_emoji,
                "severity": severity_code,

                "hosts": hosts,

                "clock": problem.get("clock"),

                "duration": duration,
            })

        return formatted_problems

    except requests.exceptions.ConnectionError:
        logger.exception(
            "Koneksi Zabbix gagal"
        )
        raise Exception(
            "⚠️ Koneksi monitoring terputus. "
            "Periksa VPN dan tunnel."
        )

    except requests.exceptions.Timeout:
        logger.exception(
            "Timeout koneksi Zabbix"
        )
        raise Exception(
            "⚠️ Server monitoring tidak merespons "
            "dalam 10 detik."
        )

    except requests.exceptions.RequestException:
        logger.exception(
            "Request Zabbix gagal"
        )
        raise Exception(
            "⚠️ Gagal menghubungi server monitoring."
        )

    except Exception as e:
        logger.exception(
            "Error saat mengambil active problems"
        )
        raise Exception(
            f"⚠️ Error Zabbix: {str(e)}"
        )
    
def get_problem_hosts(problem):
    """
    Mengambil host yang terkait dengan sebuah problem.
    """

    trigger_id = problem["objectid"]

    payload = {
        "jsonrpc": "2.0",
        "method": "trigger.get",
        "params": {
            "output": [
                "triggerid",
                "description",
            ],
            "triggerids": [trigger_id],
            "selectHosts": [
                "hostid",
                "host",
                "name",
            ],
        },
        "auth": ZABBIX_AUTH,
        "id": 2,
    }

    try:

        response = requests.post(
            ZABBIX_URL,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise Exception(
                data["error"].get(
                    "data",
                    "Zabbix API error",
                )
            )

        result = data.get("result", [])

        if not result:
            return []

        return result[0].get(
            "hosts",
            []
        )

    except requests.exceptions.ConnectionError:
        logger.exception("Koneksi Zabbix gagal")
        raise Exception(
            "⚠️ Koneksi monitoring terputus. "
            "Periksa VPN dan tunnel."
        )

    except requests.exceptions.Timeout:
        logger.exception("Timeout koneksi Zabbix")
        raise Exception(
            "⚠️ Server monitoring tidak merespons "
            "dalam 10 detik."
        )

    except requests.exceptions.RequestException:
        logger.exception("Request Zabbix gagal")
        raise Exception(
            "⚠️ Gagal menghubungi server monitoring."
        )

    except Exception as e:
        logger.exception(
            "Error saat mengambil host problem"
        )
        raise Exception(
            f"⚠️ Error Zabbix: {str(e)}"
        )

def get_active_problems_with_hosts() -> list:

    problems = get_active_problems()

    result = []

    for problem in problems:

        print("\n===== PROBLEM DEBUG =====")
        print(problem)
        print("KEYS:", list(problem.keys()))

        objectid = problem.get("objectid")

        if not objectid:
            print(
                "⚠️ SKIP: problem tidak memiliki objectid"
            )
            continue

        hosts = get_problem_hosts(problem)

        result.append({
            "eventid": problem["eventid"],
            "name": problem["name"],
            "severity": problem["severity"],
            "clock": problem["clock"],
            "hosts": [
                {
                    "hostid": host["hostid"],
                    "host": host["host"],
                    "name": host["name"],
                }
                for host in hosts
            ],
        })

    return result

def get_monitored_hosts() -> list:
    """
    Mengambil host yang sedang dimonitor oleh Zabbix.
    """

    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": [
                "hostid",
                "host",
                "name",
                "status",
            ],
            "filter": {
                "status": "0"
            },
        },
        "auth": ZABBIX_AUTH,
        "id": 3,
    }

    try:

        response = requests.post(
            ZABBIX_URL,
            json=payload,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise Exception(
                data["error"].get(
                    "data",
                    "Zabbix API error",
                )
            )

        return data.get(
            "result",
            []
        )

    except requests.exceptions.ConnectionError:
        raise Exception(
            "⚠️ Koneksi monitoring terputus."
        )

    except requests.exceptions.Timeout:
        raise Exception(
            "⚠️ Server monitoring tidak merespons."
        )

    except requests.exceptions.RequestException:
        raise Exception(
            "⚠️ Gagal menghubungi server monitoring."
        )

# DIVIDER FOR HISTORY ----------------------------------------------


# GA DIPAKE yang bawah ------------------------------------------------- 

def get_hosts_snapshot() -> list:
    """Get CPU and Memory snapshot for all hosts at once"""
    snapshot = []
    
    # Get all CPU and Memory data
    cpu_data = get_all_cpu_data()
    memory_data = get_all_memory_data()
    
    # Create a dict for quick lookup
    memory_dict = {item["kode"]: item for item in memory_data}
    
    # Combine CPU and Memory data
    for cpu_item in cpu_data:
        kode = cpu_item["kode"]
        mem_item = memory_dict.get(kode, {})
        
        snapshot.append({
            "kode": kode,
            "cpu": {
                "value": cpu_item.get("value"),
                "status": cpu_item.get("status"),
                "error": cpu_item.get("error")
            },
            "memory": {
                "value": mem_item.get("value"),
                "status": mem_item.get("status"),
                "error": mem_item.get("error")
            },
            "checked_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        })
    
    return snapshot


# def get_active_problems(status: str = "all") -> list:
#     """Get problems from Zabbix - active, resolved, or all
    
#     Args:
#         status: "all" (active + resolved), "active" (only active), "resolved" (only resolved)
#     """
#     # For "all" or "resolved", use event.get() to include resolved problems
#     # For "active", use problem.get()
    
#     if status == "active":
#         # Get only ACTIVE problems (currently open)
#         payload = {
#             "jsonrpc": "2.0",
#             "method": "problem.get",
#             "params": {
#                 "output": ["eventid", "name", "severity", "clock", "lastchange", "acknowledged"],
#                 "selectHosts": ["host", "name"],
#                 "selectTags": "extend",
#                 "sortfield": ["severity"],
#                 "sortorder": "DESC",
#                 "limit": 50
#             },
#             "auth": ZABBIX_AUTH,
#             "id": 2
#         }
#     else:
#         # Get ALL events (active + resolved) from last 30 days
#         time_from = int((datetime.datetime.now() - datetime.timedelta(days=30)).timestamp())
        
#         payload = {
#             "jsonrpc": "2.0",
#             "method": "event.get",
#             "params": {
#                 "output": ["eventid", "name", "severity", "clock", "value"],
#                 "selectHosts": ["host", "name"],
#                 "selectTags": "extend",
#                 "selectRelatedObject": "extend",
#                 "sortfield": ["clock"],
#                 "sortorder": "DESC",
#                 "time_from": time_from,
#                 "limit": 50,
#                 "source": 0  # TRIGGER_SOURCE
#             },
#             "auth": ZABBIX_AUTH,
#             "id": 2
#         }
    
#     try:
#         response = requests.post(ZABBIX_URL, json=payload, timeout=10)
#         response.raise_for_status()
#         data = response.json()
        
#         if "result" in data:
#             problems = []
#             severity_map = {
#                 "0": ("ℹ️", "Information"),
#                 "1": ("⚠️", "Warning"),
#                 "2": ("🟡", "Average"),
#                 "3": ("🔴", "High"),
#                 "4": ("💥", "Disaster"),
#                 "5": ("❌", "Critical")
#             }
            
#             for item in data["result"]:
#                 severity_code = item.get("severity", "0")
#                 severity_emoji, severity_text = severity_map.get(severity_code, ("❓", "Unknown"))
                
#                 host_names = []
#                 if item.get("hosts"):
#                     host_names = [h.get("name", h.get("host")) for h in item["hosts"]]
                
#                 # Get event time
#                 if "clock" in item:
#                     clock = int(item.get("clock", 0))
#                 else:
#                     clock = int(item.get("lastchange", 0))
                
#                 problem_time = datetime.datetime.fromtimestamp(clock).strftime("%H:%M:%S")
                
#                 # Calculate duration (from when problem started until now)
#                 now = int(datetime.datetime.now().timestamp())
#                 duration_seconds = now - clock
                
#                 # Format duration
#                 duration_text = ""
#                 if duration_seconds < 60:
#                     duration_text = f"{duration_seconds}s"
#                 elif duration_seconds < 3600:
#                     duration_text = f"{duration_seconds // 60}m"
#                 elif duration_seconds < 86400:
#                     hours = duration_seconds // 3600
#                     minutes = (duration_seconds % 3600) // 60
#                     duration_text = f"{hours}h {minutes}m"
#                 else:
#                     days = duration_seconds // 86400
#                     hours = (duration_seconds % 86400) // 3600
#                     duration_text = f"{days}d {hours}h"
                
#                 # Status (for event.get)
#                 event_status = "RESOLVED" if int(item.get("value", 0)) == 0 else "PROBLEM"
                
#                 # Get tags
#                 tags = []
#                 if item.get("tags"):
#                     tags = [f"{tag.get('tag')}:{tag.get('value')}" for tag in item["tags"]]
                
#                 # Acknowledged status
#                 ack_status = "Yes" if int(item.get("acknowledged", 0)) == 1 else "No"
                
#                 problems.append({
#                     "eventid": item.get("eventid"),
#                     "name": item.get("name"),
#                     "severity_code": severity_code,
#                     "severity": severity_text,
#                     "severity_emoji": severity_emoji,
#                     "hosts": host_names,
#                     "clock": problem_time,
#                     "duration": duration_text,
#                     "acknowledged": ack_status,
#                     "tags": tags,
#                     "event_status": event_status,
#                     "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#                 })
            
#             return problems
#         else:
#             return []
#     except requests.exceptions.ConnectionError:
#         logger.exception("Koneksi Zabbix gagal")
#         raise Exception("⚠️ Koneksi monitoring terputus. Periksa VPN dan tunnel.")
#     except requests.exceptions.Timeout:
#         logger.exception("Timeout koneksi Zabbix")
#         raise Exception("⚠️ Server monitoring tidak merespons dalam 10 detik.")
#     except Exception as e:
#         logger.exception("Error mendapatkan problems")
#         raise Exception(f"⚠️ Error: {str(e)}")


def get_recent_events(limit: int = 20) -> list:
    """Get recent events/alerts from Zabbix"""
    payload = {
        "jsonrpc": "2.0",
        "method": "event.get",
        "params": {
            "output": ["eventid", "clock", "value", "severity"],
            "selectHosts": ["host", "name"],
            "selectRelatedObject": "extend",
            "sortfield": ["clock"],
            "sortorder": "DESC",
            "limit": limit,
            "source": 0  # TRIGGER_SOURCE
        },
        "auth": ZABBIX_AUTH,
        "id": 2
    }
    
    try:
        response = requests.post(ZABBIX_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            events = []
            severity_map = {
                "0": ("ℹ️", "Information"),
                "1": ("⚠️", "Warning"),
                "2": ("🟡", "Average"),
                "3": ("🔴", "High"),
                "4": ("💥", "Disaster"),
                "5": ("❌", "Critical")
            }
            
            for event in data["result"]:
                severity_code = event.get("severity", "0")
                severity_emoji, severity_text = severity_map.get(severity_code, ("❓", "Unknown"))
                
                value = int(event.get("value", 0))
                event_type = "🔴 PROBLEM" if value == 1 else "🟢 RESOLVED"
                
                clock = int(event.get("clock", 0))
                event_time = datetime.datetime.fromtimestamp(clock).strftime("%d/%m/%Y %H:%M:%S")
                
                host_names = []
                if event.get("hosts"):
                    host_names = [h.get("name", h.get("host")) for h in event["hosts"]]
                
                events.append({
                    "eventid": event.get("eventid"),
                    "type": event_type,
                    "severity": severity_text,
                    "severity_emoji": severity_emoji,
                    "hosts": host_names,
                    "clock": event_time
                })
            
            return events
        else:
            return []
    except requests.exceptions.ConnectionError:
        logger.exception("Koneksi Zabbix gagal")
        raise Exception("⚠️ Koneksi monitoring terputus. Periksa VPN dan tunnel.")
    except requests.exceptions.Timeout:
        logger.exception("Timeout koneksi Zabbix")
        raise Exception("⚠️ Server monitoring tidak merespons dalam 10 detik.")
    except Exception as e:
        logger.exception("Error mendapatkan recent events")
        raise Exception(f"⚠️ Error: {str(e)}")
    
    return snapshot
