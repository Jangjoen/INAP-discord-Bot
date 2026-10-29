import re


PROBLEM_TRANSLATIONS = {
    "High swap space usage (less than 50% free)" : (
        "Memori Cadangan (Swap) pada server mulai menipis (kurang dari 50%)"
    ),

    "ClickHouse has been restarted" : (
        "Layanan Clickhouse telah di-restart" 
    ), 

    "ClickHouse: has been restarted (uptime < 10m)" : (
        "Layanan Clickhouse telah di-restart (baru berjalan kurang dari 10 menit)"
    ),

    "ClickHouse: Port 8123 is unavailable" : (
        "Layanan Clickhouse tidak bisa diakses, Port 8123 tidak tersedia"
    ),   

    "/data: Disk space is low (used > 80%)" : (
        "Penyimpanan /data hampir penuh (telah digunakan > 80%)"
    ),

    "/data: Disk space is critically low (used > 90%)" : (
        "Penyimpanan /data sudah menipis (telah digunakan > 90%)"
    ),

    "High memory utilization (>90% for 5m)" : (
        "Penggunaan memori server sangat tinggi (di atas 90%) selama lebih dari 5 menit."
    ),

    "vda: Disk read/write request responses are too high (read > 20 ms for 15m or write > 20 ms for 15m)" : (
        "vda: Kinerja penyimpanan data (disk) menurun. Proses membaca atau menyimpan data berjalan lebih lambat dari biasanya selama 15 menit terakhir."
    ),  

    "vdd: Disk read/write request responses are too high (read > 20 ms for 15m or write > 20 ms for 15m)" : (
            "vdd: Kinerja penyimpanan data (disk) menurun. Proses membaca atau menyimpan data berjalan lebih lambat dari biasanya selama 15 menit terakhir."
    ),

    "vdb: Disk read/write request responses are too high (read > 20 ms for 15m or write > 20 ms for 15m)" : (
            "vdb: Kinerja penyimpanan data (disk) menurun. Proses membaca atau menyimpan data berjalan lebih lambat dari biasanya selama 15 menit terakhir."
    ),  

    "vdc: Disk read/write request responses are too high (read > 20 ms for 15m or write > 20 ms for 15m)" : (
        "vdc: Kinerja penyimpanan data (disk) menurun. Proses membaca atau menyimpan data berjalan lebih lambat dari biasanya selama 15 menit terakhir."  
    ),

    "Zabbix agent is not available (for 3m)" : (
        "Zabbix agent tidak tersedia pada server"
    ),

    "ClickHouse: Failed to fetch info data (or no data for 30m)" : (
        "Tidak ada data yang diterima dari database(Clickhouse) selama 30 menit terakhir atau terjadi gangguan saat pengambilan data."
    ),

    "ClickHouse: Too many MergeTree parts (over 90% of 300)" : (
        "ClickHouse: Jumlah part (pecahan data) terlalu banyak dan sudah mencapai lebih dari 90% dari batas yang ditentukan (300 part)."
    ),

    "System time is out of sync (diff with Zabbix server > 60s)" : (
        "Waktu pada sistem tidak sinkron dengan Zabbix server (berbeda lebih dari 60 detik)"
    ),

    "ClickHouse: Too many distributed files to insert (over 600 for 5 min)" : (
        "Jumlah file pending pada tabel Distributed yang menunggu dikirim/di-insert ke node tujuan sudah lebih dari 600 file selama 5 menit"    
    ),

    "Load average is too high (per CPU load over 1.5 for 5m)" : (
        "Beban kerja server terlalu tinggi selama 5 menit terakhir. Nilai load average per CPU berada di atas 1.5, CPU mulai kewalahan menangani proses yang berjalan."
    ),

    "ClickHouse: There are queries running more than 600 seconds" : (
        "ClickHouse: Ada beberapa query yang berjalan lebih dari 600 detik"
    ),

}

CLICKHOUSE_REPLICA_PROBLEM = re.compile(
    r"ClickHouse:\s*(?P<table>.+?):\s*"
    r"Number of active replicas less than number of total replicas",
    re.IGNORECASE,
)


def translate_problem(problem: str) -> str:
    """
    Translate a problem string for dummy if a translation exists.
    If no translation exists, return the original problem string.
    """
    translation = PROBLEM_TRANSLATIONS.get(problem)
    if translation is not None:
        return translation

    match = CLICKHOUSE_REPLICA_PROBLEM.fullmatch(problem.strip())
    if match:
        return (
            "ClickHouse: Jumlah replica aktif pada "
            f"{match.group('table')} lebih sedikit daripada jumlah total replica yang ada"
        )

    return problem