from services.zabbix_service import get_active_problems


problems = get_active_problems()

print("\n===== ACTIVE PROBLEMS =====")
print(f"Jumlah: {len(problems)}")

for problem in problems:

    print("\n--------------------------")

    print(
        "Event ID  :",
        problem.get("eventid")
    )

    print(
        "Problem   :",
        problem.get("name")
    )

    print(
        "Severity  :",
        problem.get("severity_code"),
        problem.get("severity_emoji")
    )

    print(
        "Hosts     :",
        problem.get("hosts")
    )

    print(
        "Clock     :",
        problem.get("clock")
    )

    print(
        "Duration  :",
        problem.get("duration")
    )