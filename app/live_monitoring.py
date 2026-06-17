from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_v2 import build_live_v2_readiness, record_audit, redact_data, redact_text
from .live_strategy import list_theses, list_watchlist
from .live_research import freshness_summary

MONITORING_DIR = DATA_DIR / "live_v2" / "monitoring"
MONITORING_EVENTS_PATH = MONITORING_DIR / "monitoring_events.jsonl"

COLLECTIONS = {"rules", "alerts", "history", "snapshots"}
RULE_TYPES = {
    "price_threshold",
    "spread",
    "liquidity",
    "market_status",
    "watchlist",
    "thesis",
    "evidence_freshness",
    "readiness_posture",
}
RULE_STATUSES = {"enabled", "disabled", "archived"}
ALERT_STATUSES = {"active", "acknowledged", "snoozed", "resolved", "archived"}
SEVERITIES = {"info", "watch", "warning", "critical"}
CONDITIONS = {
    "above",
    "below",
    "crosses",
    "equals",
    "not_equals",
    "review_due",
    "stale",
    "aging",
    "expired",
    "failed",
    "changed",
    "manual",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    MONITORING_DIR.mkdir(parents=True, exist_ok=True)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _safe(value: Any, allowed: set[str], default: str) -> str:
    candidate = _text(value, default).lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    return candidate if candidate in allowed else default


def _tags(value: Any) -> list[str]:
    raw = value if isinstance(value, list) else str(value or "").split(",")
    return sorted({redact_text(item).strip() for item in raw if redact_text(item).strip()})


def _event(action: str, collection: str, item: dict[str, Any]) -> dict[str, Any]:
    return redact_data({
        "event_id": f"monitoring_evt_{uuid4().hex[:12]}",
        "timestamp": _now(),
        "app_version": APP_VERSION,
        "action": action,
        "collection": collection,
        "item_id": item.get("id", ""),
        "item": item,
        "secret_values_returned": False,
    })


def _append_event(action: str, collection: str, item: dict[str, Any]) -> dict[str, Any]:
    if collection not in COLLECTIONS:
        raise ValueError(f"Unsupported monitoring collection: {collection}")
    _ensure_dir()
    event = _event(action, collection, item)
    with MONITORING_EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
    record_audit(
        f"monitoring_{action}",
        "recorded",
        details={
            "collection": collection,
            "item_id": item.get("id", ""),
            "rule_type": item.get("rule_type", ""),
            "severity": item.get("severity", ""),
            "order_submitted": False,
            "order_cancelled": False,
            "live_armed_changed": False,
            "secret_values_returned": False,
        },
    )
    return event


def _read_events() -> list[dict[str, Any]]:
    if not MONITORING_EVENTS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in MONITORING_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(redact_data(json.loads(line)))
        except json.JSONDecodeError:
            continue
    return rows


def list_monitoring_events(limit: int = 500) -> list[dict[str, Any]]:
    return list(reversed(_read_events()))[: max(1, min(int(limit or 500), 5000))]


def _latest(collection: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in _read_events():
        if event.get("collection") != collection:
            continue
        item = event.get("item") or {}
        if isinstance(item, dict) and item.get("id"):
            latest[str(item["id"])] = item
    return sorted(latest.values(), key=lambda item: item.get("updated_at", item.get("triggered_at", "")), reverse=True)


def get_monitoring_item(collection: str, item_id: str) -> dict[str, Any] | None:
    for item in _latest(collection):
        if item.get("id") == item_id:
            return item
    return None


def _normalize_rule(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    now = _now()
    status = _safe(payload.get("status", existing.get("status", "enabled")), RULE_STATUSES, "enabled")
    if _bool(payload.get("enabled"), status == "enabled") and status != "archived":
        status = "enabled"
    if not _bool(payload.get("enabled", True), True) and status != "archived":
        status = "disabled"
    rule_type = _safe(payload.get("rule_type", existing.get("rule_type", "manual")), RULE_TYPES, "watchlist")
    item = {
        "id": _text(payload.get("id"), existing.get("id") or f"rule_{uuid4().hex[:12]}"),
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "rule_name": redact_text(payload.get("rule_name", payload.get("title", existing.get("rule_name", "Untitled alert rule")))),
        "title": redact_text(payload.get("title", payload.get("rule_name", existing.get("title", existing.get("rule_name", "Untitled alert rule"))))),
        "rule_type": rule_type,
        "related_market_id": redact_text(payload.get("related_market_id", payload.get("market_id", existing.get("related_market_id", "")))),
        "related_market_slug": redact_text(payload.get("related_market_slug", payload.get("market_slug", existing.get("related_market_slug", "")))),
        "related_outcome": redact_text(payload.get("related_outcome", payload.get("outcome", existing.get("related_outcome", "")))),
        "related_thesis_id": redact_text(payload.get("related_thesis_id", payload.get("thesis_id", existing.get("related_thesis_id", "")))),
        "related_evidence_id": redact_text(payload.get("related_evidence_id", payload.get("evidence_id", existing.get("related_evidence_id", "")))),
        "related_watchlist_id": redact_text(payload.get("related_watchlist_id", payload.get("watchlist_id", existing.get("related_watchlist_id", "")))),
        "condition": _safe(payload.get("condition", existing.get("condition", "manual")), CONDITIONS, "manual"),
        "threshold_value": _number(payload.get("threshold_value", existing.get("threshold_value", 0)), 0),
        "current_value": _number(payload.get("current_value", existing.get("current_value", 0)), 0),
        "review_cadence_days": max(0, _int(payload.get("review_cadence_days", existing.get("review_cadence_days", 0)), 0)),
        "review_by": redact_text(payload.get("review_by", existing.get("review_by", ""))),
        "severity": _safe(payload.get("severity", existing.get("severity", "watch")), SEVERITIES, "watch"),
        "status": status,
        "last_evaluated_at": existing.get("last_evaluated_at", ""),
        "last_triggered_at": existing.get("last_triggered_at", ""),
        "acknowledgement_state": existing.get("acknowledgement_state", "unacknowledged"),
        "snooze_until": existing.get("snooze_until", ""),
        "operator_notes": redact_text(payload.get("operator_notes", payload.get("notes", existing.get("operator_notes", "")))),
        "tags": _tags(payload.get("tags", existing.get("tags", []))),
        "audit_metadata": {"source": "live_monitoring_v2_6", "secret_values_returned": False},
    }
    return redact_data(item)


def _evaluate_condition(rule: dict[str, Any], sample: dict[str, Any] | None = None) -> tuple[bool, str, float | str]:
    sample = sample or {}
    rule_type = rule.get("rule_type")
    condition = rule.get("condition", "manual")
    threshold = _number(rule.get("threshold_value"), 0)
    value = sample.get("current_value", sample.get("price", sample.get("spread", sample.get("liquidity", rule.get("current_value", 0)))))
    numeric = _number(value, 0)

    if rule.get("status") != "enabled":
        return False, "Rule is not enabled.", numeric
    if rule.get("snooze_until") and str(rule.get("snooze_until")) > _now():
        return False, f"Rule is snoozed until {rule.get('snooze_until')}.", numeric

    if condition == "above":
        return numeric > threshold, f"Current value {numeric} is {'above' if numeric > threshold else 'not above'} threshold {threshold}.", numeric
    if condition == "below":
        return numeric < threshold, f"Current value {numeric} is {'below' if numeric < threshold else 'not below'} threshold {threshold}.", numeric
    if condition == "equals":
        text_value = _text(sample.get("current_value", sample.get("status", value)))
        target = _text(rule.get("threshold_value"))
        return text_value == target, f"Current value {text_value or 'unknown'} {'equals' if text_value == target else 'does not equal'} {target}.", text_value
    if condition == "not_equals":
        text_value = _text(sample.get("current_value", sample.get("status", value)))
        target = _text(rule.get("threshold_value"))
        return text_value != target, f"Current value {text_value or 'unknown'} {'differs from' if text_value != target else 'matches'} {target}.", text_value
    if condition in {"review_due", "stale", "aging", "expired", "failed", "changed"}:
        status = _text(sample.get("status", sample.get("freshness_status", ""))).lower()
        due = False
        if condition == "review_due" and rule.get("review_by"):
            due = str(rule.get("review_by")) <= _now()[:10]
        triggered = due or status == condition or bool(sample.get(condition))
        reason = f"Condition {condition} is {'active' if triggered else 'not active'} for linked object."
        return triggered, reason, status or ("due" if due else "not_due")
    if rule_type == "readiness_posture":
        readiness = sample.get("readiness_status") or sample.get("overall_status") or "unknown"
        triggered = readiness in {"fail", "needs_review", "not_ready"}
        return triggered, f"Readiness posture is {readiness}.", readiness
    return True, "Manual evaluation requested. No order, cancel, approval, signing, or live arming occurred.", numeric


def _normalize_alert(rule: dict[str, Any], reason: str, current_value: Any, *, status: str = "active") -> dict[str, Any]:
    now = _now()
    return redact_data({
        "id": f"alert_{uuid4().hex[:12]}",
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "rule_id": rule.get("id", ""),
        "rule_name": rule.get("rule_name", rule.get("title", "Alert rule")),
        "rule_type": rule.get("rule_type", ""),
        "title": f"{rule.get('severity', 'watch').title()}: {rule.get('rule_name', rule.get('title', 'Alert'))}",
        "severity": rule.get("severity", "watch"),
        "status": _safe(status, ALERT_STATUSES, "active"),
        "triggered_at": now,
        "last_evaluated_at": now,
        "acknowledgement_state": "unacknowledged",
        "snooze_until": "",
        "related_market_id": rule.get("related_market_id", ""),
        "related_thesis_id": rule.get("related_thesis_id", ""),
        "related_evidence_id": rule.get("related_evidence_id", ""),
        "related_watchlist_id": rule.get("related_watchlist_id", ""),
        "current_value": current_value,
        "reason": reason,
        "recommended_operator_action": recommended_action(rule),
        "safety_statement": "No action taken automatically. Alerts never place, cancel, approve, sign, or arm live orders.",
        "secret_values_returned": False,
    })


def recommended_action(rule: dict[str, Any]) -> str:
    rt = rule.get("rule_type")
    if rt == "evidence_freshness":
        return "Refresh or review the linked source/evidence before relying on it."
    if rt == "thesis":
        return "Review the linked thesis manually before creating or updating a ticket."
    if rt == "watchlist":
        return "Open the linked watchlist item and decide whether a thesis or paper rehearsal is needed."
    if rt in {"price_threshold", "spread", "liquidity", "market_status"}:
        return "Inspect market data and order book manually; no order has been created."
    if rt == "readiness_posture":
        return "Open readiness/verification before any live use."
    return "Review this alert; no automatic trading action was taken."


def create_rule(payload: dict[str, Any]) -> dict[str, Any]:
    item = _normalize_rule(payload)
    event = _append_event("monitor_rule_created", "rules", item)
    return {"ok": True, "item": item, "event": event, "order_submitted": False, "order_cancelled": False, "live_armed_changed": False, "secret_values_returned": False}


def update_rule(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_monitoring_item("rules", item_id)
    if not existing:
        return {"ok": False, "status": "not_found", "item_id": item_id, "secret_values_returned": False}
    item = _normalize_rule({**payload, "id": item_id}, existing)
    event = _append_event("monitor_rule_edited", "rules", item)
    return {"ok": True, "item": item, "event": event, "order_submitted": False, "order_cancelled": False, "live_armed_changed": False, "secret_values_returned": False}


def disable_rule(item_id: str) -> dict[str, Any]:
    return update_rule(item_id, {"status": "disabled", "enabled": False}) | {"action": "disabled"}


def archive_rule(item_id: str) -> dict[str, Any]:
    result = update_rule(item_id, {"status": "archived", "enabled": False})
    if result.get("ok"):
        _append_event("monitor_rule_archived", "rules", result["item"])
    return result | {"action": "archived"}


def evaluate_rule(item_id: str, sample: dict[str, Any] | None = None) -> dict[str, Any]:
    rule = get_monitoring_item("rules", item_id)
    if not rule:
        return {"ok": False, "status": "not_found", "item_id": item_id, "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    triggered, reason, current_value = _evaluate_condition(rule, sample)
    evaluated = {**rule, "last_evaluated_at": _now(), "current_value": current_value}
    if triggered:
        evaluated["last_triggered_at"] = _now()
    _append_event("rule_evaluated", "rules", evaluated)
    alert = None
    if triggered:
        alert = _normalize_alert(evaluated, reason, current_value)
        _append_event("alert_triggered", "alerts", alert)
    return redact_data({
        "ok": True,
        "triggered": triggered,
        "reason": reason,
        "current_value": current_value,
        "rule": evaluated,
        "alert": alert,
        "order_submitted": False,
        "order_cancelled": False,
        "live_armed_changed": False,
        "network_attempted": False,
        "secret_values_returned": False,
    })


def evaluate_all(sample: dict[str, Any] | None = None) -> dict[str, Any]:
    results = []
    for rule in list_rules(status="enabled", limit=1000).get("items", []):
        results.append(evaluate_rule(rule["id"], sample))
    return redact_data({
        "version": APP_VERSION,
        "generated_at": _now(),
        "evaluated": len(results),
        "triggered": len([r for r in results if r.get("triggered")]),
        "results": results,
        "safety_statement": "Evaluation is read-only and never places, cancels, approves, signs, or arms live orders.",
        "order_submitted": False,
        "order_cancelled": False,
        "live_armed_changed": False,
        "secret_values_returned": False,
    })


def _update_alert(alert_id: str, *, status: str, action: str, snooze_minutes: int = 0) -> dict[str, Any]:
    alert = get_monitoring_item("alerts", alert_id)
    if not alert:
        return {"ok": False, "status": "not_found", "alert_id": alert_id, "secret_values_returned": False}
    now = _now()
    updated = dict(alert)
    updated.update({"status": _safe(status, ALERT_STATUSES, status), "updated_at": now})
    if status == "acknowledged":
        updated["acknowledgement_state"] = "acknowledged"
        updated["acknowledged_at"] = now
    if status == "snoozed":
        updated["acknowledgement_state"] = "snoozed"
        updated["snooze_until"] = (datetime.now(timezone.utc) + timedelta(minutes=max(1, snooze_minutes or 60))).isoformat()
    event = _append_event(action, "alerts", updated)
    return {"ok": True, "item": updated, "event": event, "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}


def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    return _update_alert(alert_id, status="acknowledged", action="alert_acknowledged")


def snooze_alert(alert_id: str, minutes: int = 60) -> dict[str, Any]:
    return _update_alert(alert_id, status="snoozed", action="alert_snoozed", snooze_minutes=minutes)


def list_rules(status: str = "", limit: int = 200) -> dict[str, Any]:
    items = _latest("rules")
    if status:
        items = [item for item in items if item.get("status") == status]
    return {"items": items[: max(1, min(int(limit or 200), 1000))], "count": len(items), "version": APP_VERSION, "secret_values_returned": False}


def list_alerts(status: str = "", severity: str = "", limit: int = 200) -> dict[str, Any]:
    items = _latest("alerts")
    if status:
        items = [item for item in items if item.get("status") == status]
    if severity:
        items = [item for item in items if item.get("severity") == severity]
    return {"items": items[: max(1, min(int(limit or 200), 1000))], "count": len(items), "version": APP_VERSION, "secret_values_returned": False}


def list_alert_history(limit: int = 500) -> dict[str, Any]:
    return {"items": list_monitoring_events(limit=limit), "count": len(list_monitoring_events(limit=limit)), "version": APP_VERSION, "secret_values_returned": False}


def build_monitoring_workspace(limit: int = 100) -> dict[str, Any]:
    rules = _latest("rules")
    alerts = _latest("alerts")
    active_alerts = [item for item in alerts if item.get("status") == "active"]
    critical_alerts = [item for item in active_alerts if item.get("severity") == "critical"]
    watchlist_items = list_watchlist(limit=1000).get("items", [])
    theses = list_theses(limit=1000).get("items", [])
    freshness = freshness_summary()
    readiness = build_live_v2_readiness()
    stale_count = (freshness.get("summary", {}) or {}).get("stale_sources", 0) + (freshness.get("summary", {}) or {}).get("stale_candidates", 0)
    summary = {
        "rules": len(rules),
        "enabled_rules": len([r for r in rules if r.get("status") == "enabled"]),
        "active_alerts": len(active_alerts),
        "critical_alerts": len(critical_alerts),
        "watchlist_items": len(watchlist_items),
        "theses": len(theses),
        "stale_evidence_items": stale_count,
        "readiness_failures": readiness.get("summary", {}).get("fail", 0),
    }
    next_action = "Create a watchlist, thesis, or evidence freshness alert rule."
    if critical_alerts:
        next_action = "Review critical alerts first; no action has been taken automatically."
    elif active_alerts:
        next_action = "Acknowledge, snooze, or resolve active alerts after manual review."
    elif stale_count:
        next_action = "Create or evaluate evidence freshness reminders for stale research."
    return redact_data({
        "version": APP_VERSION,
        "generated_at": _now(),
        "summary": summary,
        "next_action": next_action,
        "rules": rules[:limit],
        "active_alerts": active_alerts[:limit],
        "alerts": alerts[:limit],
        "history": list_monitoring_events(limit=limit),
        "watchlist_summary": {"count": len(watchlist_items), "items": watchlist_items[:10]},
        "thesis_summary": {"count": len(theses), "items": theses[:10]},
        "freshness_summary": freshness,
        "readiness_summary": readiness.get("summary", {}),
        "safety_statement": "Monitoring alerts are workflow prompts only. They never place, cancel, approve, sign, or arm live orders.",
        "secret_values_returned": False,
    })


def monitoring_export_json() -> dict[str, Any]:
    return build_monitoring_workspace(limit=10000)


def monitoring_export_markdown() -> str:
    workspace = monitoring_export_json()
    lines = [
        f"# Monitoring / Alerts Export — {APP_VERSION}",
        "",
        f"Generated: {workspace.get('generated_at')}",
        "",
        workspace.get("safety_statement", "Alerts do not place or cancel orders."),
        "",
        "## Summary",
        "",
    ]
    for key, value in workspace.get("summary", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Active Alerts", "", "| ID | Severity | Status | Rule | Reason | Recommended Action |", "|---|---|---|---|---|---|"])
    for item in workspace.get("active_alerts", []):
        lines.append("| {id} | {sev} | {status} | {rule} | {reason} | {action} |".format(
            id=_text(item.get("id")), sev=_text(item.get("severity")), status=_text(item.get("status")), rule=_text(item.get("rule_name")).replace("|", "\\|"), reason=_text(item.get("reason")).replace("|", "\\|")[:180], action=_text(item.get("recommended_operator_action")).replace("|", "\\|")[:180]
        ))
    lines.extend(["", "## Rules", "", "| ID | Type | Status | Severity | Condition | Threshold |", "|---|---|---|---|---|---:|"])
    for item in workspace.get("rules", []):
        lines.append(f"| {_text(item.get('id'))} | {_text(item.get('rule_type'))} | {_text(item.get('status'))} | {_text(item.get('severity'))} | {_text(item.get('condition'))} | {item.get('threshold_value', '')} |")
    lines.extend(["", "Secret values are redacted. This report is operator workflow guidance only and does not approve, place, or cancel orders.", ""])
    return "\n".join(lines)


def _csv_for(items: list[dict[str, Any]], fields: list[str]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in item.items()})
    return out.getvalue()


def monitoring_csv(collection: str) -> str:
    if collection == "rules":
        return _csv_for(_latest("rules"), ["id", "created_at", "updated_at", "rule_name", "rule_type", "status", "severity", "condition", "threshold_value", "related_market_id", "related_thesis_id", "related_watchlist_id"])
    if collection in {"alerts", "active_alerts"}:
        items = _latest("alerts")
        if collection == "active_alerts":
            items = [item for item in items if item.get("status") == "active"]
        return _csv_for(items, ["id", "created_at", "updated_at", "rule_id", "rule_name", "rule_type", "severity", "status", "triggered_at", "reason", "recommended_operator_action"])
    return _csv_for(list_monitoring_events(limit=10000), ["event_id", "timestamp", "app_version", "action", "collection", "item_id"])
