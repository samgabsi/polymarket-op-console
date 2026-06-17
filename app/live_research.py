from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_strategy import create_evidence, list_evidence, list_theses
from .live_v2 import record_audit, redact_data, redact_text

RESEARCH_DIR = DATA_DIR / "live_v2" / "research"
RESEARCH_EVENTS_PATH = RESEARCH_DIR / "research_events.jsonl"

COLLECTIONS = {"sources", "queue", "notes", "evidence_candidates", "freshness"}
SOURCE_TYPES = {"news", "official_announcement", "market_page", "data_source", "social_post", "analyst_note", "operator_note", "other"}
SOURCE_STATUSES = {"new", "queued", "reviewed", "converted_to_evidence", "stale", "archived"}
QUEUE_STATUSES = {"queued", "in_review", "reviewed", "converted", "archived"}
NOTE_STATUSES = {"draft", "reviewed", "candidate_created", "archived"}
CANDIDATE_STATUSES = {"candidate", "approved", "converted", "archived"}
FRESHNESS_STATUSES = {"fresh", "aging", "stale", "expired", "unknown"}
EVIDENCE_DIRECTIONS = {"supports", "weakly_supports", "neutral", "weakly_contradicts", "contradicts"}
DESIRED_OUTPUTS = {"evidence_item", "thesis_update", "scorecard_update", "watchlist_update", "post_trade_review_note", "archive_no_action"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today() -> str:
    return _now()[:10]


def _ensure_dir() -> None:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _int(value: Any, default: int = 0, *, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        result = int(float(value))
    except Exception:
        result = default
    if minimum is not None:
        result = max(minimum, result)
    if maximum is not None:
        result = min(maximum, result)
    return result


def _safe_status(value: Any, allowed: set[str], default: str) -> str:
    candidate = _text(value, default).lower().replace(" ", "_").replace("-", "_").replace("/", "_")
    return candidate if candidate in allowed else default


def _tags(value: Any) -> list[str]:
    raw = value if isinstance(value, list) else str(value or "").split(",")
    return sorted({redact_text(item).strip() for item in raw if redact_text(item).strip()})


def _base(payload: dict[str, Any], *, object_type: str, existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    now = _now()
    return {
        "id": _text(payload.get("id"), existing.get("id") or f"{object_type}_{uuid4().hex[:12]}"),
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "app_version": APP_VERSION,
        "title": redact_text(payload.get("title", existing.get("title", f"Untitled {object_type}"))),
        "source_url": redact_text(payload.get("source_url", payload.get("url", existing.get("source_url", "")))),
        "source_type": _safe_status(payload.get("source_type", existing.get("source_type", "other")), SOURCE_TYPES, "other"),
        "market_id": redact_text(payload.get("market_id", existing.get("market_id", ""))),
        "market_slug": redact_text(payload.get("market_slug", existing.get("market_slug", ""))),
        "market_title": redact_text(payload.get("market_title", existing.get("market_title", ""))),
        "related_thesis_id": redact_text(payload.get("related_thesis_id", payload.get("thesis_id", existing.get("related_thesis_id", "")))),
        "related_evidence_id": redact_text(payload.get("related_evidence_id", existing.get("related_evidence_id", ""))),
        "operator_notes": redact_text(payload.get("operator_notes", payload.get("notes", existing.get("operator_notes", "")))),
        "tags": _tags(payload.get("tags", existing.get("tags", []))),
        "audit_metadata": {"source": "live_research_v2_5", "secret_values_returned": False},
        "secret_values_returned": False,
    }


def _event(action: str, collection: str, item: dict[str, Any]) -> dict[str, Any]:
    return redact_data({
        "event_id": f"research_evt_{uuid4().hex[:12]}",
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
        raise ValueError(f"Unsupported research collection: {collection}")
    _ensure_dir()
    event = _event(action, collection, item)
    with RESEARCH_EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
    record_audit(
        f"research_{action}",
        "recorded",
        details={"collection": collection, "item_id": item.get("id", ""), "market_id": item.get("market_id", ""), "secret_values_returned": False},
    )
    return event


def _read_events() -> list[dict[str, Any]]:
    if not RESEARCH_EVENTS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in RESEARCH_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(redact_data(json.loads(line)))
        except json.JSONDecodeError:
            continue
    return rows


def list_research_events(limit: int = 500) -> list[dict[str, Any]]:
    return list(reversed(_read_events()))[: max(1, min(int(limit or 500), 5000))]


def _latest(collection: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in _read_events():
        if event.get("collection") != collection:
            continue
        item = event.get("item") or {}
        if isinstance(item, dict) and item.get("id"):
            latest[str(item["id"])] = item
    return sorted(latest.values(), key=lambda item: item.get("updated_at", ""), reverse=True)


def get_research_item(collection: str, item_id: str) -> dict[str, Any] | None:
    for item in _latest(collection):
        if item.get("id") == item_id:
            return item
    return None


def _normalize_source(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    base = _base(payload, object_type="source", existing=existing)
    base.update({
        "publisher": redact_text(payload.get("publisher", payload.get("author", existing.get("publisher", "")))),
        "date_published": redact_text(payload.get("date_published", existing.get("date_published", ""))),
        "date_observed": redact_text(payload.get("date_observed", existing.get("date_observed", _today()))),
        "credibility_rating": _int(payload.get("credibility_rating", existing.get("credibility_rating", 0)), 0, minimum=0, maximum=5),
        "relevance_rating": _int(payload.get("relevance_rating", existing.get("relevance_rating", 0)), 0, minimum=0, maximum=5),
        "freshness_rating": _int(payload.get("freshness_rating", existing.get("freshness_rating", 0)), 0, minimum=0, maximum=5),
        "freshness_status": _safe_status(payload.get("freshness_status", existing.get("freshness_status", "unknown")), FRESHNESS_STATUSES, "unknown"),
        "status": _safe_status(payload.get("status", existing.get("status", "new")), SOURCE_STATUSES, "new"),
    })
    return redact_data(base)


def _normalize_queue(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    base = _base(payload, object_type="queue", existing=existing)
    base.update({
        "source_id": redact_text(payload.get("source_id", existing.get("source_id", ""))),
        "priority": _safe_status(payload.get("priority", existing.get("priority", "medium")), {"low", "medium", "high", "urgent"}, "medium"),
        "research_question": redact_text(payload.get("research_question", existing.get("research_question", ""))),
        "desired_output": _safe_status(payload.get("desired_output", existing.get("desired_output", "evidence_item")), DESIRED_OUTPUTS, "evidence_item"),
        "status": _safe_status(payload.get("status", existing.get("status", "queued")), QUEUE_STATUSES, "queued"),
    })
    return redact_data(base)


def _normalize_note(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    base = _base(payload, object_type="note", existing=existing)
    base.update({
        "source_id": redact_text(payload.get("source_id", existing.get("source_id", ""))),
        "summary": redact_text(payload.get("summary", existing.get("summary", ""))),
        "key_claims": redact_text(payload.get("key_claims", existing.get("key_claims", ""))),
        "supporting_details": redact_text(payload.get("supporting_details", existing.get("supporting_details", ""))),
        "contradicting_details": redact_text(payload.get("contradicting_details", existing.get("contradicting_details", ""))),
        "uncertainty": redact_text(payload.get("uncertainty", existing.get("uncertainty", ""))),
        "operator_interpretation": redact_text(payload.get("operator_interpretation", existing.get("operator_interpretation", ""))),
        "status": _safe_status(payload.get("status", existing.get("status", "draft")), NOTE_STATUSES, "draft"),
    })
    return redact_data(base)


def _normalize_candidate(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    base = _base(payload, object_type="candidate", existing=existing)
    source_id = redact_text(payload.get("source_id", existing.get("source_id", "")))
    source = get_research_item("sources", source_id) or {}
    base.update({
        "source_id": source_id,
        "note_id": redact_text(payload.get("note_id", existing.get("note_id", ""))),
        "direction": _safe_status(payload.get("direction", existing.get("direction", "neutral")), EVIDENCE_DIRECTIONS, "neutral"),
        "evidence_relevance_score": _int(payload.get("evidence_relevance_score", payload.get("relevance_score", existing.get("evidence_relevance_score", source.get("relevance_rating", 0)))), 0, minimum=0, maximum=5),
        "credibility_score": _int(payload.get("credibility_score", existing.get("credibility_score", source.get("credibility_rating", 0))), 0, minimum=0, maximum=5),
        "freshness_score": _int(payload.get("freshness_score", existing.get("freshness_score", source.get("freshness_rating", 0))), 0, minimum=0, maximum=5),
        "evidence_strength": _int(payload.get("evidence_strength", existing.get("evidence_strength", 0)), 0, minimum=0, maximum=5),
        "contradiction_strength": _int(payload.get("contradiction_strength", existing.get("contradiction_strength", 0)), 0, minimum=0, maximum=5),
        "uncertainty_level": _int(payload.get("uncertainty_level", existing.get("uncertainty_level", 0)), 0, minimum=0, maximum=5),
        "freshness_status": _safe_status(payload.get("freshness_status", existing.get("freshness_status", source.get("freshness_status", "unknown"))), FRESHNESS_STATUSES, "unknown"),
        "status": _safe_status(payload.get("status", existing.get("status", "candidate")), CANDIDATE_STATUSES, "candidate"),
        "review_recommendation": research_recommendation(payload, source),
    })
    return redact_data(base)


def research_recommendation(payload: dict[str, Any], source: dict[str, Any] | None = None) -> str:
    source = source or {}
    credibility = _int(payload.get("credibility_score", source.get("credibility_rating", 0)), 0, minimum=0, maximum=5)
    relevance = _int(payload.get("evidence_relevance_score", payload.get("relevance_score", source.get("relevance_rating", 0))), 0, minimum=0, maximum=5)
    freshness = _int(payload.get("freshness_score", source.get("freshness_rating", 0)), 0, minimum=0, maximum=5)
    direction = _safe_status(payload.get("direction", "neutral"), EVIDENCE_DIRECTIONS, "neutral")
    if not payload.get("related_thesis_id") and not payload.get("thesis_id"):
        return "Link to thesis before scoring"
    if freshness <= 1:
        return "Potentially stale"
    if credibility >= 4 and relevance >= 4:
        return "Good candidate for evidence"
    if direction in {"weakly_contradicts", "contradicts"}:
        return "Contradicts active thesis"
    if credibility <= 2:
        return "Needs corroboration"
    return "Review source before using"


def _normalize_freshness(payload: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    base = _base(payload, object_type="freshness", existing=existing)
    status = _safe_status(payload.get("freshness_status", payload.get("status", existing.get("freshness_status", "unknown"))), FRESHNESS_STATUSES, "unknown")
    base.update({
        "target_collection": _safe_status(payload.get("target_collection", existing.get("target_collection", "sources")), COLLECTIONS | {"strategy_evidence"}, "sources"),
        "target_id": redact_text(payload.get("target_id", existing.get("target_id", ""))),
        "date_observed": redact_text(payload.get("date_observed", existing.get("date_observed", _today()))),
        "date_published": redact_text(payload.get("date_published", existing.get("date_published", ""))),
        "freshness_status": status,
        "review_by": redact_text(payload.get("review_by", existing.get("review_by", ""))),
        "last_reviewed_at": redact_text(payload.get("last_reviewed_at", existing.get("last_reviewed_at", _now()))),
        "stale_reason": redact_text(payload.get("stale_reason", existing.get("stale_reason", ""))),
        "refresh_notes": redact_text(payload.get("refresh_notes", existing.get("refresh_notes", ""))),
        "status": status,
    })
    return redact_data(base)


def create_source(payload: dict[str, Any]) -> dict[str, Any]:
    item = _normalize_source(payload)
    event = _append_event("source_created", "sources", item)
    return {"ok": True, "item": item, "event": event, "secret_values_returned": False}


def update_source(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_research_item("sources", item_id)
    if not existing:
        return {"ok": False, "status": "not_found", "item_id": item_id, "secret_values_returned": False}
    item = _normalize_source({**payload, "id": item_id}, existing)
    event = _append_event("source_edited", "sources", item)
    return {"ok": True, "item": item, "event": event, "secret_values_returned": False}


def archive_source(item_id: str) -> dict[str, Any]:
    result = update_source(item_id, {"status": "archived"})
    if result.get("ok"):
        result["action"] = "source_archived"
    return result


def mark_source_reviewed(item_id: str) -> dict[str, Any]:
    result = update_source(item_id, {"status": "reviewed"})
    if result.get("ok"):
        _append_event("source_marked_reviewed", "sources", result["item"])
    return result


def mark_source_stale(item_id: str, stale_reason: str = "") -> dict[str, Any]:
    result = update_source(item_id, {"status": "stale", "freshness_status": "stale", "operator_notes": stale_reason})
    if result.get("ok"):
        _append_event("source_marked_stale", "sources", result["item"])
    return result


def create_queue_item(payload: dict[str, Any]) -> dict[str, Any]:
    item = _normalize_queue(payload)
    event = _append_event("queue_item_created", "queue", item)
    return {"ok": True, "item": item, "event": event, "secret_values_returned": False}


def update_queue_item(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_research_item("queue", item_id)
    if not existing:
        return {"ok": False, "status": "not_found", "item_id": item_id, "secret_values_returned": False}
    item = _normalize_queue({**payload, "id": item_id}, existing)
    event = _append_event("queue_item_updated", "queue", item)
    return {"ok": True, "item": item, "event": event, "secret_values_returned": False}


def create_note(payload: dict[str, Any]) -> dict[str, Any]:
    item = _normalize_note(payload)
    event = _append_event("source_note_created", "notes", item)
    return {"ok": True, "item": item, "event": event, "secret_values_returned": False}


def update_note(item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_research_item("notes", item_id)
    if not existing:
        return {"ok": False, "status": "not_found", "item_id": item_id, "secret_values_returned": False}
    item = _normalize_note({**payload, "id": item_id}, existing)
    event = _append_event("source_note_updated", "notes", item)
    return {"ok": True, "item": item, "event": event, "secret_values_returned": False}


def create_evidence_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    item = _normalize_candidate(payload)
    event = _append_event("evidence_candidate_created", "evidence_candidates", item)
    return {"ok": True, "item": item, "event": event, "secret_values_returned": False}


def update_freshness(payload: dict[str, Any]) -> dict[str, Any]:
    item = _normalize_freshness(payload)
    event = _append_event("evidence_freshness_updated", "freshness", item)
    return {"ok": True, "item": item, "event": event, "secret_values_returned": False}


def freshness_summary() -> dict[str, Any]:
    sources = _latest("sources")
    candidates = _latest("evidence_candidates")
    stale_sources = [item for item in sources if item.get("status") == "stale" or item.get("freshness_status") in {"stale", "expired"}]
    aging_sources = [item for item in sources if item.get("freshness_status") == "aging"]
    stale_candidates = [item for item in candidates if item.get("freshness_status") in {"stale", "expired"}]
    return redact_data({
        "version": APP_VERSION,
        "generated_at": _now(),
        "summary": {"stale_sources": len(stale_sources), "aging_sources": len(aging_sources), "stale_candidates": len(stale_candidates)},
        "stale_sources": stale_sources,
        "aging_sources": aging_sources,
        "stale_evidence_candidates": stale_candidates,
        "secret_values_returned": False,
    })


def convert_candidate(candidate_id: str) -> dict[str, Any]:
    candidate = get_research_item("evidence_candidates", candidate_id)
    if not candidate:
        return {"ok": False, "status": "not_found", "candidate_id": candidate_id, "order_submitted": False, "network_attempted": False, "secret_values_returned": False}
    evidence_payload = {
        "thesis_id": candidate.get("related_thesis_id", ""),
        "title": candidate.get("title", "Converted research evidence"),
        "source_url": candidate.get("source_url", ""),
        "source_type": candidate.get("source_type", "research_source"),
        "date_observed": candidate.get("date_observed", _today()),
        "relevance_score": candidate.get("evidence_relevance_score", 0),
        "credibility_score": candidate.get("credibility_score", 0),
        "direction": candidate.get("direction", "neutral"),
        "notes": candidate.get("operator_notes", ""),
        "stale": candidate.get("freshness_status") in {"stale", "expired"},
        "status": "stale" if candidate.get("freshness_status") in {"stale", "expired"} else "active",
        "market_id": candidate.get("market_id", ""),
        "market_title": candidate.get("market_title", ""),
        "tags": candidate.get("tags", []),
        "source_links": [candidate.get("source_url", "")] if candidate.get("source_url") else [],
    }
    evidence = create_evidence(evidence_payload)
    updated = _normalize_candidate({**candidate, "status": "converted", "related_evidence_id": evidence.get("item", {}).get("id", "")}, candidate)
    event = _append_event("evidence_candidate_converted", "evidence_candidates", updated)
    return redact_data({"ok": True, "candidate": updated, "evidence": evidence.get("item"), "event": event, "order_submitted": False, "network_attempted": False, "secret_values_returned": False})


def list_sources(status: str = "", limit: int = 200) -> dict[str, Any]:
    items = _latest("sources")
    if status:
        items = [item for item in items if item.get("status") == status]
    return {"items": items[: max(1, min(int(limit or 200), 1000))], "count": len(items), "version": APP_VERSION, "secret_values_returned": False}


def list_queue(status: str = "", limit: int = 200) -> dict[str, Any]:
    items = _latest("queue")
    if status:
        items = [item for item in items if item.get("status") == status]
    return {"items": items[: max(1, min(int(limit or 200), 1000))], "count": len(items), "version": APP_VERSION, "secret_values_returned": False}


def list_notes(source_id: str = "", limit: int = 200) -> dict[str, Any]:
    items = _latest("notes")
    if source_id:
        items = [item for item in items if item.get("source_id") == source_id]
    return {"items": items[: max(1, min(int(limit or 200), 1000))], "count": len(items), "version": APP_VERSION, "secret_values_returned": False}


def list_candidates(thesis_id: str = "", limit: int = 200) -> dict[str, Any]:
    items = _latest("evidence_candidates")
    if thesis_id:
        items = [item for item in items if item.get("related_thesis_id") == thesis_id]
    return {"items": items[: max(1, min(int(limit or 200), 1000))], "count": len(items), "version": APP_VERSION, "secret_values_returned": False}


def build_thesis_comparison(thesis_id: str = "") -> dict[str, Any]:
    theses = list_theses(limit=1000).get("items", [])
    thesis = next((item for item in theses if not thesis_id or item.get("id") == thesis_id), {}) if theses else {}
    tid = thesis_id or thesis.get("id", "")
    strategy_evidence = list_evidence(thesis_id=tid, limit=1000).get("items", []) if tid else []
    candidates = [item for item in _latest("evidence_candidates") if not tid or item.get("related_thesis_id") == tid]
    support_dirs = {"supports", "weakly_supports"}
    contradict_dirs = {"weakly_contradicts", "contradicts"}
    supporting = [item for item in strategy_evidence + candidates if item.get("direction") in support_dirs]
    contradicting = [item for item in strategy_evidence + candidates if item.get("direction") in contradict_dirs]
    neutral = [item for item in strategy_evidence + candidates if item.get("direction") == "neutral"]
    stale = [item for item in strategy_evidence + candidates if item.get("stale") or item.get("freshness_status") in {"stale", "expired"} or item.get("status") == "stale"]
    all_items = strategy_evidence + candidates
    avg_cred = round(sum(_int(item.get("credibility_score", 0), 0) for item in all_items) / max(len(all_items), 1), 2)
    avg_rel = round(sum(_int(item.get("relevance_score", item.get("evidence_relevance_score", 0)), 0) for item in all_items) / max(len(all_items), 1), 2)
    unresolved = [item for item in _latest("queue") if not tid or item.get("related_thesis_id") == tid]
    next_action = "Add sources and evidence candidates before updating the thesis."
    if stale:
        next_action = "Refresh stale evidence before drafting or updating a trade ticket."
    elif contradicting and len(contradicting) >= len(supporting):
        next_action = "Review contradicting evidence before promoting the thesis."
    elif supporting:
        next_action = "Review evidence quality, then update thesis or scorecard manually."
    report = redact_data({
        "version": APP_VERSION,
        "generated_at": _now(),
        "thesis_id": tid,
        "thesis_summary": thesis.get("thesis_summary", ""),
        "supporting_evidence_count": len(supporting),
        "contradicting_evidence_count": len(contradicting),
        "neutral_evidence_count": len(neutral),
        "stale_evidence_count": len(stale),
        "average_credibility": avg_cred,
        "average_relevance": avg_rel,
        "strongest_supporting_evidence": sorted(supporting, key=lambda i: _int(i.get("credibility_score", 0), 0) + _int(i.get("relevance_score", i.get("evidence_relevance_score", 0)), 0), reverse=True)[:3],
        "strongest_contradicting_evidence": sorted(contradicting, key=lambda i: _int(i.get("credibility_score", 0), 0) + _int(i.get("relevance_score", i.get("evidence_relevance_score", 0)), 0), reverse=True)[:3],
        "unresolved_research_questions": unresolved[:10],
        "recommended_next_research_action": next_action,
        "safety_statement": "This comparison does not alter theses, tickets, orders, or live trading gates.",
        "secret_values_returned": False,
    })
    _append_event("thesis_comparison_generated", "freshness", {"id": f"comparison_{uuid4().hex[:12]}", "title": "Thesis comparison", "related_thesis_id": tid, "status": "generated", "app_version": APP_VERSION, "secret_values_returned": False})
    return report


def build_research_workspace(limit: int = 100) -> dict[str, Any]:
    sources = _latest("sources")
    queue = _latest("queue")
    notes = _latest("notes")
    candidates = _latest("evidence_candidates")
    freshness = freshness_summary()
    reviewed = [item for item in sources if item.get("status") in {"reviewed", "converted_to_evidence"}]
    stale = [item for item in sources + candidates if item.get("status") == "stale" or item.get("freshness_status") in {"stale", "expired"}]
    summary = {
        "sources": len(sources),
        "reviewed_sources": len(reviewed),
        "queue_items": len(queue),
        "source_notes": len(notes),
        "evidence_candidates": len(candidates),
        "stale_items": len(stale),
    }
    next_action = "Add a research source, write notes, then convert reviewed claims into evidence candidates."
    if queue:
        next_action = "Work the highest-priority research queue item, then convert reviewed notes into evidence candidates."
    if stale:
        next_action = "Refresh stale evidence before relying on linked theses or scorecards."
    return redact_data({
        "version": APP_VERSION,
        "generated_at": _now(),
        "summary": summary,
        "next_action": next_action,
        "sources": sources[:limit],
        "queue": queue[:limit],
        "notes": notes[:limit],
        "evidence_candidates": candidates[:limit],
        "freshness": freshness,
        "recent_events": list_research_events(limit=25),
        "safety_statement": "Research output never places, signs, approves, arms, or cancels orders. Operator review and live gates remain mandatory.",
        "secret_values_returned": False,
    })


def research_export_json() -> dict[str, Any]:
    workspace = build_research_workspace(limit=10000)
    workspace["thesis_comparison"] = build_thesis_comparison("")
    return redact_data(workspace)


def research_export_markdown() -> str:
    workspace = research_export_json()
    lines = [
        f"# Research Intake Export — {APP_VERSION}",
        "",
        f"Generated: {workspace.get('generated_at')}",
        "",
        workspace.get("safety_statement", "Research data is not an order."),
        "",
        "## Summary",
        "",
    ]
    for key, value in workspace.get("summary", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Sources", "", "| ID | Status | Type | Title | Credibility | Relevance | Freshness |", "|---|---|---|---|---:|---:|---|"])
    for item in workspace.get("sources", []):
        lines.append("| {id} | {status} | {stype} | {title} | {cred} | {rel} | {fresh} |".format(
            id=_text(item.get("id")), status=_text(item.get("status")), stype=_text(item.get("source_type")), title=_text(item.get("title")).replace("|", "\\|")[:180], cred=item.get("credibility_rating", 0), rel=item.get("relevance_rating", 0), fresh=_text(item.get("freshness_status")),
        ))
    lines.extend(["", "## Evidence Candidates", "", "| ID | Direction | Thesis | Title | Recommendation |", "|---|---|---|---|---|"])
    for item in workspace.get("evidence_candidates", []):
        lines.append("| {id} | {direction} | {thesis} | {title} | {rec} |".format(
            id=_text(item.get("id")), direction=_text(item.get("direction")), thesis=_text(item.get("related_thesis_id")), title=_text(item.get("title")).replace("|", "\\|")[:180], rec=_text(item.get("review_recommendation")).replace("|", "\\|"),
        ))
    lines.extend(["", "## Thesis Comparison", "", f"Recommended next research action: {workspace.get('thesis_comparison', {}).get('recommended_next_research_action', 'unknown')}", "", "Secret values are redacted. This research export does not place, approve, sign, arm, or cancel orders.", ""])
    _append_event("research_report_exported", "freshness", {"id": f"research_export_{uuid4().hex[:12]}", "title": "Research report export", "status": "exported", "app_version": APP_VERSION, "secret_values_returned": False})
    return "\n".join(lines)


def _csv_for(items: list[dict[str, Any]], fields: list[str]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for item in items:
        writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in item.items()})
    return out.getvalue()


def research_csv(collection: str) -> str:
    if collection == "sources":
        return _csv_for(_latest("sources"), ["id", "created_at", "updated_at", "title", "source_url", "source_type", "status", "credibility_rating", "relevance_rating", "freshness_status", "related_thesis_id"])
    if collection == "queue":
        return _csv_for(_latest("queue"), ["id", "title", "source_id", "priority", "status", "desired_output", "research_question", "related_thesis_id"])
    if collection == "evidence-candidates":
        return _csv_for(_latest("evidence_candidates"), ["id", "title", "source_id", "direction", "related_thesis_id", "evidence_relevance_score", "credibility_score", "freshness_score", "freshness_status", "status"])
    if collection == "stale":
        stale = [item for item in _latest("sources") + _latest("evidence_candidates") if item.get("status") == "stale" or item.get("freshness_status") in {"stale", "expired"}]
        return _csv_for(stale, ["id", "title", "status", "freshness_status", "related_thesis_id", "updated_at"])
    return _csv_for(_latest(collection), ["id", "title", "status", "updated_at"])
