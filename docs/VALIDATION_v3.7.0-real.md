# Validation — v3.9.0-real

Validation should include syntax checks, unit tests, route smoke tests, template smoke tests, docs/version consistency checks, secret scans, package-cleanliness checks, startup smoke tests, v3 workflow safety tests, v3 export safety tests, task export safety tests, task no-live-mutation tests, task completion safety tests, demo fixture safety tests, and release validation harness execution.

## Expected safety confirmations

- No real order placement occurred.
- No real order cancellation occurred.
- Task/cadence workflows do not arm live trading.
- Task completion does not approve trades.
- Task planning is local-first and non-autonomous by default.
- Demo data is fake and secret-free.
- Screenshots are not included in the release ZIP unless explicitly safe and intended.

See the final release response for the exact commands run in this environment.
