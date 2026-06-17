# Manual QA Checklist — v2.5.0-real

Use this checklist before publishing or demoing v2.5.0-real.

## Startup

- [ ] Install dependencies.
- [ ] Launch `python run.py`.
- [ ] Open `/v2-live`.
- [ ] Expected: version shows v2.5.0-real.
- Notes:

## Research page

- [ ] Open `/v2-live/research`.
- [ ] Expected: Research Intake Workspace renders.
- [ ] Add a source.
- [ ] Add a queue item.
- [ ] Add source notes.
- [ ] Create an evidence candidate.
- [ ] Convert the candidate into strategy evidence.
- [ ] Expected: no order is submitted, signed, armed, or cancelled.
- Notes:

## Strategy integration

- [ ] Open `/v2-live/strategy`.
- [ ] Confirm converted evidence appears in strategy evidence export.
- [ ] Create or update a thesis manually.
- [ ] Expected: strategy remains draft/research only.
- Notes:

## Thesis comparison

- [ ] Generate a thesis comparison from `/v2-live/research`.
- [ ] Expected: counts for support/contradiction/neutral/stale evidence appear.
- [ ] Expected: comparison does not alter the thesis automatically.
- Notes:

## Exports

- [ ] Download research JSON export.
- [ ] Download research Markdown export.
- [ ] Download sources CSV.
- [ ] Download queue CSV.
- [ ] Download candidates CSV.
- [ ] Expected: exports contain no secrets.
- Notes:

## Safety gates

- [ ] Confirm Live Armed is not enabled by default.
- [ ] Confirm Kill Switch blocks live submit by default.
- [ ] Confirm Read-Only blocks live submit by default.
- [ ] Confirm paper mode does not call live endpoints.
- [ ] Confirm research actions do not create orders.
- Notes:

## Final acceptance

- [ ] Tests passed.
- [ ] Secret scan passed.
- [ ] Package cleanliness passed.
- [ ] No real order placement.
- [ ] No real cancellation.
- [ ] README, CHANGELOG, release notes, validation, and research guide updated.
