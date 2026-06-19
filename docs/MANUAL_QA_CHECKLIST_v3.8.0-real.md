# Manual QA Checklist — v3.9.0-real

- Launch the app.
- Open `/v3/freshness`.
- Create a policy through API.
- Create a queued demo collection job.
- Run the job manually.
- Run a freshness scan.
- Acknowledge, dismiss, snooze, and resolve a local notification.
- Export JSON/Markdown/CSV reports.
- Confirm no order placement, cancellation, or live arming.


## v3.7 Task Planner Addendum

The v3.7 release adds a local-first Operator Task Planner, task inbox, task board, daily ops checklist, weekly planning packet, review cadence manager, task templates, and task exports. These features are human-in-the-loop workflow records only. They do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass backend gates, or provide financial advice.


## v3.7 Task Planner Manual QA

- Open `/v3/tasks`, `/v3/tasks/board`, `/v3/tasks/inbox`, `/v3/tasks/today`, `/v3/tasks/week`, `/v3/tasks/cadence`, `/v3/tasks/templates`, `/v3/tasks/exports`, and `/v3/tasks/settings`.
- Confirm task pages show safety statements that tasks are not orders and task completion is not trade approval.
- Create a manual task through the API and confirm it appears on the board.
- Run inbox scan explicitly and confirm no live mutation occurs.
- Convert an inbox item to a task and confirm the source link/safety class remain visible.
- Generate daily and weekly packets and export them.
- Confirm live submission gates still require backend approval, warning acknowledgement, typed phrase, read-only disabled, live armed state, and kill switch disabled.

## Guided workspace checks

- Verify `/v3/workspace` and subroutes render.
- Verify daily, weekly, task triage, blocked, dependency, source preview, saved view, review packet, and settings panels.
- Verify no guided workspace button places or cancels orders.
- Verify guided review completion is not trade approval.
