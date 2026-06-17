# Monitoring / Alerts Guide — v2.6.0-real

## Purpose

The monitoring layer is an operator-awareness system. It helps you track market thresholds, watchlist review points, thesis reminders, evidence freshness, and readiness posture changes.

It is not an execution engine. Alerts do not place orders, cancel orders, approve orders, sign orders, arm live trading, or bypass backend gates.

## What the monitoring layer is

- A local-first alert rule registry
- An in-app notification center
- A workflow reminder system
- A read-only market-condition/checklist helper when explicitly evaluated
- A link layer between alerts, theses, watchlists, evidence, research sources, and ticket rationale
- An auditable history of rule and alert activity

## What it is not

- Not financial advice
- Not an autonomous trader
- Not an order router
- Not a kill-switch override
- Not a substitute for risk checks
- Not a substitute for human approval

## Rule types

Supported rule categories include:

- Price threshold alerts
- Spread alerts
- Liquidity alerts
- Market status alerts
- Watchlist alerts
- Thesis review reminders
- Evidence freshness alerts
- Readiness and safety posture alerts

## Creating alert rules

Open `/v2-live/monitoring`, then use **Create Alert Rule**.

Common fields:

- Rule name
- Rule type
- Condition
- Threshold value
- Severity
- Market or outcome reference
- Thesis ID
- Evidence ID
- Watchlist ID
- Review-by date
- Operator notes

Rules default to local workflow tracking. They do not run uncontrolled background polling by default.

## Manual evaluation

Use **Evaluate Rule** or **Evaluate all enabled rules**. Evaluation is explicit and read-only. A triggered alert records an alert event and audit entry only.

## Notification center

The monitoring page shows:

- Active alerts
- Critical alerts
- Rule status
- Alert reasons
- Recommended operator action
- Expandable raw details

Recommended actions are workflow guidance, for example:

- Review linked thesis before creating a ticket
- Refresh source before relying on evidence
- Inspect order book manually
- Check readiness before live use
- Open linked watchlist item
- No action taken automatically

## Acknowledgement and snooze

Use acknowledgement when an alert has been reviewed. Use snooze when an alert should be temporarily hidden from immediate review. Both actions are audited.

## Watchlist integration

Rules can link to watchlist items by ID. Use this for target entry, target exit, invalidation, spread, liquidity, and review reminders. The alert does not create a ticket or order.

## Thesis reminders

Rules can link to thesis IDs. Use this for scheduled thesis review, stale-evidence reminders, and invalidation review. The alert never edits the thesis automatically.

## Evidence freshness alerts

Use freshness alerts to track aging, stale, expired, or refresh-needed research. The alert never converts evidence automatically.

## Readiness and safety posture alerts

Readiness alerts can prompt the operator to review live-readiness failures, kill-switch changes, read-only posture, or verification failures. They are visibility tools only.

## Exports

Available exports:

- `/api/v2/live/monitoring/export.json`
- `/api/v2/live/monitoring/export.md`
- `/api/v2/live/monitoring/export/rules.csv`
- `/api/v2/live/monitoring/export/alerts.csv`

Exports include a safety statement that monitoring output does not place or cancel orders.

## Safety gates remain mandatory

Even if an alert fires, a live order still requires:

- risk checks
- human approval
- warning acknowledgement
- typed confirmation phrase
- Live Armed mode
- read-only disabled
- kill switch disabled
- backend submit gates

## Known limitations

- Monitoring storage is local-first and not synced across devices.
- Background polling is intentionally not enabled by default.
- Market-condition evaluations use explicit operator-triggered checks and/or operator-provided sample values unless safe read-only data is explicitly integrated.
- Alerts are operational prompts only and should be reviewed manually.
