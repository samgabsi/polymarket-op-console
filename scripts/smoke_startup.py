from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app
from app.config import APP_VERSION

REQUIRED = ["/", "/v2-live", "/v2-live/verify", "/v2-live/strategy", "/v2-live/governance", "/v2-live/data", "/v3", "/v3/search", "/v3/graph", "/v3/workflows", "/v3/analytics", "/v3/analytics/decisions", "/v3/analytics/learning-report", "/api/v2/live/status", "/api/v2/live/verify", "/api/v2/live/demo-readiness", "/api/v2/live/strategy", "/api/v2/live/governance", "/api/v2/live/data", "/api/v2/live/data/migrations", "/api/v3", "/api/v3/command-center", "/api/v3/search", "/api/v3/graph", "/api/v3/workflows", "/api/v3/analytics", "/api/v3/analytics/summary"]
client = TestClient(app)
results = {}
for path in REQUIRED:
    response = client.get(path)
    results[path] = response.status_code
    if response.status_code >= 500:
        raise SystemExit(f"startup smoke failed for {path}: {response.status_code}")
print({"version": APP_VERSION, "routes": results, "network_mutation": False, "orders_placed": False, "orders_cancelled": False})
