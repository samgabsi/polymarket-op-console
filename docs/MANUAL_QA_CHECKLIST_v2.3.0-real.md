# Manual QA Checklist — v2.3.0-real

Use this checklist before a demo or GitHub release. Do not enter or screenshot secrets.

## Installation and launch

- [ ] Create a clean virtual environment.
  - Steps: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
  - Expected: dependencies install without requiring live credentials.
  - Notes:
- [ ] Launch the app.
  - Steps: `python run.py`.
  - Expected: app starts locally and prints the configured host/port.
  - Notes:
- [ ] Open the console.
  - Steps: visit `/v2-live`.
  - Expected: dashboard renders with v2.3.0-real and persistent status bar.
  - Notes:

## Screenshots

Capture screenshots only after confirming no secrets are visible.

- [ ] Dashboard screenshot: `/v2-live`.
  - Expected: summary cards, status bar, and no secret values.
  - Notes:
- [ ] Markets screenshot: `/v2-live/markets`.
  - Expected: search controls, empty/loading states, collapsed raw details.
  - Notes:
- [ ] Trade Ticket screenshot: `/v2-live/trade-ticket`.
  - Expected: stepper, disabled submit until backend gates pass, confirmation fields visible.
  - Notes:
- [ ] Orders screenshot: `/v2-live/orders`.
  - Expected: read-only refresh button and cancellation gate controls.
  - Notes:
- [ ] Positions screenshot: `/v2-live/positions`.
  - Expected: unknown/unavailable states are clear when data is unavailable.
  - Notes:
- [ ] Risk screenshot: `/v2-live/risk`.
  - Expected: pass/fail readiness table and current limits.
  - Notes:
- [ ] Audit screenshot: `/v2-live/audit`.
  - Expected: filters, exports, and expandable details.
  - Notes:
- [ ] Settings screenshot: `/v2-live/settings`.
  - Expected: grouped settings and masked secret indicators.
  - Notes:
- [ ] Emergency screenshot: `/v2-live/emergency`.
  - Expected: kill-switch posture and deliberate emergency action buttons.
  - Notes:
- [ ] Verify screenshot: `/v2-live/verify`.
  - Expected: explicit verification form and no auto-network action.
  - Notes:
- [ ] Docs screenshot: `/v2-live/docs`.
  - Expected: task-based docs links including v2.3 verification/release docs.
  - Notes:

## Safety gates

- [ ] Live submit is blocked by default.
  - Expected: `READ_ONLY=true`, kill switch on, live armed off, submit gates off.
  - Notes:
- [ ] Kill switch blocks new live orders.
  - Expected: preview/risk states show blocker.
  - Notes:
- [ ] Read-only blocks live submit.
  - Expected: backend risk check returns fail/blocker.
  - Notes:
- [ ] Paper rehearsal does not call live endpoints.
  - Expected: paper preview/audit flow remains local.
  - Notes:
- [ ] No real order placement or real cancellation occurs during QA.
  - Expected: audit/validation reports confirm no submit/cancel network mutation.
  - Notes:

## Verification exports

- [ ] Run demo readiness.
  - Expected: `/api/v2/live/demo-readiness` returns pass/needs-review without live credentials.
  - Notes:
- [ ] Run verification without network.
  - Expected: `/api/v2/live/verify` returns skipped network checks and safety statement.
  - Notes:
- [ ] Export Markdown verification report.
  - Expected: `/api/v2/live/verify/report.md` renders a redacted report.
  - Notes:

## Final acceptance

- [ ] Tests pass.
- [ ] Secret scan passes.
- [ ] Package cleanliness check passes.
- [ ] Version references show v2.3.0-real.
- [ ] Release ZIP contains no runtime data, secrets, venv, caches, or OS junk.
