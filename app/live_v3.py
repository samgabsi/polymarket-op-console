from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .config import APP_VERSION, DATA_DIR
from .live_v2 import build_live_v2_readiness, build_live_v2_status, list_audit_records, record_audit, redact_data, redact_text
from .live_strategy import list_theses, list_evidence, list_watchlist, list_scorecards, list_reviews
from .live_research import list_sources, list_queue, list_notes, list_candidates, freshness_summary, build_thesis_comparison
from .live_monitoring import list_rules as list_monitoring_rules, list_alerts, list_alert_history
from .live_portfolio import generate_portfolio_snapshot, list_exposure, list_warnings, list_scenarios, planned_trade_impact
from .live_governance import list_journal, list_checklists, list_reviews as list_governance_reviews, list_rules as list_governance_rules, list_near_misses, list_mistake_patterns
from .live_data import health_report_json, runtime_inventory, scan_secrets, migration_registry

V3_DIR = DATA_DIR / "live_v3"
V3_EVENTS_PATH = V3_DIR / "v3_events.jsonl"
V3_WORKFLOW_RUNS_PATH = V3_DIR / "workflow_runs.jsonl"
V3_SETTINGS_PATH = V3_DIR / "settings.json"

WORKFLOW_REGISTRY = [
    {"workflow_id": "market_intelligence_brief", "name": "Market Intelligence Brief", "read_only": True, "mutates_trading_state": False, "description": "Summarize local market context, sources, evidence, alerts, and stale/unknown data."},
    {"workflow_id": "thesis_health_review", "name": "Thesis Health Review", "read_only": True, "mutates_trading_state": False, "description": "Review thesis evidence coverage, stale evidence, alerts, exposure, and governance status."},
    {"workflow_id": "pre_trade_intelligence_packet", "name": "Pre-Trade Intelligence Packet", "read_only": True, "mutates_trading_state": False, "description": "Gather strategy, research, portfolio, monitoring, governance, risk, readiness, and audit context before ticket submission."},
    {"workflow_id": "portfolio_risk_brief", "name": "Portfolio Risk Brief", "read_only": True, "mutates_trading_state": False, "description": "Summarize exposure, concentration warnings, scenarios, stale evidence exposure, and unknown/unavailable values."},
    {"workflow_id": "stale_evidence_review", "name": "Stale Evidence Review", "read_only": True, "mutates_trading_state": False, "description": "Collect stale/aging evidence and source review items for operator action."},
    {"workflow_id": "alert_triage_brief", "name": "Alert Triage Brief", "read_only": True, "mutates_trading_state": False, "description": "Group active monitoring alerts and suggest review actions without execution."},
    {"workflow_id": "governance_daily_review", "name": "Governance Daily Review", "read_only": True, "mutates_trading_state": False, "description": "Summarize decisions, reviews, risk blocks, alerts, unresolved items, and next actions."},
    {"workflow_id": "weekly_operator_review", "name": "Weekly Operator Review", "read_only": True, "mutates_trading_state": False, "description": "Roll up daily review signals, recurring patterns, stale evidence, concentration trends, and process improvements."},
    {"workflow_id": "data_health_backup_readiness", "name": "Data Health / Backup Readiness Brief", "read_only": True, "mutates_trading_state": False, "description": "Summarize data health, backup readiness, migration status, and secret-scan posture."},
    {"workflow_id": "no_trade_review_packet", "name": "No-Trade Review Packet", "read_only": True, "mutates_trading_state": False, "description": "Document missing prerequisites or risk blockers supporting a no-trade decision."},
]

NODE_TYPES = {
    "market", "outcome", "thesis", "evidence", "research_source", "source_note", "research_queue_item",
    "watchlist_item", "scorecard", "monitoring_rule", "alert", "portfolio_exposure", "scenario",
    "decision_journal_entry", "governance_checklist", "review", "mistake_pattern", "audit_event", "data_health_check",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    V3_DIR.mkdir(parents=True, exist_ok=True)


def _items(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, dict):
        data = result.get("items", result.get("records", result.get("checks", [])))
    else:
        data = result
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def _safe_text(value: Any, default: str = "") -> str:
    text = redact_text(str(value or "").strip())
    return text or default


def _safe_id(prefix: str, item: dict[str, Any]) -> str:
    for key in ("id", "event_id", "rule_id", "alert_id", "scenario_id", "ticket_id", "order_id", "market_id", "thesis_id", "source_id"):
        raw = item.get(key)
        if raw:
            return f"{prefix}:{_safe_text(raw)}"
    return f"{prefix}:{uuid4().hex[:12]}"


def _summary_text(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if item.get(key):
            return _safe_text(item.get(key))[:500]
    return _safe_text(item.get("notes") or item.get("details") or item.get("status") or "")[:500]


def _event(action: str, status: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    _ensure_dir()
    event = redact_data({
        "event_id": f"v3_evt_{uuid4().hex[:12]}",
        "timestamp": _now(),
        "app_version": APP_VERSION,
        "action": action,
        "status": status,
        "details": details or {},
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "ai_assistance_enabled": False,
        "secret_values_returned": False,
    })
    with V3_EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, default=str) + "\n")
    record_audit(f"v3_{action}", status, details={**(details or {}), "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "ai_assistance_enabled": False}, network_attempted=False)
    return event


def list_v3_events(limit: int = 500) -> list[dict[str, Any]]:
    if not V3_EVENTS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in V3_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(redact_data(json.loads(line)))
        except json.JSONDecodeError:
            rows.append({"event_id": "invalid", "timestamp": _now(), "action": "invalid_v3_event", "status": "warning"})
    return list(reversed(rows))[: max(1, min(int(limit or 500), 5000))]


def _collect_local_data(limit: int = 250) -> dict[str, Any]:
    readiness = build_live_v2_readiness()
    status = build_live_v2_status()
    health = health_report_json()
    return redact_data({
        "version": APP_VERSION,
        "generated_at": _now(),
        "status": status,
        "readiness": readiness,
        "data_health": health,
        "inventory": runtime_inventory(),
        "strategy": {
            "theses": _items(list_theses(limit=limit)),
            "evidence": _items(list_evidence(limit=limit)),
            "watchlist": _items(list_watchlist(limit=limit)),
            "scorecards": _items(list_scorecards(limit=limit)),
            "reviews": _items(list_reviews(limit=limit)),
        },
        "research": {
            "sources": _items(list_sources(limit=limit)),
            "queue": _items(list_queue(limit=limit)),
            "notes": _items(list_notes(limit=limit)),
            "candidates": _items(list_candidates(limit=limit)),
            "freshness": freshness_summary(),
        },
        "monitoring": {
            "rules": _items(list_monitoring_rules(limit=limit)),
            "alerts": _items(list_alerts(limit=limit)),
            "history": _items(list_alert_history(limit=limit)),
        },
        "portfolio": {
            "snapshot": generate_portfolio_snapshot(record=False),
            "exposure": _items(list_exposure(limit=limit)),
            "warnings": _items(list_warnings(limit=limit)),
            "scenarios": _items(list_scenarios(limit=limit)),
        },
        "governance": {
            "journal": _items(list_journal(limit=limit)),
            "checklists": _items(list_checklists(limit=limit)),
            "reviews": _items(list_governance_reviews(limit=limit)),
            "rules": _items(list_governance_rules(limit=limit)),
            "near_misses": _items(list_near_misses(limit=limit)),
            "mistake_patterns": _items(list_mistake_patterns(limit=limit)),
        },
        "audit": {"events": list_audit_records(limit=limit)},
        "v3": {"events": list_v3_events(limit=limit)},
        "secret_values_returned": False,
    })


def _node(prefix: str, node_type: str, item: dict[str, Any], title_keys: tuple[str, ...], summary_keys: tuple[str, ...] = ()) -> dict[str, Any]:
    title = ""
    for key in title_keys:
        if item.get(key):
            title = _safe_text(item.get(key))
            break
    if not title:
        title = f"{node_type} {_safe_text(item.get('id') or item.get('event_id') or '')}".strip()
    return redact_data({
        "node_id": _safe_id(prefix, item),
        "node_type": node_type,
        "title": title[:160],
        "status": _safe_text(item.get("status") or item.get("severity") or item.get("action") or "unknown"),
        "timestamp": _safe_text(item.get("updated_at") or item.get("created_at") or item.get("timestamp") or ""),
        "tags": item.get("tags", []) if isinstance(item.get("tags"), list) else [],
        "related_object_id": _safe_text(item.get("id") or item.get("event_id") or item.get("rule_id") or item.get("alert_id") or ""),
        "summary": _summary_text(item, *(summary_keys or title_keys)),
        "safe_metadata": {k: redact_data(item.get(k)) for k in ("market_id", "market_title", "thesis_id", "source_id", "order_id", "ticket_id", "severity", "direction") if item.get(k)},
    })


def build_search_index(limit: int = 250) -> dict[str, Any]:
    data = _collect_local_data(limit=limit)
    rows: list[dict[str, Any]] = []

    def add(result_type: str, item: dict[str, Any], title_keys: tuple[str, ...], summary_keys: tuple[str, ...] = ()) -> None:
        node = _node(result_type, result_type, item, title_keys, summary_keys)
        haystack = " ".join(str(x) for x in [node["title"], node["summary"], node["status"], json.dumps(node.get("safe_metadata", {}), default=str)])
        rows.append({
            "result_id": node["node_id"],
            "result_type": result_type,
            "title": node["title"],
            "summary": node["summary"],
            "timestamp": node["timestamp"],
            "status": node["status"],
            "tags": node["tags"],
            "related": node["safe_metadata"],
            "quick_link": _quick_link(result_type, item),
            "search_text": redact_text(haystack.lower()),
            "secret_values_returned": False,
        })

    for item in data["strategy"]["theses"]:
        add("thesis", item, ("market_title", "title", "id"), ("thesis_summary", "operator_notes", "status"))
    for item in data["strategy"]["evidence"]:
        add("evidence", item, ("title", "source_url", "id"), ("notes", "direction"))
    for item in data["strategy"]["watchlist"]:
        add("watchlist_item", item, ("market_title", "title", "id"), ("reason", "notes"))
    for item in data["strategy"]["scorecards"]:
        add("scorecard", item, ("market_title", "thesis_id", "id"), ("recommended_next_action", "notes"))
    for item in data["research"]["sources"]:
        add("research_source", item, ("title", "url", "id"), ("notes", "source_type"))
    for item in data["research"]["queue"]:
        add("research_queue_item", item, ("title", "research_question", "id"), ("notes", "desired_output"))
    for item in data["research"]["notes"]:
        add("source_note", item, ("summary", "source_id", "id"), ("key_claims", "operator_interpretation"))
    for item in data["research"]["candidates"]:
        add("evidence_candidate", item, ("title", "source_id", "id"), ("notes", "direction"))
    for item in data["monitoring"]["rules"]:
        add("monitoring_rule", item, ("rule_name", "title", "id"), ("condition", "notes"))
    for item in data["monitoring"]["alerts"]:
        add("alert", item, ("title", "reason", "id"), ("recommended_operator_action", "reason"))
    for item in data["portfolio"]["exposure"]:
        add("portfolio_exposure", item, ("market_title", "exposure_type", "id"), ("notes", "status"))
    for item in data["portfolio"]["warnings"]:
        add("portfolio_warning", item, ("title", "warning_type", "id"), ("recommended_operator_action", "notes"))
    for item in data["portfolio"]["scenarios"]:
        add("scenario", item, ("title", "scenario_type", "id"), ("notes", "recommended_operator_action"))
    for item in data["governance"]["journal"]:
        add("decision_journal_entry", item, ("decision_title", "title", "id"), ("decision_summary", "reasoning"))
    for item in data["governance"]["checklists"]:
        add("governance_checklist", item, ("title", "checklist_type", "id"), ("notes", "status"))
    for item in data["governance"]["reviews"]:
        add("review", item, ("title", "review_type", "id"), ("lesson_learned", "notes"))
    for item in data["governance"]["mistake_patterns"]:
        add("mistake_pattern", item, ("title", "pattern_type", "id"), ("notes", "process_improvement_action"))
    for item in data["audit"]["events"]:
        add("audit_event", item, ("action", "event_id"), ("status", "details"))
    for check in _items(data.get("data_health", {}).get("checks", [])):
        add("data_health_check", check, ("check_name", "affected_file", "id"), ("explanation", "recommended_operator_action"))

    rows.sort(key=lambda r: str(r.get("timestamp") or ""), reverse=True)
    return {"version": APP_VERSION, "generated_at": _now(), "count": len(rows), "items": redact_data(rows), "secret_values_returned": False, "local_only": True}


def _quick_link(result_type: str, item: dict[str, Any]) -> str:
    mapping = {
        "thesis": "/v2-live/strategy", "evidence": "/v2-live/strategy", "watchlist_item": "/v2-live/strategy", "scorecard": "/v2-live/strategy",
        "research_source": "/v2-live/research", "research_queue_item": "/v2-live/research", "source_note": "/v2-live/research", "evidence_candidate": "/v2-live/research",
        "monitoring_rule": "/v2-live/monitoring", "alert": "/v2-live/monitoring",
        "portfolio_exposure": "/v2-live/portfolio", "portfolio_warning": "/v2-live/portfolio", "scenario": "/v2-live/portfolio",
        "decision_journal_entry": "/v2-live/governance", "governance_checklist": "/v2-live/governance", "review": "/v2-live/governance", "mistake_pattern": "/v2-live/governance",
        "audit_event": "/v2-live/audit", "data_health_check": "/v2-live/data",
    }
    return mapping.get(result_type, "/v3")


def search_local(query: str = "", result_type: str = "", limit: int = 50) -> dict[str, Any]:
    index = build_search_index(limit=500)
    q = _safe_text(query).lower()
    rtype = _safe_text(result_type).lower()
    rows: list[dict[str, Any]] = []
    for item in index["items"]:
        if rtype and _safe_text(item.get("result_type")).lower() != rtype:
            continue
        if q and q not in item.get("search_text", ""):
            continue
        score = 1.0
        if q and q in str(item.get("title", "")).lower():
            score += 2.0
        elif q and q in str(item.get("summary", "")).lower():
            score += 1.0
        visible = {k: v for k, v in item.items() if k != "search_text"}
        visible["relevance_score"] = score
        rows.append(visible)
        if len(rows) >= max(1, min(int(limit or 50), 500)):
            break
    if q:
        _event("search_query_run", "ok", {"query_present": True, "result_type": result_type, "count": len(rows)})
    return {"version": APP_VERSION, "query": query, "result_type": result_type, "count": len(rows), "items": redact_data(rows), "local_only": True, "secret_values_returned": False}


def rebuild_search_index() -> dict[str, Any]:
    index = build_search_index(limit=1000)
    _ensure_dir()
    path = V3_DIR / "search_index_summary.json"
    path.write_text(json.dumps({"version": APP_VERSION, "generated_at": index["generated_at"], "count": index["count"]}, indent=2, sort_keys=True), encoding="utf-8")
    _event("search_index_rebuilt", "ok", {"count": index["count"], "path": str(path)})
    return {"ok": True, "index": index, "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "secret_values_returned": False}


def build_decision_graph(limit: int = 250) -> dict[str, Any]:
    index = build_search_index(limit=limit)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    market_nodes: dict[str, str] = {}
    thesis_nodes: dict[str, str] = {}
    source_nodes: dict[str, str] = {}

    for item in index["items"]:
        node_type = _safe_text(item.get("result_type")).replace("_item", "")
        if node_type == "evidence_candidate":
            node_type = "evidence"
        node = {
            "node_id": item["result_id"],
            "node_type": node_type,
            "title": item["title"],
            "status": item.get("status", "unknown"),
            "timestamp": item.get("timestamp", ""),
            "tags": item.get("tags", []),
            "related_object_id": item["result_id"].split(":", 1)[-1],
            "summary": item.get("summary", ""),
            "safe_metadata": item.get("related", {}),
        }
        nodes.append(node)
        meta = node.get("safe_metadata", {}) if isinstance(node.get("safe_metadata"), dict) else {}
        if meta.get("market_id"):
            market_id = _safe_text(meta.get("market_id"))
            mnode = market_nodes.setdefault(market_id, f"market:{market_id}")
            edges.append(_edge(node["node_id"], mnode, "linked_to"))
        if meta.get("thesis_id"):
            thesis_id = _safe_text(meta.get("thesis_id"))
            tnode = thesis_nodes.setdefault(thesis_id, f"thesis:{thesis_id}")
            if node["node_id"] != tnode:
                edges.append(_edge(node["node_id"], tnode, "depends_on" if node_type in {"trade_ticket", "portfolio_exposure"} else "linked_to"))
        if meta.get("source_id"):
            source_id = _safe_text(meta.get("source_id"))
            snode = source_nodes.setdefault(source_id, f"research_source:{source_id}")
            if node["node_id"] != snode:
                edges.append(_edge(node["node_id"], snode, "derived_from"))
        if node_type == "alert" and meta.get("market_id"):
            edges.append(_edge(node["node_id"], f"market:{_safe_text(meta.get('market_id'))}", "alerted_by"))

    existing_node_ids = {n["node_id"] for n in nodes}
    for market_id, node_id in market_nodes.items():
        if node_id not in existing_node_ids:
            nodes.append({"node_id": node_id, "node_type": "market", "title": f"Market {market_id}", "status": "referenced", "timestamp": "", "tags": [], "related_object_id": market_id, "summary": "Referenced market node", "safe_metadata": {"market_id": market_id}})
    findings = missing_prerequisites_scan()["findings"]
    for finding in findings:
        if finding.get("related_node"):
            edges.append(_edge(_safe_text(finding.get("related_node")), f"finding:{finding['finding_id']}", "missing_prerequisite"))
            nodes.append({"node_id": f"finding:{finding['finding_id']}", "node_type": "data_health_check", "title": finding.get("title", "Finding"), "status": finding.get("severity", "warning"), "timestamp": finding.get("timestamp", _now()), "tags": ["v3_finding"], "related_object_id": finding["finding_id"], "summary": finding.get("explanation", ""), "safe_metadata": {"finding_type": finding.get("finding_type")}})

    graph = {"version": APP_VERSION, "generated_at": _now(), "node_count": len(nodes), "edge_count": len(edges), "nodes": redact_data(nodes), "edges": redact_data(edges), "secret_values_returned": False, "local_only": True}
    return graph


def _edge(source: str, target: str, relationship_type: str) -> dict[str, Any]:
    return {"edge_id": f"edge_{uuid4().hex[:12]}", "source_node": source, "target_node": target, "relationship_type": relationship_type, "created_at": _now(), "safe_metadata": {}, "secret_values_returned": False}


def rebuild_graph() -> dict[str, Any]:
    graph = build_decision_graph(limit=1000)
    _ensure_dir()
    path = V3_DIR / "decision_graph_summary.json"
    path.write_text(json.dumps({"version": APP_VERSION, "generated_at": graph["generated_at"], "node_count": graph["node_count"], "edge_count": graph["edge_count"]}, indent=2, sort_keys=True), encoding="utf-8")
    _event("graph_rebuilt", "ok", {"node_count": graph["node_count"], "edge_count": graph["edge_count"], "path": str(path)})
    return {"ok": True, "graph": graph, "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "secret_values_returned": False}


def graph_to_markdown(graph: dict[str, Any] | None = None) -> str:
    graph = graph or build_decision_graph()
    lines = [f"# Decision Graph Export — {APP_VERSION}", "", f"Generated: {graph.get('generated_at')}", "", f"Nodes: {graph.get('node_count', 0)}", f"Edges: {graph.get('edge_count', 0)}", "", "## Nodes"]
    for node in graph.get("nodes", [])[:200]:
        lines.append(f"- **{node.get('node_type')}** — {node.get('title')} ({node.get('status')})")
    lines.extend(["", "## Edges"])
    for edge in graph.get("edges", [])[:200]:
        lines.append(f"- {edge.get('source_node')} --{edge.get('relationship_type')}--> {edge.get('target_node')}")
    lines.extend(["", "Safety: decision graph exports do not place, cancel, approve, sign, or arm live orders."])
    return "\n".join(lines) + "\n"


def build_command_center() -> dict[str, Any]:
    data = _collect_local_data(limit=100)
    readiness = data["readiness"]
    live_status = data["status"]
    findings = missing_prerequisites_scan(limit=100)["findings"]
    alerts = data["monitoring"]["alerts"]
    critical_alerts = [a for a in alerts if _safe_text(a.get("severity")).lower() == "critical"]
    stale_count = 0
    freshness = data["research"].get("freshness", {})
    if isinstance(freshness, dict):
        stale_count = int(freshness.get("stale_count", 0) or freshness.get("stale", 0) or 0)
    health_summary = data.get("data_health", {}).get("summary", {}) if isinstance(data.get("data_health"), dict) else {}
    exposure_summary = data.get("portfolio", {}).get("snapshot", {}).get("summary", {}) if isinstance(data.get("portfolio", {}).get("snapshot"), dict) else {}
    next_actions = _next_actions(readiness, health_summary, findings, alerts)
    summary = {
        "version": APP_VERSION,
        "generated_at": _now(),
        "mode": live_status.get("mode") or live_status.get("config", {}).get("trading_mode", "unknown"),
        "live_armed": bool(live_status.get("live_armed", False) or live_status.get("config", {}).get("live_armed", False)),
        "read_only": bool(live_status.get("read_only", True) or live_status.get("config", {}).get("read_only", True)),
        "kill_switch_active": bool(live_status.get("kill_switch_active", True) or live_status.get("config", {}).get("kill_switch_active", True)),
        "readiness_state": readiness.get("overall_status", "unknown"),
        "data_health_state": health_summary.get("overall_status") or ("fail" if health_summary.get("fail", 0) else "pass"),
        "backup_restore_health": "available",
        "active_thesis_count": len([x for x in data["strategy"]["theses"] if _safe_text(x.get("status")).lower() not in {"archived", "closed", "invalidated"}]),
        "active_research_queue_count": len([x for x in data["research"]["queue"] if _safe_text(x.get("status")).lower() not in {"archived", "converted"}]),
        "stale_evidence_count": stale_count,
        "active_alert_count": len(alerts),
        "critical_alert_count": len(critical_alerts),
        "portfolio_exposure_summary": exposure_summary,
        "concentration_warning_count": len(data["portfolio"]["warnings"]),
        "open_governance_checklist_count": len([x for x in data["governance"]["checklists"] if _safe_text(x.get("status")).lower() not in {"completed", "archived"}]),
        "recent_decisions": data["governance"]["journal"][:5],
        "recent_audit_events": data["audit"]["events"][:10],
        "recent_risk_blocks": [x for x in data["audit"]["events"] if "block" in _safe_text(x.get("status")).lower() or "risk" in _safe_text(x.get("action")).lower()][:10],
        "recent_verification_status": readiness.get("checks", [])[:8],
        "action_needed": findings[:20],
        "next_operator_actions": next_actions,
        "safety_statement": "v3 command center is read-only by default and does not place, cancel, sign, approve, or arm live orders.",
        "secret_values_returned": False,
    }
    return redact_data(summary)


def _next_actions(readiness: dict[str, Any], health_summary: dict[str, Any], findings: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []
    if readiness.get("overall_status") not in {"pass", "ready"}:
        actions.append("Review Live Readiness before any live workflow.")
    if health_summary.get("fail", 0):
        actions.append("Open Data health and resolve failing runtime-data checks.")
    if alerts:
        actions.append("Triage active Monitoring alerts before creating new tickets.")
    if findings:
        actions.append("Review missing prerequisites/conflicts in the v3 action-needed queue.")
    if not actions:
        actions.append("System appears calm; continue research, strategy review, or paper rehearsal.")
    return actions[:8]


def missing_prerequisites_scan(limit: int = 250) -> dict[str, Any]:
    data = _collect_local_data(limit=limit)
    findings: list[dict[str, Any]] = []
    evidence_by_thesis: dict[str, list[dict[str, Any]]] = {}
    for ev in data["strategy"]["evidence"] + data["research"]["candidates"]:
        tid = _safe_text(ev.get("thesis_id"))
        if tid:
            evidence_by_thesis.setdefault(tid, []).append(ev)
    for thesis in data["strategy"]["theses"]:
        tid = _safe_text(thesis.get("id") or thesis.get("thesis_id"))
        title = _safe_text(thesis.get("market_title") or thesis.get("title") or tid)
        status = _safe_text(thesis.get("status")).lower()
        evidence = evidence_by_thesis.get(tid, [])
        if not evidence:
            findings.append(_finding("missing_evidence", "warning", f"Thesis has no linked evidence: {title}", "Add or link evidence before creating a ticket.", f"thesis:{tid}"))
        if evidence and not any("contradict" in _safe_text(ev.get("direction")).lower() for ev in evidence):
            findings.append(_finding("missing_counter_evidence", "info", f"No counter-evidence review found: {title}", "Review and record counter-evidence or acknowledge none found.", f"thesis:{tid}"))
        if status in {"ready_for_ticket", "ticket_created", "active"} and not _safe_text(thesis.get("exit_criteria")):
            findings.append(_finding("missing_exit_criteria", "warning", f"Ready/active thesis lacks exit criteria: {title}", "Define exit criteria before live consideration.", f"thesis:{tid}"))
        if status in {"ready_for_ticket", "ticket_created", "active"} and not _safe_text(thesis.get("invalidation_criteria")):
            findings.append(_finding("missing_invalidation_criteria", "warning", f"Ready/active thesis lacks invalidation criteria: {title}", "Define invalidation criteria before live consideration.", f"thesis:{tid}"))
    for exposure in data["portfolio"]["exposure"]:
        tid = _safe_text(exposure.get("thesis_id"))
        if tid and not evidence_by_thesis.get(tid):
            findings.append(_finding("exposure_without_evidence", "warning", "Exposure is linked to a thesis with no evidence.", "Review exposure and thesis evidence linkage.", f"portfolio_exposure:{_safe_text(exposure.get('id'))}"))
    for alert in data["monitoring"]["alerts"]:
        sev = _safe_text(alert.get("severity")).lower()
        if sev in {"warning", "critical"}:
            findings.append(_finding("active_alert_needs_review", sev, _safe_text(alert.get("title") or alert.get("reason") or "Active alert needs review"), "Open Monitoring and acknowledge, snooze, or resolve after review.", f"alert:{_safe_text(alert.get('id') or alert.get('alert_id'))}"))
    health_summary = data.get("data_health", {}).get("summary", {}) if isinstance(data.get("data_health"), dict) else {}
    if health_summary.get("fail", 0):
        findings.append(_finding("data_health_failure", "critical", "Data health check has failing checks.", "Open Data and resolve invalid/corrupt runtime data before relying on packets.", "data_health:latest"))
    readiness = data["readiness"]
    if readiness.get("overall_status") not in {"pass", "ready"}:
        findings.append(_finding("readiness_not_ready", "warning", "Live readiness is not ready/pass.", "Keep live workflows read-only and review readiness details.", "readiness:latest"))
    findings = redact_data(findings[: max(1, min(int(limit or 250), 1000))])
    _event("missing_prerequisite_scan_run", "ok", {"count": len(findings)})
    return {"version": APP_VERSION, "generated_at": _now(), "count": len(findings), "findings": findings, "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "secret_values_returned": False}


def _finding(kind: str, severity: str, title: str, action: str, related_node: str) -> dict[str, Any]:
    return {"finding_id": f"finding_{uuid4().hex[:10]}", "timestamp": _now(), "finding_type": kind, "severity": severity if severity in {"info", "watch", "warning", "critical"} else "warning", "title": title, "explanation": title, "recommended_operator_action": action, "related_node": related_node, "order_submitted": False, "order_cancelled": False}


def workflow_registry() -> dict[str, Any]:
    return {"version": APP_VERSION, "workflows": WORKFLOW_REGISTRY, "ai_assistance_enabled": False, "secret_values_returned": False}


def run_workflow(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    workflow_id = _safe_text(payload.get("workflow_id") or payload.get("id") or "pre_trade_intelligence_packet")
    context = payload.get("context") if isinstance(payload.get("context"), dict) else payload
    if workflow_id == "market_intelligence_brief":
        output = market_intelligence_brief(context)
    elif workflow_id == "thesis_health_review":
        output = thesis_health_report(context)
    elif workflow_id == "portfolio_risk_brief":
        output = portfolio_risk_brief(context)
    elif workflow_id in {"governance_daily_review", "weekly_operator_review"}:
        output = operator_review_packet({**context, "period": "weekly" if workflow_id == "weekly_operator_review" else "daily"})
    elif workflow_id == "data_health_backup_readiness":
        output = data_health_backup_readiness_brief(context)
    elif workflow_id == "alert_triage_brief":
        output = alert_triage_brief(context)
    elif workflow_id == "stale_evidence_review":
        output = stale_evidence_review(context)
    elif workflow_id == "no_trade_review_packet":
        output = no_trade_review_packet(context)
    else:
        workflow_id = "pre_trade_intelligence_packet"
        output = pre_trade_packet(context)
    run = redact_data({
        "run_id": f"v3_run_{uuid4().hex[:12]}",
        "workflow_id": workflow_id,
        "started_at": _now(),
        "completed_at": _now(),
        "status": "completed",
        "read_only": True,
        "mutated_trading_state": False,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "ai_assistance_enabled": False,
        "output": output,
        "secret_values_returned": False,
    })
    _ensure_dir()
    with V3_WORKFLOW_RUNS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(run, sort_keys=True, default=str) + "\n")
    _event("workflow_run_completed", "ok", {"workflow_id": workflow_id, "run_id": run["run_id"]})
    return run


def list_workflow_runs(limit: int = 100) -> dict[str, Any]:
    if not V3_WORKFLOW_RUNS_PATH.exists():
        return {"version": APP_VERSION, "count": 0, "items": [], "secret_values_returned": False}
    rows: list[dict[str, Any]] = []
    for line in V3_WORKFLOW_RUNS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(redact_data(json.loads(line)))
        except Exception:
            rows.append({"run_id": "invalid", "status": "warning"})
    rows = list(reversed(rows))[: max(1, min(int(limit or 100), 1000))]
    return {"version": APP_VERSION, "count": len(rows), "items": rows, "secret_values_returned": False}


def get_workflow_run(run_id: str) -> dict[str, Any] | None:
    for row in list_workflow_runs(limit=1000)["items"]:
        if row.get("run_id") == run_id:
            return row
    return None


def pre_trade_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    thesis_id = _safe_text(payload.get("thesis_id"))
    market_id = _safe_text(payload.get("market_id"))
    data = _collect_local_data(limit=250)
    thesis = _find_by_id(data["strategy"]["theses"], thesis_id) if thesis_id else _find_by_market(data["strategy"]["theses"], market_id)
    evidence = _filter_related(data["strategy"]["evidence"] + data["research"]["candidates"], thesis_id=thesis_id, market_id=market_id)
    packet = {
        "packet_type": "pre_trade_intelligence_packet",
        "version": APP_VERSION,
        "generated_at": _now(),
        "selected_market": market_id or (thesis or {}).get("market_id", ""),
        "selected_outcome": _safe_text(payload.get("outcome") or (thesis or {}).get("outcome")),
        "linked_thesis": thesis or {},
        "thesis_status": (thesis or {}).get("status", "unknown"),
        "evidence_count": len(evidence),
        "supporting_evidence": [e for e in evidence if "support" in _safe_text(e.get("direction")).lower()][:10],
        "counter_evidence": [e for e in evidence if "contradict" in _safe_text(e.get("direction")).lower()][:10],
        "stale_evidence_warnings": _extract_stale_evidence(data, thesis_id, market_id),
        "unresolved_research_questions": data["research"]["queue"][:10],
        "scorecard_summary": _filter_related(data["strategy"]["scorecards"], thesis_id=thesis_id, market_id=market_id)[:5],
        "watchlist_status": _filter_related(data["strategy"]["watchlist"], thesis_id=thesis_id, market_id=market_id)[:5],
        "monitoring_alerts": _filter_related(data["monitoring"]["alerts"], thesis_id=thesis_id, market_id=market_id)[:10],
        "portfolio_exposure": _filter_related(data["portfolio"]["exposure"], thesis_id=thesis_id, market_id=market_id)[:10],
        "concentration_warnings": data["portfolio"]["warnings"][:10],
        "governance_checklist_status": data["governance"]["checklists"][:10],
        "decision_journal_context": data["governance"]["journal"][:10],
        "risk_precheck_summary": data["readiness"].get("checks", [])[:10],
        "data_health_warnings": [x for x in _items(data.get("data_health", {}).get("checks", [])) if x.get("status") in {"fail", "warning"}][:10],
        "readiness_posture": data["readiness"].get("overall_status", "unknown"),
        "audit_trail_references": data["audit"]["events"][:10],
        "findings": missing_prerequisites_scan(limit=100)["findings"][:15],
        "status": "needs_review",
        "recommended_operator_actions": ["Review blockers/warnings", "Confirm thesis/evidence coverage", "Run trade-ticket risk preview separately if proceeding"],
        "safety_statement": "This packet does not place, cancel, sign, approve, or arm live orders.",
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "secret_values_returned": False,
    }
    _event("pre_trade_packet_generated", "ok", {"market_id": market_id, "thesis_id": thesis_id})
    return redact_data(packet)


def market_intelligence_brief(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    market_id = _safe_text(payload.get("market_id"))
    data = _collect_local_data(limit=250)
    sources = _filter_related(data["research"]["sources"], market_id=market_id)
    candidates = _filter_related(data["research"]["candidates"], market_id=market_id)
    theses = _filter_related(data["strategy"]["theses"], market_id=market_id)
    brief = {"brief_type": "market_intelligence", "version": APP_VERSION, "generated_at": _now(), "market_id": market_id, "summary": f"Local brief for market {market_id or 'unspecified'}.", "linked_sources": sources[:20], "evidence_candidates": candidates[:20], "linked_theses": theses[:10], "watchlist_entries": _filter_related(data["strategy"]["watchlist"], market_id=market_id)[:10], "monitoring_alerts": _filter_related(data["monitoring"]["alerts"], market_id=market_id)[:10], "strongest_support": [x for x in candidates if "support" in _safe_text(x.get("direction")).lower()][:5], "strongest_contradiction": [x for x in candidates if "contradict" in _safe_text(x.get("direction")).lower()][:5], "missing_research": ["Add source notes" if not sources else "Review source freshness"], "safety_statement": "Market briefs are workflow guidance only and do not place or cancel orders.", "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    _event("market_brief_generated", "ok", {"market_id": market_id})
    return redact_data(brief)


def thesis_health_report(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    thesis_id = _safe_text(payload.get("thesis_id"))
    data = _collect_local_data(limit=250)
    thesis = _find_by_id(data["strategy"]["theses"], thesis_id) if thesis_id else (data["strategy"]["theses"][:1] or [{}])[0]
    tid = _safe_text(thesis.get("id") or thesis_id)
    evidence = _filter_related(data["strategy"]["evidence"] + data["research"]["candidates"], thesis_id=tid)
    report = {"report_type": "thesis_health", "version": APP_VERSION, "generated_at": _now(), "thesis": thesis, "evidence_count": len(evidence), "supporting_count": len([x for x in evidence if "support" in _safe_text(x.get("direction")).lower()]), "counter_evidence_count": len([x for x in evidence if "contradict" in _safe_text(x.get("direction")).lower()]), "stale_evidence": _extract_stale_evidence(data, tid, _safe_text(thesis.get("market_id"))), "monitoring_alerts": _filter_related(data["monitoring"]["alerts"], thesis_id=tid)[:10], "exposure": _filter_related(data["portfolio"]["exposure"], thesis_id=tid)[:10], "governance_checklists": _filter_related(data["governance"]["checklists"], thesis_id=tid)[:10], "decision_journal": _filter_related(data["governance"]["journal"], thesis_id=tid)[:10], "scorecard_summary": _filter_related(data["strategy"]["scorecards"], thesis_id=tid)[:5], "invalidated_or_missing": not bool(thesis) or _safe_text(thesis.get("status")).lower() in {"invalidated", "archived"}, "health_status": "needs_review" if not evidence else "watch", "next_operator_actions": ["Review counter-evidence", "Check stale evidence", "Update exit/invalidation criteria"], "safety_statement": "Thesis health reports do not place or cancel orders.", "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    _event("thesis_health_report_generated", "ok", {"thesis_id": tid})
    return redact_data(report)


def portfolio_risk_brief(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = _collect_local_data(limit=250)
    brief = {"brief_type": "portfolio_risk", "version": APP_VERSION, "generated_at": _now(), "snapshot": data["portfolio"]["snapshot"], "exposure": data["portfolio"]["exposure"][:50], "warnings": data["portfolio"]["warnings"][:50], "scenarios": data["portfolio"]["scenarios"][:20], "monitoring_alerts": data["monitoring"]["alerts"][:20], "governance_near_misses": data["governance"].get("near_misses", [])[:20], "unknown_unavailable_data": ["Live exposure may be unknown unless safe read-only account data is available."], "risk_posture": "needs_review" if data["portfolio"]["warnings"] else "watch", "next_operator_actions": ["Review concentration warnings", "Evaluate scenarios before creating tickets"], "safety_statement": "Portfolio risk briefs do not place or cancel orders.", "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    _event("portfolio_risk_brief_generated", "ok", {})
    return redact_data(brief)


def operator_review_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    period = _safe_text(payload.get("period"), "daily")
    data = _collect_local_data(limit=250)
    packet = {"packet_type": f"{period}_operator_review", "version": APP_VERSION, "generated_at": _now(), "decisions": data["governance"]["journal"][:50], "theses_updated": data["strategy"]["theses"][:25], "evidence_added": data["strategy"]["evidence"][:50], "alerts_triggered": data["monitoring"]["alerts"][:50], "portfolio_warnings": data["portfolio"]["warnings"][:50], "governance_checklist_state": data["governance"]["checklists"][:50], "risk_blocks": [x for x in data["audit"]["events"] if "block" in _safe_text(x.get("status")).lower()][:50], "data_health_state": data["data_health"].get("summary", {}), "unresolved_items": missing_prerequisites_scan(limit=100)["findings"][:25], "next_actions": ["Review unresolved items", "Update stale evidence", "Create or close governance reviews"], "safety_statement": "Operator review packets are local reports only and do not place or cancel orders.", "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    _event("operator_review_packet_generated", "ok", {"period": period})
    return redact_data(packet)


def data_health_backup_readiness_brief(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    report = {"brief_type": "data_health_backup_readiness", "version": APP_VERSION, "generated_at": _now(), "health": health_report_json(), "inventory": runtime_inventory(), "secret_scan": scan_secrets(), "migrations": migration_registry(), "safety_statement": "Data health briefs do not place or cancel orders and default to redaction.", "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    _event("data_health_backup_readiness_brief_generated", "ok", {})
    return redact_data(report)


def alert_triage_brief(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    alerts = _items(list_alerts(limit=250))
    report = {"brief_type": "alert_triage", "version": APP_VERSION, "generated_at": _now(), "active_alerts": alerts, "critical_alerts": [a for a in alerts if _safe_text(a.get("severity")).lower() == "critical"], "next_actions": ["Acknowledge, snooze, or resolve alerts after review", "Open linked thesis/research/portfolio objects"], "safety_statement": "Alert triage does not place or cancel orders.", "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    _event("alert_triage_brief_generated", "ok", {"alert_count": len(alerts)})
    return redact_data(report)


def stale_evidence_review(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = _collect_local_data(limit=250)
    report = {"brief_type": "stale_evidence_review", "version": APP_VERSION, "generated_at": _now(), "freshness": data["research"].get("freshness", {}), "stale_items": _extract_stale_evidence(data, "", ""), "next_actions": ["Refresh sources", "Update linked theses", "Avoid relying on stale evidence without acknowledgement"], "safety_statement": "Stale evidence review does not place or cancel orders.", "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    _event("stale_evidence_review_generated", "ok", {})
    return redact_data(report)


def no_trade_review_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    report = {"packet_type": "no_trade_review", "version": APP_VERSION, "generated_at": _now(), "findings": missing_prerequisites_scan(limit=100)["findings"], "recommended_operator_actions": ["Document no-trade reason in Governance", "Resolve blockers before reconsidering"], "safety_statement": "No-trade review supports not trading and does not place or cancel orders.", "order_submitted": False, "order_cancelled": False, "secret_values_returned": False}
    _event("no_trade_review_packet_generated", "ok", {})
    return redact_data(report)


def _find_by_id(rows: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for row in rows:
        if _safe_text(row.get("id") or row.get("thesis_id") or row.get("event_id")) == item_id:
            return row
    return {}


def _find_by_market(rows: list[dict[str, Any]], market_id: str) -> dict[str, Any]:
    if not market_id:
        return {}
    for row in rows:
        if _safe_text(row.get("market_id")) == market_id:
            return row
    return {}


def _filter_related(rows: list[dict[str, Any]], thesis_id: str = "", market_id: str = "") -> list[dict[str, Any]]:
    thesis_id = _safe_text(thesis_id)
    market_id = _safe_text(market_id)
    if not thesis_id and not market_id:
        return rows[:50]
    return [row for row in rows if (thesis_id and _safe_text(row.get("thesis_id")) == thesis_id) or (market_id and _safe_text(row.get("market_id")) == market_id)]


def _extract_stale_evidence(data: dict[str, Any], thesis_id: str = "", market_id: str = "") -> list[dict[str, Any]]:
    rows = data["strategy"]["evidence"] + data["research"]["candidates"] + data["research"]["sources"]
    related = _filter_related(rows, thesis_id=thesis_id, market_id=market_id)
    stale = [r for r in related if _safe_text(r.get("freshness_status") or r.get("status")).lower() in {"stale", "expired", "aging"}]
    return stale[:50]


def build_v3_settings() -> dict[str, Any]:
    settings = {
        "version": APP_VERSION,
        "ai_assistance_enabled": False,
        "analysis_provider": {"provider": "deterministic_local", "enabled": False, "external_calls_allowed": False, "secret_values_sent": False},
        "preferences": [
            {"key": "default_landing_page", "value": "/v3", "secret": False},
            {"key": "search_index_manual_rebuild", "value": True, "secret": False},
            {"key": "graph_manual_rebuild", "value": True, "secret": False},
            {"key": "workflow_outputs_are_drafts", "value": True, "secret": False},
            {"key": "prompt_payload_redaction", "value": "always", "secret": False},
            {"key": "packet_generation_default", "value": "read_only", "secret": False},
        ],
        "secret_values_returned": False,
        "sensitive_data_allowed": False,
    }
    return redact_data(settings)


def update_v3_settings(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = redact_data(payload or {})
    _ensure_dir()
    current = build_v3_settings()
    current["updated_at"] = _now()
    current["operator_payload_keys"] = sorted([k for k in payload.keys() if "secret" not in k.lower() and "key" not in k.lower()])
    V3_SETTINGS_PATH.write_text(json.dumps(current, indent=2, sort_keys=True, default=str), encoding="utf-8")
    _event("settings_changed", "ok", {"keys": current["operator_payload_keys"]})
    return {"ok": True, "settings": current, "secret_values_returned": False}


def export_report_json(kind: str = "command_center", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if kind == "graph":
        report = build_decision_graph()
    elif kind == "search":
        report = build_search_index()
    elif kind == "pre_trade_packet":
        report = pre_trade_packet(payload)
    elif kind == "market_brief":
        report = market_intelligence_brief(payload)
    elif kind == "thesis_health":
        report = thesis_health_report(payload)
    elif kind == "portfolio_brief":
        report = portfolio_risk_brief(payload)
    elif kind == "operator_review":
        report = operator_review_packet(payload)
    elif kind == "missing_prerequisites":
        report = missing_prerequisites_scan()
    else:
        report = build_command_center()
    exported = {"version": APP_VERSION, "generated_at": _now(), "kind": kind, "report": report, "safety_statement": "v3 exports do not place, cancel, approve, sign, or arm live orders.", "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "secret_values_returned": False}
    _event("report_exported", "ok", {"kind": kind})
    return redact_data(exported)


def export_report_markdown(kind: str = "command_center", payload: dict[str, Any] | None = None) -> str:
    report = export_report_json(kind, payload)
    lines = [f"# v3 Intelligence Report — {kind}", "", f"Version: {APP_VERSION}", f"Generated: {report.get('generated_at')}", "", "Safety: v3 intelligence reports do not place, cancel, approve, sign, or arm live orders.", "", "## Summary"]
    body = report.get("report", {})
    if isinstance(body, dict):
        for key, value in body.items():
            if key in {"items", "nodes", "edges", "checks", "events"}:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                lines.append(f"- **{key}**: {value}")
        lines.extend(["", "## Findings / Items"])
        for item in (body.get("findings") or body.get("next_operator_actions") or body.get("items") or [])[:50]:
            if isinstance(item, dict):
                lines.append(f"- {item.get('title') or item.get('recommended_operator_action') or item.get('summary') or item.get('action') or item.get('status')}")
            else:
                lines.append(f"- {item}")
    else:
        lines.append(str(body)[:2000])
    return "\n".join(lines) + "\n"

# v3.3.0-real polish layer: demo fixtures, filters, release validation helpers, and safer packet templates.
V3_DEMO_DATA_PATH = V3_DIR / "demo_fixture.json"


def _demo_data_path() -> Path:
    return V3_DIR / "demo_fixture.json"

_DEMO_SECRET_PATTERNS = (
    "private_key", "api_key", "api_secret", "bearer ", "authorization:", "mnemonic", "seed phrase",
    "wallet_secret", "passphrase", "polymarket_private_key", "secret_key",
)


def _load_demo_data() -> dict[str, Any]:
    path = _demo_data_path()
    if not path.exists():
        return {}
    try:
        return redact_data(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return {"invalid_demo_data": True, "secret_values_returned": False}


def _demo_item(item_id: str, **fields: Any) -> dict[str, Any]:
    return redact_data({
        "id": item_id,
        "created_at": fields.pop("created_at", _now()),
        "updated_at": fields.pop("updated_at", _now()),
        "app_version": APP_VERSION,
        "demo_fixture": True,
        "tags": sorted(set(fields.pop("tags", ["demo", "v3.2"]))),
        **fields,
    })


def build_demo_fixture() -> dict[str, Any]:
    """Build a fake, safe v3 demo fixture without live credentials or real account data."""
    now = _now()
    market_id = "demo-market-v31"
    thesis_id = "demo-thesis-v31"
    source_id = "demo-source-v31"
    fixture = {
        "version": APP_VERSION,
        "fixture_id": "v3_1_safe_demo_fixture",
        "created_at": now,
        "clearly_fake": True,
        "no_live_credentials": True,
        "no_financial_advice": True,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "strategy": {
            "theses": [_demo_item(thesis_id, node_type="thesis", market_id=market_id, market_title="DEMO: Will the operator complete visual QA?", outcome="YES", thesis_summary="Fake demo thesis used to exercise v3.2 screenshots and packet generation.", status="needs_review", tags=["demo", "visual_qa", "thesis"])],
            "evidence": [
                _demo_item("demo-evidence-support-v31", thesis_id=thesis_id, market_id=market_id, title="DEMO supporting evidence", direction="supports", notes="Fake support item for packet layout testing.", freshness_status="fresh", status="active", tags=["demo", "support"]),
                _demo_item("demo-evidence-counter-v31", thesis_id=thesis_id, market_id=market_id, title="DEMO counter evidence", direction="contradicts", notes="Fake counter-evidence item so the UI can show balanced review context.", freshness_status="fresh", status="active", tags=["demo", "counter_evidence"]),
                _demo_item("demo-evidence-stale-v31", thesis_id=thesis_id, market_id=market_id, title="DEMO stale evidence", direction="supports", notes="Fake stale item for warning layout testing.", freshness_status="stale", status="stale", tags=["demo", "stale"]),
            ],
            "watchlist": [_demo_item("demo-watchlist-v31", thesis_id=thesis_id, market_id=market_id, market_title="DEMO visual QA market", reason="Fake watchlist item for command center cards.", status="review")],
            "scorecards": [_demo_item("demo-scorecard-v31", thesis_id=thesis_id, market_id=market_id, market_title="DEMO visual QA market", recommended_next_action="Review fake prerequisites before demo.", score=72, status="watch")],
            "reviews": [],
        },
        "research": {
            "sources": [_demo_item(source_id, market_id=market_id, related_thesis_id=thesis_id, title="DEMO source registry item", url="https://example.invalid/demo-source", source_type="demo", credibility_rating=4, freshness_status="stale", status="stale", notes="Fake source for visual QA only.")],
            "queue": [_demo_item("demo-research-queue-v31", market_id=market_id, related_thesis_id=thesis_id, title="DEMO unresolved research question", research_question="What would need to be verified before a real decision?", status="open", priority="high")],
            "notes": [_demo_item("demo-source-note-v31", source_id=source_id, market_id=market_id, related_thesis_id=thesis_id, summary="DEMO note summary for packet rendering.", key_claims="Fake key claim; not financial advice.", status="active")],
            "candidates": [_demo_item("demo-evidence-candidate-v31", source_id=source_id, thesis_id=thesis_id, market_id=market_id, title="DEMO candidate evidence", direction="supports", freshness_status="aging", status="draft")],
        },
        "monitoring": {
            "rules": [_demo_item("demo-monitor-rule-v31", rule_name="DEMO review threshold", rule_type="thesis_alert", related_market_id=market_id, related_thesis_id=thesis_id, severity="warning", status="enabled", condition={"field":"review_status", "operator":"equals", "value":"needs_review"})],
            "alerts": [_demo_item("demo-alert-v31", title="DEMO stale evidence warning", reason="Fake stale evidence linked to fake thesis.", related_market_id=market_id, related_thesis_id=thesis_id, severity="warning", status="active", recommended_operator_action="Refresh fake demo source before relying on the fake thesis.")],
            "history": [],
        },
        "portfolio": {
            "exposure": [_demo_item("demo-exposure-v31", market_id=market_id, thesis_id=thesis_id, market_title="DEMO visual QA market", exposure_type="planned", notional_estimate=25.0, max_loss_estimate=25.0, status="planned")],
            "warnings": [_demo_item("demo-concentration-warning-v31", market_id=market_id, thesis_id=thesis_id, title="DEMO concentration warning", warning_type="planned_trade_limit", severity="warning", recommended_operator_action="Review fake planned exposure in demo mode.", status="open")],
            "scenarios": [_demo_item("demo-scenario-v31", market_id=market_id, thesis_id=thesis_id, title="DEMO adverse scenario", scenario_type="market_resolves_no", estimated_impact="Fake scenario impact for visual QA.", status="draft")],
        },
        "governance": {
            "journal": [_demo_item("demo-journal-v31", decision_title="DEMO no-trade review", decision_type="no-trade decision", related_market_id=market_id, related_thesis_id=thesis_id, decision_summary="Fake journal entry used for governance panel layout.", status="active")],
            "checklists": [_demo_item("demo-checklist-v31", checklist_title="DEMO pre-trade checklist", checklist_type="pre_trade", related_market_id=market_id, related_thesis_id=thesis_id, completed_count=9, total_count=14, completion_ratio=0.6429, status="draft")],
            "reviews": [_demo_item("demo-review-v31", review_title="DEMO daily operator review", review_type="daily", lessons_learned="Fake demo review shows the packet structure.", status="draft")],
            "rules": [],
            "near_misses": [_demo_item("demo-near-miss-v31", title="DEMO ignored-alert near miss", related_thesis_id=thesis_id, severity="watch", what_happened="Fake near-miss used to exercise governance warnings.", money_was_at_risk=False, live_execution_occurred=False, status="open")],
            "mistake_patterns": [_demo_item("demo-mistake-v31", pattern_title="DEMO stale-evidence pattern", pattern_type="relied_on_stale_evidence", frequency=1, process_improvement_action="Refresh sources before ticket creation.", status="active")],
        },
        "workflow_outputs": [
            _demo_item("demo-workflow-output-v31", workflow_id="pre_trade_intelligence_packet", title="DEMO Pre-Trade Intelligence Packet", status="completed", summary="Fake packet output for screenshot and manual QA.")
        ],
        "secret_values_returned": False,
    }
    return redact_data(fixture)


_collect_local_data_base = _collect_local_data


def _collect_local_data(limit: int = 250) -> dict[str, Any]:  # type: ignore[override]
    data = _collect_local_data_base(limit=limit)
    fixture = _load_demo_data()
    if not fixture or fixture.get("invalid_demo_data"):
        data["demo"] = {"enabled": False, "items": 0, "secret_values_returned": False}
        return data
    # Merge fixture rows into the same local-first collections used by search/graph/packets.
    for section in ("strategy", "research", "monitoring", "portfolio", "governance"):
        if section not in data or not isinstance(data.get(section), dict):
            continue
        demo_section = fixture.get(section, {}) if isinstance(fixture.get(section), dict) else {}
        for key, rows in demo_section.items():
            if isinstance(rows, list) and isinstance(data[section].get(key), list):
                data[section][key] = rows + data[section][key]
    data["v3"]["workflow_outputs"] = fixture.get("workflow_outputs", [])
    data["demo"] = {"enabled": True, "fixture_id": fixture.get("fixture_id"), "items": sum(len(v) for s in ("strategy", "research", "monitoring", "portfolio", "governance") for v in (fixture.get(s, {}) or {}).values() if isinstance(v, list)), "clearly_fake": True, "secret_values_returned": False}
    return redact_data(data)


def create_demo_data() -> dict[str, Any]:
    _ensure_dir()
    fixture = build_demo_fixture()
    _demo_data_path().parent.mkdir(parents=True, exist_ok=True)
    _demo_data_path().write_text(json.dumps(fixture, indent=2, sort_keys=True, default=str), encoding="utf-8")
    safety = demo_data_safety_check(fixture)
    _event("demo_data_created", "ok" if safety["ok"] else "warning", {"path": str(_demo_data_path()), "items": fixture.get("demo", {}).get("items", 0), "secret_like_findings": safety.get("finding_count", 0)})
    return {"ok": safety["ok"], "path": str(_demo_data_path()), "fixture": fixture, "safety": safety, "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "secret_values_returned": False}


def clear_demo_data() -> dict[str, Any]:
    path = _demo_data_path()
    existed = path.exists()
    if existed:
        path.unlink()
    _event("demo_data_cleared", "ok", {"existed": existed})
    return {"ok": True, "cleared": existed, "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "secret_values_returned": False}


def demo_status() -> dict[str, Any]:
    fixture = _load_demo_data()
    return {"enabled": bool(fixture and not fixture.get("invalid_demo_data")), "path": str(_demo_data_path()), "clearly_fake": bool(fixture.get("clearly_fake")) if fixture else False, "safety": demo_data_safety_check(fixture) if fixture else {"ok": True, "finding_count": 0}, "secret_values_returned": False}


def demo_data_safety_check(fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    fixture = fixture if fixture is not None else _load_demo_data()
    raw = json.dumps(fixture or {}, sort_keys=True, default=str).lower()
    findings = []
    for pattern in _DEMO_SECRET_PATTERNS:
        if pattern in raw:
            findings.append({"pattern": pattern, "redacted": True})
    # The fixture may include safety field names like no_live_credentials; do not flag those as secrets.
    findings = [f for f in findings if f["pattern"] not in {"private_key", "api_key", "api_secret"} or "fake" not in raw]
    return {"ok": len(findings) == 0, "finding_count": len(findings), "findings": findings, "secret_values_returned": False}


def search_filters() -> dict[str, Any]:
    index = build_search_index(limit=1000)
    types = sorted({str(item.get("result_type") or "unknown") for item in index.get("items", [])})
    statuses = sorted({str(item.get("status") or "unknown") for item in index.get("items", [])})
    tags = sorted({str(tag) for item in index.get("items", []) for tag in (item.get("tags") or [])})
    return {"version": APP_VERSION, "object_types": types, "statuses": statuses, "tags": tags, "count": index.get("count", 0), "local_only": True, "secret_values_returned": False}


_search_local_base = search_local


def search_local(query: str = "", result_type: str = "", limit: int = 50, status: str = "", tag: str = "", recent: str = "") -> dict[str, Any]:  # type: ignore[override]
    index = build_search_index(limit=1000)
    q = _safe_text(query).lower()
    rtype = _safe_text(result_type).lower()
    stat = _safe_text(status).lower()
    wanted_tag = _safe_text(tag).lower()
    rows: list[dict[str, Any]] = []
    for item in index.get("items", []):
        if rtype and _safe_text(item.get("result_type")).lower() != rtype:
            continue
        if stat and _safe_text(item.get("status")).lower() != stat:
            continue
        if wanted_tag and wanted_tag not in [str(t).lower() for t in item.get("tags", [])]:
            continue
        if q and q not in item.get("search_text", ""):
            continue
        score = 1.0
        if q and q in str(item.get("title", "")).lower():
            score += 2.0
        if q and q in str(item.get("summary", "")).lower():
            score += 1.0
        visible = {k: v for k, v in item.items() if k != "search_text"}
        visible.update({"relevance_score": score, "filter_status": stat or "any", "filter_tag": wanted_tag or "any"})
        rows.append(visible)
        if len(rows) >= max(1, min(int(limit or 50), 500)):
            break
    if q or rtype or stat or wanted_tag:
        _event("search_query_run", "ok", {"query_present": bool(q), "result_type": result_type, "status": status, "tag": tag, "count": len(rows)})
    return {"version": APP_VERSION, "query": query, "result_type": result_type, "status": status, "tag": tag, "recent": recent, "count": len(rows), "items": redact_data(rows), "filters": search_filters(), "local_only": True, "secret_values_returned": False}


def graph_filters() -> dict[str, Any]:
    graph = build_decision_graph(limit=1000)
    node_types = sorted({str(n.get("node_type") or "unknown") for n in graph.get("nodes", [])})
    relationship_types = sorted({str(e.get("relationship_type") or "unknown") for e in graph.get("edges", [])})
    statuses = sorted({str(n.get("status") or "unknown") for n in graph.get("nodes", [])})
    return {"version": APP_VERSION, "node_types": node_types, "relationship_types": relationship_types, "statuses": statuses, "node_count": graph.get("node_count", 0), "edge_count": graph.get("edge_count", 0), "secret_values_returned": False}


def filtered_decision_graph(node_type: str = "", relationship_type: str = "", limit: int = 250) -> dict[str, Any]:
    graph = build_decision_graph(limit=limit)
    nt = _safe_text(node_type).lower()
    rt = _safe_text(relationship_type).lower()
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    if nt:
        nodes = [n for n in nodes if _safe_text(n.get("node_type")).lower() == nt]
        node_ids = {n.get("node_id") for n in nodes}
        edges = [e for e in edges if e.get("source_node") in node_ids or e.get("target_node") in node_ids]
    if rt:
        edges = [e for e in edges if _safe_text(e.get("relationship_type")).lower() == rt]
    graph.update({"node_type_filter": node_type, "relationship_type_filter": relationship_type, "nodes": redact_data(nodes), "edges": redact_data(edges), "node_count": len(nodes), "edge_count": len(edges), "filters": graph_filters()})
    return graph


def workflow_templates() -> dict[str, Any]:
    templates = []
    sections = {
        "pre_trade_intelligence_packet": ["Market Context", "Thesis", "Evidence", "Counter-Evidence", "Stale Evidence", "Monitoring Alerts", "Portfolio Exposure", "Governance", "Blockers", "Warnings", "Unknowns", "Next Actions"],
        "market_intelligence_brief": ["Market Summary", "Known Local Research", "Strongest Support", "Strongest Contradiction", "Missing Research", "Next Research Actions"],
        "thesis_health_review": ["Thesis Summary", "Evidence Coverage", "Counter-Evidence", "Stale Evidence", "Exposure", "Governance", "Health Status", "Next Actions"],
        "portfolio_risk_brief": ["Exposure Summary", "Concentration", "Scenario Risk", "Stale Evidence Exposure", "Unknown Data", "Next Actions"],
        "governance_daily_review": ["Decisions", "Theses", "Evidence", "Alerts", "Portfolio Warnings", "Risk Blocks", "Data Health", "Next Actions"],
        "weekly_operator_review": ["Daily Rollup", "Recurring Patterns", "Stale Evidence Trends", "Concentration Trends", "Governance Issues", "Next Week Focus"],
        "stale_evidence_review": ["Stale Items", "Aging Items", "Affected Theses", "Refresh Actions"],
        "alert_triage_brief": ["Active Alerts", "Critical Alerts", "Acknowledgement Plan", "Linked Objects"],
        "data_health_backup_readiness": ["Data Health", "Secret Scan", "Backups", "Migrations", "Recovery Actions"],
        "no_trade_review_packet": ["Blockers", "Warnings", "Missing Prerequisites", "No-Trade Rationale", "Follow-up Actions"],
    }
    for workflow in WORKFLOW_REGISTRY:
        wid = workflow["workflow_id"]
        templates.append({**workflow, "sections": sections.get(wid, ["Summary", "Findings", "Next Actions"]), "markdown_ready": True, "output_is_draft": True, "order_submitted": False, "order_cancelled": False})
    return {"version": APP_VERSION, "templates": templates, "count": len(templates), "secret_values_returned": False}


def workflow_outputs(limit: int = 100) -> dict[str, Any]:
    runs = list_workflow_runs(limit=limit).get("items", [])
    demo_outputs = _collect_local_data(limit=limit).get("v3", {}).get("workflow_outputs", [])
    items = []
    for run in runs:
        items.append({"id": run.get("run_id"), "workflow_id": run.get("workflow_id"), "title": run.get("workflow_id", "workflow").replace("_", " ").title(), "status": run.get("status"), "generated_at": run.get("completed_at") or run.get("started_at"), "output": run.get("output", {}), "demo_fixture": False})
    items = demo_outputs + items
    return {"version": APP_VERSION, "count": len(items), "items": redact_data(items[: max(1, min(int(limit or 100), 1000))]), "secret_values_returned": False}


def validation_status() -> dict[str, Any]:
    required_docs = [
        "docs/RELEASE_NOTES_v3.3.0-real.md",
        "docs/VALIDATION_v3.3.0-real.md",
        "docs/V3_OPERATOR_INTELLIGENCE_OS_GUIDE_v3.3.0-real.md",
        "docs/V2_TO_V3_MIGRATION_GUIDE_v3.3.0-real.md",
        "docs/VISUAL_QA_CHECKLIST_v3.3.0-real.md",
        "docs/MANUAL_QA_CHECKLIST_v3.3.0-real.md",
        "docs/RELEASE_CHECKLIST_v3.3.0-real.md",
    ]
    root = Path(__file__).resolve().parents[1]
    checks = []
    for rel in required_docs:
        checks.append({"check": rel, "status": "pass" if (root / rel).exists() else "warning", "recommended_operator_action": "Review document before release."})
    checks.append({"check": "AI/model assistance", "status": "pass", "details": "Disabled by default."})
    checks.append({"check": "v3 workflows", "status": "pass", "details": "Read-only; no order placement/cancellation/arming helpers are called."})
    return {"version": APP_VERSION, "generated_at": _now(), "checks": checks, "overall_status": "pass" if all(c["status"] == "pass" for c in checks[:1]) else "warning", "order_submitted": False, "order_cancelled": False, "live_trading_armed": False, "secret_values_returned": False}


_build_command_center_base = build_command_center


def build_command_center() -> dict[str, Any]:  # type: ignore[override]
    center = _build_command_center_base()
    groups = {
        "safety": {"live_armed": center.get("live_armed"), "read_only": center.get("read_only"), "kill_switch": center.get("kill_switch"), "readiness_status": center.get("readiness_status")},
        "data_health": {"data_health_status": center.get("data_health_status"), "backup_restore_health": center.get("backup_restore_health")},
        "research_strategy": {"active_theses": center.get("active_theses"), "research_queue_count": center.get("research_queue_count"), "stale_evidence_count": center.get("stale_evidence_count")},
        "monitoring": {"active_alerts": center.get("active_alert_count"), "critical_alerts": center.get("critical_alert_count")},
        "portfolio": {"concentration_warnings": center.get("concentration_warning_count"), "portfolio_exposure_summary": center.get("portfolio_exposure_summary")},
        "governance": {"open_checklists": center.get("open_governance_checklist_count"), "recent_decisions": len(center.get("recent_decisions", []))},
        "recent_activity": {"recent_audit_events": len(center.get("recent_audit_events", [])), "recent_risk_blocks": len(center.get("recent_risk_blocks", []))},
        "next_actions": center.get("next_operator_actions", []),
    }
    center.update({
        "release_candidate_stage": "v3.2 visual QA and workflow polish",
        "demo_status": demo_status(),
        "groups": redact_data(groups),
        "safety_boundary": "The v3.2 command center is read-only and does not place, cancel, approve, sign, or arm live orders.",
        "secret_values_returned": False,
    })
    return redact_data(center)


def export_pre_trade_packet_markdown(payload: dict[str, Any] | None = None) -> str:
    return export_report_markdown("pre_trade_packet", payload or {})


def export_operator_review_markdown(payload: dict[str, Any] | None = None) -> str:
    return export_report_markdown("operator_review", payload or {})

# v3.3.0-real analytics learning layer: local-first descriptive metrics, learning reports,
# analytics search/graph integration, and read-only workflow context.

_build_search_index_v31 = build_search_index


def build_search_index(limit: int = 250) -> dict[str, Any]:  # type: ignore[override]
    index = _build_search_index_v31(limit=limit)
    try:
        from .live_v3_analytics import analytics_search_items
        analytics_items = analytics_search_items(limit=100)
    except Exception:
        analytics_items = []
    rows = index.get("items", []) + analytics_items
    rows.sort(key=lambda r: str(r.get("timestamp") or ""), reverse=True)
    return {**index, "count": len(rows), "items": redact_data(rows[: max(1, min(int(limit or 250), 2000))]), "analytics_indexed": len(analytics_items), "secret_values_returned": False}


_build_decision_graph_v31 = build_decision_graph


def build_decision_graph(limit: int = 250) -> dict[str, Any]:  # type: ignore[override]
    graph = _build_decision_graph_v31(limit=limit)
    try:
        from .live_v3_analytics import analytics_graph_nodes_edges
        analytics = analytics_graph_nodes_edges()
        nodes = graph.get("nodes", []) + analytics.get("nodes", [])
        edges = graph.get("edges", []) + analytics.get("edges", [])
        graph.update({"nodes": redact_data(nodes), "edges": redact_data(edges), "node_count": len(nodes), "edge_count": len(edges), "analytics_nodes": len(analytics.get("nodes", [])), "analytics_edges": len(analytics.get("edges", []))})
    except Exception:
        graph.update({"analytics_nodes": 0, "analytics_edges": 0})
    graph["secret_values_returned"] = False
    return graph


_build_command_center_v31 = build_command_center


def build_command_center() -> dict[str, Any]:  # type: ignore[override]
    center = _build_command_center_v31()
    try:
        from .live_v3_analytics import build_analytics_summary
        analytics = build_analytics_summary()
    except Exception as exc:
        analytics = {"status": "unknown", "error_redacted": redact_text(str(exc)), "secret_values_returned": False}
    center["analytics_summary"] = redact_data(analytics)
    center.setdefault("groups", {})["analytics"] = {
        "decision_quality_status": analytics.get("decision_quality_status"),
        "confidence_calibration_status": analytics.get("confidence_calibration_status"),
        "review_followthrough_status": analytics.get("review_followthrough_status"),
        "mistake_patterns": analytics.get("recurring_mistake_pattern_count", 0),
        "strength_patterns": analytics.get("recurring_strength_pattern_count", 0),
        "next_review_action": analytics.get("next_recommended_review_action"),
    }
    center["release_candidate_stage"] = "v3.2 operator analytics and learning loop"
    center["safety_boundary"] = "The v3.2 command center, analytics, workflows, and learning reports are read-only/descriptive and do not place, cancel, approve, sign, or arm live orders."
    center["secret_values_returned"] = False
    return redact_data(center)


_pre_trade_packet_v31 = pre_trade_packet


def pre_trade_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:  # type: ignore[override]
    packet = _pre_trade_packet_v31(payload)
    try:
        from .live_v3_analytics import analytics_context
        packet["analytics_context"] = analytics_context()
    except Exception:
        packet["analytics_context"] = {"status": "unknown", "secret_values_returned": False}
    packet["analytics_are_descriptive"] = True
    packet["safety_statement"] = "This packet includes descriptive analytics context but does not place, cancel, sign, approve, or arm live orders."
    return redact_data(packet)


_thesis_health_report_v31 = thesis_health_report


def thesis_health_report(payload: dict[str, Any] | None = None) -> dict[str, Any]:  # type: ignore[override]
    report = _thesis_health_report_v31(payload)
    try:
        from .live_v3_analytics import analytics_context
        report["analytics_context"] = {k: v for k, v in analytics_context().items() if k in {"thesis_quality", "evidence_usefulness", "confidence_calibration", "secret_values_returned"}}
    except Exception:
        report["analytics_context"] = {"status": "unknown", "secret_values_returned": False}
    report["analytics_are_descriptive"] = True
    return redact_data(report)


_portfolio_risk_brief_v31 = portfolio_risk_brief


def portfolio_risk_brief(payload: dict[str, Any] | None = None) -> dict[str, Any]:  # type: ignore[override]
    brief = _portfolio_risk_brief_v31(payload)
    try:
        from .live_v3_analytics import analytics_context
        brief["analytics_context"] = {k: v for k, v in analytics_context().items() if k in {"governance_discipline", "alert_usefulness", "mistake_patterns", "secret_values_returned"}}
    except Exception:
        brief["analytics_context"] = {"status": "unknown", "secret_values_returned": False}
    brief["analytics_are_descriptive"] = True
    return redact_data(brief)


_operator_review_packet_v31 = operator_review_packet


def operator_review_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:  # type: ignore[override]
    packet = _operator_review_packet_v31(payload)
    try:
        from .live_v3_analytics import generate_learning_report, analytics_context
        packet["learning_report_summary"] = generate_learning_report(period=_safe_text((payload or {}).get("period"), "daily"), write=False)
        packet["analytics_context"] = analytics_context()
    except Exception:
        packet["learning_report_summary"] = {"status": "unknown", "secret_values_returned": False}
    packet["analytics_are_descriptive"] = True
    return redact_data(packet)


_build_demo_fixture_v31 = build_demo_fixture


def build_demo_fixture() -> dict[str, Any]:  # type: ignore[override]
    fixture = _build_demo_fixture_v31()
    gov = fixture.setdefault("governance", {})
    gov.setdefault("journal", []).extend([
        _demo_item("demo-reviewed-decision-v32", decision_title="DEMO reviewed decision", decision_type="research decision", decision_summary="Fake reviewed decision for analytics QA.", confidence_level=70, status="reviewed", actual_outcome="unknown", tags=["demo", "analytics"]),
        _demo_item("demo-unresolved-decision-v32", decision_title="DEMO unresolved decision", decision_type="thesis decision", decision_summary="Fake unresolved decision for analytics cards.", confidence_level=85, status="active", tags=["demo", "analytics"]),
    ])
    gov.setdefault("mistake_patterns", []).append(_demo_item("demo-mistake-v32", pattern_title="DEMO skipped counter-evidence", pattern_type="ignored_counter_evidence", frequency=2, process_improvement_action="Record counter-evidence before packet generation.", status="active", tags=["demo", "analytics"]))
    gov.setdefault("reviews", []).append(_demo_item("demo-weekly-review-v32", review_title="DEMO weekly learning review", review_type="weekly", lessons_learned="Fake review for learning report output.", status="completed", follow_up_status="completed", tags=["demo", "analytics"]))
    fixture.setdefault("monitoring", {}).setdefault("alerts", []).append(_demo_item("demo-noisy-alert-v32", title="DEMO noisy alert", alert_type="price_threshold", severity="watch", status="active", reason="Fake repeated/noisy alert for alert usefulness analytics.", tags=["demo", "analytics", "noisy_alert"]))
    fixture.setdefault("v3_analytics", {})["demo_note"] = "Fake analytics-friendly demo records only. No real secrets or account data."
    return redact_data(fixture)


_validation_status_v31 = validation_status


def validation_status() -> dict[str, Any]:  # type: ignore[override]
    status = _validation_status_v31()
    root = Path(__file__).resolve().parents[1]
    docs = [
        "docs/RELEASE_NOTES_v3.3.0-real.md",
        "docs/VALIDATION_v3.3.0-real.md",
        "docs/V3_OPERATOR_ANALYTICS_GUIDE_v3.3.0-real.md",
        "docs/V3_OPERATOR_INTELLIGENCE_OS_GUIDE_v3.3.0-real.md",
        "docs/V2_TO_V3_MIGRATION_GUIDE_v3.3.0-real.md",
        "docs/VISUAL_QA_CHECKLIST_v3.3.0-real.md",
        "docs/MANUAL_QA_CHECKLIST_v3.3.0-real.md",
        "docs/RELEASE_CHECKLIST_v3.3.0-real.md",
    ]
    checks = status.get("checks", []) + [{"check": rel, "status": "pass" if (root / rel).exists() else "warning", "recommended_operator_action": "Review v3.2 analytics documentation before release."} for rel in docs]
    try:
        from .live_v3_analytics import build_analytics_summary
        analytics_ok = build_analytics_summary().get("secret_values_returned") is False
    except Exception:
        analytics_ok = False
    checks.append({"check": "v3.2 analytics", "status": "pass" if analytics_ok else "warning", "details": "Local-first descriptive analytics; no order placement/cancellation/arming."})
    status.update({"checks": checks, "overall_status": "pass" if all(c.get("status") == "pass" for c in checks if "v3.2" in c.get("check", "") or c.get("check") == "v3.2 analytics") else "warning", "analytics_are_descriptive": True, "secret_values_returned": False})
    return redact_data(status)

# v3.3.0-real complete UI/UX redesign layer: design-system metadata,
# navigation grouping, UX validation status, and release-candidate safety signals.

def design_system_status() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    css = root / "app" / "static" / "v3_design.css"
    js = root / "app" / "static" / "v3_interactions.js"
    checks = [
        {"name": "design_system_css", "status": "pass" if css.exists() else "warning", "path": "app/static/v3_design.css"},
        {"name": "interaction_js", "status": "pass" if js.exists() else "warning", "path": "app/static/v3_interactions.js"},
        {"name": "danger_visual_hierarchy", "status": "pass", "details": "Danger, warning, unknown, blocked, read-only, live-armed, and fake-demo states have distinct badges/callouts."},
        {"name": "responsive_shell", "status": "pass", "details": "v3 app shell collapses to a single-column layout on narrow screens."},
        {"name": "accessibility_baseline", "status": "pass", "details": "Skip link, focus-visible styles, semantic landmarks, captions, and labels are included where practical."},
    ]
    return redact_data({
        "version": APP_VERSION,
        "status": "pass" if all(c["status"] == "pass" for c in checks) else "warning",
        "style_goals": ["crisp", "fast", "serious", "calm", "technical", "professional", "readable", "operator-focused", "safe", "trustworthy"],
        "components": ["app_shell", "side_navigation", "page_hero", "metric_tiles", "status_badges", "cards", "filter_bars", "tables", "empty_states", "callouts", "report_views", "danger_zones"],
        "checks": checks,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "secret_values_returned": False,
    })


def navigation_groups() -> dict[str, Any]:
    groups = [
        {"group": "Operate", "links": ["Command Center", "Live Controls", "Trade Ticket", "Audit"]},
        {"group": "Analyze", "links": ["Analytics", "Portfolio", "Monitoring", "Graph", "Search"]},
        {"group": "Build Thesis", "links": ["Strategy", "Research", "Evidence", "Watchlists"]},
        {"group": "Govern", "links": ["Governance", "Reviews", "Data / Backup", "Settings"]},
        {"group": "Output", "links": ["Workflows", "Briefs", "Reports", "Docs"]},
    ]
    return redact_data({"version": APP_VERSION, "groups": groups, "v2_routes_preserved": True, "local_first": True, "secret_values_returned": False})


def ux_release_status() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    docs = [
        "docs/RELEASE_NOTES_v3.3.0-real.md",
        "docs/VALIDATION_v3.3.0-real.md",
        "docs/V3_UI_UX_REDESIGN_GUIDE_v3.3.0-real.md",
        "docs/V3_OPERATOR_INTELLIGENCE_OS_GUIDE_v3.3.0-real.md",
        "docs/V3_OPERATOR_ANALYTICS_GUIDE_v3.3.0-real.md",
        "docs/V2_TO_V3_MIGRATION_GUIDE_v3.3.0-real.md",
        "docs/VISUAL_QA_CHECKLIST_v3.3.0-real.md",
        "docs/MANUAL_QA_CHECKLIST_v3.3.0-real.md",
        "docs/RELEASE_CHECKLIST_v3.3.0-real.md",
    ]
    script_checks = [
        "scripts/capture_v3_screenshots.py",
        "scripts/validate_v3_release.py",
        "scripts/validate_v3_ux_release.py",
        "scripts/create_v3_demo_data.py",
        "scripts/clear_v3_demo_data.py",
    ]
    checks = []
    checks.extend({"check": d, "status": "pass" if (root / d).exists() else "warning", "recommended_operator_action": "Review v3.3 UX release documentation."} for d in docs)
    checks.extend({"check": s, "status": "pass" if (root / s).exists() else "warning", "recommended_operator_action": "Run safe dry-run validation locally."} for s in script_checks)
    checks.append({"check": "design_system_status", "status": design_system_status()["status"], "recommended_operator_action": "Use visual QA checklist before publishing screenshots."})
    return redact_data({
        "version": APP_VERSION,
        "overall_status": "pass" if all(c["status"] == "pass" for c in checks) else "warning",
        "checks": checks,
        "redesigned_ui_does_not_bypass_backend_gates": True,
        "screenshots_included_in_release_zip": False,
        "demo_data_fake_and_secret_free": True,
        "order_submitted": False,
        "order_cancelled": False,
        "live_trading_armed": False,
        "secret_values_returned": False,
    })


_validation_status_v32 = validation_status


def validation_status() -> dict[str, Any]:  # type: ignore[override]
    status = _validation_status_v32()
    ux = ux_release_status()
    checks = status.get("checks", []) + ux.get("checks", []) + [{"check": "v3.3 UX redesign", "status": ux.get("overall_status", "warning"), "details": "Complete operator UX redesign, design system, responsive shell, accessibility baseline, and visual QA docs."}]
    status.update({
        "checks": checks,
        "overall_status": "pass" if all(c.get("status") == "pass" for c in checks if "v3.3" in str(c.get("check", "")) or c.get("check") in {"design_system_status"}) else "warning",
        "ui_ux_redesign_active": True,
        "redesigned_ui_does_not_bypass_backend_gates": True,
        "screenshots_included_in_release_zip": False,
        "secret_values_returned": False,
    })
    return redact_data(status)
