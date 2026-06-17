# Manual QA Checklist — v2.7.0-real

Use this checklist in a local browser session. Do not enter secrets in screenshots.

## Startup

- [ ] Install dependencies.
- [ ] Launch with `python run.py`.
- [ ] Open `/v2-live`.
- Expected: dashboard renders and version displays v2.7.0-real.
- Notes:

## Portfolio page

- [ ] Open `/v2-live/portfolio`.
- Expected: portfolio dashboard, bankroll panel, exposure table, warnings, scenarios, and planned-impact panel render.
- Notes:

## Bankroll settings

- [ ] Save sample bankroll limits.
- Expected: response is recorded locally; no order is placed or cancelled.
- Notes:

## Exposure group

- [ ] Create a manual exposure group.
- Expected: exposure group appears in portfolio refresh/export and audit records.
- Notes:

## Scenario planner

- [ ] Create and evaluate a scenario.
- Expected: evaluation returns affected exposure and safety statement; no order action occurs.
- Notes:

## Planned impact

- [ ] Run planned impact preview with sample price/size.
- Expected: before/after exposure is shown; submit gates are not touched.
- Notes:

## Existing safety gates

- [ ] Confirm `/v2-live/trade-ticket` still requires preview, risk checks, human approval, warning acknowledgement, typed confirmation, Live Armed mode, read-only disabled, kill switch disabled, and backend submit gates.
- Expected: default posture blocks live submit.
- Notes:

## Exports

- [ ] Download JSON, Markdown, exposure CSV, warnings CSV, and scenarios CSV.
- Expected: exports contain no secrets and include safety statements.
- Notes:

## Release acceptance

- [ ] Run tests.
- [ ] Run version checker.
- [ ] Run package cleanliness checker.
- [ ] Confirm no runtime portfolio/audit/strategy/research/monitoring data is included in the release ZIP.
