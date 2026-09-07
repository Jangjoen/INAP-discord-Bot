from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

OPS_ROOT = Path(__file__).resolve().parents[1]


def find_hanes_root() -> Path:
    candidates = [
        Path(__file__).resolve().parents[2] / "HANES_EXE_BUILD_KIT",
        Path(__file__).resolve().parents[1] / "HANES_EXE_BUILD_KIT",
        Path(__file__).resolve().parents[0] / "HANES_EXE_BUILD_KIT",
        Path.cwd() / "HANES_EXE_BUILD_KIT",
        Path.home() / "OneDrive" / "Documents" / "orek tempe" / "work jeck" / "HANES_EXE_BUILD_KIT",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Folder HANES_EXE_BUILD_KIT tidak ditemukan. Pastikan folder ada di workspace atau jalur default Windows."
    )


def _read_env_from_hanes() -> tuple[str, str, str]:
    hanes_root = find_hanes_root()
    env_path = hanes_root / ".env"
    username = ""
    password = ""
    webhook = ""

    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = [part.strip() for part in line.split("=", 1)]
            if key == "HANES_USERNAME":
                username = value.strip().strip('"')
            elif key == "HANES_PASSWORD":
                password = value.strip().strip('"')
            elif key == "DISCORD_WEBHOOK_URL":
                webhook = value.strip().strip('"')

    username = os.getenv("HANES_USERNAME", username).strip()
    password = os.getenv("HANES_PASSWORD", password).strip()
    webhook = os.getenv("DISCORD_WEBHOOK_URL", webhook).strip()

    return username, password, webhook


def run_hanes_monitor() -> dict[str, Any]:
    hanes_root = find_hanes_root()
    username, password, webhook = _read_env_from_hanes()

    if not username or not password:
        raise RuntimeError("HANES_USERNAME atau HANES_PASSWORD belum diisi. Cek file .env di folder Hanes.")
    if not webhook:
        raise RuntimeError("DISCORD_WEBHOOK_URL belum diisi. Cek file .env di folder Hanes atau bot config.")

    env = os.environ.copy()
    env["HANES_USERNAME"] = username
    env["HANES_PASSWORD"] = password
    env["DISCORD_WEBHOOK_URL"] = webhook
    env["HANES_HEADLESS"] = "1"
    env["DRY_RUN"] = "0"
    env["PYTHONPATH"] = str(hanes_root) + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [sys.executable, str(hanes_root / "hanes_core.py")],
        cwd=str(hanes_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )

    summary = get_latest_run_summary()
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "summary": summary,
    }


def get_latest_run_summary() -> str:
    hanes_root = find_hanes_root()
    output_dir = hanes_root / "output"
    if not output_dir.exists():
        return "Belum ada hasil monitoring Hanes. Jalankan monitoring terlebih dahulu."

    run_dirs = sorted(
        [p for p in output_dir.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for run_dir in run_dirs:
        summary_file = run_dir / "run_summary.json"
        if summary_file.exists():
            try:
                payload = json.loads(summary_file.read_text(encoding="utf-8"))
                if not isinstance(payload, list):
                    continue

                healthy = sum(1 for item in payload if item.get("status") == "HEALTHY")
                warning = sum(1 for item in payload if item.get("status") == "WARNING")
                error = sum(1 for item in payload if item.get("status") == "ERROR")
                return (
                    "Hanes monitoring summary:\n"
                    f"Healthy: {healthy}\n"
                    f"Warning: {warning}\n"
                    f"Error: {error}\n"
                    f"Run folder: {run_dir.name}"
                )
            except Exception:
                continue

    return "Hanes monitoring sudah dijalankan, tetapi file ringkasan hasil belum ditemukan."
