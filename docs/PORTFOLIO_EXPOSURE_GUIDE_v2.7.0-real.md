# Portfolio / Exposure Guide — v2.7.0-real

## Purpose

The Portfolio / Exposure Intelligence Layer helps the operator understand exposure before a trade reaches execution. It is local-first and human-in-the-loop. It summarizes locally available exposure records, thesis limits, watchlist context, audit-derived notional, operator-defined exposure groups, bankroll settings, concentration warnings, scenarios, and planned trade impact previews.

## What it is not

- It is not autonomous trading.
- It is not financial advice.
- It is not approval to trade.
- It does not submit, sign, approve, arm, or cancel orders.
- It does not bypass risk checks, warning acknowledgement, typed confirmation, read-only state, kill switch state, Live Armed mode, or backend submit gates.

## Workspace

Open:

```text
/v2-live/portfolio
```

The workspace includes:

- Portfolio dashboard cards
- Exposure table
- Bankroll / risk-budget settings
- Concentration warnings
- Scenario planner
- Planned trade impact preview
- JSON, Markdown, and CSV exports

## Exposure estimates

The portfolio layer uses available local/read-only data only. It may include:

- Strategy thesis maximum acceptable exposure
- Watchlist interest with unknown size
- Locally audited ticket preview/order notional when present
- Operator-defined exposure groups
- Planned trade impact preview records

Unknown or unavailable values are shown explicitly. The system does not invent live P&L, live balances, or confirmed exposure when the data source is unavailable.

## Exposure categories

The UI distinguishes:

- Actual live exposure, when safe read-only account data is available
- Read-only reported exposure
- Locally audited exposure
- Paper exposure
- Planned exposure
- Unknown exposure

## Bankroll and risk-budget settings

The bankroll panel lets the operator set local explicit values:

- Total bankroll
- Live trading bankroll
- Paper bankroll
- Max portfolio exposure
- Max per-market exposure
- Max per-thesis exposure
- Max per-tag/playbook exposure
- Max daily notional
- Max daily loss, if available
- Reserve cash / do-not-use amount

These values are local operator settings. Do not enter secrets.

## Concentration warnings

Warnings may be generated when:

- Total exposure exceeds the configured portfolio limit
- One market exceeds the configured per-market limit
- One thesis exceeds the configured per-thesis limit
- One tag/playbook exceeds the configured per-tag limit
- Exposure records contain unknown fields
- Stale evidence exists while exposure records are present
- Active monitoring alerts exist while exposure records are present

Warnings are workflow guidance only.

## Scenario planning

Scenarios can model simple operator-review cases such as:

- Market resolves YES
- Market resolves NO
- Thesis succeeds
- Thesis fails
- Planned ticket fills fully
- Planned ticket partially fills
- Stale evidence invalidates a thesis
- Liquidity disappears

Scenario output shows affected exposure, estimated impact where possible, unknown/unavailable values, related warnings, and recommended operator review action.

## Planned trade impact

The planned impact tool accepts market, thesis, tag, price, size, and optional notional. It estimates exposure before and after the planned ticket. It does not submit a ticket or call live execution.

## Integration with strategy, research, and monitoring

Portfolio views can link context from:

- Strategy theses and watchlists
- Research stale-evidence/freshness status
- Monitoring active alerts
- Live v2 audit records

The operator must manually update theses, research, monitoring rules, or tickets. Nothing is changed automatically.

## Exports

Available exports:

- `/api/v2/live/portfolio/export.json`
- `/api/v2/live/portfolio/export.md`
- `/api/v2/live/portfolio/export/exposure.csv`
- `/api/v2/live/portfolio/export/warnings.csv`
- `/api/v2/live/portfolio/export/scenarios.csv`

Exports include a safety statement and must not contain secrets.

## Known limitations

- Storage is local-first and not synced between devices.
- Actual live exposure depends on safe read-only account data availability.
- Scenario output is simplified workflow guidance.
- Portfolio warnings are not financial advice and are not trade recommendations.
