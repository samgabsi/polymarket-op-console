# UI/UX Guide — v2.2.0-real

`v2.2.0-real` is a browser-polish release for the Live v2 operator console. It builds on the v2.1 declutter pass and focuses on actual browser usability: saved safe preferences, interactive tables, clearer loading/error states, better refresh behavior, and manual QA guidance.

## Navigation

The Live v2 console remains organized around task routes:

- Dashboard: `/v2-live`
- Markets: `/v2-live/markets`
- Trade Ticket: `/v2-live/trade-ticket`
- Orders: `/v2-live/orders`
- Positions: `/v2-live/positions`
- Risk: `/v2-live/risk`
- Audit: `/v2-live/audit`
- Settings: `/v2-live/settings`
- Emergency: `/v2-live/emergency`
- Docs: `/v2-live/docs`

## Saved UI preferences

The console uses browser localStorage for harmless UI preferences only:

- default table page size
- default market search query
- compact mode
- advanced/debug details expanded by default

The schema endpoint is `/api/v2/live/ui/preferences/schema`. It explicitly disallows secrets and sensitive account data. Do not place wallet secrets, API keys, auth headers, account payloads, or private data in browser storage.

## Interactive tables

`v2.2.0-real` adds compact filtering and sortable/readable table behavior for risk checks, audit events, fetched API results, reconciliation rows, and large operator lists where practical. Raw details remain collapsed by default.

## Refresh behavior

Refresh remains manual and read-only by default. Buttons show pending states, disable while running, and display timeout/error responses in-page. The UI does not auto-place orders, auto-cancel, sign, or call dangerous endpoints.

## Trade Ticket polish

The Trade Ticket keeps the same backend safety model but improves the browser flow with clearer disabled-state copy, reset/copy controls, loading states, and explicit step labels. Submit remains impossible unless backend risk, approval, warning acknowledgement, typed confirmation, live-armed mode, read-only, kill-switch, and submit gates all pass.

## Accessibility basics

Forms use labels, buttons have explicit text, disabled actions explain why, status is represented with text and badges, tables have headers, errors render as readable text, and focus styling is preserved.

## Manual QA

Use `docs/MANUAL_QA_CHECKLIST_v2.2.0-real.md` before publishing a release or demoing the operator console.
