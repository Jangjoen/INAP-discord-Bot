"""Test script to verify !problems output format with mock data"""

# Mock problems data
mock_problems = [
    {
        "eventid": "1001",
        "name": "High swap space usage (less than 50% free)",
        "severity_code": "2",
        "severity": "Average",
        "severity_emoji": "🟡",
        "hosts": ["Inap-61_cha4"],
        "clock": "17:23:37",
        "duration": "1h 53m",
        "acknowledged": "No",
        "tags": ["class: os", "component: memory", "component: storage"],
        "timestamp": "17/08/2026 19:30:00"
    },
    {
        "eventid": "1002",
        "name": "/data: Disk space is critically low (used > 90%)",
        "severity_code": "3",
        "severity": "High",
        "severity_emoji": "🔴",
        "hosts": ["Inap-42"],
        "clock": "16:22:44",
        "duration": "2h 54m",
        "acknowledged": "No",
        "tags": ["class: os", "component: storage", "filesystem: /data"],
        "timestamp": "17/08/2026 19:30:00"
    },
    {
        "eventid": "1003",
        "name": "High swap space usage (less than 50% free)",
        "severity_code": "2",
        "severity": "Average",
        "severity_emoji": "🟡",
        "hosts": ["Inap-41"],
        "clock": "14:20:18",
        "duration": "3d 4h",
        "acknowledged": "No",
        "tags": ["class: os", "component: memory", "component: storage"],
        "timestamp": "17/08/2026 19:30:00"
    }
]

# Print format preview
print("=" * 80)
print("DISCORD OUTPUT FORMAT - !problems")
print("=" * 80)

severity_count = {"Average": 0, "High": 0, "Disaster": 0, "Warning": 0, "Information": 0, "Critical": 0}

for problem in mock_problems:
    severity = problem.get("severity", "Unknown")
    severity_count[severity] = severity_count.get(severity, 0) + 1

summary = " | ".join([f"{emoji} {severity_count[sev]}" for emoji, sev in [
    ("💥", "Disaster"), ("🔴", "High"), ("🟡", "Average"), ("⚠️", "Warning"), ("ℹ️", "Information")
]])

print(f"\n🚨 Active Problems - Detailed List")
print(f"Total: {len(mock_problems)} problems")
print(f"{summary}\n")

for problem in mock_problems:
    hosts_text = ", ".join(problem.get("hosts", ["Unknown"])) or "Unknown"
    duration = problem.get("duration", "N/A")
    ack = problem.get("acknowledged", "No")
    clock = problem.get("clock", "N/A")
    tags_list = problem.get("tags", [])
    tags_text = " | ".join(tags_list[:3]) if tags_list else "No tags"
    
    print(f"\n{clock} | {hosts_text} | {problem['severity_emoji']} {problem['severity']}")
    print(f"  {problem.get('name', 'Unknown')[:60]}")
    print(f"  ⏱️ Duration: {duration} | ✓ Ack: {ack}")
    print(f"  🏷️ {tags_text}")

print("\n" + "=" * 80)
