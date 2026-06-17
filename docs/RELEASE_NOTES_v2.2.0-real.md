# Release Notes — v2.2.0-real

`v2.2.0-real` is the Browser-Polished Interactive Operator Console release. It preserves the v2.0/v2.1 live-trading safety model and focuses on real browser usability, interactive tables, saved safe UI preferences, loading/error polish, and manual QA coverage.

## Highlights

- Browser-polished Live v2 console with improved spacing, status refresh, disabled states, and task continuity.
- Saved safe UI preferences using localStorage for non-sensitive UI choices only.
- New preference schema endpoint: `/api/v2/live/ui/preferences/schema`.
- Interactive filtering/sorting/result counts for readiness and audit tables.
- Compact rendered tables for fetched markets, orders, positions, and reconciliation results.
- Trade Ticket reset/copy controls and clearer disabled-submit messaging.
- Server-side audit filter parameters on `/api/v2/live/audit`.
- New manual browser QA checklist and screenshot capture guidance.

## Safety preserved

- Live trading remains default-off.
- Kill switch remains default-on.
- Read-only remains default-true.
- Live submit still requires backend risk pass, human approval, warning acknowledgement, typed confirmation phrase, live armed mode, kill switch off, read-only off, real network allowed, and submit gates enabled.
- Tests do not place real orders.
- Secrets remain redacted from UI/API/audit outputs.

## Migration from v2.1.0-real

No data migration is required. Existing `.env` settings and audit ledgers continue to work. Operators may optionally reset browser UI preferences from the Live v2 preferences panel.

## Known limitations

Visual browser QA should still be performed in the operator's actual browser before public demos. Live read-only data continues to depend on local credentials, account eligibility, network access, and Polymarket API availability. P&L is not invented when reliable data is unavailable.
