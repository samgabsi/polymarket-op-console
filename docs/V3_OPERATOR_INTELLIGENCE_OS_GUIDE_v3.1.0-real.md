# v3 Operator Intelligence OS Guide — v3.3.0-real

v3 is the unified local-first operator layer on top of the detailed v2 console. v3.2 focuses on making the v3 experience polished, demo-ready, and release-candidate quality.

## What v3 is

- A command center for safety posture, data health, strategy, research, monitoring, portfolio, governance, and recent activity.
- A global local search interface.
- A local decision graph / object relationship explorer.
- A read-only workflow orchestrator for packets and briefs.
- A missing-prerequisite and conflict detector.
- A safe demo/visual QA layer.

## What v3 is not

- It is not autonomous trading.
- It is not financial advice.
- It is not an order approval system.
- It does not place, cancel, sign, approve, or arm live orders.
- It does not bypass backend live-trading gates.

## Command center

Open `/v3`. The command center groups status into Safety, Data Health, Research/Strategy, Monitoring, Portfolio, Governance, Recent Activity, and Next Actions.

## Global local search

Open `/v3/search`. Search stays local-first and uses local runtime objects only. Filter metadata is available through `/api/v3/search/filters`.

## Decision graph

Open `/v3/graph`. The graph links local objects such as theses, evidence, sources, alerts, exposure, governance, audit, and data-health findings. Filter metadata is available through `/api/v3/graph/filters`.

## Read-only workflows

Open `/v3/workflows`. Workflows generate drafts and reports only. v3.2 adds polished templates for pre-trade packets, market briefs, thesis health, portfolio risk, daily/weekly operator reviews, stale evidence, alert triage, data-health readiness, and no-trade review packets.

## Safe demo fixtures

Use `python scripts/create_v3_demo_data.py` to create fake local demo data. Use `python scripts/clear_v3_demo_data.py` to remove it. Demo data is fake, secret-free, and cannot place or cancel orders.

## Exports

v3 supports JSON and Markdown exports for graph, packets, briefs, and reports. Exports include safety statements and redact sensitive values.

## Known limitations

v3.2 does not enable external AI/model execution. It maintains a disabled provider boundary and deterministic local summaries. Visual screenshot capture may require optional local browser automation tools.
