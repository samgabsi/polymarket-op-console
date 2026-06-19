# Validation — v3.5.0-real

Validation should include syntax checks, unit tests, version checks, startup smoke tests, v3 release validation, v3 UX validation, screenshot helper dry-run, package cleanliness checks, secret scan, dataset export safety checks, and dataset no-live-mutation checks.

Expected release safety confirmations:

- No real order placement occurred.
- No real cancellation occurred.
- Dataset workflows do not arm live trading.
- Dataset/snapshot collection is read-only and non-autonomous.
- Demo data is fake and secret-free.
- Screenshots are not included in the release ZIP.
