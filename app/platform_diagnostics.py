from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .config import APP_VERSION
from .platform_exports import export_manifest, to_markdown
from .platform_plugins import load_plugin_manifests, plugin_summary
from .platform_routes import route_inventory, module_inventory
from .platform_safety import safety_flags, safety_statements
from .platform_storage import storage_summary
from .platform_version import version_metadata

PLATFORM_SETTINGS = {
    "diagnostics_run_on_startup": False,
    "platform_exports_run_on_page_load": False,
    "plugin_manifests_execute_code": False,
    "network_diagnostics_enabled_by_default": False,
    "show_unknown_unavailable_data": True,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def health_summary(app: Any | None = None) -> dict[str, Any]:
    routes = route_inventory(app)
    plugins = plugin_summary()
    storage = storage_summary()
    return safety_flags({
        "version": APP_VERSION,
        "generated_at": _now(),
        "overall_status": "pass" if plugins.get("invalid_plugin_count", 0) == 0 else "warning",
        "route_count": routes.get("count", 0),
        "route_families": routes.get("families", {}),
        "plugin_count": plugins.get("plugin_count", 0),
        "invalid_plugin_count": plugins.get("invalid_plugin_count", 0),
        "storage_namespace_count": storage.get("count", 0),
        "validation_capabilities": ["version", "routes", "plugins", "storage", "exports", "secret-safety", "no-live-mutation"],
        "known_unknown_unavailable_data": ["Runtime records may be absent in a clean package.", "Authenticated route status is summarized from path conventions only."],
    })


def diagnostics_summary(app: Any | None = None) -> dict[str, Any]:
    return safety_flags({
        "version": APP_VERSION,
        "generated_at": _now(),
        "version_metadata": version_metadata(),
        "health": health_summary(app),
        "routes": route_inventory(app),
        "modules": module_inventory(),
        "plugins": load_plugin_manifests(),
        "storage": storage_summary(),
        "safety": safety_statements(),
        "settings": build_settings(),
        "diagnostics_do_not_mutate_live_trading_state": True,
    })


def platform_summary(app: Any | None = None) -> dict[str, Any]:
    h = health_summary(app)
    return safety_flags({
        "version": APP_VERSION,
        "overall_status": h["overall_status"],
        "route_count": h["route_count"],
        "plugin_count": h["plugin_count"],
        "invalid_plugin_count": h["invalid_plugin_count"],
        "storage_namespace_count": h["storage_namespace_count"],
        "safety_posture": "fail-closed, local-first, human-in-the-loop",
        "release_candidate_stage": "v4.0.1-real platform baseline",
        "next_platform_action": "Review platform health, plugin manifests, route inventory, and storage compatibility before adding v4.x features.",
    })


def build_settings() -> dict[str, Any]:
    return safety_flags({"version": APP_VERSION, "settings": PLATFORM_SETTINGS.copy()})


def update_settings(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    # In v4.0 settings are intentionally non-persistent to avoid surprising runtime writes from diagnostics.
    requested = payload or {}
    return safety_flags({"ok": True, "settings": {**PLATFORM_SETTINGS, **{k: bool(v) for k, v in requested.items() if k in PLATFORM_SETTINGS}}, "persisted": False})


def export_json(app: Any | None = None) -> dict[str, Any]:
    diag = diagnostics_summary(app)
    return export_manifest(
        "platform_diagnostics_json",
        "v4.0 Platform Diagnostics Export",
        included_object_ids=["platform_version", "route_inventory", "plugin_manifests", "storage_namespaces", "safety_policy"],
        related_object_ids=[],
        unknown_unavailable_data=diag.get("health", {}).get("known_unknown_unavailable_data", []),
        payload=diag,
    )


def export_markdown(app: Any | None = None) -> str:
    return to_markdown(export_json(app))


def search_items(app: Any | None = None) -> list[dict[str, Any]]:
    diag = diagnostics_summary(app)
    rows = [
        {"id": "platform:version", "result_id": "platform:version", "result_type": "platform_version", "title": "Platform Version Metadata", "summary": diag["version_metadata"]["release_title"], "status": "active", "tags": ["platform", "version", "v4"], "quick_link": "/v3/platform", "search_text": "platform version v4 diagnostics metadata"},
        {"id": "platform:routes", "result_id": "platform:routes", "result_type": "platform_route_inventory", "title": "Platform Route Inventory", "summary": f"{diag['routes']['count']} route entries inventoried.", "status": "diagnostic", "tags": ["platform", "routes"], "quick_link": "/v3/platform/routes", "search_text": "platform routes inventory api ui"},
        {"id": "platform:plugins", "result_id": "platform:plugins", "result_type": "platform_plugin_manifest", "title": "Plugin Manifest Boundary", "summary": f"{diag['plugins']['count']} metadata-only plugin manifests.", "status": "safe", "tags": ["platform", "plugins", "manifest"], "quick_link": "/v3/platform/plugins", "search_text": "platform plugins manifests metadata only no code execution"},
        {"id": "platform:storage", "result_id": "platform:storage", "result_type": "platform_storage_namespace", "title": "Storage Compatibility", "summary": f"{diag['storage']['count']} local storage namespaces documented.", "status": "documented", "tags": ["platform", "storage"], "quick_link": "/v3/platform/storage", "search_text": "platform storage compatibility migration runtime data"},
        {"id": "platform:safety", "result_id": "platform:safety", "result_type": "platform_safety_policy", "title": "Platform Safety Boundary", "summary": diag['safety']['standard_safety_statement'], "status": "fail-closed", "tags": ["platform", "safety"], "quick_link": "/v3/platform/diagnostics", "search_text": "platform safety no live mutation no orders no cancellations"},
    ]
    return rows


def graph_nodes(app: Any | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = search_items(app)
    nodes = [{"node_id": row["id"], "node_type": row["result_type"], "title": row["title"], "status": row["status"], "summary": row["summary"]} for row in rows]
    edges = [
        {"source_node": "platform:version", "target_node": "platform:routes", "relationship_type": "documents"},
        {"source_node": "platform:version", "target_node": "platform:plugins", "relationship_type": "defines_boundary"},
        {"source_node": "platform:plugins", "target_node": "platform:safety", "relationship_type": "protected_by"},
        {"source_node": "platform:storage", "target_node": "platform:safety", "relationship_type": "respects"},
    ]
    return nodes, edges


def workflow_output(workflow_id: str) -> dict[str, Any]:
    diag = diagnostics_summary()
    titles = {
        "platform_health_review": "Platform Health Review",
        "route_inventory_review": "Route Inventory Review",
        "plugin_boundary_review": "Plugin Boundary Review",
        "storage_compatibility_review": "Storage Compatibility Review",
        "release_candidate_readiness_review": "Release Candidate Readiness Review",
        "package_cleanliness_review": "Package Cleanliness Review",
        "safety_boundary_review": "Safety Boundary Review",
    }
    return safety_flags({
        "workflow_id": workflow_id,
        "title": titles.get(workflow_id, "Platform Review"),
        "status": "completed",
        "generated_at": _now(),
        "sections": ["Summary", "Routes", "Plugins", "Storage", "Safety", "Unknowns", "Next Actions"],
        "summary": platform_summary(),
        "diagnostics": diag,
        "next_actions": ["Review invalid plugin manifests if any.", "Confirm release ZIP excludes runtime data.", "Keep plugin manifests metadata-only for v4.0."],
    })
