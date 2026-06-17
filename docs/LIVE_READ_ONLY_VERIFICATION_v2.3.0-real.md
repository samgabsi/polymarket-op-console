# Live Read-Only Verification — v2.3.0-real

The v2.3 verification harness is a release/demo confidence workflow for checking harmless read-only surfaces. It is explicitly triggered by the operator and is intentionally incapable of placing orders, signing orders for submission, arming live trading, mutating settings, or cancelling orders.

## Where to run it

- UI: `/v2-live/verify`
- JSON API: `/api/v2/live/verify`
- JSON report export: `/api/v2/live/verify/report`
- Markdown report export: `/api/v2/live/verify/report.md`
- Demo readiness: `/api/v2/live/demo-readiness`

## Safe defaults

Network verification is off by default at the API level. To attempt live read-only network checks, the operator must explicitly request it and set both:

```bash
POLYMARKET_LIVE_ALLOW_REAL_NETWORK=true
POLYMARKET_LIVE_NETWORK_READONLY=true
```

The harness still does not submit or cancel orders.

## Checks included

The report may include:

- environment/configuration loaded
- version check
- Gamma/CLOB/Data API host configuration
- credential presence summary with no secret values
- wallet address presence if configured
- optional Gamma market search
- optional CLOB order-book read for an operator-provided token ID
- optional positions/open-order read-only checks when credentials and read-only network gates permit
- redaction smoke check
- kill-switch/read-only/live-armed posture

## Report contents

Verification reports include app version, timestamp, mode, read-only state, live-armed state, kill-switch state, host configuration, status counts, per-check status, sanitized errors, and a safety statement confirming no real order placement or cancellation was performed.

## What not to do

Do not use this harness to test live submit/cancel. Live trading validation remains a separate, manual, gated workflow controlled by the operator and subject to Polymarket account eligibility and terms.
