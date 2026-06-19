from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_v2 import record_audit, redact_data, redact_text
from .live_v3_datasets import (
    collect_snapshots,
    datasets_summary,
    export_dataset_json,
    list_dataset_manifests,
    list_snapshots,
    replay_ready_datasets,
)

FRESHNESS_DIR = DATA_DIR / "live_v3" / "freshness"
FRESHNESS_EVENTS_PATH = FRESHNESS_DIR / "freshness_events.jsonl"
POLICIES_PATH = FRESHNESS_DIR / "policies.jsonl"
JOBS_PATH = FRESHNESS_DIR / "collection_jobs.jsonl"
FINDINGS_PATH = FRESHNESS_DIR / "findings.jsonl"
READINESS_PATH = FRESHNESS_DIR / "readiness_reports.jsonl"
NOTIFICATIONS_PATH = FRESHNESS_DIR / "notifications.jsonl"
SETTINGS_PATH = FRESHNESS_DIR / "settings.json"

SEVERITIES = {"info", "warning", "blocker", "critical"}
STATUSES = {"draft", "queued", "ready", "running", "completed", "failed", "skipped", "cancelled"}
NOTIFICATION_STATUSES = {"new", "acknowledged", "snoozed", "dismissed", "resolved"}
DEFAULT_SNAPSHOT_TYPES = [
    "market_metadata", "order_book", "local_strategy", "local_research", "local_monitoring",
    "local_portfolio", "local_governance", "local_analytics", "local_simulation", "data_health",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    FRESHNESS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_text(value: Any, default: str = "") -> str:
    text = redact_text(str(value or "").strip())
    return text or default


def _record_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


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
            rows.append(redact_data(json.loads(line)))
        except json.JSONDecodeError:
            rows.append({"id": _record_id("invalid"), "status": "invalid_json", "created_at": _now(), "secret_values_returned": False})
    return rows


def _latest_by_id(rows: list[dict[str, Any]], id_key: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        rid = str(row.get(id_key) or row.get("id") or _record_id("row"))
        latest[rid] = row
    return sorted(latest.values(), key=lambda r: str(r.get("updated_at") or r.get("created_at") or ""), reverse=True)


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _age_minutes(timestamp: Any) -> int | None:
    dt = _parse_dt(timestamp)
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, int((datetime.now(timezone.utc) - dt).total_seconds() // 60))


def _safety(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "read_only_collection_planning": True,
        "queued_collection_is_not_trading": True,
        "scheduler_enabled_by_default": False,
        "scheduled_collection_enabled": False,
        "not_financial_advice": True,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "mutates_live_trading_state": False,
        "external_network_called": False,
        "secret_values_returned": False,
        "safety_statement": "Freshness, scheduler, notification, and collection-planning workflows are read-only, local-first, operator-controlled, non-autonomous by default, and do not place orders, cancel orders, approve orders, sign orders, arm live trading, or bypass backend gates.",
    }
    if extra:
        base.update(extra)
    return base


def _audit(action: str, status: str = "ok", details: dict[str, Any] | None = None) -> dict[str, Any]:
    event = {
        "event_id": _record_id("fresh_evt"),
        "timestamp": _now(),
        "app_version": APP_VERSION,
        "action": action,
        "status": status,
        "details": redact_data(details or {}),
        **_safety(),
    }
    _write_jsonl(FRESHNESS_EVENTS_PATH, event)
    record_audit(f"v3_freshness_{action}", status, details={**redact_data(details or {}), "order_submitted": False, "order_cancelled": False, "live_trading_armed": False}, network_attempted=False)
    return redact_data(event)


def build_settings() -> dict[str, Any]:
    defaults = {
        "version": APP_VERSION,
        "scheduler_enabled": False,
        "scheduled_collection_enabled": False,
        "manual_queued_collection_default": True,
        "external_collection_on_startup": False,
        "network_heavy_polling_on_startup": False,
        "default_freshness_minutes": 1440,
        "notification_snooze_minutes": 240,
        "create_notifications_on_scan": True,
        "allow_scheduled_read_only_opt_in": True,
        **_safety(),
    }
    if SETTINGS_PATH.exists():
        try:
            current = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            current = {}
        defaults.update(redact_data(current))
    defaults["scheduler_enabled"] = bool(defaults.get("scheduler_enabled", False))
    defaults["scheduled_collection_enabled"] = bool(defaults.get("scheduled_collection_enabled", False))
    defaults["scheduler_enabled_by_default"] = False
    return redact_data(defaults)


def update_settings(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    settings = build_settings()
    allowed = {"scheduler_enabled", "scheduled_collection_enabled", "manual_queued_collection_default", "default_freshness_minutes", "notification_snooze_minutes", "create_notifications_on_scan", "allow_scheduled_read_only_opt_in"}
    for key in allowed:
        if key in payload:
            settings[key] = payload[key]
    settings["updated_at"] = _now()
    settings["external_collection_on_startup"] = False
    settings["network_heavy_polling_on_startup"] = False
    _ensure_dir()
    SETTINGS_PATH.write_text(json.dumps(redact_data(settings), indent=2, sort_keys=True, default=str), encoding="utf-8")
    _audit("scheduler_settings_changed", "ok", {"changed_keys": sorted(set(payload.keys()) & allowed)})
    return redact_data(settings)


def default_policies() -> list[dict[str, Any]]:
    now = _now()
    return [
        {"policy_id": "default-market-metadata", "created_at": now, "updated_at": now, "app_version": APP_VERSION, "title": "Market metadata freshness", "description": "Warn when market metadata snapshots are stale.", "target_snapshot_types": ["market_metadata"], "target_datasets": [], "target_markets_theses": [], "freshness_threshold_minutes": 1440, "severity_when_stale": "warning", "collection_mode": "queued manual", "enabled": True, "default_disabled_behavior": False, "operator_notes": "Default local policy; edit or create a custom policy for real operations.", **_safety()},
        {"policy_id": "default-order-book", "created_at": now, "updated_at": now, "app_version": APP_VERSION, "title": "Order book freshness", "description": "Flag stale or unavailable order book snapshots for simulation/replay inputs.", "target_snapshot_types": ["order_book"], "target_datasets": [], "target_markets_theses": [], "freshness_threshold_minutes": 60, "severity_when_stale": "warning", "collection_mode": "manual only", "enabled": True, "default_disabled_behavior": False, "operator_notes": "Order book capture remains explicit read-only/demo unless safely configured.", **_safety()},
        {"policy_id": "default-local-subsystems", "created_at": now, "updated_at": now, "app_version": APP_VERSION, "title": "Local subsystem freshness", "description": "Keep local thesis, research, portfolio, governance, analytics, and simulation state fresh for replay.", "target_snapshot_types": ["local_strategy", "local_research", "local_monitoring", "local_portfolio", "local_governance", "local_analytics", "local_simulation", "data_health"], "target_datasets": [], "target_markets_theses": [], "freshness_threshold_minutes": 1440, "severity_when_stale": "info", "collection_mode": "queued manual", "enabled": True, "default_disabled_behavior": False, "operator_notes": "Local-only snapshot freshness policy.", **_safety()},
    ]


def list_policies(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(POLICIES_PATH), "policy_id")
    if not rows:
        rows = default_policies()
    return {"version": APP_VERSION, "count": len(rows[:limit]), "items": redact_data(rows[: max(1, min(limit, 5000))]), **_safety()}


def create_policy(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    now = _now()
    target_types = payload.get("target_snapshot_types") if isinstance(payload.get("target_snapshot_types"), list) else []
    if not target_types:
        target_types = [payload.get("snapshot_type") or "market_metadata"]
    policy = {
        "policy_id": _record_id("policy"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), "Freshness policy"),
        "description": _safe_text(payload.get("description"), "Read-only freshness policy."),
        "target_snapshot_types": [_safe_text(x) for x in target_types if _safe_text(x)],
        "target_datasets": payload.get("target_datasets", []) if isinstance(payload.get("target_datasets"), list) else [],
        "target_markets_theses": payload.get("target_markets_theses", []) if isinstance(payload.get("target_markets_theses"), list) else [],
        "freshness_threshold_minutes": int(payload.get("freshness_threshold_minutes") or payload.get("threshold_minutes") or build_settings().get("default_freshness_minutes") or 1440),
        "severity_when_stale": _safe_text(payload.get("severity_when_stale"), "warning") if _safe_text(payload.get("severity_when_stale"), "warning") in SEVERITIES else "warning",
        "collection_mode": _safe_text(payload.get("collection_mode"), "queued manual"),
        "enabled": bool(payload.get("enabled", True)),
        "default_disabled_behavior": False,
        "operator_notes": _safe_text(payload.get("operator_notes") or payload.get("notes")),
        "safe_metadata": redact_data(payload.get("safe_metadata", {})) if isinstance(payload.get("safe_metadata"), dict) else {},
        "audit_metadata": {"network_attempted": False, "read_only": True},
        **_safety(),
    }
    _write_jsonl(POLICIES_PATH, policy)
    _audit("freshness_policy_created", "ok", {"policy_id": policy["policy_id"], "target_snapshot_types": policy["target_snapshot_types"]})
    return redact_data(policy)


def update_policy(policy_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    current = next((row for row in list_policies(limit=5000)["items"] if row.get("policy_id") == policy_id), None)
    if not current:
        current = create_policy({"title": f"Recovered policy {policy_id}", "enabled": False})
        current["policy_id"] = policy_id
    allowed = {"title", "description", "target_snapshot_types", "target_datasets", "target_markets_theses", "freshness_threshold_minutes", "severity_when_stale", "collection_mode", "enabled", "operator_notes"}
    for key in allowed:
        if key in payload:
            current[key] = payload[key]
    current["updated_at"] = _now()
    current["app_version"] = APP_VERSION
    current.update(_safety())
    _write_jsonl(POLICIES_PATH, current)
    _audit("freshness_policy_updated", "ok", {"policy_id": policy_id})
    return redact_data(current)


def _latest_snapshot_by_type() -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for snap in list_snapshots(limit=5000).get("items", []):
        stype = str(snap.get("snapshot_type") or "unknown")
        if stype not in latest or str(snap.get("created_at")) > str(latest[stype].get("created_at")):
            latest[stype] = snap
    return latest


def _make_finding(severity: str, title: str, affected_object: str, snapshot_type: str, explanation: str, action: str, policy_id: str | None = None, age_minutes: int | None = None, threshold_minutes: int | None = None, related_job_id: str | None = None) -> dict[str, Any]:
    return {
        "finding_id": _record_id("finding"),
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "severity": severity if severity in SEVERITIES else "warning",
        "title": title,
        "affected_object": affected_object,
        "snapshot_dataset_type": snapshot_type,
        "last_captured_timestamp": None,
        "freshness_threshold_minutes": threshold_minutes,
        "age_minutes": age_minutes,
        "status": "open",
        "explanation": explanation,
        "recommended_operator_action": action,
        "related_collection_plan_or_job": related_job_id,
        "source_policy_id": policy_id,
        "unknown_unavailable_data": [] if age_minutes is not None else ["Last capture timestamp unavailable."],
        **_safety(),
    }


def create_collection_job(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    snapshot_types = payload.get("requested_snapshot_types") or payload.get("snapshot_types")
    if not isinstance(snapshot_types, list) or not snapshot_types:
        snapshot_types = DEFAULT_SNAPSHOT_TYPES[:3]
    run_mode = _safe_text(payload.get("run_mode"), "queued")
    if run_mode == "scheduled-read-only-opt-in" and not build_settings().get("scheduled_collection_enabled"):
        status = "draft"
        warnings = ["Scheduled read-only collection is disabled by default and requires explicit operator opt-in."]
    else:
        status = _safe_text(payload.get("status"), "queued") if _safe_text(payload.get("status"), "queued") in STATUSES else "queued"
        warnings = []
    job = {
        "job_id": _record_id("job"),
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "job_type": _safe_text(payload.get("job_type"), "snapshot_collection"),
        "source_policy_id": _safe_text(payload.get("source_policy_id")),
        "requested_snapshot_types": [_safe_text(x) for x in snapshot_types if _safe_text(x)],
        "requested_dataset_ids": payload.get("requested_dataset_ids", []) if isinstance(payload.get("requested_dataset_ids"), list) else [],
        "requested_markets_theses_subsystems": payload.get("requested_markets_theses_subsystems", []) if isinstance(payload.get("requested_markets_theses_subsystems"), list) else [],
        "run_mode": run_mode,
        "status": status,
        "read_only_assertion": True,
        "mutation_endpoints_blocked_assertion": True,
        "started_at": None,
        "completed_at": None,
        "snapshots_created": [],
        "datasets_affected": [],
        "warnings": warnings,
        "errors": [],
        "unknown_unavailable_data": [],
        "audit_metadata": {"network_attempted": False, "live_mutation_endpoint_called": False},
        **_safety(),
    }
    _write_jsonl(JOBS_PATH, job)
    _audit("collection_job_created", "ok", {"job_id": job["job_id"], "requested_snapshot_types": job["requested_snapshot_types"]})
    return redact_data(job)


def list_jobs(limit: int = 250, status: str | None = None) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(JOBS_PATH), "job_id")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return {"version": APP_VERSION, "count": len(rows[:limit]), "items": redact_data(rows[: max(1, min(limit, 5000))]), **_safety()}


def get_job(job_id: str) -> dict[str, Any] | None:
    return next((row for row in list_jobs(limit=5000)["items"] if row.get("job_id") == job_id), None)


def run_collection_job(job_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    job = get_job(job_id)
    if not job:
        return {"ok": False, "status": "failed", "error": "collection job not found", **_safety()}
    if job.get("status") in {"cancelled", "completed"}:
        return {"ok": False, "status": job.get("status"), "error": "job is not runnable", "job": job, **_safety()}
    job["status"] = "running"
    job["started_at"] = _now()
    _write_jsonl(JOBS_PATH, job)
    try:
        collection_payload = {
            "snapshot_types": job.get("requested_snapshot_types", DEFAULT_SNAPSHOT_TYPES[:3]),
            "collection_mode": payload.get("collection_mode") or job.get("run_mode") or "manual",
            "notes": "Run from v3.7 freshness collection job. Read-only and operator-controlled.",
        }
        result = collect_snapshots(collection_payload)
        job["status"] = "completed" if result.get("ok", True) else "failed"
        job["completed_at"] = _now()
        job["updated_at"] = _now()
        job["snapshots_created"] = [snap.get("snapshot_id") for snap in result.get("snapshots", []) if isinstance(snap, dict)]
        job["warnings"] = list(job.get("warnings", [])) + list(result.get("warnings", []))
        job["errors"] = list(result.get("errors", [])) if isinstance(result.get("errors"), list) else []
        job["unknown_unavailable_data"] = list(result.get("unknown_unavailable_data", [])) if isinstance(result.get("unknown_unavailable_data"), list) else []
        job.update(_safety())
        _write_jsonl(JOBS_PATH, job)
        _audit("collection_job_run", "ok", {"job_id": job_id, "snapshots_created": len(job["snapshots_created"])})
        return redact_data({"ok": True, "job": job, "collection_result": result, **_safety()})
    except Exception as exc:
        job["status"] = "failed"
        job["completed_at"] = _now()
        job["errors"] = [redact_text(str(exc))]
        _write_jsonl(JOBS_PATH, job)
        create_notification({"notification_type": "collection_job_failed", "severity": "warning", "title": "Collection job failed", "message": f"Job {job_id} failed. Review the redacted error and rerun manually.", "related_object_ids": [job_id]})
        _audit("collection_job_failed", "warning", {"job_id": job_id, "error_redacted": redact_text(str(exc))})
        return redact_data({"ok": False, "job": job, "error_redacted": redact_text(str(exc)), **_safety()})


def cancel_collection_job(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        return {"ok": False, "status": "not_found", **_safety()}
    job["status"] = "cancelled"
    job["updated_at"] = _now()
    job.update(_safety())
    _write_jsonl(JOBS_PATH, job)
    _audit("collection_job_cancelled", "ok", {"job_id": job_id})
    return redact_data({"ok": True, "job": job, **_safety()})


def create_notification(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    status = _safe_text(payload.get("status"), "new")
    notification = {
        "notification_id": _record_id("note"),
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "notification_type": _safe_text(payload.get("notification_type"), "freshness_notice"),
        "severity": _safe_text(payload.get("severity"), "info") if _safe_text(payload.get("severity"), "info") in SEVERITIES else "info",
        "title": _safe_text(payload.get("title"), "Freshness notification"),
        "message": _safe_text(payload.get("message"), "Review dataset freshness."),
        "related_subsystem": _safe_text(payload.get("related_subsystem"), "freshness"),
        "related_object_ids": payload.get("related_object_ids", []) if isinstance(payload.get("related_object_ids"), list) else [],
        "recommended_operator_action": _safe_text(payload.get("recommended_operator_action"), "Open the freshness planner and review next collection steps."),
        "status": status if status in NOTIFICATION_STATUSES else "new",
        "snooze_until": _safe_text(payload.get("snooze_until")),
        "audit_metadata": {"network_attempted": False, "live_mutation_endpoint_called": False},
        **_safety(),
    }
    _write_jsonl(NOTIFICATIONS_PATH, notification)
    _audit("local_notification_created", "ok", {"notification_id": notification["notification_id"], "severity": notification["severity"]})
    return redact_data(notification)


def list_notifications(limit: int = 250, status: str | None = None) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(NOTIFICATIONS_PATH), "notification_id")
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return {"version": APP_VERSION, "count": len(rows[:limit]), "items": redact_data(rows[: max(1, min(limit, 5000))]), **_safety()}


def update_notification(notification_id: str, action: str, snooze_minutes: int | None = None) -> dict[str, Any]:
    row = next((n for n in list_notifications(limit=5000)["items"] if n.get("notification_id") == notification_id), None)
    if not row:
        return {"ok": False, "status": "not_found", **_safety()}
    mapping = {"ack": "acknowledged", "acknowledge": "acknowledged", "dismiss": "dismissed", "snooze": "snoozed", "resolve": "resolved"}
    row["status"] = mapping.get(action, action if action in NOTIFICATION_STATUSES else "acknowledged")
    row["updated_at"] = _now()
    if row["status"] == "snoozed":
        minutes = int(snooze_minutes or build_settings().get("notification_snooze_minutes", 240) or 240)
        # store minutes rather than computing wall-clock dependency for transparent local UX
        row["snooze_until"] = f"now+{minutes}m"
    row.update(_safety())
    _write_jsonl(NOTIFICATIONS_PATH, row)
    _audit(f"local_notification_{row['status']}", "ok", {"notification_id": notification_id})
    return redact_data({"ok": True, "notification": row, **_safety()})


def freshness_scan(write: bool = True) -> dict[str, Any]:
    policies = [p for p in list_policies(limit=5000)["items"] if p.get("enabled", True)]
    latest = _latest_snapshot_by_type()
    findings: list[dict[str, Any]] = []
    for policy in policies:
        threshold = int(policy.get("freshness_threshold_minutes") or 1440)
        for stype in policy.get("target_snapshot_types", []):
            snap = latest.get(str(stype))
            if not snap:
                job = create_collection_job({"source_policy_id": policy.get("policy_id"), "snapshot_types": [stype], "status": "draft", "run_mode": "queued"}) if write else {"job_id": None}
                finding = _make_finding(policy.get("severity_when_stale", "warning"), f"Missing {stype} snapshot", stype, stype, f"No local {stype} snapshot was found for this freshness policy.", "Create a queued read-only collection job or collect this snapshot manually.", policy.get("policy_id"), None, threshold, job.get("job_id"))
                findings.append(finding)
                if write:
                    _write_jsonl(FINDINGS_PATH, finding)
                    if build_settings().get("create_notifications_on_scan", True):
                        create_notification({"notification_type": "missing_snapshot", "severity": finding["severity"], "title": finding["title"], "message": finding["explanation"], "related_object_ids": [finding["finding_id"]], "recommended_operator_action": finding["recommended_operator_action"]})
                continue
            age = _age_minutes(snap.get("created_at") or snap.get("source_timestamp"))
            if age is None or age > threshold:
                job = create_collection_job({"source_policy_id": policy.get("policy_id"), "snapshot_types": [stype], "status": "draft", "run_mode": "queued"}) if write else {"job_id": None}
                finding = _make_finding(policy.get("severity_when_stale", "warning"), f"Stale {stype} snapshot", snap.get("snapshot_id", stype), stype, f"Latest {stype} snapshot is older than the configured threshold." if age is not None else "Latest snapshot timestamp is unavailable.", "Review and run a queued read-only collection job if this dataset will be used for replay/simulation.", policy.get("policy_id"), age, threshold, job.get("job_id"))
                finding["last_captured_timestamp"] = snap.get("created_at")
                findings.append(finding)
                if write:
                    _write_jsonl(FINDINGS_PATH, finding)
                    if build_settings().get("create_notifications_on_scan", True):
                        create_notification({"notification_type": "stale_snapshot", "severity": finding["severity"], "title": finding["title"], "message": finding["explanation"], "related_object_ids": [finding["finding_id"], snap.get("snapshot_id")], "recommended_operator_action": finding["recommended_operator_action"]})
    manifests = list_dataset_manifests(limit=5000).get("items", [])
    for manifest in manifests:
        if manifest.get("quality_status") in {"partial", "stale", "incomplete", "blocked", "unknown"} or manifest.get("quality_score", 0) < 60:
            finding = _make_finding("warning", "Dataset needs freshness/quality review", manifest.get("dataset_id", "dataset"), "dataset_manifest", "Dataset quality is below ideal or has unresolved unknown data.", "Open the dataset readiness planner before using this dataset for replay or simulation.", None, None, None, None)
            findings.append(finding)
            if write:
                _write_jsonl(FINDINGS_PATH, finding)
    report = {"version": APP_VERSION, "created_at": _now(), "finding_count": len(findings), "findings": redact_data(findings), "policy_count": len(policies), **_safety()}
    if write:
        _audit("freshness_scan_run", "ok", {"finding_count": len(findings), "policy_count": len(policies)})
    return redact_data(report)


def list_findings(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(FINDINGS_PATH), "finding_id")
    return {"version": APP_VERSION, "count": len(rows[:limit]), "items": redact_data(rows[: max(1, min(limit, 5000))]), **_safety()}


def readiness_report(payload: dict[str, Any] | None = None, write: bool = True) -> dict[str, Any]:
    payload = payload or {}
    ds = datasets_summary()
    findings = freshness_scan(write=False).get("findings", [])
    stale = [f for f in findings if f.get("severity") in {"warning", "blocker", "critical"}]
    quality_score = int(ds.get("quality_score") or 0)
    freshness_score = max(0, 100 - min(len(stale) * 15, 100))
    status = "ready" if freshness_score >= 75 and quality_score >= 60 and not any(f.get("severity") in {"blocker", "critical"} for f in findings) else ("needs_review" if freshness_score >= 40 else "not_ready")
    report = {
        "readiness_report_id": _record_id("ready"),
        "created_at": _now(),
        "app_version": APP_VERSION,
        "dataset_id": _safe_text(payload.get("dataset_id")),
        "readiness_status": status,
        "freshness_score": freshness_score,
        "quality_score_summary": {"score": quality_score, "status": ds.get("quality_status", "unknown")},
        "missing_snapshots": [f for f in findings if f.get("title", "").lower().startswith("missing")],
        "stale_snapshots": [f for f in findings if f.get("title", "").lower().startswith("stale")],
        "recommended_collection_jobs": [f.get("related_collection_plan_or_job") for f in findings if f.get("related_collection_plan_or_job")],
        "warnings": [f.get("title") for f in stale],
        "limitations": ["Readiness is based on local snapshots and dataset manifests only.", "No missing market data is invented."],
        "unknown_unavailable_data": ["Order book or market metadata may be unavailable unless explicitly collected or provided."],
        **_safety(),
    }
    if write:
        _write_jsonl(READINESS_PATH, report)
        _audit("readiness_report_generated", "ok", {"readiness_status": status, "finding_count": len(findings)})
    return redact_data(report)


def list_readiness_reports(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(READINESS_PATH), "readiness_report_id")
    return {"version": APP_VERSION, "count": len(rows[:limit]), "items": redact_data(rows[: max(1, min(limit, 5000))]), **_safety()}


def summary() -> dict[str, Any]:
    ds = datasets_summary()
    jobs = list_jobs(limit=5000)["items"]
    notifications = list_notifications(limit=5000)["items"]
    findings = list_findings(limit=5000)["items"]
    stale_count = sum(1 for f in findings if f.get("severity") in {"warning", "blocker", "critical"})
    queued_jobs = sum(1 for j in jobs if j.get("status") in {"queued", "ready", "draft"})
    failed_jobs = sum(1 for j in jobs if j.get("status") == "failed")
    unread = sum(1 for n in notifications if n.get("status") == "new")
    latest_job = jobs[0] if jobs else None
    latest_notification = notifications[0] if notifications else None
    return redact_data({
        "version": APP_VERSION,
        "dataset_freshness_status": "needs_review" if stale_count else "unknown" if not findings else "healthy",
        "stale_snapshot_count": stale_count,
        "stale_dataset_count": int(ds.get("stale_dataset_warnings", 0) or 0),
        "queued_collection_jobs": queued_jobs,
        "failed_collection_jobs": failed_jobs,
        "unread_local_notifications": unread,
        "replay_readiness_warnings": stale_count + int(ds.get("missing_snapshot_warnings", 0) or 0),
        "latest_collection_job": latest_job,
        "latest_notification": latest_notification,
        "policy_count": list_policies(limit=5000)["count"],
        "next_dataset_collection_action": "Run a freshness scan, review notifications, then manually run queued read-only collection jobs for stale snapshots.",
        "scheduler_disabled_by_default": True,
        "dataset_context": {"snapshot_count": ds.get("snapshot_count", 0), "dataset_count": ds.get("dataset_count", 0), "quality_status": ds.get("quality_status", "unknown")},
        **_safety(),
    })


def export_freshness_json() -> dict[str, Any]:
    report = {"version": APP_VERSION, "created_at": _now(), "summary": summary(), "policies": list_policies(limit=1000)["items"], "jobs": list_jobs(limit=1000)["items"], "findings": list_findings(limit=1000)["items"], "notifications": list_notifications(limit=1000)["items"], "readiness_reports": list_readiness_reports(limit=1000)["items"], **_safety()}
    _audit("freshness_report_exported", "ok", {"format": "json"})
    return redact_data(report)


def export_freshness_markdown() -> str:
    s = summary()
    lines = ["# v3.7 Freshness / Scheduler Report", "", f"Generated: {_now()}", f"Version: {APP_VERSION}", "", "## Summary", f"- Dataset freshness status: {s.get('dataset_freshness_status')}", f"- Stale snapshots: {s.get('stale_snapshot_count')}", f"- Stale datasets: {s.get('stale_dataset_count')}", f"- Queued jobs: {s.get('queued_collection_jobs')}", f"- Failed jobs: {s.get('failed_collection_jobs')}", f"- Unread local notifications: {s.get('unread_local_notifications')}", "", "## Safety", _safety()["safety_statement"]]
    _audit("freshness_report_exported", "ok", {"format": "markdown"})
    return "\n".join(lines) + "\n"


def export_notifications_json() -> dict[str, Any]:
    _audit("notification_exported", "ok", {"format": "json"})
    return {"version": APP_VERSION, "notifications": list_notifications(limit=5000)["items"], **_safety()}


def export_csv(kind: str = "jobs") -> str:
    kind = _safe_text(kind, "jobs")
    if kind == "findings":
        rows = list_findings(limit=5000)["items"]
        fieldnames = ["finding_id", "severity", "title", "affected_object", "snapshot_dataset_type", "age_minutes", "freshness_threshold_minutes", "status", "created_at", "order_submitted", "order_cancelled", "live_trading_armed"]
    elif kind == "notifications":
        rows = list_notifications(limit=5000)["items"]
        fieldnames = ["notification_id", "notification_type", "severity", "title", "status", "created_at", "updated_at", "order_submitted", "order_cancelled", "live_trading_armed"]
    else:
        rows = list_jobs(limit=5000)["items"]
        fieldnames = ["job_id", "job_type", "run_mode", "status", "requested_snapshot_types", "created_at", "started_at", "completed_at", "order_submitted", "order_cancelled", "live_trading_armed"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in fieldnames})
    _audit("freshness_report_exported", "ok", {"format": "csv", "kind": kind})
    return output.getvalue()


def freshness_search_items(limit: int = 100) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for policy in list_policies(limit=limit).get("items", []):
        rows.append({"result_id": f"freshness_policy:{policy.get('policy_id')}", "result_type": "freshness_policy", "title": policy.get("title", "Freshness policy"), "summary": policy.get("description", ""), "timestamp": policy.get("updated_at", policy.get("created_at", "")), "status": "enabled" if policy.get("enabled") else "disabled", "tags": ["freshness", "policy"], "quick_link": "/v3/freshness/schedules", "search_text": f"freshness policy collection scheduler {policy.get('title')} {policy.get('description')}".lower()})
    for job in list_jobs(limit=limit).get("items", []):
        rows.append({"result_id": f"collection_job:{job.get('job_id')}", "result_type": "collection_job", "title": f"Collection job {job.get('status')}", "summary": ", ".join(job.get("requested_snapshot_types", [])), "timestamp": job.get("created_at", ""), "status": job.get("status", "unknown"), "tags": ["freshness", "collection", "job"], "quick_link": "/v3/freshness/jobs", "search_text": f"collection job freshness scheduler {job.get('status')} {' '.join(job.get('requested_snapshot_types', []))}".lower()})
    for note in list_notifications(limit=limit).get("items", []):
        rows.append({"result_id": f"operator_notification:{note.get('notification_id')}", "result_type": "operator_notification", "title": note.get("title", "Notification"), "summary": note.get("message", ""), "timestamp": note.get("created_at", ""), "status": note.get("status", "new"), "tags": ["freshness", "notification", note.get("severity", "info")], "quick_link": "/v3/freshness/notifications", "search_text": f"freshness notification {note.get('title')} {note.get('message')}".lower()})
    for finding in list_findings(limit=limit).get("items", []):
        rows.append({"result_id": f"stale_dataset_finding:{finding.get('finding_id')}", "result_type": "stale_dataset_finding", "title": finding.get("title", "Finding"), "summary": finding.get("explanation", ""), "timestamp": finding.get("created_at", ""), "status": finding.get("status", "open"), "tags": ["freshness", "finding", finding.get("severity", "info")], "quick_link": "/v3/freshness/readiness", "search_text": f"freshness stale finding {finding.get('title')} {finding.get('explanation')}".lower()})
    return redact_data(rows[: max(1, min(int(limit or 100), 1000))])


def freshness_graph_nodes_edges() -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for item in freshness_search_items(limit=500):
        nodes.append({"node_id": item["result_id"], "node_type": item["result_type"], "title": item["title"], "status": item.get("status", "unknown"), "timestamp": item.get("timestamp", ""), "tags": item.get("tags", []), "related_object_id": item["result_id"].split(":", 1)[-1], "summary": item.get("summary", ""), "safe_metadata": {"quick_link": item.get("quick_link")}})
    for job in list_jobs(limit=500).get("items", []):
        if job.get("source_policy_id"):
            edges.append({"edge_id": _record_id("edge"), "source_node": f"freshness_policy:{job.get('source_policy_id')}", "target_node": f"collection_job:{job.get('job_id')}", "relationship_type": "queued_for", "created_at": job.get("created_at", _now()), "safe_metadata": {"read_only": True}})
    for note in list_notifications(limit=500).get("items", []):
        for oid in note.get("related_object_ids", [])[:10]:
            edges.append({"edge_id": _record_id("edge"), "source_node": f"operator_notification:{note.get('notification_id')}", "target_node": str(oid), "relationship_type": "notifies", "created_at": note.get("created_at", _now()), "safe_metadata": {"severity": note.get("severity")}})
    return {"nodes": redact_data(nodes), "edges": redact_data(edges), "secret_values_returned": False}


def freshness_analytics_context() -> dict[str, Any]:
    s = summary()
    jobs = list_jobs(limit=5000)["items"]
    notes = list_notifications(limit=5000)["items"]
    return {"stale_dataset_trend": s.get("stale_dataset_count", 0), "collection_job_completion_rate": round((sum(1 for j in jobs if j.get("status") == "completed") / max(1, len(jobs))) * 100, 2), "failed_collection_job_count": s.get("failed_collection_jobs", 0), "freshness_policy_coverage": list_policies(limit=5000).get("count", 0), "dataset_readiness_trend": s.get("dataset_freshness_status"), "notification_resolution_rate": round((sum(1 for n in notes if n.get("status") in {"resolved", "dismissed", "acknowledged"}) / max(1, len(notes))) * 100, 2), "recurring_stale_snapshot_types": [f.get("snapshot_dataset_type") for f in list_findings(limit=100).get("items", [])[:10]], "secret_values_returned": False}


def freshness_workflow_context() -> dict[str, Any]:
    return {"freshness_review": freshness_scan(write=False), "collection_plan_review": {"policies": list_policies(limit=100)["items"], "jobs": list_jobs(limit=100)["items"]}, "notification_triage": list_notifications(limit=100), "dataset_readiness_review": readiness_report(write=False), "secret_values_returned": False, **_safety()}


def create_demo_freshness_records() -> dict[str, Any]:
    policy = create_policy({"title": "DEMO Dataset Freshness Policy", "description": "Fake policy for screenshot QA.", "target_snapshot_types": ["market_metadata", "order_book"], "freshness_threshold_minutes": 30, "severity_when_stale": "warning", "collection_mode": "queued manual"})
    job = create_collection_job({"source_policy_id": policy["policy_id"], "snapshot_types": ["market_metadata", "order_book"], "run_mode": "demo", "status": "queued"})
    failed_job = create_collection_job({"snapshot_types": ["local_research"], "run_mode": "demo", "status": "failed"})
    completed = run_collection_job(job["job_id"], {"collection_mode": "demo"})
    report = readiness_report({"dataset_id": "DEMO-DATASET-NEEDS-REFRESH"})
    note = create_notification({"notification_type": "stale_dataset", "severity": "warning", "title": "DEMO dataset needs refresh", "message": "Fake notification: this replay dataset has stale snapshots.", "related_object_ids": [report["readiness_report_id"]], "recommended_operator_action": "Open the freshness planner and run a read-only demo collection job."})
    snoozed = create_notification({"notification_type": "scheduled_collection_opt_in_required", "severity": "info", "title": "DEMO scheduled collection disabled", "message": "Scheduling is disabled by default until the operator opts in.", "status": "snoozed", "snooze_until": "now+240m"})
    return redact_data({"ok": True, "policy": policy, "queued_job": job, "failed_job": failed_job, "completed_job": completed, "readiness_report": report, "notification": note, "snoozed_notification": snoozed, "demo_data_is_fake": True, **_safety()})
