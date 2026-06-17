# V3 Operator Intelligence OS Guide — v3.0.0-real

## What v3 is

v3.0.0-real unifies the existing v2 modules into a local-first operator intelligence OS. It gives the operator one command center for system posture, search, object relationships, read-only workflows, intelligence packets, and review outputs.

## What v3 is not

v3 is not autonomous trading. It is not financial advice. It does not place orders, cancel orders, approve orders, sign orders, arm live trading, or override risk checks.

## Command Center

Open `/v3` or `/v3/command-center` to see:

- live mode / read-only / kill switch posture
- readiness state
- data health state
- active theses
- research queue count
- stale evidence count
- active alerts
- concentration warnings
- governance checklist state
- recent decisions
- recent audit events
- risk blocks
- action-needed findings

## Global Local Search

Open `/v3/search` or use `/api/v3/search`. Search indexes local runtime data only. It searches theses, evidence, sources, notes, alerts, exposure records, governance entries, audit events, and data health results.

No local search data is sent to external services.

## Decision Graph

Open `/v3/graph` or use `/api/v3/graph`. The decision graph builds nodes and relationships from local objects, including theses, evidence, sources, alerts, exposure, governance, audit, and data health records.

The graph is an operator navigation and context tool. It is not a trade recommendation engine.

## Read-only workflow orchestrator

Open `/v3/workflows`. v3 workflows gather local context and create draft outputs such as:

- Market Intelligence Brief
- Thesis Health Review
- Pre-Trade Intelligence Packet
- Portfolio Risk Brief
- Stale Evidence Review
- Alert Triage Brief
- Governance Daily Review
- Weekly Operator Review
- Data Health / Backup Readiness Brief
- No-Trade Review Packet

Workflow runs are read-only and audited.

## Pre-trade intelligence packets

The pre-trade packet gathers market, thesis, evidence, stale evidence, research questions, scorecards, watchlist status, alerts, portfolio exposure, governance checklist state, risk pre-check context, data health warnings, readiness posture, and audit references.

It does not submit anything. If the operator later creates a trade ticket, the original backend gates still apply.

## Market briefs

Market briefs summarize local research, linked sources, evidence candidates, theses, watchlists, alerts, and missing research. They are intended to help research review, not to advise trades.

## Thesis health reports

Thesis health reports evaluate evidence coverage, counter-evidence, stale evidence, unresolved questions, alerts, exposure, governance context, and invalidation readiness.

## Portfolio risk briefs

Portfolio risk briefs summarize exposure, warnings, scenarios, stale-evidence exposure, monitoring alerts, governance near-misses, and unknown/unavailable values.

## Operator review packets

Daily and weekly packets summarize decisions, evidence added, alerts, portfolio warnings, governance checklist state, risk blocks, data health, and unresolved items.

## Missing-prerequisite detection

The v3 scan highlights conflicts such as theses without evidence, missing counter-evidence review, missing exit/invalidation criteria, exposure linked to weak data, active alerts, or failing data health.

Findings are warnings/blockers for operator review only.

## AI assistance boundary

v3 includes a safe provider boundary. AI/model assistance is disabled by default. The deterministic local fallback does not send secrets or local data to an external provider. Any future provider must remain explicit, redacted, previewable, and advisory-only.

## Exports

v3 supports JSON and Markdown exports for search/graph/workflow reports, packets, briefs, and missing-prerequisite scans. Exports include safety statements and redaction.

## Safety guarantee

v3 does not bypass live trading gates. Live order submission still requires backend risk checks, human approval, warning acknowledgement, typed confirmation, Live Armed mode, read-only disabled, kill switch disabled, and submit gate enablement.
