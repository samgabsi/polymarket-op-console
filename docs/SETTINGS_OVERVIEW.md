# Settings Overview v1.9.0-real

v1.9.0-real streamlines the configuration experience around a new `/settings` landing page.

The settings hub answers the operator's most common questions first:

- current app version
- configuration health
- host-training status
- internet-ingestion status
- paper-mode status
- live-trading status
- LAN exposure status
- restart-required count
- changed-from-default count
- warnings, blockers, and missing secret counts
- last config save, backup, and audit references

The page is a dashboard, not a raw environment editor. It links to the configuration console, setup wizard, runtime status, sanitized exports, audit history, host-training settings, data-ingestion settings, paper settings, live-readiness settings, risk controls, and advanced settings.

## Health states

- `Safe`: no blockers and no major attention items were detected.
- `Needs Attention`: warnings, LAN exposure, missing optional secrets, or other review items are present.
- `Restart Required`: saved `.env` values differ from the running process or process environment overrides are active.
- `Blocked`: validation blockers are present.
- `Advanced / Dangerous Values Present`: execution-facing or dangerous controls are enabled or need review.

These states are explanatory. They do not weaken backend gates.

## Recommended setup panel

The Recommended Setup panel provides direct links to safe next actions such as using the 100K Host Training preset, reviewing LAN exposure, or opening Advanced Mode to inspect warnings. It never makes automatic changes.

## Safety posture

The settings UI does not submit orders, cancel orders, sign messages, touch wallets, run shell commands, run pip, mutate the virtual environment, expose full secrets, or bypass live-readiness/manual-review gates.

Training and signal-preview outputs remain:

```text
manual_review_only=true
can_live_trade=false
```
