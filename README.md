# Polymarket Gamma Starter v3.3.0-real

**Current release:** `v3.3.0-real — Complete Operator UX Redesign, Performance Polish, and Interaction Overhaul`

Polymarket Gamma Starter is a local-first, human-in-the-loop Polymarket operator workstation. It combines live-control safety gates, strategy/thesis workflows, research and evidence intake, monitoring alerts, portfolio/exposure review, governance, data integrity, global search, decision graph, read-only workflows, and operator analytics into a unified command center.

v3.3.0-real is a whole-product usability pass. It redesigns the v3 interface for speed, smoothness, crispness, information architecture, visual clarity, responsive behavior, accessibility, and release/demo readiness while preserving all existing backend safety gates.

## Safety philosophy

The project is built around explicit human control. The redesigned UI, search results, graph findings, analytics, packets, briefs, alerts, demo data, and workflows are **not orders**, **not approvals**, **not financial advice**, and **not predictive guarantees**.

Live order submission remains guarded by backend risk checks, warning acknowledgement, typed confirmation, Live Armed mode, read-only disablement, kill-switch state, and existing safety gates.

## v3.3 UI/UX redesign overview

- New persistent v3 app shell and grouped navigation.
- New design system for cards, metric tiles, badges, buttons, forms, tables, filters, reports, warnings, and danger states.
- Redesigned command center focused on safety, attention queue, workbench shortcuts, intelligence summary, recent activity, and safe next actions.
- Improved global local search, decision graph, workflow cards, packet/report readability, analytics layout, and visual QA workflow.
- Better responsive behavior, visible keyboard focus, table captions, semantic landmarks, and stronger safety-status visibility.
- Lightweight interaction script for local table filtering and keyboard search focus.

## Feature map

- `/v3` — redesigned unified command center
- `/v3/search` — global local search
- `/v3/graph` — decision/object graph explorer
- `/v3/workflows` — read-only workflow orchestrator
- `/v3/briefs` — packets, reports, and operator briefs
- `/v3/analytics` — operator analytics and learning reports
- `/v3/settings` — v3 settings and safe AI/provider boundary
- `/v3/docs` — v3 documentation index
- `/v2-live/*` — compatible detailed v2 control-plane modules

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `/v3` for the redesigned command center.

## Safe demo data

Safe fake demo data can be generated locally for screenshots and manual QA:

```bash
PYTHONPATH=. python scripts/create_v3_demo_data.py
PYTHONPATH=. python scripts/clear_v3_demo_data.py
```

Demo data is fake, local, secret-free, and excluded from release packages.

## Screenshot / visual QA

```bash
PYTHONPATH=. python scripts/capture_v3_screenshots.py --dry-run
PYTHONPATH=. python scripts/validate_v3_ux_release.py --quick
```

Screenshots are runtime artifacts and are not included in release ZIPs unless explicitly reviewed and intended.

## Documentation

- [v3 UI/UX Redesign Guide](docs/V3_UI_UX_REDESIGN_GUIDE_v3.3.0-real.md)
- [v3 Operator Intelligence OS Guide](docs/V3_OPERATOR_INTELLIGENCE_OS_GUIDE_v3.3.0-real.md)
- [v3 Operator Analytics Guide](docs/V3_OPERATOR_ANALYTICS_GUIDE_v3.3.0-real.md)
- [V2 to V3 Migration Guide](docs/V2_TO_V3_MIGRATION_GUIDE_v3.3.0-real.md)
- [Visual QA Checklist](docs/VISUAL_QA_CHECKLIST_v3.3.0-real.md)
- [Manual QA Checklist](docs/MANUAL_QA_CHECKLIST_v3.3.0-real.md)
- [Release Checklist](docs/RELEASE_CHECKLIST_v3.3.0-real.md)
- [Validation Notes](docs/VALIDATION_v3.3.0-real.md)

## Legal and compliance note

Use only where permitted and in compliance with applicable laws, platform terms, account eligibility, geofencing, KYC, and jurisdictional restrictions. Do not put real secrets in Git, screenshots, issue reports, exports, backups, or release assets.
