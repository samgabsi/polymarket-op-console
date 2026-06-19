from __future__ import annotations

from typing import Any
from .config import APP_VERSION
from .platform_safety import safety_flags

ROUTE_FAMILY_HINTS = [
    ("v2_live", "/v2-live"), ("v3_command_center", "/v3"), ("v3_tasks", "/v3/tasks"), ("v3_workspace", "/v3/workspace"),
    ("v3_cockpit", "/v3/cockpit"), ("v4_platform", "/v3/platform"), ("v3_datasets", "/v3/datasets"),
    ("v3_freshness", "/v3/freshness"), ("v3_simulation", "/v3/simulation"), ("v3_analytics", "/v3/analytics"),
    ("api_v3_platform", "/api/v3/platform"), ("api_v3_cockpit", "/api/v3/cockpit"), ("api_v3_workspace", "/api/v3/workspace"),
    ("api_v3_tasks", "/api/v3/tasks"), ("api_v3", "/api/v3"), ("api_v2", "/api/v2"),
]


def _family(path: str) -> str:
    for name, prefix in ROUTE_FAMILY_HINTS:
        if path == prefix or path.startswith(prefix + "/"):
            return name
    if path.startswith("/api"):
        return "api_other"
    return "ui_other"


def route_inventory(app: Any | None = None) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    if app is not None:
        for route in getattr(app, "routes", []):
            path = getattr(route, "path", "")
            if not path:
                continue
            methods = sorted([m for m in getattr(route, "methods", []) if m not in {"HEAD", "OPTIONS"}])
            items.append({
                "path": path,
                "name": getattr(route, "name", ""),
                "methods": methods,
                "family": _family(path),
                "protected_or_authenticated": path.startswith("/v3") or path.startswith("/api/v3") or path.startswith("/v2-live"),
                "mutates_live_trading_state": False if path.startswith("/v3/platform") or path.startswith("/api/v3/platform") else "existing route-specific gates apply",
                "safety_notes": "Route inventory is diagnostic only and does not call route handlers.",
            })
    else:
        for name, prefix in ROUTE_FAMILY_HINTS:
            items.append({"path": prefix, "name": name, "methods": ["GET"], "family": name, "protected_or_authenticated": True, "safety_notes": "Static route family hint."})
    families: dict[str, int] = {}
    for item in items:
        families[item["family"]] = families.get(item["family"], 0) + 1
    return safety_flags({"version": APP_VERSION, "count": len(items), "items": items, "families": families, "route_inventory_does_not_mutate_live_trading_state": True})


def module_inventory() -> dict[str, Any]:
    modules = [
        "live_v2", "live_v3", "live_v3_tasks", "live_v3_workspace", "live_v3_cockpit", "platform_version", "platform_safety",
        "platform_exports", "platform_routes", "platform_plugins", "platform_storage", "platform_diagnostics", "live_v3_datasets", "live_v3_freshness", "live_v3_simulation", "live_v3_analytics",
    ]
    items = [{"module": m, "family": "platform" if m.startswith("platform") else "operator_intelligence", "safety_notes": "Module inventory only; no module action is executed."} for m in modules]
    return safety_flags({"version": APP_VERSION, "count": len(items), "items": items})
