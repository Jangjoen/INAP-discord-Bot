from services.zabbix_service import (
    get_cpu_history,
    get_memory_history,
    get_disk_history,
)


kode = "42"

cpu = get_cpu_history(kode, hours=2)
memory = get_memory_history(kode, hours=2)
disk = get_disk_history(kode, hours=2)


print("CPU")
print(f"Jumlah data: {len(cpu)}")
print(cpu[:3])
print(cpu[-3:])

print("\nMEMORY")
print(f"Jumlah data: {len(memory)}")
print(memory[:3])
print(memory[-3:])

print("\nDISK")
print(f"Jumlah data: {len(disk)}")
print(disk[:3])
print(disk[-3:])

