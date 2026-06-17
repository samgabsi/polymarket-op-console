# Manual QA Checklist — v2.2.0-real

This checklist validates the browser-polished Live v2 operator console without placing real orders. Use a clean local browser profile or incognito window when checking saved UI preferences.

## Preconditions

- Start the app locally with the package's normal run command.
- Keep `READ_ONLY=true`, `POLYMARKET_LIVE_KILL_SWITCH=true`, and submit/cancel gates disabled unless you are deliberately testing a local, credentialed environment.
- Do not paste real secrets into screenshots or issue reports.
- Confirm `/health` returns `2.2.0-real`.

## App startup

- Open `/` and confirm the app renders without errors.
- Open `/v2-live` and confirm the Live v2 Console loads.
- Expected: no automatic order placement, cancellation, wallet signing, or dangerous private endpoint call occurs.

## Navigation

- Visit `/v2-live`, `/v2-live/markets`, `/v2-live/trade-ticket`, `/v2-live/orders`, `/v2-live/positions`, `/v2-live/risk`, `/v2-live/audit`, `/v2-live/settings`, `/v2-live/emergency`, and `/v2-live/docs`.
- Expected: each page has a clear title, active nav item, persistent status bar, and no giant raw JSON dump by default.

## Dashboard

- Confirm dashboard cards show mode, readiness, kill switch, orders, positions, today's notional, risk, and audit count.
- Expected: unknown/unavailable account data is labeled as such rather than invented.

## Status bar

- Click **Refresh status**.
- Expected: the button shows a pending state, then updates last refresh/critical error text using only read-only status data.

## Markets

- Search for a public market keyword with a small limit.
- Expected: results appear in a compact table with a row filter and collapsed raw response.
- Fetch an order book with a token ID if available.
- Expected: best bid/ask show if present; failures are displayed as readable error states.

## Trade ticket

- Fill Market ID, Token ID, side, price, and size.
- Click **Preview + risk check**.
- Expected: default fail-closed settings produce risk blockers and keep **Submit live order** disabled.
- Check human approval and warning acknowledgement, then enter the default phrase.
- Expected: backend gates still control submit; browser UI alone cannot bypass risk/read-only/kill-switch gates.
- Use **Reset ticket** and **Copy ticket summary**.
- Expected: reset clears state; copy contains only ticket fields, not secrets.

## Orders

- Click **Refresh open orders**.
- Expected: if read-only live network is disabled, a clear disabled/unavailable state is shown.
- Use the order filter field when rows are present.
- Expected: filtering updates visible rows without full-page reload.

## Positions

- Click **Refresh positions** and **Run reconciliation**.
- Expected: wallet/network missing states are clear; reconciliation creates an audit record and never invents P&L.

## Risk

- Filter the readiness table.
- Expected: result count updates and pass/fail/warn badges remain readable.
- Confirm kill-switch, read-only, approval, confirmation, and risk-limit dependencies are visible.

## Audit

- Preview a ticket to create a local audit record.
- Open `/v2-live/audit`.
- Test text search, mode filter, status filter, sortable headers, raw details, and copy ID.
- Export JSON, CSV, and Markdown.
- Expected: exports work and secrets remain redacted.

## Settings

- Confirm grouped sections are visible: General, Trading Mode, API Hosts, Credentials / Secrets, Live Trading Gates, Risk Limits, Order Defaults, Paper Trading, Audit / Exports, Advanced / Debug.
- Validate a candidate JSON object.
- Expected: results are read-only, secret-safe, and never write environment files.

## Emergency controls

- Confirm the kill-switch state is unmistakable.
- Trigger a preview/record action only.
- Expected: confirmation appears; audit receipt is recorded; environment state remains operator-controlled.

## Docs

- Open `/v2-live/docs`.
- Expected: task-based links appear for First Run, Paper Mode, Live Read-Only, Live Trading, Trade Ticket, Risk Controls, Order Lifecycle, Emergency Controls, Audit/Exports, Troubleshooting, Environment Variables, and Manual QA.

## Responsive/narrow-width check

- Narrow the browser below 900px.
- Expected: tabs scroll/wrap, preference grid stacks, forms remain usable, and the status bar does not cover content.

## Loading/error/disabled-state checks

- Use refresh/search buttons while throttling network or entering invalid token/order IDs.
- Expected: buttons disable while pending, errors render in readable boxes, and dangerous actions remain blocked.

## Secret redaction checks

- Confirm UI preference localStorage contains only harmless UI keys.
- Confirm no private key, API key, secret, passphrase, auth header, or wallet secret appears in UI, audit exports, console output, screenshots, or docs.

## Live safety gate checks

- With default settings, attempt a ticket preview and submit.
- Expected: submit is blocked by kill switch/read-only/not-armed/submit-gate/risk settings.

## Kill switch check

- Confirm `POLYMARKET_LIVE_KILL_SWITCH=true` blocks new live submits.

## Read-only mode check

- Confirm `READ_ONLY=true` blocks live submit.

## Paper mode check

- Set paper mode only in a controlled local environment.
- Expected: ticket rehearsal and audit behavior remain local; no live endpoint is called for paper mode.

## No-real-order-placement validation

- Run tests.
- Expected: tests use mocks/fail-closed adapters only. No real submit/cancel/signing/wallet-touching behavior occurs.

## Screenshot capture guidance

Capture screenshots only with redacted/non-sensitive data. Suggested pages:

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
