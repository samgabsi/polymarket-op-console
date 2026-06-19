from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from .config import APP_VERSION
from .platform_safety import STANDARD_SAFETY_STATEMENT, NO_LIVE_MUTATION_STATEMENT, redact_data, safety_flags, secret_scan


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def export_manifest(export_type: str, title: str, included_object_ids: list[str] | None = None, related_object_ids: list[str] | None = None, warnings: list[str] | None = None, limitations: list[str] | None = None, unknown_unavailable_data: list[str] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = {
        "generated_at": now(),
        "app_version": APP_VERSION,
        "export_type": export_type,
        "title": title,
        "included_object_ids": included_object_ids or [],
        "related_object_ids": related_object_ids or [],
        "status_summary": "Generated as a local, secret-safe operator export.",
        "warnings": warnings or [],
        "limitations": limitations or ["Export reflects currently available local records only.", "Unknown/unavailable data is not invented."],
        "unknown_unavailable_data": unknown_unavailable_data or ["Runtime records may be absent until the operator creates local data."],
        "safety_statement": STANDARD_SAFETY_STATEMENT,
        "no_live_mutation_statement": NO_LIVE_MUTATION_STATEMENT,
        "payload": redact_data(payload or {}),
        **safety_flags(),
    }
    scan = secret_scan(manifest)
    manifest["secret_scan"] = scan
    manifest["secret_values_returned"] = False
    return redact_data(manifest)


def to_markdown(manifest: dict[str, Any]) -> str:
    data = redact_data(manifest)
    lines = [
        f"# {data.get('title', 'Platform Export')}",
        "",
        f"- Generated: {data.get('generated_at')}",
        f"- App version: {data.get('app_version')}",
        f"- Export type: {data.get('export_type')}",
        "",
        "## Safety Statement",
        str(data.get("safety_statement") or STANDARD_SAFETY_STATEMENT),
        "",
        "## Included Objects",
    ]
    for oid in data.get("included_object_ids") or []:
        lines.append(f"- {oid}")
    if not data.get("included_object_ids"):
        lines.append("- None listed")
    lines.extend(["", "## Unknown / Unavailable Data"])
    for item in data.get("unknown_unavailable_data") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Limitations"])
    for item in data.get("limitations") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Payload Summary", "```json", json.dumps(data.get("payload", {}), indent=2, sort_keys=True, default=str), "```", ""])
    return "\n".join(lines)


def rows_to_csv(rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> str:
    redacted = [redact_data(r) for r in rows]
    fields = fieldnames or sorted({k for row in redacted for k in row.keys()}) or ["status"]
    handle = io.StringIO()
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in redacted:
        writer.writerow(row)
    return handle.getvalue()


def validate_export_secret_safe(manifest: dict[str, Any]) -> dict[str, Any]:
    scan = secret_scan(manifest)
    return safety_flags({"ok": scan["ok"], "secret_scan": scan, "export_validated": True})
