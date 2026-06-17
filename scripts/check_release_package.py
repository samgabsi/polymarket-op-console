from __future__ import annotations

from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
blocked_names = {".git", "__pycache__", ".pytest_cache", "venv", ".venv", "node_modules"}
blocked_suffixes = {".pyc", ".pyo", ".db", ".sqlite", ".log"}
findings = []
for path in root.rglob("*"):
    rel = path.relative_to(root)
    parts = set(rel.parts)
    if parts & blocked_names:
        findings.append(str(rel))
    if path.is_file() and path.suffix.lower() in blocked_suffixes:
        findings.append(str(rel))
    if path.name in {".env", "session_secret.txt"}:
        findings.append(str(rel))
    if any(marker in str(rel) for marker in ["data/live_v2/audit_ledger.jsonl", "data/live_v2/strategy", "data/live_v2/research", "data/live_v2/monitoring", "data/live_v2/portfolio", "data/live_v2/governance", "data/live_v2/data_integrity", "data/live_v2/backups", "data/live_v2/exports", "data/live_v2/reports", "data/live_v3", "runtime_screenshots", "runtime_ui_snapshots", "workflow_runs"]):
        findings.append(str(rel))
print({"root": str(root), "blocked_findings": findings[:200], "count": len(findings)})
if findings:
    sys.exit(1)
