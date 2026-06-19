from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_v2 import record_audit, redact_data, redact_text

WORKSPACE_DIR = DATA_DIR / "live_v3" / "workspace"
WORKSPACE_EVENTS_PATH = WORKSPACE_DIR / "workspace_events.jsonl"
FLOWS_PATH = WORKSPACE_DIR / "guided_review_flows.jsonl"
SESSIONS_PATH = WORKSPACE_DIR / "guided_review_sessions.jsonl"
PACKETS_PATH = WORKSPACE_DIR / "guided_review_packets.jsonl"
DEPENDENCIES_PATH = WORKSPACE_DIR / "task_dependencies.jsonl"
SOURCE_PREVIEWS_PATH = WORKSPACE_DIR / "source_previews.jsonl"
SAVED_VIEWS_PATH = WORKSPACE_DIR / "saved_task_views.jsonl"
SETTINGS_PATH = WORKSPACE_DIR / "settings.json"
EXPORT_MANIFESTS_PATH = WORKSPACE_DIR / "export_manifests.jsonl"

FLOW_TYPES = [
    "daily-review",
    "weekly-review",
    "task-triage",
    "blocked-task-review",
    "dataset-review",
    "freshness-review",
    "simulation-review",
    "analytics-review",
    "governance-review",
    "monitoring-review",
    "portfolio-review",
    "research-review",
    "custom",
]
SESSION_STATUSES = ["draft", "active", "completed", "abandoned", "archived"]
SAFETY_CLASSES = ["informational", "review-only", "read-only-action", "gated-live-action-reference"]

DAILY_REVIEW_STEPS = [
    "Safety posture",
    "Live armed/read-only/kill-switch state",
    "Notifications",
    "Freshness findings",
    "Dataset readiness",
    "Monitoring alerts",
    "Research queue",
    "Portfolio/concentration warnings",
    "Governance checklist items",
    "Analytics warnings",
    "Simulation/replay follow-ups",
    "Open tasks",
    "Blocked tasks",
    "Due/overdue tasks",
    "Safe next actions",
    "Daily ops packet generation",
]
WEEKLY_REVIEW_STEPS = [
    "Open task rollup",
    "Overdue task rollup",
    "Recurring blockers",
    "Recurring stale data",
    "Research backlog",
    "Thesis review needs",
    "Dataset/freshness review",
    "Simulation/replay review",
    "Analytics learning report review",
    "Governance improvement items",
    "Backup/data integrity review",
    "Next-week focus",
    "Weekly task plan",
    "Weekly ops packet generation",
]
TASK_TRIAGE_STEPS = [
    "Review task inbox",
    "Preview source context",
    "Convert safe findings to tasks",
    "Dismiss irrelevant items",
    "Identify blocked work",
    "Save triage packet",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return date.today().isoformat()


def _ensure_dir() -> None:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


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
            rows.append({"id": _record_id("invalid"), "status": "invalid_json", "created_at": _now(), "secret_values_returned": False})
    return rows


def _latest_by_id(rows: list[dict[str, Any]], id_key: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        rid = str(row.get(id_key) or row.get("id") or _record_id("row"))
        latest[rid] = row
    return sorted(latest.values(), key=lambda r: str(r.get("updated_at") or r.get("created_at") or ""), reverse=True)


def _safety(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "guided_reviews_are_not_orders": True,
        "guided_review_completion_is_not_trade_approval": True,
        "task_completion_is_not_trade_approval": True,
        "dependency_chains_are_workflow_only": True,
        "saved_views_are_not_trading_recommendations": True,
        "not_financial_advice": True,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "mutates_live_trading_state": False,
        "external_network_called": False,
        "ai_model_called": False,
        "secret_values_returned": False,
        "safety_statement": "Guided reviews, task dependencies, source previews, saved views, review packets, and workspace exports are local-first human-in-the-loop workflow aids. They do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass backend gates, or provide financial advice.",
    }
    if extra:
        base.update(extra)
    return base


def _audit(action: str, status: str = "ok", details: dict[str, Any] | None = None) -> dict[str, Any]:
    event = {
        "event_id": _record_id("workspace_evt"),
        "timestamp": _now(),
        "app_version": APP_VERSION,
        "action": action,
        "status": status,
        "details": redact_data(details or {}),
        **_safety(),
    }
    _write_jsonl(WORKSPACE_EVENTS_PATH, event)
    record_audit(
        f"v3_workspace_{action}",
        status,
        details={**redact_data(details or {}), "order_submitted": False, "order_cancelled": False, "live_trading_armed": False},
        network_attempted=False,
    )
    return redact_data(event)


def _flow_type(value: Any) -> str:
    text = _safe_text(value, "custom").lower().replace("_", "-")
    return text if text in FLOW_TYPES else "custom"


def _session_status(value: Any, default: str = "active") -> str:
    text = _safe_text(value, default).lower().replace(" ", "_")
    return text if text in SESSION_STATUSES else default


def _safety_class(value: Any, subsystem: str = "") -> str:
    text = _safe_text(value).lower().replace("_", "-")
    if text in SAFETY_CLASSES:
        return text
    sub = subsystem.lower()
    if "live" in sub or "order" in sub or "trade" in sub:
        return "gated-live-action-reference"
    if sub in {"datasets", "freshness", "simulation", "data"}:
        return "read-only-action"
    if sub:
        return "review-only"
    return "informational"


def _step_records(names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "step_id": f"step_{index:02d}",
            "title": name,
            "description": f"Review {name.lower()} and document unknowns, blockers, or safe manual next actions.",
            "required": index in {1, 2, len(names)},
            "safe_actions": ["create task", "add note", "link object", "generate packet"],
            "disallowed_actions": ["place order", "cancel order", "approve trade", "arm live trading"],
            "secret_values_returned": False,
        }
        for index, name in enumerate(names, start=1)
    ]


def default_guided_flows() -> list[dict[str, Any]]:
    now = _now()
    specs = [
        ("flow_daily_review", "Guided Daily Review", "daily-review", "tasks", DAILY_REVIEW_STEPS),
        ("flow_weekly_review", "Guided Weekly Planning", "weekly-review", "tasks", WEEKLY_REVIEW_STEPS),
        ("flow_task_triage", "Task Triage Flow", "task-triage", "tasks", TASK_TRIAGE_STEPS),
        ("flow_blocked_tasks", "Blocked Task Review", "blocked-task-review", "tasks", ["Review blockers", "Inspect dependencies", "Add notes", "Generate blocked-task packet"]),
        ("flow_dataset_review", "Dataset Guided Review", "dataset-review", "datasets", ["Review manifests", "Review replay readiness", "Review quality findings", "Create safe follow-up tasks"]),
        ("flow_freshness_review", "Freshness Guided Review", "freshness-review", "freshness", ["Review policies", "Review jobs", "Review stale findings", "Create read-only refresh tasks"]),
        ("flow_simulation_review", "Simulation Guided Review", "simulation-review", "simulation", ["Review sessions", "Review findings", "Capture follow-ups", "Generate replay review packet"]),
        ("flow_analytics_review", "Analytics Guided Review", "analytics-review", "analytics", ["Review learning report", "Review calibration", "Review recurring patterns", "Create discipline tasks"]),
        ("flow_governance_review", "Governance Guided Review", "governance-review", "governance", ["Review checklists", "Review near misses", "Review rules", "Document improvement tasks"]),
        ("flow_monitoring_review", "Monitoring Guided Review", "monitoring-review", "monitoring", ["Review alerts", "Preview source", "Convert to task", "Acknowledge manually"]),
        ("flow_portfolio_review", "Portfolio Guided Review", "portfolio-review", "portfolio", ["Review exposure", "Review concentration", "Review risk blocks", "Create manual review tasks"]),
        ("flow_research_review", "Research Guided Review", "research-review", "research", ["Review queue", "Review stale evidence", "Review unknowns", "Create research tasks"]),
    ]
    flows = []
    for flow_id, title, flow_type, subsystem, steps in specs:
        flows.append({
            "flow_id": flow_id,
            "created_at": now,
            "updated_at": now,
            "app_version": APP_VERSION,
            "title": title,
            "description": f"Local guided {title.lower()} for human operator review. Completion is not trade approval.",
            "flow_type": flow_type,
            "target_subsystem": subsystem,
            "steps": _step_records(steps),
            "safety_class": _safety_class("", subsystem),
            "enabled": True,
            "operator_notes": "Default safe guided workspace flow.",
            "audit_metadata": {"default_flow": True},
            **_safety(),
        })
    return flows


def list_guided_flows(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(FLOWS_PATH), "flow_id")
    default_by_id = {str(flow.get("flow_id")): flow for flow in default_guided_flows()}
    if rows:
        seen = {str(row.get("flow_id")) for row in rows}
        rows.extend([flow for flow_id, flow in default_by_id.items() if flow_id not in seen])
    else:
        rows = list(default_by_id.values())
    rows.sort(key=lambda r: str(r.get("updated_at") or r.get("created_at") or ""), reverse=True)
    capped = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(capped), "items": redact_data(capped), **_safety()}


def get_guided_flow(flow_id: str) -> dict[str, Any] | None:
    for flow in list_guided_flows(limit=5000)["items"]:
        if flow.get("flow_id") == flow_id:
            return redact_data(flow)
    return None


def create_guided_flow(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    now = _now()
    subsystem = _safe_text(payload.get("target_subsystem"), "custom")
    steps_payload = payload.get("steps") if isinstance(payload.get("steps"), list) else []
    step_names = [str(step.get("title") if isinstance(step, dict) else step) for step in steps_payload] or ["Review context", "Capture unknowns", "Create safe follow-up task", "Generate packet"]
    flow = {
        "flow_id": _safe_text(payload.get("flow_id")) or _record_id("flow"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), "Guided review flow"),
        "description": _safe_text(payload.get("description"), "Local guided review flow. No live trading state is changed."),
        "flow_type": _flow_type(payload.get("flow_type")),
        "target_subsystem": subsystem,
        "steps": _step_records(step_names),
        "safety_class": _safety_class(payload.get("safety_class"), subsystem),
        "enabled": bool(payload.get("enabled", True)),
        "operator_notes": _safe_text(payload.get("operator_notes") or payload.get("notes")),
        "audit_metadata": _safe_dict(payload.get("audit_metadata")),
        **_safety(),
    }
    _write_jsonl(FLOWS_PATH, flow)
    _audit("guided_flow_created", "ok", {"flow_id": flow["flow_id"], "flow_type": flow["flow_type"]})
    return redact_data(flow)


def update_guided_flow(flow_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    current = get_guided_flow(flow_id)
    if not current:
        return {"ok": False, "error": "flow_not_found", "flow_id": redact_text(flow_id), **_safety()}
    payload = payload or {}
    updated = dict(current)
    for key in ["title", "description", "target_subsystem", "operator_notes"]:
        if key in payload:
            updated[key] = _safe_text(payload.get(key))
    if "flow_type" in payload:
        updated["flow_type"] = _flow_type(payload.get("flow_type"))
    if "enabled" in payload:
        updated["enabled"] = bool(payload.get("enabled"))
    if "steps" in payload and isinstance(payload.get("steps"), list):
        updated["steps"] = _step_records([str(s.get("title") if isinstance(s, dict) else s) for s in payload["steps"]])
    updated["updated_at"] = _now()
    updated.update(_safety())
    _write_jsonl(FLOWS_PATH, updated)
    _audit("guided_flow_updated", "ok", {"flow_id": flow_id, "changed_keys": sorted(payload.keys())})
    return redact_data(updated)


def _session_base(flow: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    now = _now()
    steps = flow.get("steps") if isinstance(flow.get("steps"), list) else []
    return {
        "session_id": _safe_text(payload.get("session_id")) or _record_id("session"),
        "flow_id": flow.get("flow_id"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), flow.get("title", "Guided review session")),
        "flow_type": flow.get("flow_type", "custom"),
        "target_subsystem": flow.get("target_subsystem", "custom"),
        "current_step": steps[0].get("step_id") if steps else "step_01",
        "steps": redact_data(steps),
        "completed_steps": _safe_list(payload.get("completed_steps")),
        "skipped_steps": _safe_list(payload.get("skipped_steps")),
        "unresolved_items": _safe_list(payload.get("unresolved_items")),
        "tasks_created": _safe_list(payload.get("tasks_created")),
        "tasks_linked": _safe_list(payload.get("tasks_linked")),
        "blockers_found": _safe_list(payload.get("blockers_found")),
        "unknown_unavailable_data": _safe_list(payload.get("unknown_unavailable_data")) or ["Runtime module data may be unavailable until operator creates local records."],
        "generated_packet_id": _safe_text(payload.get("generated_packet_id")),
        "status": _session_status(payload.get("status"), "active"),
        "operator_notes": _safe_text(payload.get("operator_notes") or payload.get("notes")),
        "safety_statement": _safety()["safety_statement"],
        "audit_metadata": _safe_dict(payload.get("audit_metadata")),
        **_safety(),
    }


def list_sessions(limit: int = 250, status: str | None = None) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(SESSIONS_PATH), "session_id")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    capped = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(capped), "items": redact_data(capped), **_safety()}


def get_session(session_id: str) -> dict[str, Any] | None:
    for session in _latest_by_id(_read_jsonl(SESSIONS_PATH), "session_id"):
        if session.get("session_id") == session_id:
            return redact_data(session)
    return None


def start_flow(flow_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    flow = get_guided_flow(flow_id)
    if not flow:
        return {"ok": False, "error": "flow_not_found", "flow_id": redact_text(flow_id), **_safety()}
    session = _session_base(flow, payload)
    _write_jsonl(SESSIONS_PATH, session)
    _audit("guided_review_session_started", "ok", {"flow_id": flow_id, "session_id": session["session_id"]})
    return {"ok": True, "session": redact_data(session), **_safety()}


def _start_by_type(flow_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    for flow in list_guided_flows(limit=5000)["items"]:
        if flow.get("flow_type") == flow_type:
            return start_flow(str(flow.get("flow_id")), payload)
    flow = create_guided_flow({"title": flow_type.replace("-", " ").title(), "flow_type": flow_type, "target_subsystem": "tasks"})
    return start_flow(flow["flow_id"], payload)


def start_daily_review(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _start_by_type("daily-review", payload)


def start_weekly_review(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _start_by_type("weekly-review", payload)


def start_task_triage(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _start_by_type("task-triage", payload)


def update_session_step(session_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    current = get_session(session_id)
    if not current:
        return {"ok": False, "error": "session_not_found", "session_id": redact_text(session_id), **_safety()}
    payload = payload or {}
    updated = dict(current)
    completed = list(updated.get("completed_steps") if isinstance(updated.get("completed_steps"), list) else [])
    skipped = list(updated.get("skipped_steps") if isinstance(updated.get("skipped_steps"), list) else [])
    step_id = _safe_text(payload.get("step_id") or updated.get("current_step"), "step_01")
    if bool(payload.get("skip", False)):
        if step_id not in skipped:
            skipped.append(step_id)
        action = "guided_review_step_skipped"
    else:
        if step_id not in completed:
            completed.append(step_id)
        action = "guided_review_step_completed"
    if payload.get("next_step"):
        updated["current_step"] = _safe_text(payload.get("next_step"))
    else:
        steps = updated.get("steps") if isinstance(updated.get("steps"), list) else []
        ids = [s.get("step_id") for s in steps if isinstance(s, dict)]
        try:
            idx = ids.index(step_id)
            updated["current_step"] = ids[min(idx + 1, len(ids) - 1)] if ids else step_id
        except ValueError:
            updated["current_step"] = step_id
    updated["completed_steps"] = completed
    updated["skipped_steps"] = skipped
    for field in ["unresolved_items", "tasks_created", "tasks_linked", "blockers_found", "unknown_unavailable_data"]:
        if field in payload:
            existing = list(updated.get(field) if isinstance(updated.get(field), list) else [])
            for item in _safe_list(payload.get(field)):
                if item not in existing:
                    existing.append(item)
            updated[field] = existing
    if "operator_notes" in payload or "notes" in payload:
        existing_note = _safe_text(updated.get("operator_notes"))
        new_note = _safe_text(payload.get("operator_notes") or payload.get("notes"))
        updated["operator_notes"] = "\n".join([v for v in [existing_note, new_note] if v])
    updated["updated_at"] = _now()
    updated.update(_safety())
    _write_jsonl(SESSIONS_PATH, updated)
    _audit(action, "ok", {"session_id": session_id, "step_id": step_id})
    return redact_data(updated)


def complete_session(session_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    current = get_session(session_id)
    if not current:
        return {"ok": False, "error": "session_not_found", "session_id": redact_text(session_id), **_safety()}
    payload = payload or {}
    packet = generate_review_packet({"session_id": session_id, "packet_type": current.get("flow_type", "guided-review"), **payload}, write=True)
    completed = dict(current)
    completed.update({"status": "completed", "generated_packet_id": packet.get("packet_id"), "updated_at": _now(), **_safety()})
    _write_jsonl(SESSIONS_PATH, completed)
    _audit("guided_review_session_completed", "ok", {"session_id": session_id, "packet_id": packet.get("packet_id"), "guided_review_completion_is_not_trade_approval": True})
    return {"ok": True, "session": redact_data(completed), "packet": redact_data(packet), **_safety()}


def abandon_session(session_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    current = get_session(session_id)
    if not current:
        return {"ok": False, "error": "session_not_found", "session_id": redact_text(session_id), **_safety()}
    updated = dict(current)
    updated.update({"status": "abandoned", "operator_notes": _safe_text((payload or {}).get("notes") or current.get("operator_notes")), "updated_at": _now(), **_safety()})
    _write_jsonl(SESSIONS_PATH, updated)
    _audit("guided_review_session_abandoned", "ok", {"session_id": session_id})
    return redact_data(updated)


def list_dependencies(limit: int = 250) -> dict[str, Any]:
    rows = [r for r in _latest_by_id(_read_jsonl(DEPENDENCIES_PATH), "dependency_id") if r.get("status") != "deleted"]
    capped = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(capped), "items": redact_data(capped), **_safety()}


def create_dependency(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    task_id = _safe_text(payload.get("task_id") or payload.get("from_task_id"), "unknown_task")
    depends_on = _safe_text(payload.get("depends_on_task_id") or payload.get("to_task_id"), "unknown_dependency")
    now = _now()
    edge = {
        "dependency_id": _safe_text(payload.get("dependency_id")) or _record_id("dep"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "task_id": task_id,
        "depends_on_task_id": depends_on,
        "relationship": _safe_text(payload.get("relationship"), "depends_on"),
        "status": "active",
        "blocker": bool(payload.get("blocker", True)),
        "notes": _safe_text(payload.get("notes"), "Operator workflow dependency. Completion is not trade approval."),
        "unknown_unavailable_data": _safe_list(payload.get("unknown_unavailable_data")),
        "audit_metadata": _safe_dict(payload.get("audit_metadata")),
        **_safety(),
    }
    _write_jsonl(DEPENDENCIES_PATH, edge)
    try:
        from .live_v3_tasks import update_task
        update_task(task_id, {"status": "blocked" if edge["blocker"] else "planned", "follow_up_note": f"Dependency added: {depends_on}"})
    except Exception:
        pass
    _audit("task_dependency_created", "ok", {"dependency_id": edge["dependency_id"], "task_id": task_id, "depends_on_task_id": depends_on})
    return redact_data(edge)


def delete_dependency(dependency_id: str) -> dict[str, Any]:
    current = None
    for dep in _latest_by_id(_read_jsonl(DEPENDENCIES_PATH), "dependency_id"):
        if dep.get("dependency_id") == dependency_id:
            current = dep
            break
    if not current:
        return {"ok": False, "error": "dependency_not_found", "dependency_id": redact_text(dependency_id), **_safety()}
    updated = dict(current)
    updated.update({"status": "deleted", "updated_at": _now(), **_safety()})
    _write_jsonl(DEPENDENCIES_PATH, updated)
    _audit("task_dependency_removed", "ok", {"dependency_id": dependency_id})
    return {"ok": True, "dependency": redact_data(updated), **_safety()}


def blocked_review(payload: dict[str, Any] | None = None, write: bool = True) -> dict[str, Any]:
    try:
        from .live_v3_tasks import list_tasks
        blocked = list_tasks(limit=500, status="blocked").get("items", [])
    except Exception:
        blocked = []
    dependencies = list_dependencies(limit=500).get("items", [])
    packet = generate_review_packet({
        "packet_type": "blocked-task-review",
        "title": "Blocked Task Review Packet",
        "included_task_ids": [str(t.get("task_id")) for t in blocked],
        "blockers": [str(b) for task in blocked for b in (task.get("blockers", []) if isinstance(task.get("blockers"), list) else [])],
        "unresolved_items": [f"{dep.get('task_id')} depends on {dep.get('depends_on_task_id')}" for dep in dependencies],
        "unknown_unavailable_data": ["Blocked task context is local-only and may be incomplete."],
    }, write=write)
    _audit("blocker_review_generated", "ok", {"packet_id": packet.get("packet_id"), "blocked_count": len(blocked)})
    return {"version": APP_VERSION, "blocked_tasks": redact_data(blocked), "dependencies": redact_data(dependencies), "packet": packet, **_safety()}


def create_source_preview(payload: dict[str, Any] | None = None, write: bool = True) -> dict[str, Any]:
    payload = payload or {}
    subsystem = _safe_text(payload.get("source_subsystem") or payload.get("source"), "manual")
    now = _now()
    preview = {
        "preview_id": _safe_text(payload.get("preview_id")) or _record_id("preview"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "source_subsystem": subsystem,
        "source_object_type": _safe_text(payload.get("source_object_type") or payload.get("object_type"), "finding"),
        "source_object_id": _safe_text(payload.get("source_object_id") or payload.get("object_id") or payload.get("id")),
        "finding_title": _safe_text(payload.get("finding_title") or payload.get("title"), "Source context preview"),
        "severity": _safe_text(payload.get("severity"), "unknown"),
        "timestamp": _safe_text(payload.get("timestamp"), now),
        "related_object_ids": _safe_list(payload.get("related_object_ids")),
        "safe_summary": _safe_text(payload.get("safe_summary") or payload.get("description") or payload.get("message"), "Local source preview. Missing data is not invented."),
        "unknown_unavailable_data": _safe_list(payload.get("unknown_unavailable_data")) or ["Source details may be unavailable until the operator opens the linked module."],
        "recommended_task_template_id": _safe_text(payload.get("recommended_task_template_id") or payload.get("template_id"), "tpl_missing_prerequisite"),
        "safety_class": _safety_class(payload.get("safety_class"), subsystem),
        "source_url": _safe_text(payload.get("source_url") or payload.get("url"), "/v3/tasks/inbox"),
        "status": "awaiting_review",
        **_safety(),
    }
    if write:
        _write_jsonl(SOURCE_PREVIEWS_PATH, preview)
        _audit("source_preview_generated", "ok", {"preview_id": preview["preview_id"], "source_subsystem": subsystem})
    return redact_data(preview)


def list_source_previews(limit: int = 250, status: str | None = None) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(SOURCE_PREVIEWS_PATH), "preview_id")
    if status:
        rows = [r for r in rows if r.get("status") == status]
    capped = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(capped), "items": redact_data(capped), **_safety()}


def default_saved_views() -> list[dict[str, Any]]:
    now = _now()
    specs = [
        ("view_due_today", "Due today", {"due_date": _today()}),
        ("view_overdue", "Overdue", {"due": "overdue"}),
        ("view_urgent_critical", "Urgent and critical", {"priority": ["urgent", "critical"]}),
        ("view_blocked", "Blocked", {"status": "blocked"}),
        ("view_waiting", "Waiting", {"status": "waiting"}),
        ("view_freshness", "Freshness-related", {"source_subsystem": "freshness"}),
        ("view_datasets", "Dataset-related", {"source_subsystem": "datasets"}),
        ("view_simulation", "Simulation follow-ups", {"source_subsystem": "simulation"}),
        ("view_governance", "Governance follow-ups", {"source_subsystem": "governance"}),
        ("view_analytics", "Analytics follow-ups", {"source_subsystem": "analytics"}),
        ("view_monitoring", "Monitoring alerts", {"source_subsystem": "monitoring"}),
        ("view_research", "Research review", {"source_subsystem": "research"}),
        ("view_live_refs", "Live-action references", {"safety_class": "gated-live-action-reference"}),
        ("view_no_due_date", "No due date", {"due_date": ""}),
        ("view_recent_done", "Recently completed", {"status": "done"}),
    ]
    return [
        {
            "view_id": view_id,
            "created_at": now,
            "updated_at": now,
            "app_version": APP_VERSION,
            "title": title,
            "description": f"Saved local task view: {title}. Saved views do not perform live actions.",
            "filters": redact_data(filters),
            "sort": "updated_at_desc",
            "enabled": True,
            "audit_metadata": {"default_view": True},
            **_safety(),
        }
        for view_id, title, filters in specs
    ]


def list_saved_views(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(SAVED_VIEWS_PATH), "view_id")
    default_by_id = {str(view.get("view_id")): view for view in default_saved_views()}
    if rows:
        seen = {str(row.get("view_id")) for row in rows}
        rows.extend([view for view_id, view in default_by_id.items() if view_id not in seen])
    else:
        rows = list(default_by_id.values())
    rows.sort(key=lambda r: str(r.get("updated_at") or r.get("created_at") or ""), reverse=True)
    capped = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(capped), "items": redact_data(capped), **_safety()}


def create_saved_view(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    now = _now()
    view = {
        "view_id": _safe_text(payload.get("view_id")) or _record_id("view"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), "Saved task view"),
        "description": _safe_text(payload.get("description"), "Local saved task filter. It does not perform live actions."),
        "filters": _safe_dict(payload.get("filters")),
        "sort": _safe_text(payload.get("sort"), "updated_at_desc"),
        "enabled": bool(payload.get("enabled", True)),
        "audit_metadata": _safe_dict(payload.get("audit_metadata")),
        **_safety(),
    }
    _write_jsonl(SAVED_VIEWS_PATH, view)
    _audit("saved_view_created", "ok", {"view_id": view["view_id"]})
    return redact_data(view)


def update_saved_view(view_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    current = next((v for v in list_saved_views(limit=5000)["items"] if v.get("view_id") == view_id), None)
    if not current:
        return {"ok": False, "error": "saved_view_not_found", "view_id": redact_text(view_id), **_safety()}
    payload = payload or {}
    updated = dict(current)
    for key in ["title", "description", "sort"]:
        if key in payload:
            updated[key] = _safe_text(payload.get(key))
    if "filters" in payload:
        updated["filters"] = _safe_dict(payload.get("filters"))
    if "enabled" in payload:
        updated["enabled"] = bool(payload.get("enabled"))
    updated["updated_at"] = _now()
    updated.update(_safety())
    _write_jsonl(SAVED_VIEWS_PATH, updated)
    _audit("saved_view_updated", "ok", {"view_id": view_id})
    return redact_data(updated)


def generate_review_packet(payload: dict[str, Any] | None = None, write: bool = True) -> dict[str, Any]:
    payload = payload or {}
    now = _now()
    session_id = _safe_text(payload.get("session_id"))
    session = get_session(session_id) if session_id else None
    packet_type = _safe_text(payload.get("packet_type") or (session or {}).get("flow_type"), "guided-review")
    included_task_ids = _safe_list(payload.get("included_task_ids") or (session or {}).get("tasks_linked") or (session or {}).get("tasks_created"))
    packet = {
        "packet_id": _safe_text(payload.get("packet_id")) or _record_id("packet"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), f"{packet_type.replace('-', ' ').title()} Packet"),
        "packet_type": packet_type,
        "flow_id": _safe_text(payload.get("flow_id") or (session or {}).get("flow_id")),
        "session_id": session_id,
        "included_task_ids": included_task_ids,
        "related_object_ids": _safe_list(payload.get("related_object_ids")),
        "unresolved_items": _safe_list(payload.get("unresolved_items") or (session or {}).get("unresolved_items")),
        "blockers": _safe_list(payload.get("blockers") or (session or {}).get("blockers_found")),
        "unknown_unavailable_data": _safe_list(payload.get("unknown_unavailable_data") or (session or {}).get("unknown_unavailable_data")) or ["No runtime records were available or selected."],
        "limitations": _safe_list(payload.get("limitations")) or ["Packet is a local operator review aid and may not include all module context."],
        "status_summary": _safe_text(payload.get("status_summary"), "Generated local guided review packet."),
        "safety_statement": _safety()["safety_statement"],
        "packets_do_not_place_or_cancel_orders": True,
        **_safety(),
    }
    if write:
        _write_jsonl(PACKETS_PATH, packet)
        _audit("guided_review_packet_generated", "ok", {"packet_id": packet["packet_id"], "packet_type": packet_type})
    return redact_data(packet)


def list_review_packets(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(PACKETS_PATH), "packet_id")
    capped = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(capped), "items": redact_data(capped), **_safety()}


def workspace_summary() -> dict[str, Any]:
    sessions = list_sessions(limit=5000)["items"]
    deps = list_dependencies(limit=5000)["items"]
    packets = list_review_packets(limit=5000)["items"]
    previews = list_source_previews(limit=5000)["items"]
    saved_views = list_saved_views(limit=5000)["items"]
    active = [s for s in sessions if s.get("status") == "active"]
    latest_daily = next((s for s in sessions if s.get("flow_type") == "daily-review"), None)
    latest_weekly = next((s for s in sessions if s.get("flow_type") == "weekly-review"), None)
    next_step = active[0].get("current_step") if active else "Start a guided review when ready."
    return {
        "version": APP_VERSION,
        "active_guided_review_session": active[0] if active else None,
        "active_session_count": len(active),
        "latest_daily_review": latest_daily,
        "latest_weekly_review": latest_weekly,
        "blocked_task_count": len({d.get("task_id") for d in deps if d.get("blocker") and d.get("status") == "active"}),
        "dependency_warning_count": len(deps),
        "next_guided_step": next_step,
        "latest_review_packet": packets[0] if packets else None,
        "review_packet_count": len(packets),
        "saved_views_count": len(saved_views),
        "source_previews_awaiting_review": len([p for p in previews if p.get("status") == "awaiting_review"]),
        "guided_reviews_are_local_first": True,
        **_safety(),
    }


def build_workspace_context() -> dict[str, Any]:
    return {
        "summary": workspace_summary(),
        "flows": list_guided_flows(limit=250),
        "sessions": list_sessions(limit=250),
        "dependencies": list_dependencies(limit=250),
        "blocked_review": blocked_review(write=False),
        "source_previews": list_source_previews(limit=250),
        "saved_views": list_saved_views(limit=250),
        "review_packets": list_review_packets(limit=250),
        "settings": build_settings(),
        **_safety(),
    }


def build_settings() -> dict[str, Any]:
    defaults = {
        "version": APP_VERSION,
        "auto_start_guided_reviews": False,
        "auto_generate_packets": False,
        "show_source_previews_before_task_creation": True,
        "dependency_warning_before_archive": True,
        "default_daily_flow_id": "flow_daily_review",
        "default_weekly_flow_id": "flow_weekly_review",
        "local_first_storage": True,
        **_safety(),
    }
    if SETTINGS_PATH.exists():
        try:
            loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                defaults.update(redact_data(loaded))
        except json.JSONDecodeError:
            defaults["warnings"] = ["Workspace settings file is invalid JSON; defaults are shown."]
    return redact_data(defaults)


def update_settings(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    settings = build_settings()
    for key in ["auto_start_guided_reviews", "auto_generate_packets", "show_source_previews_before_task_creation", "dependency_warning_before_archive", "local_first_storage"]:
        if key in payload:
            settings[key] = bool(payload.get(key))
    for key in ["default_daily_flow_id", "default_weekly_flow_id"]:
        if key in payload:
            settings[key] = _safe_text(payload.get(key))
    settings["updated_at"] = _now()
    settings.update(_safety())
    _ensure_dir()
    SETTINGS_PATH.write_text(json.dumps(redact_data(settings), indent=2, sort_keys=True, default=str), encoding="utf-8")
    _audit("guided_workspace_settings_changed", "ok", {"changed_keys": sorted(payload.keys())})
    return redact_data(settings)


def export_json() -> dict[str, Any]:
    manifest = {
        "export_id": _record_id("workspace_export"),
        "created_at": _now(),
        "app_version": APP_VERSION,
        "summary": workspace_summary(),
        "flows": list_guided_flows(limit=5000)["items"],
        "sessions": list_sessions(limit=5000)["items"],
        "packets": list_review_packets(limit=5000)["items"],
        "dependencies": list_dependencies(limit=5000)["items"],
        "source_previews": list_source_previews(limit=5000)["items"],
        "saved_views": list_saved_views(limit=5000)["items"],
        "warnings": ["Guided workspace export is local operator workflow context only."],
        "limitations": ["Exports do not include private secrets and do not perform live actions."],
        **_safety(),
    }
    _write_jsonl(EXPORT_MANIFESTS_PATH, {"export_id": manifest["export_id"], "created_at": manifest["created_at"], "kind": "json", **_safety()})
    _audit("guided_export_generated", "ok", {"export_id": manifest["export_id"], "kind": "json"})
    return redact_data(manifest)


def _packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        f"# {packet.get('title', 'Guided Review Packet')}",
        "",
        f"Version: {APP_VERSION}",
        f"Generated: {packet.get('created_at', _now())}",
        f"Packet type: {packet.get('packet_type', 'guided-review')}",
        "",
        "## Safety",
        _safety()["safety_statement"],
        "",
        "## Included Tasks",
    ]
    for task_id in packet.get("included_task_ids", []) if isinstance(packet.get("included_task_ids"), list) else []:
        lines.append(f"- {task_id}")
    if not packet.get("included_task_ids"):
        lines.append("- None selected.")
    lines.extend(["", "## Unresolved Items"])
    for item in packet.get("unresolved_items", []) if isinstance(packet.get("unresolved_items"), list) else []:
        lines.append(f"- {item}")
    if not packet.get("unresolved_items"):
        lines.append("- None recorded.")
    lines.extend(["", "## Blockers"])
    for blocker in packet.get("blockers", []) if isinstance(packet.get("blockers"), list) else []:
        lines.append(f"- {blocker}")
    if not packet.get("blockers"):
        lines.append("- None recorded.")
    lines.extend(["", "## Unknown / Unavailable Data"])
    for item in packet.get("unknown_unavailable_data", []) if isinstance(packet.get("unknown_unavailable_data"), list) else []:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def export_markdown() -> str:
    export = export_json()
    lines = [
        "# Guided Operator Workspace Export",
        "",
        f"Version: {APP_VERSION}",
        f"Generated: {export['created_at']}",
        "",
        "## Safety",
        _safety()["safety_statement"],
        "",
        "## Summary",
        f"- Active sessions: {export['summary'].get('active_session_count', 0)}",
        f"- Dependencies: {len(export.get('dependencies', []))}",
        f"- Saved views: {len(export.get('saved_views', []))}",
        f"- Source previews awaiting review: {export['summary'].get('source_previews_awaiting_review', 0)}",
        "",
        "## Review Packets",
    ]
    for packet in export.get("packets", []):
        lines.append(f"- {packet.get('packet_id')}: {packet.get('title')} ({packet.get('packet_type')})")
    if not export.get("packets"):
        lines.append("- No packets generated yet.")
    lines.append("")
    lines.append("No guided workspace export places orders, cancels orders, approves trades, signs transactions, or arms live trading.")
    return "\n".join(lines) + "\n"


def export_dependency_json() -> dict[str, Any]:
    return {"version": APP_VERSION, "created_at": _now(), "dependencies": list_dependencies(limit=5000)["items"], **_safety()}


def export_dependency_markdown() -> str:
    deps = list_dependencies(limit=5000)["items"]
    lines = ["# Task Dependency Report", "", f"Version: {APP_VERSION}", "", _safety()["safety_statement"], ""]
    for dep in deps:
        lines.append(f"- {dep.get('task_id')} depends on {dep.get('depends_on_task_id')} ({dep.get('status')})")
    if not deps:
        lines.append("- No task dependencies recorded.")
    return "\n".join(lines) + "\n"


def export_saved_views_json() -> dict[str, Any]:
    return {"version": APP_VERSION, "created_at": _now(), "saved_views": list_saved_views(limit=5000)["items"], **_safety()}


def export_saved_views_markdown() -> str:
    views = list_saved_views(limit=5000)["items"]
    lines = ["# Saved Task Views Report", "", f"Version: {APP_VERSION}", "", "Saved views are filters only. They are not trading recommendations and do not perform live actions.", ""]
    for view in views:
        lines.append(f"- {view.get('title')}: `{json.dumps(view.get('filters', {}), sort_keys=True)}`")
    return "\n".join(lines) + "\n"


def export_csv(kind: str = "dependencies") -> str:
    kind = _safe_text(kind, "dependencies")
    if kind == "saved_views":
        rows = list_saved_views(limit=5000)["items"]
        fields = ["view_id", "title", "description", "filters", "sort", "enabled"]
    elif kind == "sessions":
        rows = list_sessions(limit=5000)["items"]
        fields = ["session_id", "flow_id", "flow_type", "status", "current_step", "created_at", "updated_at"]
    else:
        rows = list_dependencies(limit=5000)["items"]
        fields = ["dependency_id", "task_id", "depends_on_task_id", "relationship", "status", "blocker", "created_at"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        safe = {k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()}
        writer.writerow(redact_data(safe))
    _audit("guided_export_generated", "ok", {"kind": f"csv:{kind}"})
    return output.getvalue()


def workspace_search_items(limit: int = 250) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for flow in list_guided_flows(limit=limit)["items"]:
        rows.append({"result_id": f"guided_flow:{flow.get('flow_id')}", "result_type": "guided_review_flow", "title": flow.get("title"), "summary": flow.get("description"), "status": "enabled" if flow.get("enabled") else "disabled", "timestamp": flow.get("updated_at"), "url": "/v3/workspace/review-flows", "quick_link": "/v3/workspace/review-flows", "tags": [flow.get("flow_type", ""), flow.get("target_subsystem", "")], "search_text": " ".join(str(v).lower() for v in [flow.get("title"), flow.get("description"), flow.get("flow_type"), flow.get("target_subsystem"), "guided workspace"]), "secret_values_returned": False})
    for session in list_sessions(limit=limit)["items"]:
        rows.append({"result_id": f"guided_session:{session.get('session_id')}", "result_type": "guided_review_session", "title": session.get("title"), "summary": session.get("operator_notes") or session.get("safety_statement"), "status": session.get("status"), "timestamp": session.get("updated_at"), "url": "/v3/workspace", "quick_link": "/v3/workspace", "tags": [session.get("flow_type", "")], "search_text": " ".join(str(v).lower() for v in [session.get("title"), session.get("flow_type"), session.get("status"), "guided session"]), "secret_values_returned": False})
    for packet in list_review_packets(limit=limit)["items"]:
        rows.append({"result_id": f"guided_packet:{packet.get('packet_id')}", "result_type": "guided_review_packet", "title": packet.get("title"), "summary": packet.get("status_summary"), "status": "generated", "timestamp": packet.get("created_at"), "url": "/v3/workspace/review-packets", "quick_link": "/v3/workspace/review-packets", "tags": [packet.get("packet_type", "")], "search_text": f"guided review packet {packet.get('title','')} {packet.get('packet_type','')}", "secret_values_returned": False})
    for view in list_saved_views(limit=limit)["items"]:
        rows.append({"result_id": f"saved_view:{view.get('view_id')}", "result_type": "saved_task_view", "title": view.get("title"), "summary": view.get("description"), "status": "enabled" if view.get("enabled") else "disabled", "timestamp": view.get("updated_at"), "url": "/v3/workspace/saved-views", "quick_link": "/v3/workspace/saved-views", "tags": ["saved_view"], "search_text": f"saved task view {view.get('title','')} {json.dumps(view.get('filters', {}), sort_keys=True)}", "secret_values_returned": False})
    rows.sort(key=lambda r: str(r.get("timestamp") or ""), reverse=True)
    return redact_data(rows[: max(1, min(int(limit or 250), 5000))])


def workspace_graph_nodes_edges() -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for flow in list_guided_flows(limit=500)["items"]:
        fid = f"guided_review_flow:{flow.get('flow_id')}"
        nodes.append({"node_id": fid, "node_type": "guided_review_flow", "title": flow.get("title"), "status": "enabled" if flow.get("enabled") else "disabled", "timestamp": flow.get("updated_at"), "summary": flow.get("description"), "secret_values_returned": False})
    for session in list_sessions(limit=500)["items"]:
        sid = f"guided_review_session:{session.get('session_id')}"
        nodes.append({"node_id": sid, "node_type": "guided_review_session", "title": session.get("title"), "status": session.get("status"), "timestamp": session.get("updated_at"), "summary": session.get("flow_type"), "secret_values_returned": False})
        if session.get("flow_id"):
            edges.append({"edge_id": f"edge:{sid}:generated_from:guided_review_flow:{session.get('flow_id')}", "from": sid, "to": f"guided_review_flow:{session.get('flow_id')}", "relationship": "generated_from", "secret_values_returned": False})
        for task_id in session.get("tasks_linked", []) if isinstance(session.get("tasks_linked"), list) else []:
            edges.append({"edge_id": f"edge:{sid}:reviews:operator_task:{task_id}", "from": sid, "to": f"operator_task:{task_id}", "relationship": "reviews", "secret_values_returned": False})
    for dep in list_dependencies(limit=500)["items"]:
        node = f"task_dependency:{dep.get('dependency_id')}"
        nodes.append({"node_id": node, "node_type": "task_dependency", "title": f"{dep.get('task_id')} depends on {dep.get('depends_on_task_id')}", "status": dep.get("status"), "timestamp": dep.get("updated_at"), "summary": dep.get("notes"), "secret_values_returned": False})
        edges.append({"edge_id": f"edge:operator_task:{dep.get('task_id')}:depends_on:operator_task:{dep.get('depends_on_task_id')}", "from": f"operator_task:{dep.get('task_id')}", "to": f"operator_task:{dep.get('depends_on_task_id')}", "relationship": "depends_on", "secret_values_returned": False})
    for packet in list_review_packets(limit=500)["items"]:
        pid = f"guided_review_packet:{packet.get('packet_id')}"
        nodes.append({"node_id": pid, "node_type": "guided_review_packet", "title": packet.get("title"), "status": "generated", "timestamp": packet.get("created_at"), "summary": packet.get("packet_type"), "secret_values_returned": False})
        if packet.get("session_id"):
            edges.append({"edge_id": f"edge:{pid}:generated_from:guided_review_session:{packet.get('session_id')}", "from": pid, "to": f"guided_review_session:{packet.get('session_id')}", "relationship": "generated_from", "secret_values_returned": False})
    return {"nodes": redact_data(nodes), "edges": redact_data(edges), "node_count": len(nodes), "edge_count": len(edges), **_safety()}


def create_demo_workspace_records(write_runtime: bool = True) -> dict[str, Any]:
    flow = default_guided_flows()[0]
    session = _session_base(flow, {"title": "DEMO guided daily review", "unresolved_items": ["Fake stale dataset review"], "blockers_found": ["Fake dependency blocker"]})
    dep = {"task_id": "demo-blocked-task-v38", "depends_on_task_id": "demo-prereq-task-v38", "notes": "Fake task dependency graph."}
    preview = {"title": "DEMO source preview", "source_subsystem": "freshness", "source_object_type": "freshness_finding", "source_object_id": "demo-source-v38", "severity": "warning"}
    view = {"title": "DEMO saved view", "filters": {"status": "blocked", "tag": "demo"}}
    packet = generate_review_packet({"title": "DEMO guided review packet", "packet_type": "daily-review", "included_task_ids": ["demo-task-v38"], "unresolved_items": ["Fake unresolved item"]}, write=False)
    created = {"session": session, "dependency": dep, "source_preview": preview, "saved_view": view, "packet": packet}
    if write_runtime:
        _write_jsonl(SESSIONS_PATH, session)
        create_dependency(dep)
        create_source_preview(preview, write=True)
        create_saved_view(view)
        generate_review_packet(packet, write=True)
    return {"version": APP_VERSION, "created": redact_data(created), "demo_data_is_fake": True, "contains_sensitive_values": False, **_safety()}


def demo_fixture() -> dict[str, Any]:
    return {
        "guided_workspace": {
            "fake_guided_daily_review_session": _session_base(default_guided_flows()[0], {"session_id": "demo-session-daily-v38", "title": "DEMO daily review session"}),
            "fake_guided_weekly_review_session": _session_base(default_guided_flows()[1], {"session_id": "demo-session-weekly-v38", "title": "DEMO weekly review session"}),
            "fake_blocked_task_dependency": {"dependency_id": "demo-dep-v38", "task_id": "demo-blocked-task-v38", "depends_on_task_id": "demo-prereq-task-v38", "status": "active", **_safety()},
            "fake_source_preview": create_source_preview({"preview_id": "demo-preview-v38", "title": "DEMO source preview", "source_subsystem": "freshness"}, write=False),
            "fake_saved_task_view": default_saved_views()[0],
            "fake_guided_review_packet": generate_review_packet({"packet_id": "demo-packet-v38", "title": "DEMO guided review packet", "packet_type": "daily-review"}, write=False),
            "fake_task_dependency_graph": {"nodes": [{"node_id": "operator_task:demo", "node_type": "operator_task"}], "edges": [{"from": "operator_task:demo", "to": "operator_task:prereq", "relationship": "depends_on"}]},
            "fake_module_review_flow": default_guided_flows()[4],
            "fake_workflow_packet": generate_review_packet({"packet_id": "demo-workflow-packet-v38", "packet_type": "guided-weekly-review"}, write=False),
            "safe_demo_data": True,
            "contains_sensitive_values": False,
        },
        **_safety(),
    }
