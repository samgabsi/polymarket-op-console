# Changelog

## v4.0.1-real — Polymarket OP Console Rename and Package Identity Update

- Renamed the software from **the former project name** to **Polymarket OP Console** across application title metadata, templates, docs, scripts, package references, user-agent strings, and visible UI copy.
- Updated package identity from the former package slug to `polymarket-op-console`.
- Updated current release version to `v4.0.1-real` and current package name to `polymarket-op-console-v4.0.1-real.zip`.
- Added v4.0.1 documentation references while preserving the v4.0 platform stabilization baseline.
- Confirmed this patch does not add autonomous trading, order placement, order cancellation, live arming, or financial-advice behavior.


## v4.0.0-real — Operator Intelligence Platform Stabilization, Plugin Boundary, and Release Candidate Hardening

- Added v4 platform support modules for version metadata, safety helpers, export helpers, route inventory, plugin manifests, storage compatibility, and diagnostics.
- Added `/v3/platform` UI routes and `/api/v3/platform/*` APIs for summary, health, routes, plugins, storage, diagnostics, exports, and settings.
- Added metadata-only plugin manifest boundary; manifests do not execute arbitrary code, load remote code, access secrets by default, or call live mutation endpoints.
- Added platform route inventory, module inventory, storage namespace summaries, runtime compatibility notes, and platform health summaries.
- Added centralized no-live-mutation, no-financial-advice, task-not-approval, guided-review-not-approval, cockpit-not-trading, plugin-not-trading, redaction, and forbidden-capability helpers.
- Added platform-aware command center, local search, decision graph, read-only workflows, demo fixture, screenshot helper, validation harness, docs, and tests.
- Strengthened validation and package cleanliness checks for v4 platform diagnostics, plugin manifests, exports, route inventory, storage namespaces, and no-live-mutation boundaries.
- Safety: platform diagnostics, plugin manifests, route inventory, storage summaries, exports, command-palette actions, keyboard shortcuts, guided reviews, tasks, cockpit panels, and workflows do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass gates, or provide financial advice.

## v3.9.0-real — Multi-Panel Operator Cockpit, Keyboard Navigation, and Review Layout System

- Added `/v3/cockpit` UI routes for cockpit, layouts, focus modes, review, tasks, dependencies, source context, packets, command palette, shortcuts, and settings.
- Added local-first `app/live_v3_cockpit.py` with cockpit layouts, panels, focus modes, keyboard shortcut manifests, safe command-palette manifests, dependency views, source context, settings, exports, search objects, graph nodes, workflow hooks, validation hooks, and fake demo fixtures.
- Added saved cockpit layouts for daily ops, weekly review, task triage, blocked tasks, source review, datasets, freshness, simulation, analytics, governance, research, monitoring, and portfolio.
- Added safe keyboard navigation and a safe command palette; forbidden live-mutation actions are rejected.
- Added side-by-side task/source/review context and lightweight dependency visualization.
- Added cockpit JSON, Markdown, focus-mode, command-palette, shortcut, and CSV exports.
- Integrated cockpit status with command center, tasks, guided workspace, freshness, datasets, simulation, analytics, search, graph, workflows, docs, demo fixtures, screenshot helper, validation harness, and tests.
- Safety: cockpit layouts, panels, keyboard shortcuts, command-palette actions, focus modes, exports, tasks, guided reviews, and dependencies do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass gates, or provide financial advice.

## v3.8.0-real — Guided Operator Workspace, Interactive Review Flows, and Task Dependency Intelligence

- Added Guided Operator Workspace routes under `/v3/workspace` for daily review, weekly review, task triage, blocked-task review, dependencies, source previews, saved views, review flows, review packets, and settings.
- Added local-first `app/live_v3_workspace.py` with guided review flows, sessions, packets, dependency edges, source preview manifests, saved task views, settings, exports, search objects, graph nodes, and fake demo fixtures.
- Added task dependency intelligence and blocked-task review packets while keeping dependencies as workflow relationships only.
- Added source-context previews before finding/notification task conversion and saved task views.
- Added guided workspace search, graph, workflow, command-center, task planner, module entry point, docs, screenshot, validation, and test coverage.
- Safety: guided reviews, packets, dependencies, saved views, and source previews do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass gates, or provide financial advice.

## v3.7.0-real — Operator Task Planner, Review Cadence Manager, and Human-in-the-Loop Daily Ops Layer

- Added local-first operator task planner and `app/live_v3_tasks.py`.
- Added task inbox, task board, task status/priority/due-date/notes/blocker/related-object tracking, and task templates.
- Added daily ops checklist, Daily Ops Packet, weekly planning workflow, and Weekly Ops Packet.
- Added review cadence manager and operator-triggered cadence generation.
- Added notification-to-task and finding-to-task conversion.
- Added task JSON/Markdown/CSV exports plus daily/weekly packet exports.
- Integrated task status with v3 command center, global search, decision graph, workflow templates, freshness, datasets, simulation, analytics, docs, demo fixtures, screenshot helper, and validation harness.
- Preserved all existing live/paper/risk/audit/emergency safety controls. Task workflows do not place orders, cancel orders, arm live trading, approve trades, or provide financial advice.

## v3.6.0-real — Read-Only Collection Scheduler, Dataset Freshness Planner, and Operator Notification Layer

- Added `/v3/freshness` workspace and subroutes for planner, schedules, jobs, notifications, readiness, history, and settings.
- Added `app/live_v3_freshness.py` with freshness policies, collection jobs, readiness reports, stale findings, local notifications, settings, exports, search/graph/analytics/workflow integrations, and fake demo records.
- Added `/api/v3/freshness/*` endpoints for policies, jobs, scan, readiness, notifications, exports, and settings.
- Preserved all live-trading safety gates; scheduler behavior is disabled by default and read-only/non-autonomous.

## v3.5.0-real and earlier

Historical v2.0.0-real through v3.5.0-real features are preserved, including v2 live controls, risk gates, audit logging, strategy/research/monitoring/portfolio/governance workspaces, v3 command center, analytics, simulation, datasets, visual QA, and release validation.
