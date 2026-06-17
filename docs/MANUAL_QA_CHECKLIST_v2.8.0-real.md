# Manual QA Checklist — v2.8.0-real

Use this checklist in a browser before demo or release.

## Startup

- [ ] Install dependencies.
- [ ] Launch the app.
- [ ] Open `/v2-live`.
- [ ] Expected: dashboard renders and version displays v2.8.0-real.
- Notes:

## Navigation

- [ ] Open Dashboard.
- [ ] Open Markets.
- [ ] Open Strategy.
- [ ] Open Research.
- [ ] Open Monitoring.
- [ ] Open Portfolio.
- [ ] Open Governance.
- [ ] Open Trade Ticket.
- [ ] Open Audit.
- [ ] Expected: current nav item is obvious and pages render without errors.
- Notes:

## Governance workspace

- [ ] Open `/v2-live/governance`.
- [ ] Create a decision journal entry.
- [ ] Create a pre-trade checklist.
- [ ] Create a post-trade review.
- [ ] Create a daily review.
- [ ] Create a weekly review.
- [ ] Create a governance rule.
- [ ] Record a near-miss.
- [ ] Create a mistake pattern.
- [ ] Expected: each action records local governance data and does not place or cancel orders.
- Notes:

## Trade ticket governance panel

- [ ] Open `/v2-live/trade-ticket`.
- [ ] Confirm governance status panel is visible.
- [ ] Confirm it clearly states checklist/governance is not execution approval.
- Notes:

## Exports

- [ ] Open `/api/v2/live/governance/export.json`.
- [ ] Open `/api/v2/live/governance/export.md`.
- [ ] Open `/api/v2/live/governance/export/journal.csv`.
- [ ] Open `/api/v2/live/governance/export/checklists.csv`.
- [ ] Open `/api/v2/live/governance/export/mistakes.csv`.
- [ ] Expected: exports download/render and contain no secrets.
- Notes:

## Safety gates

- [ ] Attempt live submit without required gates in a test environment.
- [ ] Expected: backend blocks submit.
- [ ] Confirm governance actions do not submit, sign, approve, arm, or cancel orders.
- Notes:

## Final acceptance

- [ ] Tests passed.
- [ ] Package cleanliness check passed.
- [ ] Secret scan passed.
- [ ] Browser QA passed.
- [ ] Release notes reviewed.
- [ ] Release ZIP contains no runtime governance data.
