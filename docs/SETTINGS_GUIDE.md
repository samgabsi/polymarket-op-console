# Settings Guide — v2.3.0-real

Live v2 settings are grouped for operator readability at `/v2-live/settings`.

## Sections

- General
- Trading Mode
- API Hosts
- Credentials / Secrets
- Live Trading Gates
- Risk Limits
- Order Defaults
- Audit / Exports
- Advanced / Debug

The page is a safe map and validator. It does not write secrets or silently mutate `.env`.

## Validation endpoint

`POST /api/v2/live/settings/validate` accepts a small JSON object of candidate values and returns:

- `valid`
- `errors`
- `warnings`
- `secret_values_returned=false`

Use the full configuration console at `/settings/configuration` when you want to apply changes through the existing audited settings workflow.

## v2.2.0 safe UI preferences

The Live v2 console includes a small browser-local preference panel for non-sensitive UI behavior: default table size, optional default market query, compact mode, and advanced/debug expansion. The endpoint `/api/v2/live/ui/preferences/schema` documents the allowed keys. Do not store secrets, private keys, wallet data, auth headers, or API credentials in browser localStorage.
