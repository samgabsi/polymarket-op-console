from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_v2 import list_audit_records, record_audit, redact_data, redact_text

GOVERNANCE_DIR = DATA_DIR / "live_v2" / "governance"
GOVERNANCE_EVENTS_PATH = GOVERNANCE_DIR / "governance_events.jsonl"

COLLECTIONS = {"journal", "checklists", "reviews", "rules", "near_misses", "mistake_patterns", "improvements"}
DECISION_TYPES = {
    "research_decision", "thesis_decision", "watchlist_decision", "trade_ticket_decision", "risk_decision",
    "portfolio_decision", "monitoring_decision", "emergency_decision", "no_trade_decision", "other",
}
CHECKLIST_STATUSES = {"draft", "in_progress", "completed", "archived"}
REVIEW_TYPES = {"post_trade", "daily", "weekly", "process", "manual"}
SEVERITIES = {"info", "watch", "warning", "critical"}

DEFAULT_PRETRADE_ITEMS = [
    "thesis_exists", "evidence_reviewed", "counter_evidence_reviewed", "stale_evidence_checked",
    "research_questions_acknowledged", "risk_limits_checked", "portfolio_exposure_checked",
    "monitoring_alerts_checked", "entry_criteria_satisfied", "exit_criteria_defined",
    "invalidation_criteria_defined", "bankroll_impact_reviewed", "no_active_emergency_condition",
    "operator_reviewed_warnings", "no_trade_alternative_considered",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = redact_text(str(value).strip())
    return text if text else default


def _number(value: Any, default: float = 0.0, *, minimum: float | None = None, maximum: float | None = None) -> float:
    try:
        result = float(value)
    except Exception:
        result = default
    if minimum is not None:
        result = max(minimum, result)
    if maximum is not None:
        result = min(maximum, result)
    return result


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on", "checked", "complete", "completed"}


def _tags(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or "").split(",")
    return sorted({_text(item) for item in raw if _text(item)})


def _safe_choice(value: Any, allowed: set[str], default: str) -> str:
    candidate = str(value or default).strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    return candidate if candidate in allowed else default


def _event(action: str, collection: str, item: dict[str, Any]) -> dict[str, Any]:
    return redact_data({
        "event_id": f"governance_evt_{uuid4().hex[:12]}",
        "timestamp": _now(),
        "app_version": APP_VERSION,
        "action": action,
        "collection": collection,
        "item_id": item.get("id", ""),
        "item": item,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "secret_values_returned": False,
    })


def _append_event(action: str, collection: str, item: dict[str, Any]) -> dict[str, Any]:
    if collection not in COLLECTIONS:
        raise ValueError(f"Unsupported governance collection: {collection}")
    _ensure_dir()
    event = _event(action, collection, item)
    with GOVERNANCE_EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
    record_audit(
        f"governance_{action}",
        "recorded",
        details={
            "collection": collection,
            "item_id": item.get("id", ""),
            "market_id": item.get("related_market_id", item.get("market_id", "")),
            "secret_values_returned": False,
        },
    )
    return event


def _read_events() -> list[dict[str, Any]]:
    if not GOVERNANCE_EVENTS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in GOVERNANCE_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(redact_data(json.loads(line)))
        except json.JSONDecodeError:
            continue
    return rows


def list_governance_events(limit: int = 500) -> list[dict[str, Any]]:
    return list(reversed(_read_events()))[: max(1, min(int(limit or 500), 5000))]


def _latest(collection: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in _read_events():
        if event.get("collection") != collection:
            continue
        item = event.get("item") or {}
        if isinstance(item, dict) and item.get("id"):
            latest[str(item["id"])] = item
    return sorted(latest.values(), key=lambda item: item.get("updated_at", item.get("created_at", "")), reverse=True)


def _list(collection: str, *, status: str = "", limit: int = 200) -> dict[str, Any]:
    items = _latest(collection)
    if status:
        normalized = _safe_choice(status, {"draft", "active", "reviewed", "closed", "archived", "completed", "enabled", "disabled", "resolved", "open", "in_progress"}, status)
        items = [item for item in items if str(item.get("status", "")).lower() == normalized]
    return {"items": items[: max(1, min(int(limit or 200), 1000))], "count": len(items), "version": APP_VERSION, "secret_values_returned": False}


def get_governance_item(collection: str, item_id: str) -> dict[str, Any] | None:
    if collection not in COLLECTIONS:
        return None
    for item in _latest(collection):
        if item.get("id") == item_id:
            return item
    return None


def list_journal(status: str = "", limit: int = 200) -> dict[str, Any]:
    return _list("journal", status=status, limit=limit)


def list_checklists(status: str = "", limit: int = 200) -> dict[str, Any]:
    return _list("checklists", status=status, limit=limit)


def list_reviews(status: str = "", limit: int = 200) -> dict[str, Any]:
    return _list("reviews", status=status, limit=limit)


def list_rules(status: str = "", limit: int = 200) -> dict[str, Any]:
    return _list("rules", status=status, limit=limit)


def list_near_misses(status: str = "", limit: int = 200) -> dict[str, Any]:
    return _list("near_misses", status=status, limit=limit)


def list_mistake_patterns(status: str = "", limit: int = 200) -> dict[str, Any]:
    return _list("mistake_patterns", status=status, limit=limit)


def _common(payload: dict[str, Any], *, prefix: str, collection: str, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    now = _now()
    existing = existing or {}
    return {
        "id": _text(payload.get("id"), existing.get("id") or f"{prefix}_{uuid4().hex[:12]}"),
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "object_type": collection,
        "related_market_id": _text(payload.get("related_market_id", payload.get("market_id", existing.get("related_market_id", "")))),
        "related_thesis_id": _text(payload.get("related_thesis_id", payload.get("thesis_id", existing.get("related_thesis_id", "")))),
        "related_research_id": _text(payload.get("related_research_id", payload.get("research_id", existing.get("related_research_id", "")))),
        "related_evidence_id": _text(payload.get("related_evidence_id", payload.get("evidence_id", existing.get("related_evidence_id", "")))),
        "related_alert_id": _text(payload.get("related_alert_id", payload.get("alert_id", existing.get("related_alert_id", "")))),
        "related_portfolio_id": _text(payload.get("related_portfolio_id", payload.get("portfolio_id", existing.get("related_portfolio_id", "")))),
        "related_trade_ticket_id": _text(payload.get("related_trade_ticket_id", payload.get("ticket_id", existing.get("related_trade_ticket_id", "")))),
        "related_order_id": _text(payload.get("related_order_id", payload.get("order_id", existing.get("related_order_id", "")))),
        "operator_notes": _text(payload.get("operator_notes", payload.get("notes", existing.get("operator_notes", "")))),
        "tags": _tags(payload.get("tags", existing.get("tags", []))),
        "audit_metadata": {"source": "live_governance_v2_8", "secret_values_returned": False},
        "secret_values_returned": False,
    }


def create_journal_entry(payload: dict[str, Any]) -> dict[str, Any]:
    item = _common(payload, prefix="journal", collection="journal")
    item.update({
        "decision_title": _text(payload.get("decision_title", payload.get("title", "Decision journal entry"))),
        "decision_type": _safe_choice(payload.get("decision_type", "other"), DECISION_TYPES, "other"),
        "decision_summary": _text(payload.get("decision_summary", payload.get("summary", ""))),
        "reasoning": _text(payload.get("reasoning", "")),
        "confidence_level": _number(payload.get("confidence_level", 0), 0, minimum=0, maximum=100),
        "expected_outcome": _text(payload.get("expected_outcome", "")),
        "risk_considered": _text(payload.get("risk_considered", "")),
        "alternative_considered": _text(payload.get("alternative_considered", "")),
        "rule_checklist_status": _text(payload.get("rule_checklist_status", payload.get("checklist_status", "not_linked"))),
        "emotional_operational_state": _text(payload.get("emotional_operational_state", "")),
        "follow_up_date": _text(payload.get("follow_up_date", "")),
        "status": _safe_choice(payload.get("status", "draft"), {"draft", "active", "reviewed", "closed", "archived"}, "draft"),
    })
    item = redact_data(item)
    event = _append_event("journal_entry_created", "journal", item)
    return _receipt(item, event)


def update_journal_entry(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_governance_item("journal", item_id)
    if not existing:
        return _not_found(item_id)
    merged = {**existing, **payload, "id": item_id}
    item = create_journal_entry(merged)["item"]
    event = _append_event("journal_entry_edited", "journal", item)
    return _receipt(item, event)


def _checklist_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        rows = value
    else:
        rows = [{"key": key, "label": key.replace("_", " ").title(), "checked": False} for key in DEFAULT_PRETRADE_ITEMS]
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            key = _text(row.get("key", row.get("label", "check")), "check")
            normalized.append({"key": key, "label": _text(row.get("label"), key.replace("_", " ").title()), "checked": _bool(row.get("checked"), False), "notes": _text(row.get("notes", ""))})
        else:
            key = _text(row, "check")
            normalized.append({"key": key, "label": key.replace("_", " ").title(), "checked": False, "notes": ""})
    return normalized


def create_checklist(payload: dict[str, Any]) -> dict[str, Any]:
    item = _common(payload, prefix="checklist", collection="checklists")
    checks = _checklist_items(payload.get("checks", payload.get("items")))
    completed_count = sum(1 for row in checks if row.get("checked"))
    item.update({
        "checklist_title": _text(payload.get("checklist_title", payload.get("title", "Pre-trade governance checklist"))),
        "checklist_type": _safe_choice(payload.get("checklist_type", "pre_trade"), {"pre_trade", "post_trade", "daily", "weekly", "manual"}, "pre_trade"),
        "checks": checks,
        "completed_count": completed_count,
        "total_count": len(checks),
        "completion_ratio": round(completed_count / len(checks), 4) if checks else 0.0,
        "no_trade_alternative_considered": _bool(payload.get("no_trade_alternative_considered"), False),
        "status": _safe_choice(payload.get("status", "draft"), CHECKLIST_STATUSES, "draft"),
        "completed_at": _text(payload.get("completed_at", "")),
    })
    if item["completed_count"] == item["total_count"] and item["total_count"] > 0 and payload.get("status") is None:
        item["status"] = "completed"
        item["completed_at"] = item["completed_at"] or _now()
    item = redact_data(item)
    event = _append_event("pre_trade_checklist_created", "checklists", item)
    return _receipt(item, event)


def update_checklist(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_governance_item("checklists", item_id)
    if not existing:
        return _not_found(item_id)
    merged = {**existing, **payload, "id": item_id}
    item = create_checklist(merged)["item"]
    action = "pre_trade_checklist_completed" if item.get("status") == "completed" else "pre_trade_checklist_updated"
    event = _append_event(action, "checklists", item)
    return _receipt(item, event)


def create_review(payload: dict[str, Any]) -> dict[str, Any]:
    review_type = _safe_choice(payload.get("review_type", payload.get("type", "post_trade")), REVIEW_TYPES, "post_trade")
    item = _common(payload, prefix=f"{review_type}_review", collection="reviews")
    item.update({
        "review_title": _text(payload.get("review_title", payload.get("title", f"{review_type.replace('_', ' ').title()} review"))),
        "review_type": review_type,
        "original_decision_journal_id": _text(payload.get("original_decision_journal_id", payload.get("journal_id", ""))),
        "expected_outcome": _text(payload.get("expected_outcome", "")),
        "actual_outcome": _text(payload.get("actual_outcome", "unknown"), "unknown"),
        "fill_cancel_status": _text(payload.get("fill_cancel_status", "unknown"), "unknown"),
        "thesis_quality": _number(payload.get("thesis_quality", 0), 0, minimum=0, maximum=10),
        "evidence_quality": _number(payload.get("evidence_quality", 0), 0, minimum=0, maximum=10),
        "execution_quality": _number(payload.get("execution_quality", 0), 0, minimum=0, maximum=10),
        "risk_management_quality": _number(payload.get("risk_management_quality", 0), 0, minimum=0, maximum=10),
        "rules_followed": _bool(payload.get("rules_followed"), False),
        "what_went_right": _text(payload.get("what_went_right", "")),
        "what_went_wrong": _text(payload.get("what_went_wrong", "")),
        "lesson_learned": _text(payload.get("lesson_learned", "")),
        "follow_up_action": _text(payload.get("follow_up_action", payload.get("next_actions", ""))),
        "decisions_made": _text(payload.get("decisions_made", "")),
        "theses_updated": _text(payload.get("theses_updated", "")),
        "evidence_added": _text(payload.get("evidence_added", "")),
        "alerts_triggered": _text(payload.get("alerts_triggered", "")),
        "portfolio_warnings": _text(payload.get("portfolio_warnings", "")),
        "risk_blocks": _text(payload.get("risk_blocks", "")),
        "recurring_patterns": _text(payload.get("recurring_patterns", "")),
        "next_focus": _text(payload.get("next_focus", "")),
        "status": _safe_choice(payload.get("status", "draft"), {"draft", "completed", "archived"}, "draft"),
    })
    item = redact_data(item)
    action = f"{review_type}_review_created" if review_type in {"post_trade", "daily", "weekly"} else "review_created"
    event = _append_event(action, "reviews", item)
    return _receipt(item, event)


def update_review(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_governance_item("reviews", item_id)
    if not existing:
        return _not_found(item_id)
    merged = {**existing, **payload, "id": item_id}
    item = create_review(merged)["item"]
    event = _append_event("post_trade_review_completed" if item.get("review_type") == "post_trade" and item.get("status") == "completed" else "review_updated", "reviews", item)
    return _receipt(item, event)


def create_rule(payload: dict[str, Any]) -> dict[str, Any]:
    item = _common(payload, prefix="governance_rule", collection="rules")
    item.update({
        "rule_title": _text(payload.get("rule_title", payload.get("title", "Governance rule"))),
        "rule_description": _text(payload.get("rule_description", payload.get("description", ""))),
        "category": _safe_choice(payload.get("category", "process"), {"process", "risk", "research", "portfolio", "monitoring", "emergency", "execution", "other"}, "process"),
        "severity": _safe_choice(payload.get("severity", "watch"), SEVERITIES, "watch"),
        "enabled": _bool(payload.get("enabled"), True),
        "related_checklist_item": _text(payload.get("related_checklist_item", "")),
        "status": _safe_choice(payload.get("status", "enabled"), {"enabled", "disabled", "archived"}, "enabled"),
    })
    item = redact_data(item)
    event = _append_event("governance_rule_created", "rules", item)
    return _receipt(item, event)


def update_rule(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_governance_item("rules", item_id)
    if not existing:
        return _not_found(item_id)
    merged = {**existing, **payload, "id": item_id}
    item = create_rule(merged)["item"]
    event = _append_event("governance_rule_edited", "rules", item)
    return _receipt(item, event)


def create_near_miss(payload: dict[str, Any]) -> dict[str, Any]:
    item = _common(payload, prefix="near_miss", collection="near_misses")
    item.update({
        "title": _text(payload.get("title", "Rule violation / near-miss")),
        "related_rule_id": _text(payload.get("related_rule_id", payload.get("rule_id", ""))),
        "what_happened": _text(payload.get("what_happened", payload.get("summary", ""))),
        "severity": _safe_choice(payload.get("severity", "watch"), SEVERITIES, "watch"),
        "money_was_at_risk": _bool(payload.get("money_was_at_risk"), False),
        "live_execution_occurred": _bool(payload.get("live_execution_occurred"), False),
        "corrective_action": _text(payload.get("corrective_action", "")),
        "status": _safe_choice(payload.get("status", "open"), {"open", "reviewed", "resolved", "archived"}, "open"),
    })
    item = redact_data(item)
    action = "rule_violation_created" if item.get("live_execution_occurred") else "near_miss_created"
    event = _append_event(action, "near_misses", item)
    return _receipt(item, event)


def create_mistake_pattern(payload: dict[str, Any]) -> dict[str, Any]:
    item = _common(payload, prefix="mistake_pattern", collection="mistake_patterns")
    item.update({
        "pattern_title": _text(payload.get("pattern_title", payload.get("title", "Mistake pattern"))),
        "pattern_type": _safe_choice(payload.get("pattern_type", "other"), {
            "entered_thesis_too_early", "ignored_counter_evidence", "relied_on_stale_evidence",
            "violated_exposure_limit", "over_concentrated", "missing_exit_criteria",
            "missing_invalidation_criteria", "ignored_monitoring_alert", "insufficient_evidence",
            "emotional_impulsive_decision", "unclear_reasoning", "other",
        }, "other"),
        "frequency": int(_number(payload.get("frequency", 1), 1, minimum=0)),
        "process_improvement_action": _text(payload.get("process_improvement_action", payload.get("corrective_action", ""))),
        "status": _safe_choice(payload.get("status", "active"), {"active", "resolved", "archived"}, "active"),
    })
    item = redact_data(item)
    event = _append_event("mistake_pattern_created", "mistake_patterns", item)
    return _receipt(item, event)


def update_mistake_pattern(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_governance_item("mistake_patterns", item_id)
    if not existing:
        return _not_found(item_id)
    merged = {**existing, **payload, "id": item_id}
    item = create_mistake_pattern(merged)["item"]
    event = _append_event("mistake_pattern_updated", "mistake_patterns", item)
    return _receipt(item, event)


def _not_found(item_id: str) -> dict[str, Any]:
    return {"ok": False, "status": "not_found", "item_id": item_id, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "live_trading_armed": False, "secret_values_returned": False}


def _receipt(item: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "item": redact_data(item), "event": event, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "live_trading_armed": False, "secret_values_returned": False}


def governance_summary() -> dict[str, Any]:
    journal = _latest("journal")
    checklists = _latest("checklists")
    reviews = _latest("reviews")
    rules = _latest("rules")
    near_misses = _latest("near_misses")
    patterns = _latest("mistake_patterns")
    unresolved_checks = sum(1 for item in checklists if item.get("status") not in {"completed", "archived"})
    open_near_misses = sum(1 for item in near_misses if item.get("status") in {"open", "reviewed"})
    active_patterns = sum(1 for item in patterns if item.get("status") == "active")
    critical_rules = sum(1 for item in rules if item.get("severity") == "critical" and item.get("status") == "enabled")
    return {
        "journal_entries": len(journal),
        "active_decisions": sum(1 for item in journal if item.get("status") in {"active", "draft"}),
        "checklists": len(checklists),
        "unresolved_checklists": unresolved_checks,
        "post_trade_reviews": sum(1 for item in reviews if item.get("review_type") == "post_trade"),
        "daily_reviews": sum(1 for item in reviews if item.get("review_type") == "daily"),
        "weekly_reviews": sum(1 for item in reviews if item.get("review_type") == "weekly"),
        "rules": len(rules),
        "critical_rules": critical_rules,
        "near_misses": len(near_misses),
        "open_near_misses": open_near_misses,
        "mistake_patterns": len(patterns),
        "active_mistake_patterns": active_patterns,
        "next_action": "Complete a pre-trade checklist before drafting or submitting any serious ticket." if unresolved_checks else "Create a decision journal entry or daily review to keep the operator process accountable.",
    }


def build_governance_workspace(limit: int = 50) -> dict[str, Any]:
    return redact_data({
        "version": APP_VERSION,
        "generated_at": _now(),
        "summary": governance_summary(),
        "journal": list_journal(limit=limit)["items"],
        "checklists": list_checklists(limit=limit)["items"],
        "reviews": list_reviews(limit=limit)["items"],
        "rules": list_rules(limit=limit)["items"],
        "near_misses": list_near_misses(limit=limit)["items"],
        "mistake_patterns": list_mistake_patterns(limit=limit)["items"],
        "recent_events": list_governance_events(limit=limit),
        "safety_statement": "Governance records, checklists, reviews, and mistake-pattern tracking never place orders, cancel orders, arm live trading, or bypass backend gates.",
        "secret_values_returned": False,
    })


def governance_export_json() -> dict[str, Any]:
    workspace = build_governance_workspace(limit=1000)
    workspace["export_type"] = "governance_json"
    workspace["order_submitted"] = False
    workspace["order_cancelled"] = False
    workspace["live_trading_armed"] = False
    return redact_data(workspace)


def governance_export_markdown() -> str:
    data = governance_export_json()
    summary = data.get("summary", {})
    lines = [
        f"# Governance / Decision Journal Export — {APP_VERSION}",
        "",
        f"Generated: {data.get('generated_at')}",
        "",
        data.get("safety_statement", "Governance exports do not place or cancel orders."),
        "",
        "## Summary",
        "",
        f"- Decision journal entries: {summary.get('journal_entries', 0)}",
        f"- Checklists: {summary.get('checklists', 0)}",
        f"- Post-trade reviews: {summary.get('post_trade_reviews', 0)}",
        f"- Daily reviews: {summary.get('daily_reviews', 0)}",
        f"- Weekly reviews: {summary.get('weekly_reviews', 0)}",
        f"- Governance rules: {summary.get('rules', 0)}",
        f"- Near-misses / rule violations: {summary.get('near_misses', 0)}",
        f"- Active mistake patterns: {summary.get('active_mistake_patterns', 0)}",
        "",
        "## Decision Journal",
        "",
    ]
    for item in data.get("journal", [])[:100]:
        lines.append(f"- **{item.get('decision_title', item.get('id'))}** — {item.get('decision_type')} · {item.get('status')} · confidence {item.get('confidence_level')}")
    lines += ["", "## Checklists", ""]
    for item in data.get("checklists", [])[:100]:
        lines.append(f"- **{item.get('checklist_title', item.get('id'))}** — {item.get('status')} · {item.get('completed_count')}/{item.get('total_count')} complete")
    lines += ["", "## Reviews", ""]
    for item in data.get("reviews", [])[:100]:
        lines.append(f"- **{item.get('review_title', item.get('id'))}** — {item.get('review_type')} · {item.get('status')} · lesson: {item.get('lesson_learned', '')}")
    lines += ["", "## Mistake Patterns", ""]
    for item in data.get("mistake_patterns", [])[:100]:
        lines.append(f"- **{item.get('pattern_title', item.get('id'))}** — {item.get('pattern_type')} · frequency {item.get('frequency')} · {item.get('status')}")
    lines += ["", "## Near-Misses / Rule Violations", ""]
    for item in data.get("near_misses", [])[:100]:
        lines.append(f"- **{item.get('title', item.get('id'))}** — {item.get('severity')} · {item.get('status')} · live execution: {item.get('live_execution_occurred')}")
    return redact_text("\n".join(lines))


def governance_csv(collection: str) -> str:
    mapping = {
        "journal": list_journal(limit=1000)["items"],
        "checklists": list_checklists(limit=1000)["items"],
        "mistakes": list_mistake_patterns(limit=1000)["items"],
        "near-misses": list_near_misses(limit=1000)["items"],
        "rules": list_rules(limit=1000)["items"],
        "reviews": list_reviews(limit=1000)["items"],
    }
    rows = mapping.get(collection)
    if rows is None:
        raise ValueError(f"Unsupported governance CSV collection: {collection}")
    output = io.StringIO()
    fieldnames = sorted({key for row in rows for key in row.keys()} | {"id", "created_at", "updated_at", "status"})
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in redact_data(row).items()})
    return output.getvalue()
