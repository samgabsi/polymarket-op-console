# Manual QA Checklist — v2.4.0-real

Use this checklist in a browser with non-sensitive data.

## Startup

- [ ] Install dependencies.
- [ ] Start app with `python run.py`.
- [ ] Open `/v2-live`.
- Expected: version shows v2.4.0-real and safety status bar renders.
- Notes:

## Strategy page

- [ ] Open `/v2-live/strategy`.
- [ ] Confirm summary cards render.
- [ ] Create a draft thesis with test data.
- [ ] Add evidence linked to the thesis.
- [ ] Create a scorecard.
- [ ] Add a watchlist item.
- [ ] Create a post-trade review.
- [ ] Draft ticket from thesis.
- Expected: all actions create local strategy/audit records and no order is submitted.
- Notes:

## Safety checks

- [ ] Confirm thesis page states that a thesis is not an order.
- [ ] Confirm ticket draft does not call submit endpoint.
- [ ] Confirm live submit remains blocked by existing gates under default config.
- [ ] Confirm kill switch and read-only default posture remain visible.
- Notes:

## Exports

- [ ] Open `/api/v2/live/strategy/export.json`.
- [ ] Open `/api/v2/live/strategy/export.md`.
- [ ] Open `/api/v2/live/strategy/evidence.csv`.
- Expected: exports contain only redacted, non-secret research objects.
- Notes:

## Final acceptance

- [ ] Manual QA passed.
- [ ] No secrets exposed.
- [ ] No live order placed.
- [ ] No live order cancelled.
