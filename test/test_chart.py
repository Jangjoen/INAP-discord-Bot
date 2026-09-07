from services.zabbix_service import get_vm_report_data
from reports.chart_generator import generate_metric_chart


kode = "42"

report = get_vm_report_data(
    kode,
    hours=2,
)


generate_metric_chart(
    history=report["cpu"]["history"],
    title="CPU UTILIZATION",
    output_path="cpu_test.png",
)

print("CPU chart berhasil dibuat: cpu_test.png")