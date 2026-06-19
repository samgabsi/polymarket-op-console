# Polymarket OP Console

Current version: **v4.0.1-real**

Polymarket OP Console is a local-first research, readiness, playbook, risk-budget, execution-queue, audit, review, dataset, simulation, freshness, analytics, task, guided-review, cockpit, and platform diagnostics application for Polymarket-oriented work. It preserves human-in-the-loop control and clear separation between research, paper workflows, live-trading safety gates, simulation/replay, dataset collection, freshness planning, task management, guided reviews, cockpit navigation, platform diagnostics, and plugin manifest metadata.

## v4.0.1 Project Rename and Package Identity Update

v4.0.1-real renames the software from **the former project name** to **Polymarket OP Console** and updates the package identity to match the renamed GitHub repository:

- Repository: `https://github.com/samgabsi/polymarket-op-console`
- Release ZIP naming pattern: `polymarket-op-console-vX.Y.Z-real.zip`
- Current release ZIP: `polymarket-op-console-v4.0.1-real.zip`

This is a focused rebrand/package-identity patch. It preserves the v4.0 platform stabilization baseline, plugin manifest boundary, diagnostics, task planner, guided workspace, cockpit, simulation, dataset, freshness, analytics, v2 live-control compatibility, and all existing live-trading safety gates.

New/current UI entrypoints remain:

- `/v3/platform` for platform health, diagnostics, route inventory, plugins, storage, exports, and settings
- `/v3/cockpit` for the multi-panel operator cockpit
- `/v3/workspace` for guided review flows
- `/v3/tasks` for task planning and daily ops

## Safety philosophy

This package is not autonomous trading software. Platform diagnostics are local operational aids. Plugin manifests are metadata only and do not execute plugin code. Cockpit views are not orders. Keyboard shortcuts are safe navigation/local workflow actions only. Command-palette actions do not place or cancel orders. Task completion and guided review completion are not trade approval. Task priority is not financial advice. Cadence plans are not trading automation.

Live order submission remains guarded by existing backend safety gates, warning acknowledgements, approval checkbox, typed confirmation phrase, read-only state, live armed state, kill switch state, risk checks, and audit logging.

## Local-first workflow philosophy

The v4.0 platform layer summarizes local metadata and runtime namespace expectations. Runtime records are created lazily under `data/` only when operator-triggered workflows create them. Clean release packages exclude runtime records, exports, screenshots, caches, logs, credentials, venvs, node modules, and local data.

## Mode distinctions

- **Live trading:** backend-gated, explicit, fail-closed.
- **Paper trading:** local simulation only.
- **Demo:** fake, secret-free, clearly labeled.
- **Simulation/replay:** descriptive process evaluation only.
- **Dataset collection:** read-only snapshots and replay manifests.
- **Freshness scheduling:** read-only collection planning and local notifications.
- **Task planning:** local workflow records and human follow-through.
- **Guided reviews:** local review sessions and packets; not orders.
- **Cockpit:** local navigation/layout/safe-summary layer; not trading automation.
- **Platform diagnostics:** local operational metadata; not live mutation.
- **Plugin manifests:** metadata-only future extension boundary; no arbitrary code execution.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open the app, create the initial admin user, then visit:

- `/v3` for the command center
- `/v3/platform` for platform diagnostics
- `/v3/cockpit` for the multi-panel cockpit
- `/v3/workspace` for guided reviews
- `/v3/tasks` for the task planner
- `/v3/freshness` for freshness planning
- `/v3/datasets` for dataset builder
- `/v3/simulation` for replay and simulation
- `/v2-live` for v2 live-control compatibility

## Demo data

Safe demo fixture tools remain fake and secret-free:

```bash
python scripts/create_v3_demo_data.py
```

Do not mix real credentials, real account data, or private keys into demo records.

## Documentation index

- [V4 Platform Architecture Guide](docs/V4_PLATFORM_ARCHITECTURE_GUIDE_v4.0.1-real.md)
- [V4 Plugin Boundary Guide](docs/V4_PLUGIN_BOUNDARY_GUIDE_v4.0.1-real.md)
- [V4 Platform Diagnostics Guide](docs/V4_PLATFORM_DIAGNOSTICS_GUIDE_v4.0.1-real.md)
- [V4 Storage Compatibility Guide](docs/V4_STORAGE_COMPATIBILITY_GUIDE_v4.0.1-real.md)
- [Operator Cockpit Guide](docs/V3_OPERATOR_COCKPIT_GUIDE_v4.0.1-real.md)
- [Guided Operator Workspace Guide](docs/V3_GUIDED_OPERATOR_WORKSPACE_GUIDE_v4.0.1-real.md)
- [Operator Task Planner Guide](docs/V3_OPERATOR_TASK_PLANNER_GUIDE_v4.0.1-real.md)
- [Freshness Scheduler Guide](docs/V3_FRESHNESS_SCHEDULER_GUIDE_v4.0.1-real.md)
- [Dataset Builder Guide](docs/V3_DATASET_BUILDER_GUIDE_v4.0.1-real.md)
- [Simulation Lab Guide](docs/V3_SIMULATION_LAB_GUIDE_v4.0.1-real.md)
- [UI/UX Redesign Guide](docs/V3_UI_UX_REDESIGN_GUIDE_v4.0.1-real.md)
- [Operator Analytics Guide](docs/V3_OPERATOR_ANALYTICS_GUIDE_v4.0.1-real.md)
- [Operator Intelligence OS Guide](docs/V3_OPERATOR_INTELLIGENCE_OS_GUIDE_v4.0.1-real.md)
- [V2 to V3 Migration Guide](docs/V2_TO_V3_MIGRATION_GUIDE_v4.0.1-real.md)
- [Visual QA Checklist](docs/VISUAL_QA_CHECKLIST_v4.0.1-real.md)
- [Manual QA Checklist](docs/MANUAL_QA_CHECKLIST_v4.0.1-real.md)
- [Release Checklist](docs/RELEASE_CHECKLIST_v4.0.1-real.md)
- [Validation Notes](docs/VALIDATION_v4.0.1-real.md)
- [Release Notes](docs/RELEASE_NOTES_v4.0.1-real.md)

## No-secrets warning

Never place real private keys, API keys, wallet secrets, auth headers, credentials, or sensitive account data in `.env.example`, docs, tests, screenshots, task records, cockpit records, platform diagnostics, plugin manifests, exports, audit logs, reports, model prompts, model outputs, browser storage, or release assets. Use `.env` locally and keep it out of release packages.
