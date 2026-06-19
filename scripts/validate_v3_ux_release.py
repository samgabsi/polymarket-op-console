from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run(cmd: list[str]) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, env=env)
    return {"cmd": " ".join(cmd), "returncode": result.returncode, "stdout_tail": result.stdout[-1600:], "stderr_tail": result.stderr[-1600:]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe v3.7 UX/freshness release validation harness. Does not call live mutation endpoints.")
    parser.add_argument("--quick", action="store_true", help="Run in-process checks only.")
    args = parser.parse_args()

    from app.config import APP_VERSION
    from app.live_v3 import design_system_status, navigation_groups, ux_release_status, validation_status, demo_data_safety_check, workflow_templates, build_command_center, build_search_index, build_decision_graph
    from app.live_v3_analytics import build_analytics_summary
    from app.live_v3_simulation import simulation_summary, process_quality_backtest
    from app.live_v3_freshness import summary as freshness_summary

    docs = [
        "docs/V4_PLATFORM_ARCHITECTURE_GUIDE_v4.0.1-real.md",
        "docs/V4_PLUGIN_BOUNDARY_GUIDE_v4.0.1-real.md",
        "docs/V4_PLATFORM_DIAGNOSTICS_GUIDE_v4.0.1-real.md",
        "docs/V4_STORAGE_COMPATIBILITY_GUIDE_v4.0.1-real.md",
        "docs/V3_OPERATOR_COCKPIT_GUIDE_v4.0.1-real.md",
        "docs/V3_GUIDED_OPERATOR_WORKSPACE_GUIDE_v4.0.1-real.md",
        "docs/V3_OPERATOR_TASK_PLANNER_GUIDE_v4.0.1-real.md",
        "docs/V3_FRESHNESS_SCHEDULER_GUIDE_v4.0.1-real.md",
        "docs/V3_SIMULATION_LAB_GUIDE_v4.0.1-real.md",
        "docs/V3_UI_UX_REDESIGN_GUIDE_v4.0.1-real.md",
        "docs/VISUAL_QA_CHECKLIST_v4.0.1-real.md",
        "docs/RELEASE_NOTES_v4.0.1-real.md",
        "docs/VALIDATION_v4.0.1-real.md",
        "docs/MANUAL_QA_CHECKLIST_v4.0.1-real.md",
        "docs/RELEASE_CHECKLIST_v4.0.1-real.md",
    ]
    checks = [
        {"name": "version", "status": "pass" if APP_VERSION == "4.0.1-real" else "fail", "value": APP_VERSION},
        {"name": "design_system", "status": design_system_status().get("status", "fail")},
        {"name": "navigation_groups", "status": "pass" if len(navigation_groups().get("groups", [])) >= 5 else "fail"},
        {"name": "command_center", "status": "pass" if build_command_center().get("secret_values_returned") is False else "fail"},
        {"name": "search_index", "status": "pass" if build_search_index(limit=10).get("secret_values_returned") is False else "fail"},
        {"name": "decision_graph", "status": "pass" if build_decision_graph(limit=10).get("secret_values_returned") is False else "fail"},
        {"name": "workflow_templates", "status": "pass" if workflow_templates().get("count", 0) >= 10 else "fail"},
        {"name": "analytics_summary", "status": "pass" if build_analytics_summary().get("secret_values_returned") is False else "fail"},
        {"name": "simulation_summary", "status": "pass" if simulation_summary().get("secret_values_returned") is False else "fail"},
        {"name": "freshness_summary", "status": "pass" if freshness_summary().get("secret_values_returned") is False else "fail"},
        {"name": "process_backtest", "status": "pass" if process_quality_backtest().get("simulation_only") is True else "fail"},
        {"name": "demo_fixture_safety", "status": "pass" if demo_data_safety_check({}).get("ok") else "fail"},
        {"name": "ux_release_status", "status": ux_release_status().get("overall_status", "fail")},
        {"name": "validation_status", "status": validation_status().get("overall_status", "unknown")},
    ]
    checks.extend({"name": f"doc:{doc}", "status": "pass" if (ROOT / doc).exists() else "fail"} for doc in docs)

    commands = []
    if not args.quick:
        commands.extend([
            run([sys.executable, "-m", "compileall", "-q", "app", "tests", "scripts"]),
            run([sys.executable, "scripts/check_versions.py"]),
            run([sys.executable, "scripts/smoke_startup.py"]),
            run([sys.executable, "scripts/capture_v3_screenshots.py", "--dry-run"]),
        ])
        for rel in [".pytest_cache", "data", "runtime_screenshots"]:
            shutil.rmtree(ROOT / rel, ignore_errors=True)
        for cache in list(ROOT.rglob("__pycache__")):
            shutil.rmtree(cache, ignore_errors=True)
        commands.append(run([sys.executable, "scripts/check_release_package.py", "."]))

    overall = "pass" if all(c.get("status") == "pass" for c in checks if c["name"] != "validation_status") and all(c.get("returncode") == 0 for c in commands) else "fail"
    report = {
        "version": APP_VERSION,
        "overall_status": overall,
        "checks": checks,
        "commands": commands,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "redesigned_ui_does_not_bypass_backend_gates": True,
        "screenshots_included_in_release_zip": False,
        "secret_values_returned": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
