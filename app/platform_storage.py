from __future__ import annotations

from typing import Any
from .config import APP_VERSION, DATA_DIR
from .platform_safety import safety_flags

KNOWN_STORAGE_NAMESPACES = [
    {"namespace": "live_v2_audit", "path": "data/live_v2/audit_ledger.jsonl", "created_lazily": True, "package_excluded": True},
    {"namespace": "v3_workflows", "path": "data/live_v3/workflow_runs.jsonl", "created_lazily": True, "package_excluded": True},
    {"namespace": "v3_datasets", "path": "data/live_v3/datasets", "created_lazily": True, "package_excluded": True},
    {"namespace": "v3_freshness", "path": "data/live_v3/freshness", "created_lazily": True, "package_excluded": True},
    {"namespace": "v3_tasks", "path": "data/live_v3/tasks", "created_lazily": True, "package_excluded": True},
    {"namespace": "v3_workspace", "path": "data/live_v3/workspace", "created_lazily": True, "package_excluded": True},
    {"namespace": "v3_cockpit", "path": "data/live_v3/cockpit", "created_lazily": True, "package_excluded": True},
    {"namespace": "v4_platform", "path": "data/live_v3/platform", "created_lazily": True, "package_excluded": True},
]
PACKAGE_EXCLUDED_RUNTIME_DIRS = [
    "data", "runtime_screenshots", ".pytest_cache", "__pycache__", "venv", ".venv", "node_modules", "logs", "backups",
]
COMPATIBILITY_NOTES = [
    "v3.5 dataset manifests, v3.6 freshness records, v3.7 task records, v3.8 workspace records, v4.0 cockpit records, and v4.0 platform diagnostics are local JSON/JSONL runtime stores.",
    "Stores are created lazily by operator-triggered actions and are excluded from clean release packages.",
    "v4.0.1-real provides compatibility notes only; it does not perform destructive automatic migrations.",
    "Live trading state is not migrated, deleted, approved, submitted, cancelled, or armed by storage helpers.",
]


def storage_summary() -> dict[str, Any]:
    rows = []
    for item in KNOWN_STORAGE_NAMESPACES:
        path = DATA_DIR.parent / item["path"]
        rows.append({**item, "exists_now": path.exists(), "safety_note": "Runtime only; exclude from release ZIP."})
    return safety_flags({
        "version": APP_VERSION,
        "count": len(rows),
        "items": rows,
        "package_excluded_runtime_dirs": PACKAGE_EXCLUDED_RUNTIME_DIRS,
        "compatibility_notes": COMPATIBILITY_NOTES,
        "migration_policy": "documentation-only, no destructive automatic migration",
    })
