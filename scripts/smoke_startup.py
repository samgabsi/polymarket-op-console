from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app
from app.config import APP_VERSION

REQUIRED = [
    "/", "/v2-live", "/v2-live/verify", "/v2-live/strategy", "/v2-live/research", "/v2-live/monitoring", "/v2-live/portfolio", "/v2-live/governance", "/v2-live/data",
    "/v3", "/v3/search", "/v3/graph", "/v3/workflows", "/v3/analytics", "/v3/analytics/decisions", "/v3/analytics/learning-report",
    "/v3/simulation", "/v3/simulation/replay", "/v3/simulation/no-trade", "/v3/datasets", "/v3/datasets/quality", "/v3/freshness", "/v3/freshness/notifications",
    "/v3/platform", "/v3/platform/health", "/v3/platform/routes", "/v3/platform/plugins", "/v3/platform/storage", "/v3/platform/diagnostics", "/v3/platform/exports", "/v3/platform/settings",
    "/v3/tasks", "/v3/tasks/board", "/v3/tasks/inbox", "/v3/tasks/today", "/v3/tasks/week", "/v3/tasks/cadence", "/v3/tasks/templates", "/v3/tasks/exports", "/v3/tasks/settings", "/v3/cockpit", "/v3/cockpit/layouts", "/v3/cockpit/focus", "/v3/cockpit/review", "/v3/cockpit/tasks", "/v3/cockpit/dependencies", "/v3/cockpit/source", "/v3/cockpit/packets", "/v3/cockpit/command-palette", "/v3/cockpit/shortcuts", "/v3/cockpit/settings", "/v3/workspace", "/v3/workspace/daily-review", "/v3/workspace/weekly-review", "/v3/workspace/task-triage", "/v3/workspace/blocked", "/v3/workspace/dependencies", "/v3/workspace/source-preview", "/v3/workspace/review-flows", "/v3/workspace/review-packets", "/v3/workspace/saved-views", "/v3/workspace/settings",
    "/api/v2/live/status", "/api/v2/live/verify", "/api/v2/live/demo-readiness", "/api/v2/live/strategy", "/api/v2/live/governance", "/api/v2/live/data", "/api/v2/live/data/migrations",
    "/api/v3", "/api/v3/command-center", "/api/v3/search", "/api/v3/graph", "/api/v3/workflows", "/api/v3/analytics", "/api/v3/analytics/summary", "/api/v3/simulation", "/api/v3/simulation/sessions", "/api/v3/simulation/reports",
    "/api/v3/datasets", "/api/v3/freshness", "/api/v3/platform/summary", "/api/v3/platform/health", "/api/v3/platform/routes", "/api/v3/platform/plugins", "/api/v3/platform/storage", "/api/v3/platform/diagnostics", "/api/v3/platform/settings",
    "/api/v3/tasks", "/api/v3/tasks/summary", "/api/v3/tasks/inbox", "/api/v3/tasks/board", "/api/v3/tasks/today", "/api/v3/tasks/week", "/api/v3/tasks/cadence", "/api/v3/tasks/templates", "/api/v3/tasks/settings", "/api/v3/cockpit/summary", "/api/v3/cockpit/layouts", "/api/v3/cockpit/focus-modes", "/api/v3/cockpit/panels", "/api/v3/cockpit/shortcuts", "/api/v3/cockpit/command-palette", "/api/v3/cockpit/dependencies", "/api/v3/cockpit/source-context", "/api/v3/cockpit/settings", "/api/v3/workspace/summary", "/api/v3/workspace/flows", "/api/v3/workspace/sessions", "/api/v3/workspace/dependencies", "/api/v3/workspace/blocked", "/api/v3/workspace/source-preview", "/api/v3/workspace/saved-views", "/api/v3/workspace/review-packets", "/api/v3/workspace/settings",
]
client = TestClient(app)
results = {}
for path in REQUIRED:
    response = client.get(path)
    results[path] = response.status_code
    if response.status_code >= 500:
        raise SystemExit(f"startup smoke failed for {path}: {response.status_code}")
print({"version": APP_VERSION, "routes": results, "network_mutation": False, "orders_placed": False, "orders_cancelled": False})
