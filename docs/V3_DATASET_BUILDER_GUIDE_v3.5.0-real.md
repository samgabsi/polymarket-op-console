# v3 Dataset Builder Guide — v3.5.0-real

Version: v3.5.0-real

## What v3.5 adds

v3.5.0-real adds a read-only market data snapshot collector, replay dataset builder, dataset quality scoring, provenance tracking, validation, and export layer. It is designed to improve replay, simulation, analytics, graph, search, workflows, and operator review without creating autonomous trading.

## What snapshots are

Snapshots are local records of safe read-only state. Snapshot types include market metadata, order book summaries when safe read-only data is available, strategy/thesis state, research/evidence state, monitoring/alert state, portfolio/exposure state, governance/review state, analytics state, simulation state, data-health state, and audit summaries.

Each snapshot records a snapshot ID, app version, created timestamp, snapshot type, source subsystem, collection mode, safe metadata, redacted payload summary, payload hash, validation status, quality status, provenance record, and safety metadata.

## What datasets are

A dataset is a manifest that groups snapshots for replay and simulation. A dataset manifest records included snapshots, date range, market/thesis scope, collection assumptions, quality score, warnings, limitations, unknown/unavailable data, and provenance summary.

## What dataset building is not

Dataset building is not trading, not order submission, not order cancellation, not account management, not financial advice, and not a guarantee of replay or trading quality.

## Live / paper / demo / simulation / replay / dataset distinction

- Live: real execution path guarded by backend gates.
- Paper: non-live paper workflow.
- Demo: clearly fake records for screenshots and QA.
- Simulation: hypothetical/local replay output.
- Replay: best-effort reconstruction from local records and timestamps.
- Dataset: read-only snapshots and manifests used as replay inputs.

## Read-only snapshot collection

Snapshot collection is explicit/manual by default. v3.5 does not collect snapshots on startup and does not run network-heavy collection automatically. Scheduled collection scaffolding, if extended later, must remain disabled by default and clearly read-only.

## Market metadata snapshots

Market metadata snapshots store safe fields such as market ID, condition ID, question/title, slug, outcomes, token IDs, category/tags, end date, status, source timestamp, local capture timestamp, payload hash, and redacted payload summary.

## Order book snapshots

Order book snapshots store safe fields such as market ID, condition ID, token ID, outcome, bid/ask summary, best bid, best ask, spread, midpoint/depth summary where calculable, source timestamp, local capture timestamp, payload hash, and redacted payload summary. If safe read-only order book access is not configured, v3.5 supports the structure through demo/local/mock input and documents the limitation.

## Local subsystem snapshots

Local subsystem snapshots summarize strategy, research, monitoring, portfolio, governance, analytics, simulation, data-health, and audit state. These are local snapshots, not external data pulls.

## Replay dataset manifests

The replay dataset builder creates manifests from selected snapshots. It reports included and missing snapshot types, quality score, freshness and coverage limitations, unknown fields, and recommended next collection actions.

## Dataset quality scoring

Quality checks include completeness, freshness, coverage, duplicate snapshot detection, malformed snapshot detection, missing required safe fields, unknown/unavailable fields, source timestamp availability, provenance availability, payload hash availability, stale snapshot warnings, replay readiness, simulation readiness, and export readiness.

Quality statuses include excellent, good, usable, partial, stale, incomplete, blocked, and unknown.

## Provenance

Every snapshot and dataset records source subsystem, source label, collection mode, collection timestamp, source timestamp when available, operator action, audit event if available, payload hash, redaction status, and import/export history when available.

## Validation

Snapshot validation checks schema shape, safe required fields, timestamp validity, payload hash presence, redaction status, secret-like content absence, snapshot type consistency, market ID consistency, source subsystem consistency, and duplicate ID/hash behavior.

## Integration

Datasets integrate with:

- `/v3` command center summary
- `/v3/search` global local search
- `/v3/graph` object graph
- `/v3/analytics` analytics context
- `/v3/simulation` replay inputs
- `/v3/workflows` dataset quality and replay-readiness reviews

## Exports

v3.5 supports JSON dataset exports, Markdown dataset reports, snapshot index CSV, quality CSV, and provenance CSV. Exports are redacted and include safety statements.

## Safety boundary

Dataset workflows do not place orders, cancel orders, approve orders, sign orders, arm live trading, or bypass backend gates. Dataset outputs are workflow data and not financial advice.

## Known limitations

Replay quality depends on available local snapshots. Missing or stale data is labeled unknown/unavailable rather than invented. Order book capture may require a safe read-only data source or demo/mock input.
