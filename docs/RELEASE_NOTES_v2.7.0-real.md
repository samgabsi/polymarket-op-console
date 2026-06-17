# Release Notes — v2.7.0-real

v2.7.0-real adds the Portfolio / Exposure Intelligence Layer.

## Highlights

- New `/v2-live/portfolio` workspace.
- New `app/live_portfolio.py` local-first data layer.
- Exposure summaries by market, thesis, tag/playbook, watchlist, audit-derived notional, and operator-defined exposure groups.
- Local bankroll and risk-budget settings.
- Concentration warnings.
- Scenario planner and evaluation workflow.
- Planned trade impact preview.
- Portfolio JSON, Markdown, exposure CSV, warnings CSV, and scenarios CSV exports.
- Portfolio audit events integrated into the Live v2 audit ledger.

## Safety

No real order placement occurred during validation. No real cancellation occurred. Portfolio intelligence does not submit, sign, approve, arm, or cancel orders. Existing Live v2 gates remain intact.
