from datetime import datetime

from services.zabbix_service import get_vm_report_data


kode = "42"

report = get_vm_report_data(kode, hours=2)


print("\n===== VM REPORT DATA =====")

print("VM:", report["kode"])

print("\nCPU")
print("Current:", report["cpu"]["current"])
print("Status:", report["cpu"]["status"])
print("History:", len(report["cpu"]["history"]), "points")

print("\nMEMORY")
print("Current:", report["memory"]["current"])
print("Status:", report["memory"]["status"])
print("History:", len(report["memory"]["history"]), "points")

print("\nDISK")
print("Current:", report["disk"]["current"])
print("Status:", report["disk"]["status"])
print("History:", len(report["disk"]["history"]), "points")

print("\nPERIOD")

start = datetime.fromtimestamp(report["period"]["start"])
end = datetime.fromtimestamp(report["period"]["end"])

print("Start:", start)
print("End:", end)

print("\nCHECKED AT")
print(report["checked_at"])

print("\nSTATISTICS")

for name in ["cpu", "memory", "disk"]:
    values = [
        point["value"]
        for point in report[name]["history"]
    ]

    print(f"\n{name.upper()}")
    print("Min:", min(values))
    print("Max:", max(values))
    print("Avg:", sum(values) / len(values))

print("==========================")