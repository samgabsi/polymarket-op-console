# Release Checklist — v3.9.0-real

- Version references updated to v3.9.0-real.
- Freshness scheduler docs present.
- Tests pass.
- Release validation passes.
- Package cleanliness passes.
- No runtime freshness policies/jobs/notifications are included.
- No real orders or cancellations occurred.


## v3.7 Task Planner Addendum

The v3.7 release adds a local-first Operator Task Planner, task inbox, task board, daily ops checklist, weekly planning packet, review cadence manager, task templates, and task exports. These features are human-in-the-loop workflow records only. They do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass backend gates, or provide financial advice.


## v3.7 Task Planner Release Checks

- Version references updated to v3.9.0-real.
- Operator task planner guide included.
- Task routes and APIs smoke-tested.
- Task exports are secret-safe.
- Task completion safety tested.
- No live mutation endpoints are called from task, cadence, daily ops, weekly planning, notification, finding, dataset, freshness, simulation, analytics, search, graph, or workflow integrations.
- Runtime task records, runtime task exports, daily ops packets, weekly ops packets, cadence runs, screenshots, caches, logs, and local credentials are excluded from the release ZIP.

## Guided workspace checks

- Verify `/v3/workspace` and subroutes render.
- Verify daily, weekly, task triage, blocked, dependency, source preview, saved view, review packet, and settings panels.
- Verify no guided workspace button places or cancels orders.
- Verify guided review completion is not trade approval.
