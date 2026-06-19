from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_v2 import build_live_v2_readiness, list_audit_records, record_audit, redact_data, redact_text
from .live_strategy import list_theses, list_evidence, list_watchlist, list_scorecards, list_reviews
from .live_research import list_sources, list_queue, list_notes, list_candidates, freshness_summary
from .live_monitoring import list_rules as list_monitoring_rules, list_alerts, list_alert_history
from .live_portfolio import generate_portfolio_snapshot, list_exposure, list_warnings, list_scenarios
from .live_governance import list_journal, list_checklists, list_reviews as list_governance_reviews, list_rules as list_governance_rules, list_near_misses, list_mistake_patterns
from .live_data import health_report_json, runtime_inventory
try:  # optional integration; not required for startup
    from .live_v3_analytics import build_analytics_summary, generate_analytics_snapshot
except Exception:  # pragma: no cover
    build_analytics_summary = None  # type: ignore
    generate_analytics_snapshot = None  # type: ignore
try:
    from .live_v3_simulation import simulation_summary, list_sessions as list_simulation_sessions, list_reports as list_simulation_reports
except Exception:  # pragma: no cover
    simulation_summary = None  # type: ignore
    list_simulation_sessions = None  # type: ignore
    list_simulation_reports = None  # type: ignore

DATASETS_DIR = DATA_DIR / "live_v3" / "datasets"
DATASET_EVENTS_PATH = DATASETS_DIR / "dataset_events.jsonl"
SNAPSHOTS_PATH = DATASETS_DIR / "snapshots.jsonl"
COLLECTION_RUNS_PATH = DATASETS_DIR / "collection_runs.jsonl"
DATASET_MANIFESTS_PATH = DATASETS_DIR / "dataset_manifests.jsonl"
QUALITY_REPORTS_PATH = DATASETS_DIR / "quality_reports.jsonl"
PROVENANCE_PATH = DATASETS_DIR / "provenance.jsonl"
DATASET_SETTINGS_PATH = DATASETS_DIR / "settings.json"

SNAPSHOT_TYPES = {
    "market_metadata", "order_book", "local_strategy", "local_research", "local_monitoring",
    "local_portfolio", "local_governance", "local_analytics", "local_simulation", "data_health", "audit_summary"
}
LOCAL_SUBSYSTEM_TYPES = {
    "local_strategy", "local_research", "local_monitoring", "local_portfolio", "local_governance",
    "local_analytics", "local_simulation", "data_health", "audit_summary"
}
QUALITY_STATUSES = ["excellent", "good", "usable", "partial", "stale", "incomplete", "blocked", "unknown"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_text(value: Any, default: str = "") -> str:
    text = redact_text(str(value or "").strip())
    return text or default


def _items(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, dict):
        data = result.get("items", result.get("records", result.get("checks", [])))
    else:
        data = result
    if not isinstance(data, list):
        return []
    return [redact_data(x) for x in data if isinstance(x, dict)]


def _record_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _payload_hash(payload: Any) -> str:
    text = json.dumps(redact_data(payload), sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
            rows.append({"id": _record_id("invalid"), "created_at": _now(), "status": "invalid_json", "secret_values_returned": False})
    return rows


def _latest_by_id(rows: list[dict[str, Any]], id_key: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        rid = str(row.get(id_key) or row.get("id") or _record_id("row"))
        latest[rid] = row
    return sorted(latest.values(), key=lambda r: str(r.get("updated_at") or r.get("created_at") or r.get("collection_timestamp") or ""), reverse=True)


def _safety(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "read_only_snapshot_collection": True,
        "dataset_building_is_not_trading": True,
        "not_financial_advice": True,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "mutates_live_trading_state": False,
        "external_network_called": False,
        "scheduled_collection_enabled": False,
        "secret_values_returned": False,
        "safety_statement": "Dataset and snapshot workflows are read-only, local-first, non-autonomous, and do not place orders, cancel orders, approve orders, sign orders, arm live trading, or bypass backend gates.",
    }
    if extra:
        base.update(extra)
    return base


def _audit(action: str, status: str = "ok", details: dict[str, Any] | None = None) -> dict[str, Any]:
    event = {
        "event_id": _record_id("dataset_evt"),
        "timestamp": _now(),
        "app_version": APP_VERSION,
        "action": action,
        "status": status,
        "details": details or {},
        **_safety(),
    }
    _write_jsonl(DATASET_EVENTS_PATH, event)
    record_audit(f"v3_dataset_{action}", status, details={**(details or {}), "order_submitted": False, "order_cancelled": False, "live_trading_armed": False}, network_attempted=False)
    return redact_data(event)


def list_dataset_events(limit: int = 500) -> dict[str, Any]:
    rows = list(reversed(_read_jsonl(DATASET_EVENTS_PATH)))[: max(1, min(int(limit or 500), 5000))]
    return {"version": APP_VERSION, "count": len(rows), "items": redact_data(rows), **_safety()}


def _payload_summary(snapshot_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    payload = redact_data(payload if isinstance(payload, dict) else {})
    summary: dict[str, Any] = {"snapshot_type": snapshot_type, "field_count": len(payload), "contains_raw_secret_values": False}
    if snapshot_type == "market_metadata":
        summary.update({
            "market_id": payload.get("market_id", "unknown"),
            "condition_id": payload.get("condition_id", "unknown"),
            "question": _safe_text(payload.get("question") or payload.get("title"), "unknown"),
            "outcomes": payload.get("outcomes", []),
            "status": payload.get("status", "unknown"),
        })
    elif snapshot_type == "order_book":
        bids = payload.get("bids", []) if isinstance(payload.get("bids"), list) else []
        asks = payload.get("asks", []) if isinstance(payload.get("asks"), list) else []
        best_bid = payload.get("best_bid")
        best_ask = payload.get("best_ask")
        try:
            spread = None if best_bid is None or best_ask is None else round(float(best_ask) - float(best_bid), 6)
        except Exception:
            spread = "unknown"
        summary.update({"market_id": payload.get("market_id", "unknown"), "token_id": payload.get("token_id", "unknown"), "outcome": payload.get("outcome", "unknown"), "bid_levels": len(bids), "ask_levels": len(asks), "best_bid": best_bid, "best_ask": best_ask, "spread": spread})
    else:
        for key in ("count", "items_count", "status", "summary", "subsystem", "generated_at"):
            if key in payload:
                summary[key] = payload.get(key)
    return redact_data(summary)


def _local_snapshot_payload(snapshot_type: str, limit: int = 100) -> tuple[str, dict[str, Any], list[str]]:
    unknowns: list[str] = []
    if snapshot_type == "local_strategy":
        payload = {"theses": _items(list_theses(limit=limit)), "evidence": _items(list_evidence(limit=limit)), "watchlist": _items(list_watchlist(limit=limit)), "scorecards": _items(list_scorecards(limit=limit)), "reviews": _items(list_reviews(limit=limit))}
    elif snapshot_type == "local_research":
        payload = {"sources": _items(list_sources(limit=limit)), "queue": _items(list_queue(limit=limit)), "notes": _items(list_notes(limit=limit)), "candidates": _items(list_candidates(limit=limit)), "freshness": freshness_summary()}
    elif snapshot_type == "local_monitoring":
        payload = {"rules": _items(list_monitoring_rules(limit=limit)), "alerts": _items(list_alerts(limit=limit)), "history": _items(list_alert_history(limit=limit))}
    elif snapshot_type == "local_portfolio":
        payload = {"snapshot": generate_portfolio_snapshot(record=False), "exposure": _items(list_exposure(limit=limit)), "warnings": _items(list_warnings(limit=limit)), "scenarios": _items(list_scenarios(limit=limit))}
    elif snapshot_type == "local_governance":
        payload = {"journal": _items(list_journal(limit=limit)), "checklists": _items(list_checklists(limit=limit)), "reviews": _items(list_governance_reviews(limit=limit)), "rules": _items(list_governance_rules(limit=limit)), "near_misses": _items(list_near_misses(limit=limit)), "mistake_patterns": _items(list_mistake_patterns(limit=limit))}
    elif snapshot_type == "local_analytics":
        if build_analytics_summary is None:
            payload = {"status": "analytics_unavailable"}
            unknowns.append("Analytics module was unavailable while creating this snapshot.")
        else:
            payload = {"summary": build_analytics_summary(), "snapshot": generate_analytics_snapshot(write=False) if generate_analytics_snapshot is not None else {}}
    elif snapshot_type == "local_simulation":
        payload = {"summary": simulation_summary() if simulation_summary is not None else {"status": "simulation_unavailable"}, "sessions": list_simulation_sessions(limit=limit).get("items", []) if list_simulation_sessions is not None else [], "reports": list_simulation_reports(limit=limit).get("items", []) if list_simulation_reports is not None else []}
    elif snapshot_type == "data_health":
        payload = {"health_report": health_report_json(), "readiness": build_live_v2_readiness(), "inventory": runtime_inventory(), "secret_scan": {"skipped": True, "reason": "Dataset page/demo collection avoids deep secret scans on request; run release validation for full scan."}}
    elif snapshot_type == "audit_summary":
        payload = {"events": list_audit_records(limit=limit)}
    else:
        payload = {"status": "unknown_snapshot_type"}
        unknowns.append(f"Unknown local snapshot type: {snapshot_type}")
    count = sum(len(v) for v in payload.values() if isinstance(v, list)) if isinstance(payload, dict) else 0
    return _safe_text(snapshot_type), redact_data({"subsystem": snapshot_type, "generated_at": _now(), "count": count, **payload}), unknowns


def _create_provenance(snapshot: dict[str, Any], operator_action: str = "manual_snapshot_collection") -> dict[str, Any]:
    provenance = {
        "provenance_id": _record_id("prov"),
        "created_at": _now(),
        "app_version": APP_VERSION,
        "snapshot_id": snapshot.get("snapshot_id"),
        "dataset_id": snapshot.get("dataset_id"),
        "source_subsystem": snapshot.get("source_subsystem", "unknown"),
        "source_label": snapshot.get("source_name", "local"),
        "collection_mode": snapshot.get("collection_mode", "manual"),
        "collection_timestamp": snapshot.get("created_at"),
        "source_timestamp": snapshot.get("source_timestamp"),
        "operator_action": operator_action,
        "related_audit_event": None,
        "payload_hash": snapshot.get("payload_hash"),
        "redaction_status": snapshot.get("redaction_status", "redacted"),
        "import_export_history": [],
        **_safety(),
    }
    _write_jsonl(PROVENANCE_PATH, provenance)
    return redact_data(provenance)


def validate_snapshot(snapshot: dict[str, Any] | None = None, snapshot_id: str | None = None) -> dict[str, Any]:
    if snapshot is None and snapshot_id:
        snapshot = next((row for row in list_snapshots(limit=5000).get("items", []) if row.get("snapshot_id") == snapshot_id), None)
    snapshot = redact_data(snapshot or {})
    findings: list[dict[str, Any]] = []
    status = "pass"
    required = ["snapshot_id", "created_at", "app_version", "snapshot_type", "source_subsystem", "collection_mode", "payload_hash", "redaction_status", "payload_summary"]
    for key in required:
        if not snapshot.get(key):
            findings.append({"severity": "blocker", "title": f"Missing {key}", "recommended_operator_action": "Recreate or repair this snapshot before using it for replay."})
            status = "fail"
    if snapshot.get("snapshot_type") not in SNAPSHOT_TYPES:
        findings.append({"severity": "warning", "title": "Unknown snapshot type", "recommended_operator_action": "Confirm this imported/custom snapshot before using it."})
        if status != "fail":
            status = "warning"
    dumped = json.dumps(snapshot, default=str).lower()
    for marker in ("private_key", "api_key=", "authorization:", "bearer ", "wallet_secret", "mnemonic"):
        if marker in dumped:
            findings.append({"severity": "critical", "title": "Secret-like marker detected", "recommended_operator_action": "Do not export this snapshot; remove and regenerate with redaction."})
            status = "fail"
    duplicate_hash_count = 0
    if snapshot.get("payload_hash"):
        duplicate_hash_count = sum(1 for row in list_snapshots(limit=5000).get("items", []) if row.get("payload_hash") == snapshot.get("payload_hash"))
        if duplicate_hash_count > 1:
            findings.append({"severity": "info", "title": "Duplicate payload hash", "recommended_operator_action": "Review duplicates before building a dataset."})
    if not findings:
        findings.append({"severity": "info", "title": "Snapshot passed schema and redaction checks", "recommended_operator_action": "Safe to include in a replay dataset if freshness/coverage are acceptable."})
    return redact_data({"version": APP_VERSION, "snapshot_id": snapshot.get("snapshot_id"), "validation_status": status, "quality_status": "usable" if status in {"pass", "warning"} else "blocked", "duplicate_hash_count": duplicate_hash_count, "findings": findings, **_safety()})


def create_snapshot(snapshot_type: str, payload: dict[str, Any] | None = None, collection_mode: str = "manual", source_name: str | None = None, source_url: str | None = None, run_id: str | None = None, operator_notes: str = "") -> dict[str, Any]:
    snapshot_type = _safe_text(snapshot_type, "local_derived")
    payload = redact_data(payload or {})
    unknowns: list[str] = []
    if snapshot_type in LOCAL_SUBSYSTEM_TYPES and not payload:
        source_name, payload, unknowns = _local_snapshot_payload(snapshot_type)
    if snapshot_type == "market_metadata" and not payload:
        payload = {"market_id": "unknown", "question": "Unknown market metadata; operator did not provide read-only market data.", "outcomes": [], "status": "unknown"}
        unknowns.append("No market metadata payload was provided; values are unknown/unavailable.")
    if snapshot_type == "order_book" and not payload:
        payload = {"market_id": "unknown", "token_id": "unknown", "bids": [], "asks": [], "best_bid": None, "best_ask": None, "status": "mock_or_unavailable"}
        unknowns.append("No safe read-only order book client/payload was available; structure is present for local/demo/mock input only.")
    payload_hash = _payload_hash(payload)
    snapshot = {
        "snapshot_id": _record_id("snap"),
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "snapshot_type": snapshot_type,
        "source_subsystem": "external_market_data" if snapshot_type in {"market_metadata", "order_book"} else snapshot_type.replace("local_", ""),
        "source_name": _safe_text(source_name or payload.get("source_name") or snapshot_type, snapshot_type),
        "source_url": _safe_text(source_url or payload.get("source_url") or payload.get("url") or ""),
        "collection_mode": _safe_text(collection_mode, "manual"),
        "market_id": _safe_text(payload.get("market_id") or payload.get("id") or ""),
        "condition_id": _safe_text(payload.get("condition_id") or ""),
        "token_ids": payload.get("token_ids", []) if isinstance(payload.get("token_ids"), list) else ([payload.get("token_id")] if payload.get("token_id") else []),
        "local_object_ids": payload.get("local_object_ids", []) if isinstance(payload.get("local_object_ids"), list) else [],
        "source_timestamp": _safe_text(payload.get("source_timestamp") or payload.get("timestamp") or ""),
        "operator_notes": _safe_text(operator_notes),
        "safe_metadata": {k: payload.get(k) for k in ("market_id", "condition_id", "token_id", "status", "category", "tags") if payload.get(k) is not None},
        "payload_summary": _payload_summary(snapshot_type, payload),
        "payload_hash": payload_hash,
        "redaction_status": "redacted",
        "unknown_unavailable_fields": unknowns,
        "validation_status": "not_validated",
        "quality_status": "unknown",
        "provenance_record_id": None,
        "collection_run_id": run_id,
        "audit_metadata": {"network_attempted": False, "read_only": True},
        **_safety(),
    }
    validation = validate_snapshot(snapshot)
    snapshot["validation_status"] = validation["validation_status"]
    snapshot["quality_status"] = validation["quality_status"]
    provenance = _create_provenance(snapshot)
    snapshot["provenance_record_id"] = provenance["provenance_id"]
    _write_jsonl(SNAPSHOTS_PATH, snapshot)
    return redact_data(snapshot)


def collect_snapshots(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    requested = payload.get("snapshot_types") if isinstance(payload.get("snapshot_types"), list) else None
    if not requested:
        requested = ["market_metadata", "order_book", "local_strategy", "local_research", "local_monitoring", "local_portfolio", "local_governance", "local_analytics", "local_simulation", "data_health", "audit_summary"]
    requested = [_safe_text(t) for t in requested if _safe_text(t)]
    run = {
        "run_id": _record_id("snapshot_run"),
        "created_at": _now(),
        "updated_at": _now(),
        "started_at": _now(),
        "completed_at": None,
        "app_version": APP_VERSION,
        "requested_snapshot_types": requested,
        "included_markets": payload.get("markets", []) if isinstance(payload.get("markets"), list) else ([payload.get("market_id")] if payload.get("market_id") else []),
        "included_theses": payload.get("theses", []) if isinstance(payload.get("theses"), list) else ([payload.get("thesis_id")] if payload.get("thesis_id") else []),
        "included_subsystems": [t for t in requested if t.startswith("local_") or t in {"data_health", "audit_summary"}],
        "collection_mode": _safe_text(payload.get("collection_mode"), "manual"),
        "status": "running",
        "warnings": [],
        "unknown_unavailable_data": [],
        "snapshots_created": [],
        "validation_results": [],
        "audit_reference": None,
        **_safety(),
    }
    _write_jsonl(COLLECTION_RUNS_PATH, run)
    _audit("snapshot_collection_started", "ok", {"run_id": run["run_id"], "snapshot_types": requested})
    market_payload = payload.get("market") if isinstance(payload.get("market"), dict) else {}
    order_book_payload = payload.get("order_book") if isinstance(payload.get("order_book"), dict) else {}
    snapshots: list[dict[str, Any]] = []
    for stype in requested:
        raw_payload: dict[str, Any] = {}
        if stype == "market_metadata":
            raw_payload = {**market_payload, **{k: payload.get(k) for k in ("market_id", "condition_id", "question", "title", "outcomes", "status") if payload.get(k) is not None}}
        elif stype == "order_book":
            raw_payload = {**order_book_payload, **{k: payload.get(k) for k in ("market_id", "condition_id", "token_id", "outcome", "bids", "asks", "best_bid", "best_ask") if payload.get(k) is not None}}
        snapshot = create_snapshot(stype, raw_payload, collection_mode=run["collection_mode"], run_id=run["run_id"], operator_notes=_safe_text(payload.get("notes")))
        snapshots.append(snapshot)
        run["snapshots_created"].append(snapshot["snapshot_id"])
        run["validation_results"].append({"snapshot_id": snapshot["snapshot_id"], "validation_status": snapshot["validation_status"], "quality_status": snapshot["quality_status"]})
        run["unknown_unavailable_data"].extend(snapshot.get("unknown_unavailable_fields", []))
    run["completed_at"] = _now()
    run["updated_at"] = run["completed_at"]
    run["status"] = "completed" if all(s.get("validation_status") in {"pass", "warning"} for s in snapshots) else "partial"
    run["warnings"] = sorted(set(run["unknown_unavailable_data"]))[:50]
    audit = _audit("snapshot_collection_completed", "ok", {"run_id": run["run_id"], "snapshot_count": len(snapshots), "status": run["status"]})
    run["audit_reference"] = audit["event_id"]
    _write_jsonl(COLLECTION_RUNS_PATH, run)
    return redact_data({"ok": True, "run": run, "snapshots": snapshots, **_safety()})


def list_snapshots(limit: int = 250, snapshot_type: str | None = None) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(SNAPSHOTS_PATH), "snapshot_id")
    if snapshot_type:
        rows = [r for r in rows if r.get("snapshot_type") == snapshot_type]
    rows = rows[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(rows), "items": redact_data(rows), **_safety()}


def list_collection_runs(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(COLLECTION_RUNS_PATH), "run_id")[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(rows), "items": redact_data(rows), **_safety()}


def get_collection_run(run_id: str) -> dict[str, Any] | None:
    return next((row for row in list_collection_runs(limit=5000).get("items", []) if row.get("run_id") == run_id), None)


def list_provenance(limit: int = 250) -> dict[str, Any]:
    rows = list(reversed(_read_jsonl(PROVENANCE_PATH)))[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(rows), "items": redact_data(rows), **_safety()}


def _quality_from_snapshots(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    required_types = {"market_metadata", "local_strategy", "local_research", "local_monitoring", "local_portfolio", "local_governance", "data_health"}
    present_types = {str(s.get("snapshot_type")) for s in snapshots}
    missing = sorted(required_types - present_types)
    malformed = [s for s in snapshots if s.get("validation_status") == "fail"]
    unknown_count = sum(len(s.get("unknown_unavailable_fields", [])) for s in snapshots)
    hashes = [s.get("payload_hash") for s in snapshots if s.get("payload_hash")]
    duplicate_hashes = sorted({h for h in hashes if hashes.count(h) > 1})
    score = 100
    score -= min(40, len(missing) * 6)
    score -= min(25, len(malformed) * 10)
    score -= min(15, unknown_count * 2)
    score -= min(10, len(duplicate_hashes) * 3)
    score = max(0, min(100, score))
    if score >= 90:
        status = "excellent"
    elif score >= 75:
        status = "good"
    elif score >= 60:
        status = "usable"
    elif score >= 40:
        status = "partial"
    elif malformed:
        status = "blocked"
    else:
        status = "incomplete"
    findings = []
    if missing:
        findings.append({"severity": "warning", "title": "Missing expected snapshot types", "details": missing, "recommended_operator_action": "Collect missing local subsystem snapshots before high-quality replay."})
    if duplicate_hashes:
        findings.append({"severity": "info", "title": "Duplicate payload hashes detected", "details": duplicate_hashes[:10], "recommended_operator_action": "Review duplicates if dataset size or coverage looks inflated."})
    if unknown_count:
        findings.append({"severity": "warning", "title": "Unknown/unavailable fields present", "details": unknown_count, "recommended_operator_action": "Treat replay outputs as partial and review missing data manually."})
    if not findings:
        findings.append({"severity": "info", "title": "Dataset passed basic quality checks", "recommended_operator_action": "Review provenance before using this dataset in simulation."})
    return {"quality_score": score, "quality_status": status, "present_snapshot_types": sorted(present_types), "missing_expected_snapshot_types": missing, "malformed_snapshot_count": len(malformed), "duplicate_payload_hashes": duplicate_hashes, "unknown_unavailable_field_count": unknown_count, "replay_readiness": status in {"excellent", "good", "usable", "partial"}, "simulation_readiness": status in {"excellent", "good", "usable", "partial"}, "export_readiness": len(malformed) == 0, "findings": findings}


def build_dataset_manifest(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    snapshots = list_snapshots(limit=5000).get("items", [])
    requested_types = payload.get("snapshot_types") if isinstance(payload.get("snapshot_types"), list) else []
    if requested_types:
        snapshots = [s for s in snapshots if s.get("snapshot_type") in requested_types]
    include_demo = bool(payload.get("include_demo_data", True))
    if not include_demo:
        snapshots = [s for s in snapshots if s.get("collection_mode") != "demo"]
    quality = _quality_from_snapshots(snapshots)
    dataset = {
        "dataset_id": _record_id("dataset"),
        "created_at": _now(),
        "updated_at": _now(),
        "app_version": APP_VERSION,
        "title": _safe_text(payload.get("title"), "Replay Dataset"),
        "description": _safe_text(payload.get("description"), "Local-first replay dataset manifest built from read-only snapshots."),
        "dataset_type": _safe_text(payload.get("dataset_type"), "replay_dataset"),
        "included_snapshot_ids": [s.get("snapshot_id") for s in snapshots],
        "included_subsystems": sorted({str(s.get("source_subsystem")) for s in snapshots}),
        "date_range": payload.get("date_range", {"start": payload.get("start"), "end": payload.get("end")}),
        "market_scope": payload.get("markets", []),
        "thesis_scope": payload.get("theses", []),
        "collection_assumptions": {"include_demo_data": include_demo, "quality_threshold": payload.get("quality_threshold", "usable"), "local_first": True, "read_only": True},
        "validation_results": {"snapshot_count": len(snapshots), "malformed_snapshot_count": quality["malformed_snapshot_count"]},
        "quality_score": quality["quality_score"],
        "quality_status": quality["quality_status"],
        "warnings": [f.get("title") for f in quality["findings"] if f.get("severity") in {"warning", "blocker", "critical"}],
        "limitations": ["Dataset quality depends on local snapshots available at build time.", "Read-only snapshot collection does not guarantee future market behavior or trading results."],
        "unknown_unavailable_fields": quality.get("missing_expected_snapshot_types", []) + (["some snapshot fields unknown/unavailable"] if quality.get("unknown_unavailable_field_count") else []),
        "provenance_summary": {"snapshot_count": len(snapshots), "provenance_count": len(list_provenance(limit=5000).get("items", [])), "payload_hashes_present": sum(1 for s in snapshots if s.get("payload_hash"))},
        "export_paths": [],
        "audit_metadata": {"read_only": True, "network_attempted": False},
        **_safety(),
    }
    _write_jsonl(DATASET_MANIFESTS_PATH, dataset)
    quality_report = {"quality_report_id": _record_id("quality"), "created_at": _now(), "app_version": APP_VERSION, "dataset_id": dataset["dataset_id"], **quality, **_safety()}
    _write_jsonl(QUALITY_REPORTS_PATH, quality_report)
    prov = _create_provenance({"dataset_id": dataset["dataset_id"], "source_subsystem": "dataset_builder", "source_name": dataset["title"], "collection_mode": "local-derived", "created_at": dataset["created_at"], "payload_hash": _payload_hash(dataset), "redaction_status": "redacted"}, "dataset_manifest_built")
    dataset["provenance_record_id"] = prov["provenance_id"]
    _write_jsonl(DATASET_MANIFESTS_PATH, dataset)
    _audit("dataset_manifest_built", "ok", {"dataset_id": dataset["dataset_id"], "snapshot_count": len(snapshots), "quality_status": dataset["quality_status"]})
    return redact_data({"ok": True, "manifest": dataset, "quality_report": quality_report, **_safety()})


def list_dataset_manifests(limit: int = 250) -> dict[str, Any]:
    rows = _latest_by_id(_read_jsonl(DATASET_MANIFESTS_PATH), "dataset_id")[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(rows), "items": redact_data(rows), **_safety()}


def get_dataset_manifest(dataset_id: str) -> dict[str, Any] | None:
    return next((row for row in list_dataset_manifests(limit=5000).get("items", []) if row.get("dataset_id") == dataset_id), None)


def validate_dataset_manifest(dataset_id: str | None = None, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = redact_data(manifest or (get_dataset_manifest(dataset_id or "") or {}))
    findings: list[dict[str, Any]] = []
    status = "pass"
    for key in ("dataset_id", "created_at", "app_version", "included_snapshot_ids", "quality_score", "quality_status", "provenance_summary"):
        if manifest.get(key) in (None, "", []):
            findings.append({"severity": "warning", "title": f"Missing {key}", "recommended_operator_action": "Rebuild or inspect dataset manifest before use."})
            if status == "pass":
                status = "warning"
    if manifest.get("quality_status") in {"blocked", "incomplete", "unknown"}:
        findings.append({"severity": "blocker", "title": "Dataset quality is not replay-ready", "recommended_operator_action": "Collect missing snapshots or validate imported data first."})
        status = "fail"
    if not findings:
        findings.append({"severity": "info", "title": "Dataset manifest validated", "recommended_operator_action": "Review provenance and limitations before simulation."})
    _audit("dataset_manifest_validated", "ok" if status != "fail" else "warning", {"dataset_id": manifest.get("dataset_id"), "status": status})
    return redact_data({"version": APP_VERSION, "dataset_id": manifest.get("dataset_id"), "validation_status": status, "findings": findings, **_safety()})


def dataset_quality_report(dataset_id: str | None = None) -> dict[str, Any]:
    manifest = get_dataset_manifest(dataset_id or "") if dataset_id else None
    if manifest:
        snapshot_ids = set(manifest.get("included_snapshot_ids", []))
        snapshots = [s for s in list_snapshots(limit=5000).get("items", []) if s.get("snapshot_id") in snapshot_ids]
    else:
        snapshots = list_snapshots(limit=5000).get("items", [])
    quality = _quality_from_snapshots(snapshots)
    report = {"version": APP_VERSION, "quality_report_id": _record_id("quality"), "created_at": _now(), "dataset_id": dataset_id, "snapshot_count": len(snapshots), **quality, **_safety()}
    _write_jsonl(QUALITY_REPORTS_PATH, report)
    _audit("dataset_quality_report_generated", "ok", {"dataset_id": dataset_id, "quality_status": report["quality_status"]})
    return redact_data(report)


def list_quality_reports(limit: int = 250) -> dict[str, Any]:
    rows = list(reversed(_read_jsonl(QUALITY_REPORTS_PATH)))[: max(1, min(int(limit or 250), 5000))]
    return {"version": APP_VERSION, "count": len(rows), "items": redact_data(rows), **_safety()}


def replay_ready_datasets(limit: int = 250) -> dict[str, Any]:
    rows = [r for r in list_dataset_manifests(limit=5000).get("items", []) if r.get("quality_status") in {"excellent", "good", "usable", "partial"}]
    return {"version": APP_VERSION, "count": len(rows[:limit]), "items": redact_data(rows[: max(1, min(int(limit or 250), 5000))]), "readiness_criteria": ["quality_status is excellent/good/usable/partial", "operator reviews warnings before simulation"], **_safety()}


def datasets_summary() -> dict[str, Any]:
    snapshots = list_snapshots(limit=5000).get("items", [])
    manifests = list_dataset_manifests(limit=5000).get("items", [])
    runs = list_collection_runs(limit=5000).get("items", [])
    quality = _quality_from_snapshots(snapshots)
    stale_warnings = len([s for s in snapshots if s.get("quality_status") in {"stale", "incomplete", "blocked"}])
    return redact_data({"version": APP_VERSION, "generated_at": _now(), "snapshot_count": len(snapshots), "dataset_count": len(manifests), "collection_run_count": len(runs), "replay_ready_dataset_count": len([d for d in manifests if d.get("quality_status") in {"excellent", "good", "usable", "partial"}]), "latest_collection_run": runs[0] if runs else None, "latest_dataset": manifests[0] if manifests else None, "quality_status": quality["quality_status"], "quality_score": quality["quality_score"], "stale_dataset_warnings": stale_warnings, "missing_snapshot_warnings": len(quality.get("missing_expected_snapshot_types", [])), "next_recommended_dataset_action": "Collect a read-only local snapshot set and build a replay dataset before relying on simulation quality.", **_safety()})


def export_dataset_json(dataset_id: str | None = None) -> dict[str, Any]:
    manifest = get_dataset_manifest(dataset_id or "") if dataset_id else None
    data = {"version": APP_VERSION, "generated_at": _now(), "summary": datasets_summary(), "dataset": manifest, "manifests": [] if manifest else list_dataset_manifests(limit=1000).get("items", []), "snapshots": list_snapshots(limit=1000).get("items", []), "quality": dataset_quality_report(dataset_id), "provenance": list_provenance(limit=1000).get("items", []), **_safety()}
    _audit("dataset_exported", "ok", {"format": "json", "dataset_id": dataset_id})
    return redact_data(data)


def export_dataset_markdown(dataset_id: str | None = None) -> str:
    data = export_dataset_json(dataset_id)
    summary = data.get("summary", {})
    lines = [f"# v3.5 Dataset / Snapshot Report — {APP_VERSION}", "", f"Generated: {_now()}", "", "Datasets and snapshots are read-only workflow data. They do not place orders, cancel orders, arm live trading, or provide financial advice.", "", "## Summary"]
    for key in ("snapshot_count", "dataset_count", "replay_ready_dataset_count", "quality_status", "quality_score", "missing_snapshot_warnings"):
        lines.append(f"- **{key}:** {summary.get(key, 'unknown') if isinstance(summary, dict) else 'unknown'}")
    lines += ["", "## Quality Findings"]
    quality = data.get("quality", {}) if isinstance(data.get("quality"), dict) else {}
    for finding in quality.get("findings", []):
        lines.append(f"- **{finding.get('severity', 'info')}:** {finding.get('title', '')} — {finding.get('recommended_operator_action', '')}")
    lines += ["", "## Provenance", f"- Provenance records: {len(data.get('provenance', [])) if isinstance(data.get('provenance'), list) else 0}", "", "## Safety Statement", "No dataset output is an order, approval, live-trading authorization, or financial advice. Live order submission still requires existing backend gates."]
    _audit("dataset_exported", "ok", {"format": "markdown", "dataset_id": dataset_id})
    return "\n".join(lines) + "\n"


def export_csv(kind: str = "snapshots") -> str:
    kind = _safe_text(kind, "snapshots")
    if kind == "quality":
        rows = list_quality_reports(limit=1000).get("items", [])
        fieldnames = ["quality_report_id", "dataset_id", "quality_status", "quality_score", "snapshot_count", "created_at", "app_version", "order_submitted", "order_cancelled", "live_trading_armed"]
    elif kind == "provenance":
        rows = list_provenance(limit=1000).get("items", [])
        fieldnames = ["provenance_id", "snapshot_id", "dataset_id", "source_subsystem", "collection_mode", "collection_timestamp", "payload_hash", "redaction_status", "order_submitted", "order_cancelled", "live_trading_armed"]
    else:
        rows = list_snapshots(limit=1000).get("items", [])
        fieldnames = ["snapshot_id", "snapshot_type", "source_subsystem", "collection_mode", "market_id", "condition_id", "source_timestamp", "created_at", "validation_status", "quality_status", "payload_hash", "order_submitted", "order_cancelled", "live_trading_armed"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, "") for key in fieldnames})
    _audit("dataset_exported", "ok", {"format": "csv", "kind": kind})
    return output.getvalue()


def dataset_search_items(limit: int = 100) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for snap in list_snapshots(limit=limit).get("items", []):
        title = f"{_safe_text(snap.get('snapshot_type'), 'Snapshot').replace('_', ' ').title()} snapshot"
        rows.append({"result_id": f"dataset_snapshot:{snap.get('snapshot_id')}", "result_type": str(snap.get("snapshot_type") or "dataset_snapshot"), "title": title, "summary": json.dumps(snap.get("payload_summary", {}), default=str)[:500], "timestamp": snap.get("created_at", ""), "status": snap.get("quality_status", "unknown"), "tags": ["dataset", "snapshot", str(snap.get("snapshot_type"))], "quick_link": "/v3/datasets/snapshots", "search_text": f"{title} dataset snapshot provenance replay quality {snap.get('source_subsystem')}".lower(), "related": {"snapshot_id": snap.get("snapshot_id")}})
    for ds in list_dataset_manifests(limit=limit).get("items", []):
        title = _safe_text(ds.get("title"), "Replay Dataset")
        rows.append({"result_id": f"dataset_manifest:{ds.get('dataset_id')}", "result_type": "dataset_manifest", "title": title, "summary": _safe_text(ds.get("description")), "timestamp": ds.get("created_at", ""), "status": ds.get("quality_status", "unknown"), "tags": ["dataset", "manifest", "replay"], "quick_link": "/v3/datasets", "search_text": f"{title} replay dataset manifest quality provenance snapshots".lower(), "related": {"dataset_id": ds.get("dataset_id")}})
    return redact_data(rows[: max(1, min(int(limit or 100), 1000))])


def dataset_graph_nodes_edges() -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for item in dataset_search_items(limit=500):
        node_type = item.get("result_type", "dataset_object")
        if node_type not in {"dataset_manifest", "market_snapshot", "order_book_snapshot", "local_subsystem_snapshot", "dataset_quality_report", "provenance_record", "snapshot_collection_run", "replay_dataset"}:
            if str(node_type).endswith("snapshot") or "snapshot" in str(node_type):
                node_type = "market_snapshot" if "market" in str(item.get("result_type")) else ("order_book_snapshot" if "order_book" in str(item.get("result_type")) else "local_subsystem_snapshot")
        nodes.append({"node_id": item["result_id"], "node_type": node_type, "title": item["title"], "status": item.get("status", "unknown"), "timestamp": item.get("timestamp", ""), "tags": item.get("tags", []), "related_object_id": item["result_id"].split(":", 1)[-1], "summary": item.get("summary", ""), "safe_metadata": item.get("related", {})})
    for manifest in list_dataset_manifests(limit=500).get("items", []):
        for sid in manifest.get("included_snapshot_ids", [])[:250]:
            edges.append({"edge_id": _record_id("edge"), "source_node": f"dataset_manifest:{manifest.get('dataset_id')}", "target_node": f"dataset_snapshot:{sid}", "relationship_type": "included_in", "created_at": _now(), "safe_metadata": {"supports_replay": True, "supports_simulation": True}})
    return {"nodes": redact_data(nodes), "edges": redact_data(edges), "secret_values_returned": False}


def dataset_analytics_context() -> dict[str, Any]:
    summary = datasets_summary()
    return {"snapshot_count": summary.get("snapshot_count", 0), "dataset_count": summary.get("dataset_count", 0), "replay_ready_dataset_count": summary.get("replay_ready_dataset_count", 0), "stale_dataset_count": summary.get("stale_dataset_warnings", 0), "dataset_quality_status": summary.get("quality_status"), "dataset_quality_score": summary.get("quality_score"), "missing_snapshot_patterns": summary.get("missing_snapshot_warnings"), "collection_reliability": "local/manual only unless explicitly extended", "secret_values_returned": False}


def dataset_simulation_context(dataset_id: str | None = None) -> dict[str, Any]:
    manifest = get_dataset_manifest(dataset_id or "") if dataset_id else (replay_ready_datasets(limit=1).get("items", []) or [None])[0]
    return redact_data({"dataset_selected": bool(manifest), "dataset_id": manifest.get("dataset_id") if isinstance(manifest, dict) else None, "dataset_quality_status": manifest.get("quality_status") if isinstance(manifest, dict) else "unknown", "dataset_quality_score": manifest.get("quality_score") if isinstance(manifest, dict) else 0, "missing_snapshot_warnings": manifest.get("unknown_unavailable_fields", []) if isinstance(manifest, dict) else ["No replay dataset selected."], "dataset_provenance": manifest.get("provenance_summary", {}) if isinstance(manifest, dict) else {}, "dataset_limitations": manifest.get("limitations", []) if isinstance(manifest, dict) else [], **_safety()})


def dataset_workflow_context() -> dict[str, Any]:
    summary = datasets_summary()
    return {"dataset_quality_review": summary, "snapshot_freshness_review": {"latest_collection_run": summary.get("latest_collection_run"), "missing_snapshot_warnings": summary.get("missing_snapshot_warnings")}, "replay_dataset_readiness_review": replay_ready_datasets(limit=25), "secret_values_returned": False}


def build_dataset_settings() -> dict[str, Any]:
    defaults = {"version": APP_VERSION, "scheduled_collection_enabled": False, "manual_collection_default": True, "include_demo_data_by_default": True, "quality_threshold": "usable", "store_raw_payloads": False, "redact_payload_summaries": True, "external_market_collection_enabled": False, "order_book_capture_mode": "explicit_read_only_or_demo", **_safety()}
    if DATASET_SETTINGS_PATH.exists():
        try:
            current = json.loads(DATASET_SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            current = {}
        defaults.update(redact_data(current))
    return redact_data(defaults)


def update_dataset_settings(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    settings = build_dataset_settings()
    allowed = {"scheduled_collection_enabled", "manual_collection_default", "include_demo_data_by_default", "quality_threshold", "store_raw_payloads", "redact_payload_summaries", "external_market_collection_enabled", "order_book_capture_mode"}
    for key in allowed:
        if key in payload:
            settings[key] = payload[key]
    settings["scheduled_collection_enabled"] = False if not bool(payload.get("scheduled_collection_enabled", False)) else bool(payload.get("scheduled_collection_enabled"))
    settings["updated_at"] = _now()
    _ensure_dir()
    DATASET_SETTINGS_PATH.write_text(json.dumps(redact_data(settings), indent=2, sort_keys=True, default=str), encoding="utf-8")
    _audit("dataset_settings_changed", "ok", {"changed_keys": sorted(set(payload.keys()) & allowed)})
    return redact_data(settings)


def create_demo_dataset_records() -> dict[str, Any]:
    market = {"market_id": "DEMO-MARKET-DATASET", "condition_id": "DEMO-CONDITION-DATASET", "question": "DEMO: Will the fake dataset pass quality checks?", "outcomes": ["YES", "NO"], "status": "active", "source_timestamp": "2026-01-01T12:00:00+00:00", "category": "demo"}
    order_book = {"market_id": "DEMO-MARKET-DATASET", "condition_id": "DEMO-CONDITION-DATASET", "token_id": "DEMO-TOKEN-YES", "outcome": "YES", "bids": [[0.45, 100]], "asks": [[0.55, 120]], "best_bid": 0.45, "best_ask": 0.55, "source_timestamp": "2026-01-01T12:01:00+00:00"}
    collected = collect_snapshots({"collection_mode": "demo", "snapshot_types": ["market_metadata", "order_book", "local_strategy", "local_research", "local_monitoring", "local_portfolio", "local_governance", "local_analytics", "local_simulation", "data_health"], "market": market, "order_book": order_book, "notes": "Fake v3.5 dataset demo records."})
    manifest = build_dataset_manifest({"title": "DEMO Replay Dataset", "description": "Fake, secret-free replay-ready dataset for screenshots and manual QA.", "include_demo_data": True, "snapshot_types": ["market_metadata", "order_book", "local_strategy", "local_research", "local_monitoring", "local_portfolio", "local_governance", "local_analytics", "local_simulation", "data_health"]})
    return redact_data({"ok": True, "collected": collected, "manifest": manifest, "demo_data_is_fake": True, **_safety()})
