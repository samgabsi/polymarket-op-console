# Governance / Decision Journal Guide — v2.8.0-real

## Purpose

The v2.8 governance layer adds a local-first operator accountability system to the Live v2 console. It helps the operator record decision rationale, run pre-trade checklists, complete post-trade and routine reviews, track recurring process mistakes, and document near-misses without automating execution.

## What it is not

- It is not autonomous trading.
- It is not financial advice.
- It is not approval to trade.
- It does not place orders.
- It does not cancel orders.
- It does not arm live trading.
- It does not bypass risk, approval, warning acknowledgement, typed confirmation, read-only, or kill-switch gates.

## Governance workspace

Open:

```text
/v2-live/governance
```

The workspace contains:

- Governance dashboard cards
- Decision journal table
- Pre-trade checklist panel
- Post-trade, daily, and weekly review workflow
- Governance rules
- Near-miss / rule violation tracking
- Mistake pattern tracking
- Governance report exports

## Decision journal entries

Decision journal entries capture structured operator reasoning before, during, or after a decision.

Recommended uses:

- Research decision
- Thesis decision
- Watchlist decision
- Trade-ticket decision
- Risk decision
- Portfolio decision
- Monitoring decision
- Emergency decision
- No-trade decision

Suggested fields:

- Decision summary
- Reasoning
- Confidence level
- Expected outcome
- Risk considered
- Alternative considered
- Follow-up date
- Linked market, thesis, evidence, alert, exposure, ticket, or order

A journal entry is not an order and does not authorize execution.

## Pre-trade checklists

The pre-trade checklist is a governance aid. It encourages the operator to verify:

- A thesis exists
- Evidence was reviewed
- Counter-evidence was reviewed
- Stale evidence was checked
- Research questions were resolved or acknowledged
- Risk limits were checked
- Portfolio exposure was checked
- Monitoring alerts were checked
- Entry, exit, and invalidation criteria exist
- Bankroll impact was reviewed
- No active emergency condition exists
- Warnings were reviewed
- A no-trade alternative was considered

Completing a checklist does not submit or approve a live order. Backend gates remain authoritative.

## Reviews

The governance layer supports:

- Post-trade reviews
- Daily operator reviews
- Weekly operator reviews
- Process/manual reviews

Reviews can document what went right, what went wrong, lessons learned, follow-up action, recurring patterns, and next focus areas.

Unknown live results must remain unknown/unavailable unless reliable audit or read-only data exists.

## Mistake patterns

Mistake patterns help track recurring process issues such as:

- Entering thesis too early
- Ignoring counter-evidence
- Relying on stale evidence
- Violating intended exposure limits
- Over-concentration
- Missing exit or invalidation criteria
- Ignoring monitoring alerts
- Creating tickets with insufficient evidence
- Emotional or impulsive decisions
- Unclear reasoning

This is process improvement, not medical or financial advice.

## Rule violations and near-misses

Near-miss records help document situations where process almost failed or a rule was violated.

Record:

- Related rule
- What happened
- Severity
- Whether money was at risk
- Whether live execution occurred
- Corrective action
- Status

Near-miss records do not block, submit, or cancel orders. They support operator review and discipline.

## Integration with the rest of Live v2

Governance links to:

- Strategy theses and reviews
- Research sources and evidence
- Monitoring alerts
- Portfolio exposure and scenarios
- Trade tickets
- Audit records

The trade-ticket page includes a governance status panel, but live submit still requires all existing backend gates.

## Exports

Available exports:

```text
/api/v2/live/governance/export.json
/api/v2/live/governance/export.md
/api/v2/live/governance/export/journal.csv
/api/v2/live/governance/export/checklists.csv
/api/v2/live/governance/export/mistakes.csv
/api/v2/live/governance/export/near-misses.csv
/api/v2/live/governance/export/rules.csv
/api/v2/live/governance/export/reviews.csv
```

Exports redact secrets and include a safety statement that governance records do not place or cancel orders.

## Known limitations

- Governance storage is local-first and not synced across devices.
- Governance guidance is workflow guidance only.
- Visual browser QA should be performed locally before release/demo.
- Governance does not replace legal, compliance, risk, or financial review.
