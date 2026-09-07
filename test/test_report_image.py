from services.zabbix_service import get_vm_report_data
from reports.report_generator import generate_vm_report
import reports.chart_generator

kode = "42"

print(f"Mengambil data VM {kode}...")



print(
    "CHART GENERATOR:",
    reports.chart_generator.__file__
)

report = get_vm_report_data(
    kode,
    hours=2,
)

output_path = f"vm_{kode}_report.png"

generate_vm_report(
    report=report,
    output_path=output_path,
)

print(f"Report berhasil dibuat: {output_path}")