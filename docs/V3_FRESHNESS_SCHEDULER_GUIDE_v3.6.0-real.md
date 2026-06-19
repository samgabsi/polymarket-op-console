# V3 Freshness Scheduler Guide — v3.6.0-real

## What freshness planning is
Freshness planning tracks whether local snapshots and replay datasets are current enough for operator review, analytics, replay, and simulation. It creates local findings and notifications when expected data is missing, stale, failed, or low quality.

## What it is not
It is not trading automation, financial advice, hidden execution, order submission, order cancellation, or live-trading authorization. Scheduler support is disabled by default unless explicitly enabled.

## Modes
Live, paper, demo, simulation, replay, dataset collection, and freshness scheduling remain visually and operationally distinct. Freshness planning only queues/readies read-only collection jobs and local reminders.

## Policies
Freshness policies define target snapshot types, thresholds, severity when stale, and collection mode. Manual queued collection is preferred.

## Collection jobs
Jobs hold requested snapshot types, run mode, status, read-only assertion, mutation-endpoint-block assertion, warnings, errors, and audit metadata. Running a job calls read-only dataset snapshot collection only.

## Notifications
Notifications are local and can be acknowledged, dismissed, snoozed, or resolved. Notification actions never place/cancel orders or arm live trading.

## Readiness reports
Readiness reports combine freshness findings and dataset quality to show ready/needs review/not ready status, missing snapshots, stale snapshots, recommended jobs, limitations, and unknown data.

## Integrations
Freshness integrates with datasets, simulation, analytics, search, graph, workflows, command center, demo data, screenshot QA, and release validation.

## Known limitations
Freshness quality depends on local snapshot history. Missing data is labeled unknown/unavailable and is never invented.
