# V2 to V3 Migration Guide — v3.3.0-real

v3.2 preserves all v2 Live Console routes and adds analytics to the v3 namespace.

## What changed

- New `/v3/analytics` workspace.
- New analytics APIs under `/api/v3/analytics/*`.
- Learning reports and analytics exports.
- Analytics search and graph nodes.

## What stayed compatible

Existing `/v2-live/*` modules remain available for detailed live trading, strategy, research, monitoring, portfolio, governance, and data workflows.

## After upgrade

1. Start the app.
2. Open `/v3`.
3. Open `/v3/analytics`.
4. Generate or load demo data if needed.
5. Run validation and visual QA.
6. Confirm live trading safety gates remain intact.
