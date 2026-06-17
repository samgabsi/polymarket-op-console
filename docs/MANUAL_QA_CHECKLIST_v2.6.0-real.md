# Manual QA Checklist — v2.6.0-real

Use this checklist before tagging or demoing the release.

## Startup

- [ ] Install dependencies.
- [ ] Run `python run.py`.
- [ ] Open `/v2-live`.
- Expected: dashboard renders and version displays v2.6.0-real.
- Notes:

## Monitoring page

- [ ] Open `/v2-live/monitoring`.
- Expected: monitoring dashboard cards, rule form, notification center, rules table, and exports are visible.
- Notes:

## Create alert rule

- [ ] Create a price threshold or manual alert rule.
- Expected: API result appears; no order is submitted; audit entry is recorded.
- Notes:

## Evaluate alert rule

- [ ] Evaluate the rule with a sample current value that triggers it.
- Expected: active alert appears; no order/cancel/arm action occurs.
- Notes:

## Acknowledge / snooze

- [ ] Copy alert ID.
- [ ] Acknowledge it.
- [ ] Create/evaluate another alert and snooze it.
- Expected: status changes are visible and audited.
- Notes:

## Exports

- [ ] Open JSON export.
- [ ] Open Markdown export.
- [ ] Open rules CSV.
- [ ] Open alerts CSV.
- Expected: exports contain no secrets and include safety statement.
- Notes:

## Existing routes

- [ ] Strategy route still renders.
- [ ] Research route still renders.
- [ ] Trade Ticket route still renders.
- [ ] Emergency route still renders.
- Expected: no safety regression.
- Notes:

## No real execution

- [ ] Confirm no live orders were placed.
- [ ] Confirm no live orders were cancelled.
- [ ] Confirm live mode was not armed by monitoring.
- Expected: monitoring is awareness-only.
- Notes:
