from services.report_services import generate_all_vm_reports
from services.global_report_services import (
    build_global_report_text,
)


reports = generate_all_vm_reports(
    hours=2
)

if not reports:
    print("Tidak ada report.")
    raise SystemExit


print("\n===== GLOBAL REPORT =====\n")

print(
    build_global_report_text(reports)
)