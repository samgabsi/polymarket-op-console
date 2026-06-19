# Release Notes — v4.0.0-real

## Operator Intelligence Platform Stabilization, Plugin Boundary, and Release Candidate Hardening

v4.0.0-real is a stabilization release after v3.9.0-real. It deliberately avoids another broad trading or automation feature layer and instead hardens the project as a maintainable v4 baseline.

## Added

- Platform support modules: `platform_version`, `platform_safety`, `platform_exports`, `platform_routes`, `platform_plugins`, `platform_storage`, and `platform_diagnostics`.
- `/v3/platform` UI routes for health, route inventory, plugin manifests, storage compatibility, diagnostics, exports, and settings.
- `/api/v3/platform/*` endpoints for summary, health, routes, plugins, storage, diagnostics, JSON export, Markdown export, and settings.
- Metadata-only plugin manifest boundary for future v4.x extension planning.
- Route inventory and module inventory helpers.
- Local storage compatibility notes for v3.5 through v4.0 runtime JSON/JSONL stores.
- Centralized safety statements, forbidden live-mutation actions, secret redaction helpers, and export manifests.
- Platform-aware search, graph, command center, workflow, and demo fixture integration.
- Platform validation hardening and package-cleanliness checks.

## Safety

Platform diagnostics, plugin manifests, route inventory, storage summaries, and exports do not execute plugin code, do not load remote code, do not place orders, do not cancel orders, do not approve trades, do not sign transactions, do not arm live trading, do not bypass backend gates, and do not provide financial advice.

## Preserved

All existing v2 and v3 functionality is preserved, including live trading gates, paper trading, risk controls, audit logging, emergency controls, strategy, research, monitoring, portfolio, governance, data integrity, analytics, simulation, datasets, freshness, task planner, guided workspace, cockpit, command palette, screenshot helpers, docs, tests, and validation scripts.
