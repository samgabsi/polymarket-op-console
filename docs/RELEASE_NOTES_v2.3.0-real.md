# Release Notes — v2.3.0-real

v2.3.0-real is a release/demo hardening milestone. It adds explicit live read-only verification, demo readiness checks, release checklist, manual browser QA guidance, startup/package validation scripts, and redacted verification report exports.

## Highlights

- `/v2-live/verify` verification page
- `/api/v2/live/verify` JSON verification endpoint
- `/api/v2/live/verify/report` JSON report export
- `/api/v2/live/verify/report.md` Markdown report export
- `/api/v2/live/demo-readiness` no-credential demo checks
- v2.3 manual QA checklist
- v2.3 release checklist with GitHub release draft
- startup/package/version helper scripts
- all live safety gates preserved

## Safety

No validation path places orders, signs orders for submission, arms live trading, mutates settings, or cancels orders. Live trading remains default-off, kill switch default-on, and read-only default-on.
