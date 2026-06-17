from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_v2 import list_audit_records, record_audit, redact_data, redact_text
from .live_strategy import list_evidence, list_theses, list_watchlist
from .live_research import freshness_summary
from .live_monitoring import list_alerts

PORTFOLIO_DIR = DATA_DIR / "live_v2" / "portfolio"
PORTFOLIO_EVENTS_PATH = PORTFOLIO_DIR / "portfolio_events.jsonl"

COLLECTIONS = {"snapshots", "bankroll", "scenarios", "warnings", "planned_impacts", "exposure_groups"}
SCENARIO_TYPES = {
    "market_resolves_yes",
    "market_resolves_no",
    "thesis_succeeds",
    "thesis_fails",
    "linked_markets_move_against_thesis",
    "planned_ticket_fills_fully",
    "planned_ticket_partially_fills",
    "open_orders_cancelled",
    "stale_evidence_invalidates_thesis",
    "liquidity_disappears",
    "manual",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
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


def _tags(value: Any) -> list[str]:
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or "").split(",")
    return sorted({redact_text(item).strip() for item in raw if redact_text(item).strip()})


def _safe_choice(value: Any, allowed: set[str], default: str) -> str:
    candidate = _text(value, default).lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    return candidate if candidate in allowed else default


def _event(action: str, collection: str, item: dict[str, Any]) -> dict[str, Any]:
    return redact_data({
        "event_id": f"portfolio_evt_{uuid4().hex[:12]}",
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
        raise ValueError(f"Unsupported portfolio collection: {collection}")
    _ensure_dir()
    event = _event(action, collection, item)
    with PORTFOLIO_EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
    record_audit(
        f"portfolio_{action}",
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
    if not PORTFOLIO_EVENTS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in PORTFOLIO_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(redact_data(json.loads(line)))
        except json.JSONDecodeError:
            continue
    return rows


def list_portfolio_events(limit: int = 500) -> list[dict[str, Any]]:
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


def get_portfolio_item(collection: str, item_id: str) -> dict[str, Any] | None:
    for item in _latest(collection):
        if item.get("id") == item_id:
            return item
    return None


def _default_bankroll() -> dict[str, Any]:
    return redact_data({
        "id": "bankroll_default",
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "total_bankroll": 0.0,
        "live_trading_bankroll": 0.0,
        "paper_bankroll": 0.0,
        "max_portfolio_exposure": 0.0,
        "max_per_market_exposure": 0.0,
        "max_per_thesis_exposure": 0.0,
        "max_per_tag_exposure": 0.0,
        "max_daily_notional": 0.0,
        "max_daily_loss": 0.0,
        "reserve_cash": 0.0,
        "operator_notes": "Default zero-value bankroll configuration. Set explicit local limits before using concentration warnings.",
        "tags": [],
        "audit_metadata": {"source": "live_portfolio_v2_7", "secret_values_returned": False},
        "secret_values_returned": False,
    })


def get_bankroll_settings() -> dict[str, Any]:
    items = _latest("bankroll")
    return items[0] if items else _default_bankroll()


def update_bankroll(payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_bankroll_settings()
    now = _now()
    item = {
        "id": "bankroll_current",
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "total_bankroll": _number(payload.get("total_bankroll", existing.get("total_bankroll", 0)), 0, minimum=0),
        "live_trading_bankroll": _number(payload.get("live_trading_bankroll", existing.get("live_trading_bankroll", 0)), 0, minimum=0),
        "paper_bankroll": _number(payload.get("paper_bankroll", existing.get("paper_bankroll", 0)), 0, minimum=0),
        "max_portfolio_exposure": _number(payload.get("max_portfolio_exposure", existing.get("max_portfolio_exposure", 0)), 0, minimum=0),
        "max_per_market_exposure": _number(payload.get("max_per_market_exposure", existing.get("max_per_market_exposure", 0)), 0, minimum=0),
        "max_per_thesis_exposure": _number(payload.get("max_per_thesis_exposure", existing.get("max_per_thesis_exposure", 0)), 0, minimum=0),
        "max_per_tag_exposure": _number(payload.get("max_per_tag_exposure", existing.get("max_per_tag_exposure", 0)), 0, minimum=0),
        "max_daily_notional": _number(payload.get("max_daily_notional", existing.get("max_daily_notional", 0)), 0, minimum=0),
        "max_daily_loss": _number(payload.get("max_daily_loss", existing.get("max_daily_loss", 0)), 0, minimum=0),
        "reserve_cash": _number(payload.get("reserve_cash", existing.get("reserve_cash", 0)), 0, minimum=0),
        "operator_notes": redact_text(payload.get("operator_notes", payload.get("notes", existing.get("operator_notes", "")))),
        "tags": _tags(payload.get("tags", existing.get("tags", []))),
        "audit_metadata": {"source": "live_portfolio_v2_7", "secret_values_returned": False},
        "secret_values_returned": False,
    }
    event = _append_event("bankroll_setting_updated", "bankroll", redact_data(item))
    return {"ok": True, "item": redact_data(item), "event": event, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}


def create_exposure_group(payload: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    item = redact_data({
        "id": _text(payload.get("id"), f"exposure_group_{uuid4().hex[:12]}"),
        "created_at": now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "group_name": redact_text(payload.get("group_name", payload.get("title", "Manual exposure group"))),
        "related_market_id": redact_text(payload.get("related_market_id", payload.get("market_id", ""))),
        "related_thesis_id": redact_text(payload.get("related_thesis_id", payload.get("thesis_id", ""))),
        "related_watchlist_id": redact_text(payload.get("related_watchlist_id", payload.get("watchlist_id", ""))),
        "strategy_tag": redact_text(payload.get("strategy_tag", payload.get("tag", ""))),
        "exposure_type": redact_text(payload.get("exposure_type", "operator_defined")),
        "notional_estimate": _number(payload.get("notional_estimate", 0), 0, minimum=0),
        "max_loss_estimate": _number(payload.get("max_loss_estimate", payload.get("notional_estimate", 0)), 0, minimum=0),
        "status": _safe_choice(payload.get("status", "active"), {"active", "watch", "archived"}, "active"),
        "operator_notes": redact_text(payload.get("operator_notes", payload.get("notes", ""))),
        "tags": _tags(payload.get("tags", [])),
        "source": "operator_defined",
        "audit_metadata": {"source": "live_portfolio_v2_7", "secret_values_returned": False},
        "secret_values_returned": False,
    })
    event = _append_event("exposure_group_created", "exposure_groups", item)
    return {"ok": True, "item": item, "event": event, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}


def update_exposure_group(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_portfolio_item("exposure_groups", item_id)
    if not existing:
        return {"ok": False, "status": "not_found", "item_id": item_id, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}
    merged = {**existing, **payload, "id": item_id, "created_at": existing.get("created_at")}
    item = create_exposure_group(merged)["item"]
    item["id"] = item_id
    item["created_at"] = existing.get("created_at")
    item["updated_at"] = _now()
    event = _append_event("exposure_group_updated", "exposure_groups", item)
    return {"ok": True, "item": item, "event": event, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}


def _audit_exposures(limit: int = 500) -> list[dict[str, Any]]:
    records = []
    for row in list_audit_records(limit=limit):
        notional = _number(row.get("notional"), 0, minimum=0)
        if notional <= 0:
            continue
        records.append(redact_data({
            "id": f"audit_{row.get('timestamp', '')}_{row.get('action', '')}".replace(":", "").replace(".", ""),
            "created_at": row.get("timestamp", ""),
            "updated_at": row.get("timestamp", ""),
            "app_version": APP_VERSION,
            "related_market_id": row.get("market_id", ""),
            "related_thesis_id": "",
            "related_watchlist_id": "",
            "related_trade_ticket": row.get("order_id", ""),
            "strategy_tag": row.get("mode", ""),
            "exposure_type": f"locally_audited_{row.get('action', 'unknown')}",
            "notional_estimate": notional,
            "max_loss_estimate": notional,
            "current_status": row.get("status", "unknown"),
            "source": "local_audit_ledger",
            "notes": "Derived from local Live v2 audit ledger. This may include previews and must not be treated as confirmed live exposure.",
            "tags": [row.get("mode", "")],
            "unknown_fields": [],
            "secret_values_returned": False,
        }))
    return records


def calculate_exposure_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for thesis in list_theses(limit=1000).get("items", []):
        exposure = _number(thesis.get("maximum_acceptable_exposure"), 0, minimum=0)
        if exposure > 0:
            records.append(redact_data({
                "id": f"thesis_{thesis.get('id')}",
                "created_at": thesis.get("created_at", ""),
                "updated_at": thesis.get("updated_at", ""),
                "app_version": APP_VERSION,
                "related_market_id": thesis.get("market_id", ""),
                "related_thesis_id": thesis.get("id", ""),
                "related_watchlist_id": "",
                "related_trade_ticket": "",
                "strategy_tag": ",".join(thesis.get("tags", [])),
                "exposure_type": "thesis_max_acceptable_exposure",
                "notional_estimate": exposure,
                "max_loss_estimate": exposure,
                "current_status": thesis.get("status", "unknown"),
                "source": "strategy_thesis",
                "market_title": thesis.get("market_title", ""),
                "outcome": thesis.get("outcome", ""),
                "notes": "Operator-defined maximum acceptable exposure from the linked thesis.",
                "tags": thesis.get("tags", []),
                "unknown_fields": [],
                "secret_values_returned": False,
            }))
    for item in list_watchlist(limit=1000).get("items", []):
        records.append(redact_data({
            "id": f"watchlist_{item.get('id')}",
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "app_version": APP_VERSION,
            "related_market_id": item.get("market_id", ""),
            "related_thesis_id": item.get("thesis_id", ""),
            "related_watchlist_id": item.get("id", ""),
            "related_trade_ticket": "",
            "strategy_tag": ",".join(item.get("tags", [])),
            "exposure_type": "watchlist_planned_interest_unknown_size",
            "notional_estimate": 0.0,
            "max_loss_estimate": 0.0,
            "current_status": item.get("status", "unknown"),
            "source": "strategy_watchlist",
            "market_title": item.get("market_title", ""),
            "outcome": item.get("outcome", ""),
            "notes": "Watchlist target has no position size by default; exposure remains unknown/unavailable until a ticket or thesis limit is defined.",
            "tags": item.get("tags", []),
            "unknown_fields": ["position_size", "confirmed_live_exposure"],
            "secret_values_returned": False,
        }))
    records.extend(_audit_exposures())
    for item in _latest("exposure_groups"):
        if item.get("status") != "archived":
            records.append(redact_data({
                "id": item.get("id", ""),
                "created_at": item.get("created_at", ""),
                "updated_at": item.get("updated_at", ""),
                "app_version": APP_VERSION,
                "related_market_id": item.get("related_market_id", ""),
                "related_thesis_id": item.get("related_thesis_id", ""),
                "related_watchlist_id": item.get("related_watchlist_id", ""),
                "related_trade_ticket": "",
                "strategy_tag": item.get("strategy_tag", ""),
                "exposure_type": item.get("exposure_type", "operator_defined"),
                "notional_estimate": _number(item.get("notional_estimate"), 0, minimum=0),
                "max_loss_estimate": _number(item.get("max_loss_estimate"), 0, minimum=0),
                "current_status": item.get("status", "active"),
                "source": item.get("source", "operator_defined"),
                "market_title": "",
                "outcome": "",
                "notes": item.get("operator_notes", ""),
                "tags": item.get("tags", []),
                "unknown_fields": [],
                "secret_values_returned": False,
            }))
    return sorted(records, key=lambda row: row.get("updated_at", row.get("created_at", "")), reverse=True)


def _sum_by(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for row in records:
        key = _text(row.get(field), "unlinked") or "unlinked"
        if key not in groups:
            groups[key] = {"key": key, "notional_estimate": 0.0, "max_loss_estimate": 0.0, "count": 0, "unknown_count": 0}
        groups[key]["notional_estimate"] += _number(row.get("notional_estimate"), 0, minimum=0)
        groups[key]["max_loss_estimate"] += _number(row.get("max_loss_estimate"), 0, minimum=0)
        groups[key]["count"] += 1
        if row.get("unknown_fields"):
            groups[key]["unknown_count"] += 1
    return sorted(groups.values(), key=lambda row: row.get("notional_estimate", 0), reverse=True)


def concentration_warnings(records: list[dict[str, Any]] | None = None, bankroll: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    records = records if records is not None else calculate_exposure_records()
    bankroll = bankroll or get_bankroll_settings()
    warnings: list[dict[str, Any]] = []
    total = sum(_number(row.get("notional_estimate"), 0, minimum=0) for row in records)
    limits = {
        "portfolio": _number(bankroll.get("max_portfolio_exposure"), 0, minimum=0),
        "market": _number(bankroll.get("max_per_market_exposure"), 0, minimum=0),
        "thesis": _number(bankroll.get("max_per_thesis_exposure"), 0, minimum=0),
        "tag": _number(bankroll.get("max_per_tag_exposure"), 0, minimum=0),
    }
    if limits["portfolio"] and total > limits["portfolio"]:
        warnings.append(_warning("portfolio_limit_exceeded", "critical", "Total exposure exceeds configured portfolio exposure limit.", total, limits["portfolio"]))
    for field, limit_key, label in [("related_market_id", "market", "market"), ("related_thesis_id", "thesis", "thesis"), ("strategy_tag", "tag", "tag/playbook")]:
        limit = limits[limit_key]
        if not limit:
            continue
        for group in _sum_by(records, field):
            if group["key"] != "unlinked" and group["notional_estimate"] > limit:
                warnings.append(_warning(f"{limit_key}_limit_exceeded", "warning", f"One {label} exceeds its configured exposure limit: {group['key']}.", group["notional_estimate"], limit, related_id=group["key"]))
    if any(row.get("unknown_fields") for row in records):
        warnings.append(_warning("unknown_exposure_fields", "watch", "Some records have unknown/unavailable exposure fields. Treat exposure cautiously.", 0, 0))
    fresh = freshness_summary()
    if records and int(fresh.get("stale", 0) or 0) > 0:
        warnings.append(_warning("stale_evidence_with_exposure", "warning", "Stale evidence exists while exposure records are present. Review linked theses before ticketing.", float(fresh.get("stale", 0) or 0), 0))
    alerts = list_alerts(status="active", limit=100).get("items", [])
    if records and alerts:
        warnings.append(_warning("active_alerts_with_exposure", "watch", "Active monitoring alerts exist while exposure records are present.", float(len(alerts)), 0))
    if not records:
        warnings.append(_warning("no_exposure_records", "info", "No local exposure records found. Live/read-only exposure may still be unavailable or unknown.", 0, 0))
    return [redact_data(w) for w in warnings]


def _warning(kind: str, severity: str, message: str, observed: float, limit: float, related_id: str = "") -> dict[str, Any]:
    return {
        "id": f"warning_{kind}_{uuid4().hex[:8]}",
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "warning_type": kind,
        "severity": severity,
        "message": message,
        "observed_value": observed,
        "limit_value": limit,
        "related_id": redact_text(related_id),
        "recommended_operator_action": "Review exposure context manually before creating or submitting any ticket.",
        "secret_values_returned": False,
    }


def portfolio_summary(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    records = records if records is not None else calculate_exposure_records()
    total = sum(_number(row.get("notional_estimate"), 0, minimum=0) for row in records)
    max_loss = sum(_number(row.get("max_loss_estimate"), 0, minimum=0) for row in records)
    return redact_data({
        "exposure_records": len(records),
        "total_notional_exposure": round(total, 6),
        "total_max_loss_estimate": round(max_loss, 6),
        "market_groups": len(_sum_by(records, "related_market_id")),
        "thesis_groups": len(_sum_by(records, "related_thesis_id")),
        "tag_groups": len(_sum_by(records, "strategy_tag")),
        "unknown_exposure_records": len([row for row in records if row.get("unknown_fields")]),
        "live_exposure_state": "unknown_unavailable_without_read_only_account_data",
        "paper_exposure_state": "local_audit_if_present",
        "planned_exposure_state": "preview_only_until_ticket_is_submitted",
        "secret_values_returned": False,
    })


def generate_portfolio_snapshot(record: bool = True) -> dict[str, Any]:
    records = calculate_exposure_records()
    bankroll = get_bankroll_settings()
    warnings = concentration_warnings(records, bankroll)
    item = redact_data({
        "id": f"snapshot_{uuid4().hex[:12]}",
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "summary": portfolio_summary(records),
        "bankroll": bankroll,
        "exposure_records": records,
        "exposure_by_market": _sum_by(records, "related_market_id"),
        "exposure_by_thesis": _sum_by(records, "related_thesis_id"),
        "exposure_by_tag": _sum_by(records, "strategy_tag"),
        "warnings": warnings,
        "unknown_unavailable_notes": [
            "Actual live exposure requires safe read-only account data and may be unknown.",
            "Watchlist records without size are tracked as unknown/unavailable exposure.",
        ],
        "safety_statement": "Portfolio intelligence does not approve, place, sign, arm, or cancel orders.",
        "secret_values_returned": False,
    })
    event = _append_event("portfolio_snapshot_generated", "snapshots", item) if record else None
    return {"ok": True, "snapshot": item, "event": event, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}


def list_exposure(limit: int = 500) -> dict[str, Any]:
    items = calculate_exposure_records()[: max(1, min(int(limit or 500), 5000))]
    return {"items": items, "count": len(items), "summary": portfolio_summary(items), "secret_values_returned": False}


def list_warnings(limit: int = 500) -> dict[str, Any]:
    records = calculate_exposure_records()
    items = concentration_warnings(records, get_bankroll_settings())[: max(1, min(int(limit or 500), 5000))]
    return {"items": items, "count": len(items), "secret_values_returned": False}


def _normalize_scenario(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    now = _now()
    return redact_data({
        "id": _text(payload.get("id"), existing.get("id") or f"scenario_{uuid4().hex[:12]}"),
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "scenario_name": redact_text(payload.get("scenario_name", payload.get("title", existing.get("scenario_name", "Manual scenario")))),
        "scenario_type": _safe_choice(payload.get("scenario_type", existing.get("scenario_type", "manual")), SCENARIO_TYPES, "manual"),
        "related_market_id": redact_text(payload.get("related_market_id", payload.get("market_id", existing.get("related_market_id", "")))),
        "related_thesis_id": redact_text(payload.get("related_thesis_id", payload.get("thesis_id", existing.get("related_thesis_id", "")))),
        "planned_notional": _number(payload.get("planned_notional", existing.get("planned_notional", 0)), 0, minimum=0),
        "assumed_fill_fraction": _number(payload.get("assumed_fill_fraction", existing.get("assumed_fill_fraction", 1)), 1, minimum=0, maximum=1),
        "operator_notes": redact_text(payload.get("operator_notes", payload.get("notes", existing.get("operator_notes", "")))),
        "tags": _tags(payload.get("tags", existing.get("tags", []))),
        "status": _safe_choice(payload.get("status", existing.get("status", "draft")), {"draft", "evaluated", "archived"}, "draft"),
        "audit_metadata": {"source": "live_portfolio_v2_7", "secret_values_returned": False},
        "secret_values_returned": False,
    })


def create_scenario(payload: dict[str, Any]) -> dict[str, Any]:
    item = _normalize_scenario(payload)
    event = _append_event("scenario_created", "scenarios", item)
    return {"ok": True, "item": item, "event": event, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}


def list_scenarios(limit: int = 200) -> dict[str, Any]:
    items = _latest("scenarios")[: max(1, min(int(limit or 200), 5000))]
    return {"items": items, "count": len(items), "secret_values_returned": False}


def evaluate_scenario(item_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    scenario = get_portfolio_item("scenarios", item_id)
    if not scenario:
        return {"ok": False, "status": "not_found", "item_id": item_id, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}
    payload = payload or {}
    records = calculate_exposure_records()
    if scenario.get("related_market_id"):
        affected = [row for row in records if row.get("related_market_id") == scenario.get("related_market_id")]
    elif scenario.get("related_thesis_id"):
        affected = [row for row in records if row.get("related_thesis_id") == scenario.get("related_thesis_id")]
    else:
        affected = records
    affected_notional = sum(_number(row.get("notional_estimate"), 0, minimum=0) for row in affected)
    planned = _number(payload.get("planned_notional", scenario.get("planned_notional", 0)), 0, minimum=0) * _number(payload.get("assumed_fill_fraction", scenario.get("assumed_fill_fraction", 1)), 1, minimum=0, maximum=1)
    scenario_type = scenario.get("scenario_type", "manual")
    downside_multiplier = -1 if scenario_type in {"market_resolves_no", "thesis_fails", "linked_markets_move_against_thesis", "stale_evidence_invalidates_thesis", "liquidity_disappears"} else 1
    result = redact_data({
        "id": f"scenario_eval_{uuid4().hex[:12]}",
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "scenario_id": item_id,
        "scenario_type": scenario_type,
        "affected_markets": sorted({row.get("related_market_id", "") for row in affected if row.get("related_market_id")}),
        "affected_theses": sorted({row.get("related_thesis_id", "") for row in affected if row.get("related_thesis_id")}),
        "affected_exposure_count": len(affected),
        "estimated_exposure_impact": round((affected_notional + planned) * downside_multiplier, 6),
        "estimated_max_loss_impact": round(affected_notional + planned, 6),
        "unknown_unavailable_values": ["actual live P&L", "live fills"] if affected else ["affected exposure"],
        "related_warnings": concentration_warnings(records, get_bankroll_settings()),
        "recommended_operator_review_action": "Review affected thesis, research freshness, monitoring alerts, and trade ticket gates manually before taking any action.",
        "safety_statement": "Scenario evaluation is read-only workflow guidance and does not submit or cancel orders.",
        "secret_values_returned": False,
    })
    updated = {**scenario, "status": "evaluated", "updated_at": _now(), "last_evaluation": result}
    event = _append_event("scenario_evaluated", "scenarios", updated)
    return {"ok": True, "scenario": updated, "evaluation": result, "event": event, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}


def planned_trade_impact(payload: dict[str, Any]) -> dict[str, Any]:
    price = _number(payload.get("price", payload.get("limit_price", 0)), 0, minimum=0)
    size = _number(payload.get("size", 0), 0, minimum=0)
    planned_notional = _number(payload.get("planned_notional", price * size), price * size, minimum=0)
    records = calculate_exposure_records()
    before = portfolio_summary(records)
    after_records = list(records)
    planned_record = redact_data({
        "id": f"planned_{uuid4().hex[:12]}",
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "related_market_id": redact_text(payload.get("market_id", payload.get("related_market_id", ""))),
        "related_thesis_id": redact_text(payload.get("thesis_id", payload.get("strategy_ref", ""))),
        "related_watchlist_id": redact_text(payload.get("watchlist_id", "")),
        "related_trade_ticket": redact_text(payload.get("ticket_id", "planned_ticket")),
        "strategy_tag": redact_text(payload.get("strategy_tag", payload.get("tag", "planned"))),
        "exposure_type": "planned_trade_preview",
        "notional_estimate": planned_notional,
        "max_loss_estimate": planned_notional,
        "current_status": "planned_preview_only",
        "source": "trade_ticket_preview",
        "market_title": redact_text(payload.get("market_title", "")),
        "outcome": redact_text(payload.get("outcome", "")),
        "notes": "Planned trade impact preview only. No order was submitted.",
        "tags": _tags(payload.get("tags", [])),
        "unknown_fields": [],
        "secret_values_returned": False,
    })
    after_records.append(planned_record)
    after = portfolio_summary(after_records)
    warnings = concentration_warnings(after_records, get_bankroll_settings())
    item = redact_data({
        "id": f"impact_{uuid4().hex[:12]}",
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "planned_record": planned_record,
        "before": before,
        "after": after,
        "warnings": warnings,
        "safety_statement": "Planned trade impact does not submit, sign, approve, arm, or cancel orders. Existing live gates still apply.",
        "secret_values_returned": False,
    })
    event = _append_event("planned_trade_impact_evaluated", "planned_impacts", item)
    return {"ok": True, "impact": item, "event": event, "order_submitted": False, "order_cancelled": False, "network_attempted": False, "secret_values_returned": False}


def build_portfolio_workspace(limit: int = 100) -> dict[str, Any]:
    records = calculate_exposure_records()
    bankroll = get_bankroll_settings()
    warnings = concentration_warnings(records, bankroll)
    summary = portfolio_summary(records)
    next_action = "Set explicit bankroll/risk-budget limits, then generate a portfolio snapshot."
    if records and warnings:
        next_action = "Review concentration warnings before creating or submitting any ticket."
    elif records:
        next_action = "Use planned trade impact before moving a thesis into a ticket."
    return redact_data({
        "version": APP_VERSION,
        "generated_at": _now(),
        "summary": summary,
        "bankroll": bankroll,
        "exposures": records[:limit],
        "exposure_by_market": _sum_by(records, "related_market_id")[:limit],
        "exposure_by_thesis": _sum_by(records, "related_thesis_id")[:limit],
        "exposure_by_tag": _sum_by(records, "strategy_tag")[:limit],
        "warnings": warnings[:limit],
        "scenarios": _latest("scenarios")[:limit],
        "recent_events": list_portfolio_events(limit=25),
        "next_action": next_action,
        "safety_statement": "Portfolio intelligence is workflow guidance only. It never places, cancels, signs, approves, or arms orders.",
        "secret_values_returned": False,
    })


def portfolio_export_json() -> dict[str, Any]:
    workspace = build_portfolio_workspace(limit=10000)
    return redact_data({**workspace, "exported_at": _now(), "export_format": "json"})


def portfolio_export_markdown() -> str:
    data = portfolio_export_json()
    lines = [
        f"# Portfolio / Exposure Export — {APP_VERSION}",
        "",
        f"Generated: {data['generated_at']}",
        "",
        "Portfolio intelligence does not approve, place, sign, arm, or cancel orders. Exposure guidance is workflow guidance only, not financial advice.",
        "",
        "## Summary",
        f"- Exposure records: {data['summary']['exposure_records']}",
        f"- Total notional exposure estimate: {data['summary']['total_notional_exposure']}",
        f"- Total max loss estimate: {data['summary']['total_max_loss_estimate']}",
        f"- Unknown exposure records: {data['summary']['unknown_exposure_records']}",
        "",
        "## Bankroll / Risk Budget",
    ]
    bankroll = data.get("bankroll", {})
    for key in ["total_bankroll", "live_trading_bankroll", "paper_bankroll", "max_portfolio_exposure", "max_per_market_exposure", "max_per_thesis_exposure", "max_per_tag_exposure", "reserve_cash"]:
        lines.append(f"- {key}: {bankroll.get(key, 0)}")
    lines += ["", "## Concentration Warnings"]
    for warning in data.get("warnings", [])[:100]:
        lines.append(f"- **{warning.get('severity', 'info')}** {warning.get('message', '')}")
    if not data.get("warnings"):
        lines.append("- None recorded.")
    lines += ["", "## Exposure Records"]
    for item in data.get("exposures", [])[:100]:
        lines.append(f"- {item.get('exposure_type')} · market={item.get('related_market_id') or 'unlinked'} · thesis={item.get('related_thesis_id') or 'unlinked'} · notional={item.get('notional_estimate')}")
    return "\n".join(lines) + "\n"


def _csv_for(items: list[dict[str, Any]], fields: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in item.items()})
    return output.getvalue()


def portfolio_csv(collection: str) -> str:
    if collection == "exposure":
        fields = ["id", "exposure_type", "related_market_id", "related_thesis_id", "strategy_tag", "notional_estimate", "max_loss_estimate", "source", "current_status"]
        return _csv_for(calculate_exposure_records(), fields)
    if collection == "warnings":
        fields = ["id", "warning_type", "severity", "message", "observed_value", "limit_value", "related_id", "recommended_operator_action"]
        return _csv_for(concentration_warnings(calculate_exposure_records(), get_bankroll_settings()), fields)
    if collection == "scenarios":
        fields = ["id", "scenario_name", "scenario_type", "related_market_id", "related_thesis_id", "planned_notional", "status"]
        return _csv_for(_latest("scenarios"), fields)
    return _csv_for([], ["id"])
