# Manual QA Checklist — v3.0.0-real

## Startup

- [ ] Run `python run.py`.
- [ ] Open `/v2-live`.
- [ ] Expected: version displays v3.0.0-real.

## Data workspace

- [ ] Open `/v2-live/data`.
- [ ] Expected: Data health dashboard renders.
- [ ] Run health check.
- [ ] Expected: results show pass/warning/fail counts without secrets.
- [ ] Run secret scan.
- [ ] Expected: findings, if any, are redacted.
- [ ] Create redacted backup.
- [ ] Expected: backup bundle path and manifest appear.
- [ ] Validate backup.
- [ ] Expected: manifest is readable.
- [ ] Preview restore.
- [ ] Expected: impact summary is shown.
- [ ] Try restore without confirmation.
- [ ] Expected: blocked.
- [ ] Run migration dry-run.
- [ ] Expected: no mutation performed.

## Safety

- [ ] Confirm no order was placed.
- [ ] Confirm no order was cancelled.
- [ ] Confirm live trading did not arm.
- [ ] Confirm existing trade-ticket gates still block without required approval/risk/confirmation state.
