# V4 Platform Diagnostics Guide — v4.0.0-real

## UI Routes

- `/v3/platform`
- `/v3/platform/health`
- `/v3/platform/routes`
- `/v3/platform/plugins`
- `/v3/platform/storage`
- `/v3/platform/diagnostics`
- `/v3/platform/exports`
- `/v3/platform/settings`

## API Routes

- `/api/v3/platform/summary`
- `/api/v3/platform/health`
- `/api/v3/platform/routes`
- `/api/v3/platform/plugins`
- `/api/v3/platform/storage`
- `/api/v3/platform/diagnostics`
- `/api/v3/platform/export.json`
- `/api/v3/platform/export.md`
- `/api/v3/platform/settings`

## What Diagnostics Show

Diagnostics show app version, route inventory, module inventory, local storage namespaces, plugin manifests, validation capability summary, export capability summary, safety posture, unknown/unavailable data, and no-live-mutation statements.

## What Diagnostics Do Not Do

Diagnostics do not place orders, cancel orders, approve trades, sign transactions, arm live trading, bypass backend gates, run network-heavy workflows on startup, call AI/model providers, expose secrets, or mutate live trading state.
