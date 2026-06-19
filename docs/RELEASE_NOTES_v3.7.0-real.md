# Release Notes — v3.9.0-real

v3.9.0-real adds the **Operator Task Planner, Review Cadence Manager, and Human-in-the-Loop Daily Ops Layer**.

## Added

- Local-first operator task model in `app/live_v3_tasks.py`.
- Task inbox for notifications, findings, stale data, governance items, analytics warnings, simulation follow-ups, monitoring alerts, research items, portfolio warnings, data health issues, and manual tasks.
- Task board with Inbox, Planned, Active, Waiting, Blocked, Done, and Archived states.
- Daily ops checklist and Daily Ops Packet generation.
- Weekly planning workflow and Weekly Ops Packet generation.
- Review cadence rules and operator-triggered cadence runs.
- Task templates for stale evidence, dataset refresh, monitoring alert, thesis health, pre-trade packet review, governance checklist, portfolio warning, simulation replay, learning report, data health, unresolved research, missing prerequisites, and backup/export readiness.
- Notification-to-task and finding-to-task conversion APIs.
- Task exports in JSON, Markdown, and CSV; daily/weekly packet exports in JSON and Markdown.
- Command center, search, graph, workflow, freshness, dataset, simulation, analytics, demo fixture, screenshot-helper, and validation integrations.

## Safety

- Tasks do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass backend gates, or provide financial advice.
- Task completion is explicitly not trade approval.
- Cadence plans are not trading automation.
- Priority is operator workflow priority only.
- Existing v2-live safety controls, read-only gates, kill switch behavior, approval checkbox, typed confirmation phrase, warning acknowledgements, audit logging, and emergency controls are preserved.
