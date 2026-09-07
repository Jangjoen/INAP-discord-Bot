from services.report_services import generate_all_vm_reports


reports = generate_all_vm_reports(hours=2)

print("\n===== REPORT RESULT =====")

for item in reports:

    kode = item["kode"]
    report = item["report"]
    image = item["image"]

    print(f"\nVM {kode}")

    print(
        "CPU:",
        report["cpu"]["current"],
        report["cpu"]["status"],
    )

    print(
        "MEMORY:",
        report["memory"]["current"],
        report["memory"]["status"],
    )

    print(
        "DISK:",
        report["disk"]["current"],
        report["disk"]["status"],
    )

    print(
        "IMAGE TYPE:",
        type(image),
    )

    print(
        "IMAGE SIZE:",
        image.getbuffer().nbytes,
        "bytes",
    )

print("\n========================")