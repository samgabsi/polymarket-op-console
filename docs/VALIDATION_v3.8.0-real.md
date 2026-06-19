# Validation — v3.9.0-real

Validation expectations for this release include syntax checks, startup smoke tests, route smoke tests, v3 release validation, UX validation, task export safety, guided workspace export safety, no-live-mutation checks, guided review completion safety, package cleanliness, and secret scanning.

Safety confirmations expected before packaging:

- No real order placement occurred.
- No real cancellation occurred.
- Task, cadence, and guided workflows do not arm live trading.
- Task completion does not approve trades.
- Guided review completion does not approve trades.
- Guided reviews are local-first and non-autonomous by default.
- Demo data is fake and secret-free.
- Screenshots are not included in the release ZIP unless explicitly safe and intended.
