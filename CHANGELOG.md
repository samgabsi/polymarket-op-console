# Changelog

## v3.3.0-real — Complete Operator UX Redesign, Performance Polish, and Interaction Overhaul

- Added complete v3 UI/UX redesign with a persistent app shell and grouped navigation.
- Added shared design-system assets: `app/static/v3_design.css` and `app/static/v3_interactions.js`.
- Redesigned the v3 command center around System Safety, Operator Attention Queue, Workbench Shortcuts, Intelligence Summary, Recent Activity, and Safe Next Actions.
- Improved global local search UX with stronger filter affordances, index-health links, result counts, better snippets, and keyboard focus support.
- Improved decision graph UX with node/relationship filters, graph summary cards, exports, and a stable table/tree relationship explorer.
- Improved read-only workflow cards, packet/report readability, analytics dashboard layout, and safety statements.
- Strengthened safety UX for live armed, read-only, kill switch, risk blocks, unknown/unavailable data, fake demo data, generated outputs, exports, and backups.
- Added responsive/accessibility polish including skip link, semantic landmarks, visible focus states, table captions, and reduced reliance on color alone.
- Updated screenshot helper for the redesigned v3 route set.
- Added `scripts/validate_v3_ux_release.py` release-candidate UX validation harness.
- Added v3.3 UI/UX redesign guide, visual QA checklist, validation notes, manual QA checklist, release checklist, and documentation updates.
- Preserved all v2/v3 routes, local-first data, demo fixture safety, analytics, workflow outputs, and live-trading backend gates.
- No autonomous execution, no live order placement, no cancellation, no live arming, and no secrets in release artifacts.

- Added workflow output templates for pre-trade packets, market briefs, thesis health, portfolio risk, daily/weekly reviews, stale evidence, alert triage, data-health readiness, and no-trade review packets.
- Added safe fake demo fixture support with create/clear/status APIs and scripts.
- Added v3 visual QA checklist and screenshot helper dry-run workflow.
- Added release validation harness for v3 route/API/docs/demo safety checks.
- Updated v3 docs, release notes, manual QA checklist, release checklist, README, tests, and version checks.
- Preserved v2 compatibility and live-trading backend safety gates.
- No autonomous execution, no live order placement, no cancellation, no live arming, and no secrets in release artifacts.

## v3.0.0-real

- Added unified `/v3` command center.
- Added global local search across strategy, research, monitoring, portfolio, governance, data health, and audit records.
- Added decision graph / object graph with relationship explorer and JSON/Markdown exports.
- Added read-only workflow orchestrator.
- Added pre-trade intelligence packets, market intelligence briefs, thesis health reports, portfolio risk briefs, and operator review packets.
- Added missing-prerequisite and conflict detection.
- Added v3 settings boundary with AI/model assistance disabled by default.
- Added v2-to-v3 migration guide, v3 operator guide, release notes, validation report, manual QA checklist, and release checklist.
- Preserved all v2-live routes, safety gates, audit behavior, emergency controls, and fail-closed live trading boundaries.

## v3.0.0-real

Data Integrity / Backup / Migration / Recovery Layer.

Added:

- `/v2-live/data` workspace.
- Local-first `app/live_data.py` data integrity and recovery layer.
- Runtime inventory for audit, strategy, research, monitoring, portfolio, governance, and settings data.
- Data health checks for missing paths, invalid JSON/JSONL, duplicate IDs, oversized files, empty files, and secret-like content.
- Redacted secret scanning across runtime data, docs, app files, tests, and examples.
- Redacted backup bundles with manifest, app version, selected subsystems, schema versions, checksums, redaction policy, and restore instructions.
- Backup validation, restore preview, explicit-confirmation restore apply, controlled import/export bundles, and migration registry/dry-run/apply workflows.
- Recovery reports in JSON, Markdown, and CSV check output.
- Data workflow audit events integrated into the Live v2 audit ledger.
- Tests for data route rendering, APIs, inventory, health checks, invalid JSON detection, secret redaction, backups, restore confirmation, import/export, migrations, reports, and safety non-execution.
- `docs/DATA_INTEGRITY_BACKUP_RECOVERY_GUIDE_v3.0.0-real.md`.
- `docs/RELEASE_NOTES_v3.0.0-real.md`.
- `docs/VALIDATION_v3.0.0-real.md`.
- `docs/MANUAL_QA_CHECKLIST_v3.0.0-real.md`.
- `docs/RELEASE_CHECKLIST_v3.0.0-real.md`.

Safety:

- Data workflows never place orders, sign orders for submission, approve orders, cancel orders, arm live trading, or bypass backend gates.
- Backup/export defaults exclude or redact secrets.
- Restore, import, and migration apply paths require explicit operator confirmation.
- Existing kill switch, read-only, risk, human approval, warning acknowledgement, and typed confirmation gates remain intact.

## v2.8.0-real

Review / Governance / Operator Decision Journal Layer.

Added governance workspace, structured decision journal entries, pre-trade checklists, reviews, governance rules, near-miss tracking, mistake-pattern tracking, exports, docs, and tests while preserving all live safety gates.

## v2.7.0-real

Portfolio / Exposure Intelligence Layer.

Added:

- `/v2-live/portfolio` workspace.
- Local-first `app/live_portfolio.py` data layer.
- Exposure summaries by market, thesis, tag/playbook, watchlist, local audit records, and operator-defined groups.
- Explicit bankroll and risk-budget settings.
- Concentration warnings for portfolio, market, thesis, tag/playbook, stale-evidence, active-alert, and unknown-exposure conditions.
- Scenario planner and scenario evaluation workflow.
- Planned trade impact preview that never submits, signs, approves, arms, or cancels orders.
- Portfolio JSON, Markdown, exposure CSV, warnings CSV, and scenarios CSV exports.
- Portfolio audit events integrated into the Live v2 audit ledger.
- Tests for portfolio CRUD, snapshots, bankroll, warnings, scenarios, planned impact, exports, route rendering, redaction, and safety non-execution.
- `docs/PORTFOLIO_EXPOSURE_GUIDE_v2.7.0-real.md`.
- `docs/RELEASE_NOTES_v2.7.0-real.md`.
- `docs/VALIDATION_v2.7.0-real.md`.
- `docs/MANUAL_QA_CHECKLIST_v2.7.0-real.md`.
- `docs/RELEASE_CHECKLIST_v2.7.0-real.md`.

Safety:

- Portfolio intelligence never places orders, signs orders for submission, approves orders, cancels orders, arms live trading, or bypasses backend gates.
- Exposure and scenario guidance are workflow guidance only and not financial advice.
- Existing kill switch, read-only, risk, human approval, warning acknowledgement, and typed confirmation gates remain intact.

## v2.6.0-real

Market Monitoring and Alert Workflow Layer.

Added:

- `/v2-live/monitoring` workspace.
- Local-first `app/live_monitoring.py` data layer.
- Alert rule builder for price threshold, spread, liquidity, market status, watchlist, thesis, evidence freshness, and readiness posture alerts.
- Manual rule evaluation with explicit read-only alert triggering.
- Operator notification center for active alerts, rules, and recent monitoring events.
- Alert acknowledgement and snooze workflow.
- Monitoring JSON, Markdown, rules CSV, alerts CSV, and history exports.
- Watchlist/thesis/research/evidence linkage fields for monitoring rules.
- Monitoring audit events integrated into the Live v2 audit ledger.
- Tests for monitoring CRUD, evaluation, acknowledgement, snooze, exports, route rendering, redaction, and safety non-execution.
- `docs/MONITORING_ALERTS_GUIDE_v2.6.0-real.md`.
- `docs/RELEASE_NOTES_v2.6.0-real.md`.
- `docs/VALIDATION_v2.6.0-real.md`.
- `docs/MANUAL_QA_CHECKLIST_v2.6.0-real.md`.
- `docs/RELEASE_CHECKLIST_v2.6.0-real.md`.

Safety:

- Alerts never place orders, sign orders for submission, approve orders, cancel orders, arm live trading, or bypass backend gates.
- Alert recommendations are workflow guidance only and not financial advice.
- Existing kill switch, read-only, risk, human approval, warning acknowledgement, and typed confirmation gates remain intact.


## v2.5.0-real

Research Intake and Source Workflow Layer.

Added:

- `/v2-live/research` workspace.
- Local-first `app/live_research.py` data layer.
- Source registry with source type, publisher, URL, credibility, relevance, freshness, status, tags, and thesis linkage.
- Research queue items with priority, desired output, and review status.
- Source notes for key claims, support/contradiction, uncertainty, and operator interpretation.
- Evidence candidates with direction, relevance, credibility, freshness, contradiction strength, and uncertainty scoring.
- Deliberate candidate conversion workflow into v2.4 strategy evidence.
- Freshness/staleness summary and warnings.
- Thesis comparison summary for supporting, contradicting, neutral, and stale evidence.
- Research JSON, Markdown, and CSV exports.
- Research audit events integrated into the Live v2 audit ledger.
- Tests for research CRUD, conversion, exports, route rendering, audit events, redaction, and safety non-submission.
- `docs/RESEARCH_INTAKE_GUIDE_v2.5.0-real.md`.
- `docs/RELEASE_NOTES_v2.5.0-real.md`.
- `docs/VALIDATION_v2.5.0-real.md`.
- `docs/MANUAL_QA_CHECKLIST_v2.5.0-real.md`.
- `docs/RELEASE_CHECKLIST_v2.5.0-real.md`.

Safety:

- Research output never places orders, signs orders for submission, cancels orders, arms live trading, or bypasses backend gates.
- Evidence conversion creates strategy evidence only.
- Existing kill switch, read-only, risk, human approval, warning acknowledgement, and typed confirmation gates remain intact.

## v2.4.0-real

Strategy / Playbook Intelligence Layer: thesis builder, evidence tracking, scorecards, watchlists, entry/exit/invalidation criteria, post-trade reviews, strategy exports, and ticket-draft linkage without order submission.

## v2.3.0-real

Release/demo hardening, safe live read-only verification harness, demo readiness, manual QA, startup hardening, release checklist, and package cleanliness tooling.

## v2.2.0-real

Browser-polished interactive operator console with saved UI preferences, table filters, explicit refresh behavior, better empty/loading/error states, and manual QA guidance.

## v2.1.0-real

UI/UX redesign, cleanup, declutter, persistent status bar, grouped settings, dashboard cards, and safer operator console layout.

## v2.0.0-real

Fully functional Live v2 control plane with live/paper/read-only modes, readiness, ticket preview, risk checks, approval, typed confirmation, fail-closed CLOB adapter boundary, order management, positions/reconciliation, audit, and emergency controls.
