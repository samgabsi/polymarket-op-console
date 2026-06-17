from __future__ import annotations

import argparse
import json
import subprocess
import sys
import shutil
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run(cmd: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, env=env)
    return {"cmd": " ".join(cmd), "returncode": result.returncode, "stdout_tail": result.stdout[-1200:], "stderr_tail": result.stderr[-1200:]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe v3 release validation harness. Does not call live mutation endpoints.")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    from app.config import APP_VERSION
    from app.live_v3 import build_command_center, search_filters, graph_filters, workflow_templates, validation_status, demo_data_safety_check, design_system_status, ux_release_status
    from app.live_v3_analytics import build_analytics_summary, generate_analytics_snapshot, generate_learning_report, export_analytics_json
    checks = []
    checks.append({"name": "version", "status": "pass" if APP_VERSION == "3.3.0-real" else "fail", "value": APP_VERSION})
    checks.append({"name": "command_center", "status": "pass" if build_command_center().get("secret_values_returned") is False else "fail"})
    checks.append({"name": "search_filters", "status": "pass" if search_filters().get("secret_values_returned") is False else "fail"})
    checks.append({"name": "graph_filters", "status": "pass" if graph_filters().get("secret_values_returned") is False else "fail"})
    checks.append({"name": "workflow_templates", "status": "pass" if workflow_templates().get("count", 0) >= 10 else "fail"})
    checks.append({"name": "demo_fixture_safety", "status": "pass" if demo_data_safety_check({}).get("ok") else "fail"})
    checks.append({"name": "analytics_summary", "status": "pass" if build_analytics_summary().get("secret_values_returned") is False else "fail"})
    checks.append({"name": "analytics_snapshot", "status": "pass" if generate_analytics_snapshot(write=False).get("order_submitted") is False else "fail"})
    checks.append({"name": "learning_report", "status": "pass" if generate_learning_report(write=False).get("analytics_are_descriptive") is True else "fail"})
    checks.append({"name": "analytics_export", "status": "pass" if export_analytics_json().get("secret_values_returned") is False else "fail"})
    checks.append({"name": "design_system", "status": design_system_status().get("status", "unknown")})
    checks.append({"name": "ux_release_status", "status": ux_release_status().get("overall_status", "unknown")})
    checks.append({"name": "validation_status", "status": validation_status().get("overall_status", "unknown")})
    commands = []
    if not args.quick:
        commands.extend([
            run([sys.executable, "-m", "compileall", "-q", "app", "tests", "scripts"]),
            run([sys.executable, "scripts/check_versions.py"]),
            run([sys.executable, "scripts/smoke_startup.py"]),
        ])
        # Smoke/compile checks intentionally create transient runtime/cache files. Remove them before packaging hygiene.
        for rel in [".pytest_cache", "data", "runtime_screenshots"]:
            shutil.rmtree(ROOT / rel, ignore_errors=True)
        for cache in list(ROOT.rglob("__pycache__")):
            shutil.rmtree(cache, ignore_errors=True)
        commands.append(run([sys.executable, "scripts/check_release_package.py", "."]))
    overall = "pass" if all(c.get("status") == "pass" for c in checks if c["name"] != "validation_status") and all(c.get("returncode") == 0 for c in commands) else "fail"
    report = {"version": APP_VERSION, "overall_status": overall, "checks": checks, "commands": commands, "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "ai_assistance_enabled": False, "secret_values_returned": False}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
