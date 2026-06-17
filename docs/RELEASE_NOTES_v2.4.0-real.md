# Release Notes — v2.4.0-real

`v2.4.0-real` adds the Strategy / Playbook Intelligence Layer.

## Highlights

- New `/v2-live/strategy` workspace.
- Local-first append-only strategy events for theses, evidence, watchlist items, scorecards, and reviews.
- Structured thesis builder.
- Evidence tracking with direction, relevance, credibility, and stale/archive state.
- Transparent scorecards with total and weighted scoring.
- Watchlists with target entry/exit and invalidation conditions.
- Post-trade review objects.
- Ticket-draft-from-thesis endpoint that never submits orders.
- Strategy JSON, Markdown, and CSV exports.
- Audit records for strategy actions.

## Safety

No live trading safety gates were weakened. Strategy objects are research artifacts only and never submit or cancel orders.
