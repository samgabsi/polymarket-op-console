from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_v2 import record_audit, redact_data, redact_text

TASKS_DIR = DATA_DIR / "live_v3" / "tasks"
TASK_EVENTS_PATH = TASKS_DIR / "task_events.jsonl"
TASKS_PATH = TASKS_DIR / "operator_tasks.jsonl"
INBOX_PATH = TASKS_DIR / "task_inbox.jsonl"
TEMPLATES_PATH = TASKS_DIR / "task_templates.jsonl"
CADENCE_PATH = TASKS_DIR / "cadence_rules.jsonl"
CADENCE_EVENTS_PATH = TASKS_DIR / "cadence_events.jsonl"
DAILY_OPS_PATH = TASKS_DIR / "daily_ops_packets.jsonl"
WEEKLY_OPS_PATH = TASKS_DIR / "weekly_ops_packets.jsonl"
SETTINGS_PATH = TASKS_DIR / "settings.json"
EXPORT_MANIFESTS_PATH = TASKS_DIR / "export_manifests.jsonl"

PRIORITIES = ["low", "medium", "high", "urgent", "critical"]
STATUSES = ["inbox", "planned", "active", "waiting", "blocked", "done", "dismissed", "archived"]
INBOX_STATUSES = ["new", "converted", "dismissed", "archived", "snoozed"]
SAFETY_CLASSES = ["informational", "review-only", "read-only-action", "gated-live-action-reference"]
CADENCE_TYPES = ["daily", "weekly", "monthly", "per-session", "event-driven"]
DEFAULT_DAILY_CHECKS = [
    "System safety posture",
    "Live armed/read-only/kill switch state",
    "Data health",
    "Freshness notifications",
    "Dataset readiness",
    "Monitoring alerts",
    "Research queue",
    "Stale evidence",
    "Portfolio/concentration warnings",
    "Governance checklist items",
    "Analytics warnings",
    "Simulation/replay follow-ups",
    "Open tasks",
    "Blocked tasks",
    "Exports/backups if relevant",
    "Safe next actions",
]
DEFAULT_WEEKLY_CHECKS = [
    "Open task rollup",
    "Overdue task rollup",
    "Recurring blockers",
    "Recurring stale data",
    "Unresolved research",
    "Thesis review needs",
    "Dataset/freshness review",
    "Simulation/replay review",
    "Analytics learning report review",
    "Governance improvement items",
    "Backup/data integrity review",
    "Next-week focus",
    "Task plan for the week",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return date.today().isoformat()


def _ensure_dir() -> None:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)


def _record_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _safe_text(value: Any, default: str = "") -> str:
    text = redact_text(str(value or "").strip())
    return text or default


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [redact_text(str(v).strip()) for v in value if str(v or "").strip()]


def _safe_dict(value: Any) -> dict[str, Any]:
    return redact_data(value) if isinstance(value, dict) else {}


def _write_jsonl(path: Path, row: dict[str, Any]) -> None:
    _ensure_dir()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(redact_data(row), sort_keys=True, default=str) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                rows.append(redact_data(parsed))
        except json.JSONDecodeError:
            rows.append({"id": _record_id("invalid"), "created_at": _now(), "status": "invalid_json", "secret_values_returned": False})
    return rows


def _latest_by_id(rows: list[dict[str, Any]], id_key: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        rid = str(row.get(id_key) or row.get("id") or _record_id("row"))
        latest[rid] = row
    return sorted(latest.values(), key=lambda r: str(r.get("updated_at") or r.get("created_at") or ""), reverse=True)


def _parse_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except Exception:
        try:
            return date.fromisoformat(text[:10])
        except Exception:
            return None


def _safety(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "task_planning_is_not_trading": True,
        "task_completion_is_not_trade_approval": True,
        "cadence_is_not_trading_automation": True,
        "not_financial_advice": True,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "mutates_live_trading_state": False,
        "external_network_called": False,
        "ai_model_called": False,
        "secret_values_returned": False,
        "safety_statement": "Operator tasks, daily ops packets, weekly plans, cadence rules, and task exports are local-first human-in-the-loop workflow records. They do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass backend gates, or provide financial advice.",
    }
    if extra:
        base.update(extra)
    return base


def _audit(action: str, status: str = "ok", details: dict[str, Any] | None = None) -> dict[str, Any]:
    event = {
        "event_id": _record_id("task_evt"),
        "timestamp": _now(),
        "app_version": APP_VERSION,
        "action": action,
        "status": status,
        "details": redact_data(details or {}),
        **_safety(),
    }
    _write_jsonl(TASK_EVENTS_PATH, event)
    record_audit(
        f"v3_task_{action}",
        status,
        details={**redact_data(details or {}), "order_submitted": False, "order_cancelled": False, "live_trading_armed": False},
        network_attempted=False,
    )
    return redact_data(event)


def _items(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, dict):
        data = result.get("items", result.get("records", result.get("findings", result.get("checks", []))))
    else:
        data = result
    if not isinstance(data, list):
        return []
    return [redact_data(x) for x in data if isinstance(x, dict)]


def _priority(value: Any, default: str = "medium") -> str:
    text = _safe_text(value, default).lower()
    severity_map = {"blocker": "critical", "critical": "critical", "danger": "urgent", "warning": "high", "warn": "high", "info": "low"}
    text = severity_map.get(text, text)
    return text if text in PRIORITIES else default


def _status(value: Any, default: str = "inbox") -> str:
    text = _safe_text(value, default).lower().replace(" ", "_")
    return text if text in STATUSES else default


def _safety_class(value: Any, source: str = "") -> str:
    text = _safe_text(value).lower().replace("_", "-")
    if text in SAFETY_CLASSES:
        return text
    source_lower = source.lower()
    if "live" in source_lower or "order" in source_lower or "trade" in source_lower:
        return "gated-live-action-reference"
    if "dataset" in source_lower or "freshness" in source_lower or "snapshot" in source_lower:
        return "read-only-action"
    if source_lower:
        return "review-only"
    return "informational"


def _task_base(payload: dict[str, Any] | None = None, *, task_id: str | None = None, created_at: str | None = None) -> dict[str, Any]:
    payload = payload or {}
    now = _now()
    source_subsystem = _safe_text(payload.get("source_subsystem") or payload.get("source") or "manual")
    related_ids = payload.get("related_object_ids") if isinstance(payload.get("related_object_ids"), list) else []
    if payload.get("source_object_id") and payload.get("source_object_id") not in related_ids:
        related_ids.append(payload.get("source_object_id"))
    return redact_data({
        "task_id": task_id or _record_id("task"),
        "created_at": created_at or now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), "Operator task"),
        "description": _safe_text(payload.get("description") or payload.get("message"), "Local operator workflow task."),
        "source_subsystem": source_subsystem,
        "source_object_type": _safe_text(payload.get("source_object_type") or payload.get("object_type") or "manual"),
        "source_object_id": _safe_text(payload.get("source_object_id") or payload.get("object_id") or payload.get("id")),
        "related_object_ids": _safe_list(related_ids),
        "task_type": _safe_text(payload.get("task_type") or payload.get("type") or "review"),
        "priority": _priority(payload.get("priority") or payload.get("severity"), "medium"),
        "status": _status(payload.get("status"), "inbox"),
        "due_date": _safe_text(payload.get("due_date")),
        "cadence_tag": _safe_text(payload.get("cadence_tag")),
        "safety_class": _safety_class(payload.get("safety_class"), source_subsystem),
        "operator_notes": _safe_text(payload.get("operator_notes") or payload.get("notes")),
        "completion_notes": _safe_text(payload.get("completion_notes")),
        "blockers": _safe_list(payload.get("blockers")),
        "unknown_unavailable_data": _safe_list(payload.get("unknown_unavailable_data") or payload.get("unknowns")),
        "tags": _safe_list(payload.get("tags")),
        "follow_up_notes": payload.get("follow_up_notes", []) if isinstance(payload.get("follow_up_notes"), list) else [],
        "dependencies": payload.get("dependencies", []) if isinstance(payload.get("dependencies"), list) else [],
        "audit_metadata": _safe_dict(payload.get("audit_metadata")),
        **_safety(),
    })


def default_task_templates() -> list[dict[str, Any]]:
    now = _now()
    specs = [
        ("tpl_stale_evidence", "Review stale evidence", "research", "Review stale evidence and decide whether to refresh, archive, or escalate it.", "high", "review-only"),
        ("tpl_refresh_dataset", "Refresh dataset", "datasets", "Review dataset freshness and queue an explicit read-only refresh if appropriate.", "high", "read-only-action"),
        ("tpl_monitoring_alert", "Review monitoring alert", "monitoring", "Triage a monitoring alert and document a human review outcome.", "urgent", "review-only"),
        ("tpl_thesis_health", "Run thesis health report", "strategy", "Generate or review thesis health without approving a trade.", "medium", "review-only"),
        ("tpl_pretrade_review", "Run pre-trade packet review", "workflow", "Prepare a pre-trade intelligence packet. Packet review is not trade approval.", "high", "gated-live-action-reference"),
        ("tpl_governance_checklist", "Complete governance checklist", "governance", "Resolve governance checklist items and document blockers.", "high", "review-only"),
        ("tpl_portfolio_warning", "Review portfolio concentration warning", "portfolio", "Review concentration/exposure warning before any next action.", "urgent", "review-only"),
        ("tpl_simulation_replay", "Run simulation replay", "simulation", "Run local descriptive replay/simulation and capture follow-ups.", "medium", "read-only-action"),
        ("tpl_learning_report", "Generate learning report", "analytics", "Generate descriptive learning report and create follow-up tasks.", "medium", "review-only"),
        ("tpl_data_health", "Resolve data health warning", "data", "Review data health warning, backups, and recovery readiness.", "high", "review-only"),
        ("tpl_research_question", "Review unresolved research question", "research", "Resolve, update, or defer a research queue item.", "medium", "review-only"),
        ("tpl_missing_prerequisite", "Review missing prerequisite finding", "v3", "Inspect missing prerequisite and decide safe next operator action.", "high", "review-only"),
        ("tpl_backup_readiness", "Backup/export readiness check", "data", "Review local backups/exports before release or major workflow changes.", "medium", "read-only-action"),
    ]
    return [
        {
            "template_id": tid,
            "created_at": now,
            "updated_at": now,
            "app_version": APP_VERSION,
            "title": title,
            "description": desc,
            "source_subsystem": subsystem,
            "task_type": "review",
            "default_priority": priority,
            "default_status": "planned",
            "safety_class": safety,
            "tags": ["default", subsystem, "v3.7"],
            "editable": True,
            **_safety(),
        }
        for tid, title, subsystem, desc, priority, safety in specs
    ]


def list_task_templates(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(TEMPLATES_PATH), "template_id")
    if not rows:
        rows = default_task_templates()
    return {"version": APP_VERSION, "count": len(rows[:limit]), "items": redact_data(rows[: max(1, min(int(limit or 250), 5000))]), **_safety()}


def create_task_template(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    now = _now()
    template = {
        "template_id": _safe_text(payload.get("template_id")) or _record_id("tpl"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), "Operator task template"),
        "description": _safe_text(payload.get("description"), "Reusable local workflow task template."),
        "source_subsystem": _safe_text(payload.get("source_subsystem"), "manual"),
        "task_type": _safe_text(payload.get("task_type"), "review"),
        "default_priority": _priority(payload.get("default_priority") or payload.get("priority"), "medium"),
        "default_status": _status(payload.get("default_status") or payload.get("status"), "planned"),
        "safety_class": _safety_class(payload.get("safety_class"), _safe_text(payload.get("source_subsystem"), "manual")),
        "tags": _safe_list(payload.get("tags")),
        "editable": True,
        **_safety(),
    }
    _write_jsonl(TEMPLATES_PATH, template)
    _audit("task_template_created", "ok", {"template_id": template["template_id"]})
    return redact_data(template)


def list_tasks(limit: int = 250, status: str | None = None, priority: str | None = None, source_subsystem: str | None = None) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(TASKS_PATH), "task_id")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if priority:
        rows = [r for r in rows if r.get("priority") == priority]
    if source_subsystem:
        rows = [r for r in rows if str(r.get("source_subsystem", "")).lower() == source_subsystem.lower()]
    capped = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(capped), "total_count": len(rows), "items": redact_data(capped), **_safety()}


def get_task(task_id: str) -> dict[str, Any] | None:
    for task in _latest_by_id(_read_jsonl(TASKS_PATH), "task_id"):
        if task.get("task_id") == task_id:
            return redact_data(task)
    return None


def create_task(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    task = _task_base(payload)
    _write_jsonl(TASKS_PATH, task)
    _audit("task_created", "ok", {"task_id": task["task_id"], "source_subsystem": task["source_subsystem"], "safety_class": task["safety_class"]})
    return redact_data(task)


def update_task(task_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    current = get_task(task_id)
    if not current:
        return {"ok": False, "error": "task_not_found", "task_id": redact_text(task_id), **_safety()}
    payload = payload or {}
    updated = dict(current)
    for key in ["title", "description", "source_subsystem", "source_object_type", "source_object_id", "task_type", "due_date", "cadence_tag", "operator_notes", "completion_notes"]:
        if key in payload:
            updated[key] = _safe_text(payload.get(key))
    if "priority" in payload:
        updated["priority"] = _priority(payload.get("priority"), current.get("priority", "medium"))
    if "status" in payload:
        updated["status"] = _status(payload.get("status"), current.get("status", "inbox"))
    if "safety_class" in payload:
        updated["safety_class"] = _safety_class(payload.get("safety_class"), updated.get("source_subsystem", ""))
    for key in ["related_object_ids", "blockers", "unknown_unavailable_data", "tags"]:
        if key in payload:
            updated[key] = _safe_list(payload.get(key))
    if "follow_up_note" in payload:
        notes = updated.get("follow_up_notes") if isinstance(updated.get("follow_up_notes"), list) else []
        notes.append({"note_id": _record_id("note"), "created_at": _now(), "note": _safe_text(payload.get("follow_up_note")), "secret_values_returned": False})
        updated["follow_up_notes"] = notes
    updated["updated_at"] = _now()
    updated.update(_safety())
    _write_jsonl(TASKS_PATH, updated)
    _audit("task_updated", "ok", {"task_id": task_id, "changed_keys": sorted(payload.keys())})
    return redact_data(updated)


def change_task_status(task_id: str, status: str, notes: str = "") -> dict[str, Any]:
    updated = update_task(task_id, {"status": status, "follow_up_note": notes} if notes else {"status": status})
    if updated.get("ok") is False:
        return updated
    _audit("task_status_changed", "ok", {"task_id": task_id, "status": updated.get("status")})
    return updated


def complete_task(task_id: str, notes: str = "") -> dict[str, Any]:
    payload = {"status": "done", "completion_notes": notes or "Operator marked task done. This is not trade approval."}
    updated = update_task(task_id, payload)
    if updated.get("ok") is False:
        return updated
    updated["task_completion_is_not_trade_approval"] = True
    updated["order_submitted"] = False
    _audit("task_completed", "ok", {"task_id": task_id, "task_completion_is_not_trade_approval": True})
    return redact_data(updated)


def archive_task(task_id: str, notes: str = "") -> dict[str, Any]:
    updated = update_task(task_id, {"status": "archived", "follow_up_note": notes} if notes else {"status": "archived"})
    if updated.get("ok") is False:
        return updated
    _audit("task_archived", "ok", {"task_id": task_id})
    return updated


def task_board() -> dict[str, Any]:
    items = list_tasks(limit=5000)["items"]
    columns = []
    for status in ["inbox", "planned", "active", "waiting", "blocked", "done", "archived"]:
        rows = [t for t in items if t.get("status") == status]
        columns.append({"status": status, "title": status.replace("_", " ").title(), "count": len(rows), "items": rows[:100]})
    return {"version": APP_VERSION, "columns": redact_data(columns), "total_count": len(items), **_safety()}


def _inbox_source_key(item: dict[str, Any]) -> str:
    return "|".join([str(item.get("source_subsystem", "")), str(item.get("source_object_type", "")), str(item.get("source_object_id", "")), str(item.get("title", ""))])


def _inbox_item(payload: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    source_subsystem = _safe_text(payload.get("source_subsystem") or payload.get("source") or "manual")
    item = {
        "inbox_id": _safe_text(payload.get("inbox_id")) or _record_id("inbox"),
        "created_at": _safe_text(payload.get("created_at")) or now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), "Suggested operator task"),
        "description": _safe_text(payload.get("description") or payload.get("message"), "Suggested local workflow item."),
        "source_subsystem": source_subsystem,
        "source_object_type": _safe_text(payload.get("source_object_type") or payload.get("object_type") or "finding"),
        "source_object_id": _safe_text(payload.get("source_object_id") or payload.get("object_id") or payload.get("id")),
        "priority": _priority(payload.get("priority") or payload.get("severity"), "medium"),
        "status": _safe_text(payload.get("status"), "new") if _safe_text(payload.get("status"), "new") in INBOX_STATUSES else "new",
        "safety_class": _safety_class(payload.get("safety_class"), source_subsystem),
        "recommended_operator_action": _safe_text(payload.get("recommended_operator_action") or payload.get("action"), "Review and create a task if useful."),
        "related_object_ids": _safe_list(payload.get("related_object_ids")),
        "unknown_unavailable_data": _safe_list(payload.get("unknown_unavailable_data")),
        "tags": _safe_list(payload.get("tags")),
        "converted_task_id": _safe_text(payload.get("converted_task_id")),
        "source_link": _safe_text(payload.get("source_link")),
        **_safety(),
    }
    item["source_key"] = _inbox_source_key(item)
    return redact_data(item)


def list_inbox(limit: int = 250, status: str | None = None) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(INBOX_PATH), "inbox_id")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    capped = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(capped), "total_count": len(rows), "items": redact_data(capped), **_safety()}


def get_inbox_item(inbox_id: str) -> dict[str, Any] | None:
    for item in _latest_by_id(_read_jsonl(INBOX_PATH), "inbox_id"):
        if item.get("inbox_id") == inbox_id:
            return redact_data(item)
    return None


def _write_inbox_update(item: dict[str, Any], action: str) -> dict[str, Any]:
    item["updated_at"] = _now()
    item.update(_safety())
    _write_jsonl(INBOX_PATH, item)
    _audit(action, "ok", {"inbox_id": item.get("inbox_id"), "status": item.get("status")})
    return redact_data(item)


def _suggestions_from_freshness() -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    try:
        from .live_v3_freshness import list_notifications, list_findings
        for note in _items(list_notifications(limit=100, status="new")):
            suggestions.append(_inbox_item({
                "title": note.get("title") or "Review freshness notification",
                "description": note.get("message") or note.get("description") or "Freshness notification needs human triage.",
                "source_subsystem": "freshness",
                "source_object_type": "operator_notification",
                "source_object_id": note.get("notification_id"),
                "priority": note.get("severity", "medium"),
                "recommended_operator_action": "Convert to task, acknowledge, snooze, dismiss, or resolve after review.",
                "source_link": "/v3/freshness/notifications",
                "tags": ["freshness", "notification"],
                "safety_class": "read-only-action",
            }))
        for finding in _items(list_findings(limit=100)):
            suggestions.append(_inbox_item({
                "title": finding.get("title") or "Review freshness finding",
                "description": finding.get("explanation") or finding.get("description") or "Freshness finding needs review.",
                "source_subsystem": "freshness",
                "source_object_type": "freshness_finding",
                "source_object_id": finding.get("finding_id"),
                "priority": finding.get("severity", "high"),
                "recommended_operator_action": finding.get("recommended_operator_action") or "Review stale/missing data and decide whether to queue read-only collection.",
                "source_link": "/v3/freshness",
                "tags": ["freshness", "finding"],
                "safety_class": "read-only-action",
            }))
    except Exception as exc:
        suggestions.append(_inbox_item({"title": "Freshness scan unavailable", "description": f"Freshness integration could not be scanned: {redact_text(str(exc))}", "source_subsystem": "freshness", "priority": "low", "unknown_unavailable_data": ["Freshness scan raised an exception."], "tags": ["freshness", "unknown"]}))
    return suggestions


def _suggestions_from_local_modules() -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    integrations = [
        ("monitoring", "monitoring_alert", "/v2-live/monitoring", "Review monitoring alert", lambda: __import__("app.live_monitoring", fromlist=["list_alerts"]).list_alerts(limit=100)),
        ("portfolio", "portfolio_warning", "/v2-live/portfolio", "Review portfolio warning", lambda: __import__("app.live_portfolio", fromlist=["list_warnings"]).list_warnings(limit=100)),
        ("research", "research_queue_item", "/v2-live/research", "Review research queue item", lambda: __import__("app.live_research", fromlist=["list_queue"]).list_queue(limit=100)),
        ("governance", "governance_checklist", "/v2-live/governance", "Review governance checklist", lambda: __import__("app.live_governance", fromlist=["list_checklists"]).list_checklists(limit=100)),
    ]
    for subsystem, object_type, link, title_default, getter in integrations:
        try:
            for row in _items(getter())[:25]:
                status_text = str(row.get("status") or row.get("severity") or "").lower()
                if status_text in {"done", "completed", "archived", "resolved", "dismissed"}:
                    continue
                rid = row.get("alert_id") or row.get("warning_id") or row.get("queue_id") or row.get("checklist_id") or row.get("id") or row.get("event_id")
                suggestions.append(_inbox_item({
                    "title": row.get("title") or row.get("name") or title_default,
                    "description": row.get("description") or row.get("message") or row.get("notes") or title_default,
                    "source_subsystem": subsystem,
                    "source_object_type": object_type,
                    "source_object_id": rid,
                    "priority": row.get("priority") or row.get("severity") or "medium",
                    "recommended_operator_action": row.get("recommended_operator_action") or title_default,
                    "source_link": link,
                    "tags": [subsystem, object_type],
                    "safety_class": "review-only",
                }))
        except Exception:
            continue
    try:
        from .live_v3_datasets import dataset_quality_report
        quality = dataset_quality_report()
        for finding in _items(quality.get("findings", []))[:50]:
            suggestions.append(_inbox_item({
                "title": finding.get("title") or "Review dataset quality finding",
                "description": finding.get("description") or finding.get("explanation") or "Dataset quality finding needs review.",
                "source_subsystem": "datasets",
                "source_object_type": "dataset_quality_finding",
                "source_object_id": finding.get("finding_id") or finding.get("id"),
                "priority": finding.get("severity") or "high",
                "source_link": "/v3/datasets/quality",
                "tags": ["datasets", "quality"],
                "safety_class": "read-only-action",
            }))
    except Exception:
        pass
    return suggestions


def scan_inbox(write: bool = True, include_existing: bool = True) -> dict[str, Any]:
    existing = list_inbox(limit=5000)["items"] if include_existing else []
    existing_keys = {str(item.get("source_key")) for item in existing if item.get("status") not in {"archived", "dismissed", "converted"}}
    suggestions = _suggestions_from_freshness() + _suggestions_from_local_modules()
    new_items: list[dict[str, Any]] = []
    for item in suggestions:
        key = _inbox_source_key(item)
        if key in existing_keys:
            continue
        existing_keys.add(key)
        new_items.append(item)
        if write:
            _write_jsonl(INBOX_PATH, item)
    _audit("inbox_scan_run", "ok", {"new_items": len(new_items), "write": write})
    return {"version": APP_VERSION, "write": write, "generated_count": len(suggestions), "new_count": len(new_items), "items": redact_data(new_items), **_safety()}


def create_task_from_inbox(inbox_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    item = get_inbox_item(inbox_id)
    if not item:
        return {"ok": False, "error": "inbox_item_not_found", "inbox_id": redact_text(inbox_id), **_safety()}
    payload = payload or {}
    task_payload = {
        "title": payload.get("title") or item.get("title"),
        "description": payload.get("description") or item.get("description"),
        "source_subsystem": item.get("source_subsystem"),
        "source_object_type": item.get("source_object_type"),
        "source_object_id": item.get("source_object_id"),
        "related_object_ids": item.get("related_object_ids", []),
        "priority": payload.get("priority") or item.get("priority"),
        "status": payload.get("status") or "planned",
        "task_type": payload.get("task_type") or "review",
        "due_date": payload.get("due_date"),
        "tags": list(dict.fromkeys((item.get("tags") or []) + _safe_list(payload.get("tags")))),
        "safety_class": item.get("safety_class"),
        "unknown_unavailable_data": item.get("unknown_unavailable_data", []),
        "operator_notes": payload.get("operator_notes") or "Created from task inbox after operator review.",
    }
    task = create_task(task_payload)
    item["status"] = "converted"
    item["converted_task_id"] = task["task_id"]
    _write_inbox_update(item, "inbox_item_converted_to_task")
    _audit("notification_or_finding_converted_to_task", "ok", {"inbox_id": inbox_id, "task_id": task["task_id"]})
    return {"ok": True, "task": task, "inbox_item": redact_data(item), **_safety()}


def dismiss_inbox_item(inbox_id: str, notes: str = "") -> dict[str, Any]:
    item = get_inbox_item(inbox_id)
    if not item:
        return {"ok": False, "error": "inbox_item_not_found", "inbox_id": redact_text(inbox_id), **_safety()}
    item["status"] = "dismissed"
    item["operator_notes"] = _safe_text(notes)
    return _write_inbox_update(item, "task_inbox_item_dismissed")


def archive_inbox_item(inbox_id: str, notes: str = "") -> dict[str, Any]:
    item = get_inbox_item(inbox_id)
    if not item:
        return {"ok": False, "error": "inbox_item_not_found", "inbox_id": redact_text(inbox_id), **_safety()}
    item["status"] = "archived"
    item["operator_notes"] = _safe_text(notes)
    return _write_inbox_update(item, "task_inbox_item_archived")


def snooze_inbox_item(inbox_id: str, snooze_minutes: int = 240, notes: str = "") -> dict[str, Any]:
    item = get_inbox_item(inbox_id)
    if not item:
        return {"ok": False, "error": "inbox_item_not_found", "inbox_id": redact_text(inbox_id), **_safety()}
    item["status"] = "snoozed"
    item["snoozed_until"] = (datetime.now(timezone.utc) + timedelta(minutes=max(1, int(snooze_minutes or 240)))).isoformat()
    item["operator_notes"] = _safe_text(notes)
    return _write_inbox_update(item, "task_inbox_item_snoozed")


def create_task_from_notification(notification_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    # Prefer an existing inbox suggestion; fall back to scanning freshness notifications.
    for item in list_inbox(limit=5000)["items"]:
        if item.get("source_object_type") == "operator_notification" and item.get("source_object_id") == notification_id:
            return create_task_from_inbox(str(item.get("inbox_id")), payload)
    scan_inbox(write=True)
    for item in list_inbox(limit=5000)["items"]:
        if item.get("source_object_type") == "operator_notification" and item.get("source_object_id") == notification_id:
            return create_task_from_inbox(str(item.get("inbox_id")), payload)
    return {"ok": False, "error": "notification_not_found", "notification_id": redact_text(notification_id), **_safety()}


def create_task_from_finding(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    task = create_task({
        "title": payload.get("title") or "Review finding",
        "description": payload.get("description") or payload.get("explanation") or "Finding converted to local operator task.",
        "source_subsystem": payload.get("source_subsystem") or payload.get("source") or "finding",
        "source_object_type": payload.get("source_object_type") or "finding",
        "source_object_id": payload.get("source_object_id") or payload.get("finding_id") or payload.get("id"),
        "priority": payload.get("priority") or payload.get("severity") or "high",
        "status": payload.get("status") or "planned",
        "safety_class": payload.get("safety_class") or "review-only",
        "tags": payload.get("tags") if isinstance(payload.get("tags"), list) else ["finding"],
        "unknown_unavailable_data": payload.get("unknown_unavailable_data", []),
        "operator_notes": payload.get("operator_notes") or "Created from finding after operator review.",
    })
    _audit("finding_converted_to_task", "ok", {"task_id": task["task_id"], "source_subsystem": task.get("source_subsystem")})
    return {"ok": True, "task": task, **_safety()}


def default_cadence_rules() -> list[dict[str, Any]]:
    now = _now()
    specs = [
        ("cad_daily_ops", "Daily operator safety and task review", "daily", "v3_tasks", "daily_ops", "Every operating day", "tpl_missing_prerequisite"),
        ("cad_weekly_plan", "Weekly planning review", "weekly", "v3_tasks", "weekly_plan", "Every week", "tpl_backup_readiness"),
        ("cad_thesis_review", "Thesis health review", "weekly", "strategy", "thesis", "Weekly or after material news", "tpl_thesis_health"),
        ("cad_evidence_freshness", "Evidence freshness review", "daily", "research", "evidence", "Daily for active theses", "tpl_stale_evidence"),
        ("cad_dataset_readiness", "Dataset readiness review", "weekly", "datasets", "dataset_manifest", "Before simulation/replay", "tpl_refresh_dataset"),
        ("cad_simulation_review", "Simulation follow-up review", "weekly", "simulation", "simulation_session", "After replay/process tests", "tpl_simulation_replay"),
        ("cad_analytics_learning", "Analytics learning report review", "weekly", "analytics", "learning_report", "Weekly", "tpl_learning_report"),
        ("cad_governance", "Governance review", "weekly", "governance", "checklist", "Weekly and before gated live references", "tpl_governance_checklist"),
    ]
    return [
        {
            "cadence_id": cid,
            "created_at": now,
            "updated_at": now,
            "app_version": APP_VERSION,
            "title": title,
            "description": f"Default v3.7 review cadence for {target_subsystem} / {target_object_type}.",
            "cadence_type": ctype,
            "target_subsystem": target_subsystem,
            "target_object_type": target_object_type,
            "target_object_id": "",
            "recurrence_hint": recurrence,
            "freshness_threshold": 1440 if ctype == "daily" else 10080,
            "task_template_id": template_id,
            "enabled": True,
            "operator_notes": "Default editable cadence rule. Generation is operator-triggered.",
            "audit_metadata": {},
            **_safety(),
        }
        for cid, title, ctype, target_subsystem, target_object_type, recurrence, template_id in specs
    ]


def list_cadence_rules(limit: int = 250, enabled: bool | None = None) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(CADENCE_PATH), "cadence_id")
    if not rows:
        rows = default_cadence_rules()
    if enabled is not None:
        rows = [r for r in rows if bool(r.get("enabled")) is enabled]
    return {"version": APP_VERSION, "count": len(rows[:limit]), "items": redact_data(rows[: max(1, min(int(limit or 250), 5000))]), **_safety()}


def create_cadence_rule(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    now = _now()
    ctype = _safe_text(payload.get("cadence_type"), "weekly")
    if ctype not in CADENCE_TYPES:
        ctype = "weekly"
    rule = {
        "cadence_id": _safe_text(payload.get("cadence_id")) or _record_id("cad"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), "Review cadence rule"),
        "description": _safe_text(payload.get("description"), "Operator-triggered cadence rule."),
        "cadence_type": ctype,
        "target_subsystem": _safe_text(payload.get("target_subsystem"), "v3_tasks"),
        "target_object_type": _safe_text(payload.get("target_object_type"), "review"),
        "target_object_id": _safe_text(payload.get("target_object_id")),
        "recurrence_hint": _safe_text(payload.get("recurrence_hint"), ctype),
        "freshness_threshold": int(payload.get("freshness_threshold") or 0),
        "task_template_id": _safe_text(payload.get("task_template_id")),
        "enabled": bool(payload.get("enabled", True)),
        "operator_notes": _safe_text(payload.get("operator_notes") or payload.get("notes")),
        "audit_metadata": _safe_dict(payload.get("audit_metadata")),
        **_safety(),
    }
    _write_jsonl(CADENCE_PATH, rule)
    _audit("cadence_rule_created", "ok", {"cadence_id": rule["cadence_id"]})
    return redact_data(rule)


def run_cadence(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    create_tasks_directly = bool(payload.get("create_tasks", False))
    rules = [r for r in list_cadence_rules(limit=1000, enabled=True)["items"] if bool(r.get("enabled", True))]
    created_inbox: list[dict[str, Any]] = []
    created_tasks: list[dict[str, Any]] = []
    for rule in rules:
        title = f"Cadence review: {rule.get('title')}"
        base = {
            "title": title,
            "description": rule.get("description") or "Cadence-generated operator review suggestion.",
            "source_subsystem": rule.get("target_subsystem") or "v3_tasks",
            "source_object_type": rule.get("target_object_type") or "cadence_rule",
            "source_object_id": rule.get("target_object_id") or rule.get("cadence_id"),
            "priority": "high" if rule.get("cadence_type") in {"daily", "event-driven"} else "medium",
            "cadence_tag": rule.get("cadence_type"),
            "tags": ["cadence", str(rule.get("cadence_type")), str(rule.get("target_subsystem"))],
            "safety_class": _safety_class("review-only", str(rule.get("target_subsystem"))),
            "operator_notes": "Generated by an operator-triggered cadence run.",
        }
        if create_tasks_directly:
            created_tasks.append(create_task({**base, "status": "planned"}))
        else:
            inbox = _inbox_item({**base, "recommended_operator_action": "Review cadence item and create a planned task if still relevant."})
            _write_jsonl(INBOX_PATH, inbox)
            created_inbox.append(inbox)
    event = {"event_id": _record_id("cad_run"), "created_at": _now(), "updated_at": _now(), "app_version": APP_VERSION, "rule_count": len(rules), "created_inbox_count": len(created_inbox), "created_task_count": len(created_tasks), "operator_triggered": True, **_safety()}
    _write_jsonl(CADENCE_EVENTS_PATH, event)
    _audit("cadence_run_generated_tasks", "ok", {"created_inbox_count": len(created_inbox), "created_task_count": len(created_tasks), "create_tasks_directly": create_tasks_directly})
    return {"version": APP_VERSION, "event": redact_data(event), "inbox_items": redact_data(created_inbox), "tasks": redact_data(created_tasks), **_safety()}


def task_summary() -> dict[str, Any]:
    tasks = list_tasks(limit=5000)["items"]
    inbox = list_inbox(limit=5000)["items"]
    today = date.today()
    open_statuses = {"inbox", "planned", "active", "waiting", "blocked"}
    open_tasks = [t for t in tasks if t.get("status") in open_statuses]
    overdue = [t for t in open_tasks if (d := _parse_date(t.get("due_date"))) and d < today]
    due_today = [t for t in open_tasks if _parse_date(t.get("due_date")) == today]
    urgent = [t for t in open_tasks if t.get("priority") in {"urgent", "critical"}]
    blocked = [t for t in open_tasks if t.get("status") == "blocked"]
    daily = _latest_by_id(_read_jsonl(DAILY_OPS_PATH), "packet_id")
    weekly = _latest_by_id(_read_jsonl(WEEKLY_OPS_PATH), "packet_id")
    status_counts = {status: len([t for t in tasks if t.get("status") == status]) for status in STATUSES}
    priority_counts = {priority: len([t for t in tasks if t.get("priority") == priority]) for priority in PRIORITIES}
    next_task = sorted(open_tasks, key=lambda t: (PRIORITIES.index(t.get("priority", "low")) if t.get("priority") in PRIORITIES else 0, str(t.get("due_date") or "9999")), reverse=True)[:1]
    return redact_data({
        "version": APP_VERSION,
        "open_tasks": len(open_tasks),
        "total_tasks": len(tasks),
        "inbox_items": len([i for i in inbox if i.get("status") in {"new", "snoozed"}]),
        "urgent_tasks": len(urgent),
        "blocked_tasks": len(blocked),
        "overdue_tasks": len(overdue),
        "tasks_due_today": len(due_today),
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "daily_checklist_status": "generated" if daily and str(daily[0].get("date")) == _today() else "not_generated_today",
        "weekly_planning_status": "generated" if weekly else "not_generated",
        "next_operator_task": next_task[0] if next_task else None,
        "latest_daily_ops_packet": daily[0] if daily else None,
        "latest_weekly_ops_packet": weekly[0] if weekly else None,
        **_safety(),
    })


def today_view() -> dict[str, Any]:
    today = date.today()
    tasks = [t for t in list_tasks(limit=5000)["items"] if t.get("status") in {"planned", "active", "waiting", "blocked", "inbox"}]
    due_today = [t for t in tasks if _parse_date(t.get("due_date")) == today]
    overdue = [t for t in tasks if (d := _parse_date(t.get("due_date"))) and d < today]
    no_due_high = [t for t in tasks if not t.get("due_date") and t.get("priority") in {"urgent", "critical", "high"}]
    return {"version": APP_VERSION, "date": _today(), "checklist": DEFAULT_DAILY_CHECKS, "due_today": redact_data(due_today), "overdue": redact_data(overdue), "high_priority_without_due_date": redact_data(no_due_high), "summary": task_summary(), **_safety()}


def week_view() -> dict[str, Any]:
    today = date.today()
    end = today + timedelta(days=7)
    tasks = [t for t in list_tasks(limit=5000)["items"] if t.get("status") in {"planned", "active", "waiting", "blocked", "inbox"}]
    due_week = [t for t in tasks if (d := _parse_date(t.get("due_date"))) and today <= d <= end]
    overdue = [t for t in tasks if (d := _parse_date(t.get("due_date"))) and d < today]
    return {"version": APP_VERSION, "week_start": today.isoformat(), "week_end": end.isoformat(), "checklist": DEFAULT_WEEKLY_CHECKS, "due_this_week": redact_data(due_week), "overdue": redact_data(overdue), "summary": task_summary(), **_safety()}


def generate_daily_ops_packet(payload: dict[str, Any] | None = None, write: bool = True) -> dict[str, Any]:
    payload = payload or {}
    summary = task_summary()
    checks_payload = payload.get("completed_checks") if isinstance(payload.get("completed_checks"), list) else []
    completed_checks = _safe_list(checks_payload) or []
    unresolved = []
    if summary.get("overdue_tasks"):
        unresolved.append(f"{summary.get('overdue_tasks')} overdue task(s) need review.")
    if summary.get("blocked_tasks"):
        unresolved.append(f"{summary.get('blocked_tasks')} blocked task(s) need unblock planning.")
    if summary.get("inbox_items"):
        unresolved.append(f"{summary.get('inbox_items')} inbox item(s) need triage.")
    packet = {
        "packet_id": _record_id("daily_ops"),
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "date": _safe_text(payload.get("date"), _today()),
        "summary": _safe_text(payload.get("summary"), "Daily operator workflow packet."),
        "checklist": DEFAULT_DAILY_CHECKS,
        "completed_checks": completed_checks,
        "unresolved_items": unresolved + _safe_list(payload.get("unresolved_items")),
        "tasks_created": _safe_list(payload.get("tasks_created")),
        "tasks_completed": _safe_list(payload.get("tasks_completed")),
        "blockers": _safe_list(payload.get("blockers")) + (["Blocked tasks exist."] if summary.get("blocked_tasks") else []),
        "unknown_unavailable_data": _safe_list(payload.get("unknown_unavailable_data")) or ["Unavailable source data is shown as unknown and must be manually reviewed."],
        "task_summary": summary,
        **_safety(),
    }
    if write:
        _write_jsonl(DAILY_OPS_PATH, packet)
        _audit("daily_ops_packet_generated", "ok", {"packet_id": packet["packet_id"]})
    return redact_data(packet)


def generate_weekly_plan(payload: dict[str, Any] | None = None, write: bool = True) -> dict[str, Any]:
    payload = payload or {}
    summary = task_summary()
    view = week_view()
    packet = {
        "packet_id": _record_id("weekly_ops"),
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "week_start": _safe_text(payload.get("week_start"), view["week_start"]),
        "week_end": _safe_text(payload.get("week_end"), view["week_end"]),
        "summary": _safe_text(payload.get("summary"), "Weekly planning packet."),
        "checklist": DEFAULT_WEEKLY_CHECKS,
        "open_task_rollup": summary.get("status_counts", {}),
        "overdue_task_rollup": view.get("overdue", []),
        "recurring_blockers": _safe_list(payload.get("recurring_blockers")),
        "recurring_stale_data": _safe_list(payload.get("recurring_stale_data")),
        "unresolved_research": _safe_list(payload.get("unresolved_research")),
        "review_needs": ["thesis", "dataset", "freshness", "simulation", "analytics", "governance", "backup"],
        "next_week_focus": _safe_list(payload.get("next_week_focus")) or ["Triage inbox", "Unblock critical tasks", "Review dataset freshness before simulations"],
        "task_plan_for_week": view.get("due_this_week", []),
        "blockers": _safe_list(payload.get("blockers")) + (["Blocked tasks exist."] if summary.get("blocked_tasks") else []),
        "unknown_unavailable_data": _safe_list(payload.get("unknown_unavailable_data")) or ["Unavailable source data is shown as unknown and must be manually reviewed."],
        **_safety(),
    }
    if write:
        _write_jsonl(WEEKLY_OPS_PATH, packet)
        _audit("weekly_planning_packet_generated", "ok", {"packet_id": packet["packet_id"]})
    return redact_data(packet)


def build_settings() -> dict[str, Any]:
    defaults = {
        "version": APP_VERSION,
        "task_generation_on_startup": False,
        "cadence_generation_on_startup": False,
        "auto_create_tasks_from_notifications": False,
        "default_task_status": "planned",
        "default_priority": "medium",
        "default_daily_ops_enabled": True,
        "default_weekly_planning_enabled": True,
        "external_network_on_task_pages": False,
        "ai_model_calls_on_task_pages": False,
        **_safety(),
    }
    if SETTINGS_PATH.exists():
        try:
            current = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            current = {}
        if isinstance(current, dict):
            defaults.update(redact_data(current))
    defaults["task_generation_on_startup"] = False
    defaults["cadence_generation_on_startup"] = False
    return redact_data(defaults)


def update_settings(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    settings = build_settings()
    allowed = {"auto_create_tasks_from_notifications", "default_task_status", "default_priority", "default_daily_ops_enabled", "default_weekly_planning_enabled"}
    for key in allowed:
        if key in payload:
            if key == "default_task_status":
                settings[key] = _status(payload.get(key), "planned")
            elif key == "default_priority":
                settings[key] = _priority(payload.get(key), "medium")
            else:
                settings[key] = bool(payload.get(key))
    settings["updated_at"] = _now()
    settings["task_generation_on_startup"] = False
    settings["cadence_generation_on_startup"] = False
    _ensure_dir()
    SETTINGS_PATH.write_text(json.dumps(redact_data(settings), indent=2, sort_keys=True, default=str), encoding="utf-8")
    _audit("task_settings_changed", "ok", {"changed_keys": sorted(set(payload.keys()) & allowed)})
    return redact_data(settings)


def export_json() -> dict[str, Any]:
    summary = task_summary()
    export = {
        "export_id": _record_id("task_export"),
        "created_at": _now(),
        "app_version": APP_VERSION,
        "summary": summary,
        "tasks": list_tasks(limit=5000)["items"],
        "inbox": list_inbox(limit=5000)["items"],
        "cadence_rules": list_cadence_rules(limit=5000)["items"],
        "task_templates": list_task_templates(limit=5000)["items"],
        "daily_ops_packets": _latest_by_id(_read_jsonl(DAILY_OPS_PATH), "packet_id")[:100],
        "weekly_ops_packets": _latest_by_id(_read_jsonl(WEEKLY_OPS_PATH), "packet_id")[:100],
        "warnings": ["Task exports are workflow records only and do not place or cancel orders."],
        "limitations": ["Runtime source data may be unavailable or incomplete; unknown values are explicit."],
        **_safety(),
    }
    _write_jsonl(EXPORT_MANIFESTS_PATH, {"export_id": export["export_id"], "created_at": export["created_at"], "app_version": APP_VERSION, "included_task_ids": [t.get("task_id") for t in export["tasks"]], "status_summary": summary.get("status_counts", {}), **_safety()})
    _audit("task_export_generated", "ok", {"export_id": export["export_id"], "format": "json"})
    return redact_data(export)


def export_markdown() -> str:
    data = export_json()
    lines = [
        f"# Operator Task Export — {APP_VERSION}",
        "",
        f"Generated: {data.get('created_at')}",
        "",
        "> Safety: task planning does not place orders, cancel orders, approve trades, sign transactions, arm live trading, or provide financial advice.",
        "",
        "## Summary",
        f"- Open tasks: {data['summary'].get('open_tasks')}",
        f"- Urgent tasks: {data['summary'].get('urgent_tasks')}",
        f"- Blocked tasks: {data['summary'].get('blocked_tasks')}",
        f"- Overdue tasks: {data['summary'].get('overdue_tasks')}",
        f"- Inbox items: {data['summary'].get('inbox_items')}",
        "",
        "## Tasks",
    ]
    for task in data.get("tasks", [])[:250]:
        lines.append(f"- [{task.get('status')}] {task.get('priority')} — {task.get('title')} ({task.get('task_id')})")
        if task.get("blockers"):
            lines.append(f"  - Blockers: {', '.join(task.get('blockers', []))}")
        if task.get("unknown_unavailable_data"):
            lines.append(f"  - Unknown/unavailable: {', '.join(task.get('unknown_unavailable_data', []))}")
    if not data.get("tasks"):
        lines.append("- No task records yet.")
    return "\n".join(lines) + "\n"


def export_csv(kind: str = "tasks") -> str:
    output = io.StringIO()
    if kind == "inbox":
        rows = list_inbox(limit=5000)["items"]
        fields = ["inbox_id", "created_at", "title", "source_subsystem", "source_object_type", "priority", "status", "safety_class"]
    elif kind == "cadence":
        rows = list_cadence_rules(limit=5000)["items"]
        fields = ["cadence_id", "title", "cadence_type", "target_subsystem", "target_object_type", "enabled", "task_template_id"]
    else:
        rows = list_tasks(limit=5000)["items"]
        fields = ["task_id", "created_at", "updated_at", "title", "source_subsystem", "task_type", "priority", "status", "due_date", "safety_class"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(redact_data(row))
    _audit("task_export_generated", "ok", {"format": "csv", "kind": kind})
    return output.getvalue()


def export_daily_ops_json() -> dict[str, Any]:
    packets = _latest_by_id(_read_jsonl(DAILY_OPS_PATH), "packet_id")
    return {"version": APP_VERSION, "count": len(packets), "items": redact_data(packets[:500]), **_safety()}


def export_daily_ops_markdown() -> str:
    packets = export_daily_ops_json()["items"]
    lines = [f"# Daily Ops Packets — {APP_VERSION}", "", "> Daily ops packets are local workflow reviews and never approve or submit trades.", ""]
    for packet in packets[:50]:
        lines.append(f"## {packet.get('date')} — {packet.get('packet_id')}")
        lines.append(packet.get("summary", ""))
        for item in packet.get("unresolved_items", []):
            lines.append(f"- Unresolved: {item}")
    if not packets:
        lines.append("No daily ops packets generated yet.")
    return "\n".join(lines) + "\n"


def export_weekly_ops_json() -> dict[str, Any]:
    packets = _latest_by_id(_read_jsonl(WEEKLY_OPS_PATH), "packet_id")
    return {"version": APP_VERSION, "count": len(packets), "items": redact_data(packets[:500]), **_safety()}


def export_weekly_ops_markdown() -> str:
    packets = export_weekly_ops_json()["items"]
    lines = [f"# Weekly Ops Packets — {APP_VERSION}", "", "> Weekly planning packets are local workflow reviews and never approve or submit trades.", ""]
    for packet in packets[:50]:
        lines.append(f"## {packet.get('week_start')} to {packet.get('week_end')} — {packet.get('packet_id')}")
        lines.append(packet.get("summary", ""))
        for item in packet.get("next_week_focus", []):
            lines.append(f"- Focus: {item}")
    if not packets:
        lines.append("No weekly ops packets generated yet.")
    return "\n".join(lines) + "\n"


def tasks_search_items(limit: int = 250) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in list_tasks(limit=limit)["items"]:
        rows.append({"result_id": f"task:{task.get('task_id')}", "result_type": "operator_task", "title": task.get("title"), "summary": task.get("description"), "status": task.get("status"), "timestamp": task.get("updated_at"), "url": "/v3/tasks/board", "tags": task.get("tags", []), "search_text": " ".join(str(v).lower() for v in [task.get("title"), task.get("description"), task.get("source_subsystem"), task.get("status"), task.get("priority"), " ".join(task.get("tags", []) if isinstance(task.get("tags"), list) else [])]), "secret_values_returned": False})
    for item in list_inbox(limit=limit)["items"]:
        rows.append({"result_id": f"task_inbox:{item.get('inbox_id')}", "result_type": "task_inbox_item", "title": item.get("title"), "summary": item.get("description"), "status": item.get("status"), "timestamp": item.get("updated_at"), "url": "/v3/tasks/inbox", "tags": item.get("tags", []), "search_text": " ".join(str(v).lower() for v in [item.get("title"), item.get("description"), item.get("source_subsystem"), item.get("status"), " ".join(item.get("tags", []) if isinstance(item.get("tags"), list) else [])]), "secret_values_returned": False})
    for rule in list_cadence_rules(limit=limit)["items"]:
        rows.append({"result_id": f"cadence:{rule.get('cadence_id')}", "result_type": "cadence_rule", "title": rule.get("title"), "summary": rule.get("description"), "status": "enabled" if rule.get("enabled") else "disabled", "timestamp": rule.get("updated_at"), "url": "/v3/tasks/cadence", "tags": ["cadence", rule.get("cadence_type", "")], "search_text": " ".join(str(v).lower() for v in [rule.get("title"), rule.get("description"), rule.get("target_subsystem"), rule.get("cadence_type"), "cadence"]), "secret_values_returned": False})
    for packet in _latest_by_id(_read_jsonl(DAILY_OPS_PATH), "packet_id")[:limit]:
        rows.append({"result_id": f"daily_ops:{packet.get('packet_id')}", "result_type": "daily_ops_packet", "title": f"Daily Ops Packet {packet.get('date')}", "summary": packet.get("summary"), "status": "generated", "timestamp": packet.get("created_at"), "url": "/v3/tasks/today", "tags": ["daily_ops"], "search_text": f"daily ops packet task {packet.get('summary', '')}", "secret_values_returned": False})
    for packet in _latest_by_id(_read_jsonl(WEEKLY_OPS_PATH), "packet_id")[:limit]:
        rows.append({"result_id": f"weekly_ops:{packet.get('packet_id')}", "result_type": "weekly_ops_packet", "title": f"Weekly Ops Packet {packet.get('week_start')}", "summary": packet.get("summary"), "status": "generated", "timestamp": packet.get("created_at"), "url": "/v3/tasks/week", "tags": ["weekly_ops"], "search_text": f"weekly ops packet task {packet.get('summary', '')}", "secret_values_returned": False})
    rows.sort(key=lambda r: str(r.get("timestamp") or ""), reverse=True)
    return redact_data(rows[: max(1, min(int(limit or 250), 5000))])


def tasks_graph_nodes_edges() -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for task in list_tasks(limit=500)["items"]:
        task_node = f"operator_task:{task.get('task_id')}"
        nodes.append({"node_id": task_node, "node_type": "operator_task", "title": task.get("title"), "status": task.get("status"), "timestamp": task.get("updated_at"), "summary": task.get("description"), "secret_values_returned": False})
        if task.get("source_object_id"):
            source_node = f"{task.get('source_object_type')}:{task.get('source_object_id')}"
            nodes.append({"node_id": source_node, "node_type": task.get("source_object_type") or "source_object", "title": task.get("source_object_id"), "status": "linked", "summary": task.get("source_subsystem"), "secret_values_returned": False})
            edges.append({"edge_id": f"edge:{task_node}:created_from:{source_node}", "from": task_node, "to": source_node, "relationship": "created_from", "secret_values_returned": False})
        for dep in task.get("dependencies", []) if isinstance(task.get("dependencies"), list) else []:
            edges.append({"edge_id": f"edge:{task_node}:depends_on:{dep}", "from": task_node, "to": str(dep), "relationship": "depends_on", "secret_values_returned": False})
    for item in list_inbox(limit=250)["items"]:
        node = f"task_inbox_item:{item.get('inbox_id')}"
        nodes.append({"node_id": node, "node_type": "task_inbox_item", "title": item.get("title"), "status": item.get("status"), "timestamp": item.get("updated_at"), "summary": item.get("description"), "secret_values_returned": False})
        if item.get("converted_task_id"):
            edges.append({"edge_id": f"edge:{node}:generated_from:operator_task:{item.get('converted_task_id')}", "from": node, "to": f"operator_task:{item.get('converted_task_id')}", "relationship": "generated_from", "secret_values_returned": False})
    for rule in list_cadence_rules(limit=250)["items"]:
        nodes.append({"node_id": f"cadence_rule:{rule.get('cadence_id')}", "node_type": "cadence_rule", "title": rule.get("title"), "status": "enabled" if rule.get("enabled") else "disabled", "timestamp": rule.get("updated_at"), "summary": rule.get("description"), "secret_values_returned": False})
    return {"nodes": redact_data(nodes), "edges": redact_data(edges), "node_count": len(nodes), "edge_count": len(edges), **_safety()}


def task_context_for_subsystem(subsystem: str, limit: int = 20) -> dict[str, Any]:
    tasks = [t for t in list_tasks(limit=5000)["items"] if str(t.get("source_subsystem", "")).lower() == subsystem.lower()]
    return {"version": APP_VERSION, "subsystem": redact_text(subsystem), "count": len(tasks[:limit]), "items": redact_data(tasks[: max(1, min(int(limit or 20), 500))]), **_safety()}


def build_task_context() -> dict[str, Any]:
    return {"summary": task_summary(), "today": today_view(), "week": week_view(), "board": task_board(), "inbox": list_inbox(limit=100), "cadence": list_cadence_rules(limit=100), "templates": list_task_templates(limit=100), "settings": build_settings(), **_safety()}


def create_demo_task_records(write_runtime: bool = True) -> dict[str, Any]:
    now = _now()
    records = [
        {"title": "DEMO urgent freshness review", "description": "Fake urgent task linked to stale dataset finding.", "source_subsystem": "freshness", "source_object_type": "freshness_finding", "source_object_id": "demo-stale-dataset-v37", "priority": "urgent", "status": "active", "due_date": _today(), "tags": ["demo", "freshness"], "safety_class": "read-only-action"},
        {"title": "DEMO blocked governance follow-up", "description": "Fake blocked task linked to a governance checklist item.", "source_subsystem": "governance", "source_object_type": "governance_checklist", "source_object_id": "demo-governance-v37", "priority": "high", "status": "blocked", "blockers": ["Need human review notes."], "tags": ["demo", "governance"], "safety_class": "review-only"},
        {"title": "DEMO completed simulation replay review", "description": "Fake completed replay follow-up task.", "source_subsystem": "simulation", "source_object_type": "simulation_report", "source_object_id": "demo-simulation-v37", "priority": "medium", "status": "done", "completion_notes": "Reviewed fake report only.", "tags": ["demo", "simulation"], "safety_class": "read-only-action"},
        {"title": "DEMO overdue research queue item", "description": "Fake overdue research task.", "source_subsystem": "research", "source_object_type": "research_queue_item", "source_object_id": "demo-research-v37", "priority": "high", "status": "planned", "due_date": (date.today() - timedelta(days=1)).isoformat(), "tags": ["demo", "research"], "safety_class": "review-only"},
    ]
    inbox = _inbox_item({"title": "DEMO task inbox item", "description": "Fake inbox suggestion ready to convert to a task.", "source_subsystem": "notifications", "source_object_type": "operator_notification", "source_object_id": "demo-note-v37", "priority": "medium", "tags": ["demo", "inbox"], "safety_class": "review-only"})
    created: list[dict[str, Any]] = []
    if write_runtime:
        for row in records:
            created.append(create_task(row))
        _write_jsonl(INBOX_PATH, inbox)
        for rule in default_cadence_rules()[:3]:
            _write_jsonl(CADENCE_PATH, rule)
        for tpl in default_task_templates()[:3]:
            _write_jsonl(TEMPLATES_PATH, tpl)
        generate_daily_ops_packet({"summary": "DEMO daily ops packet with fake tasks."}, write=True)
        generate_weekly_plan({"summary": "DEMO weekly planning packet with fake tasks."}, write=True)
    return {"version": APP_VERSION, "created_task_count": len(created), "inbox_item": inbox, "tasks": redact_data(created or records), "demo_data_is_fake": True, "secret_values_returned": False, "created_at": now, **_safety()}


def demo_fixture() -> dict[str, Any]:
    return {
        "tasks": {
            "inbox_item": _inbox_item({"title": "DEMO inbox item: review stale dataset finding", "description": "Fake task inbox item for v3.7 demo fixture.", "source_subsystem": "freshness", "source_object_type": "freshness_finding", "source_object_id": "demo-stale-dataset-v37", "priority": "high", "tags": ["demo", "tasks"]}),
            "urgent_task": _task_base({"title": "DEMO urgent task: review notification", "description": "Fake urgent task; no orders are placed.", "source_subsystem": "freshness", "priority": "urgent", "status": "active", "safety_class": "read-only-action", "tags": ["demo"]}),
            "blocked_task": _task_base({"title": "DEMO blocked task: governance checklist", "description": "Fake blocked governance task.", "source_subsystem": "governance", "priority": "high", "status": "blocked", "blockers": ["Need human notes"], "tags": ["demo"]}),
            "completed_task": _task_base({"title": "DEMO completed task: simulation review", "description": "Fake completed simulation task.", "source_subsystem": "simulation", "priority": "medium", "status": "done", "completion_notes": "Reviewed fake output only.", "tags": ["demo"]}),
            "overdue_task": _task_base({"title": "DEMO overdue task: research queue", "description": "Fake overdue research task.", "source_subsystem": "research", "priority": "high", "status": "planned", "due_date": (date.today() - timedelta(days=1)).isoformat(), "tags": ["demo"]}),
            "daily_ops_checklist": DEFAULT_DAILY_CHECKS,
            "weekly_planning_packet": generate_weekly_plan({"summary": "Fake weekly planning packet fixture."}, write=False),
            "cadence_rule": default_cadence_rules()[0],
            "task_template": default_task_templates()[0],
            "safe_demo_data": True,
            "contains_sensitive_values": False,
        },
        **_safety(),
    }
