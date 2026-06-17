# V2 to V3 Migration Guide — v3.0.0-real

## What changed

v3.0.0-real adds a new `/v3` namespace on top of the existing `/v2-live` console. v3 unifies local v2 modules through command-center summaries, search, decision graph relationships, read-only workflows, intelligence packets, and missing-prerequisite scans.

## What remained compatible

Existing `/v2-live/*` pages and `/api/v2/live/*` endpoints are preserved. v3 reads existing v2 local runtime data instead of requiring a destructive migration.

## Old and new routes

- Existing detailed console: `/v2-live`
- New unified command center: `/v3`
- Search: `/v3/search`
- Graph: `/v3/graph`
- Workflows and briefs: `/v3/workflows`, `/v3/briefs`

## Local data reuse

v3 reads the existing local-first strategy, research, monitoring, portfolio, governance, data integrity, and audit data. It does not require secrets or live network access.

## Rebuild indexes and graph

Use:

- `POST /api/v3/search/rebuild`
- `POST /api/v3/graph/rebuild`

These rebuild summaries from local data and do not place or cancel orders.

## Validate after upgrade

Run:

```bash
python -m compileall -q app tests scripts
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/check_release_package.py .
```

## Rollback guidance

Keep the v2.9.0-real ZIP and a redacted backup bundle before upgrading. If rollback is required, stop the app, restore the previous package, and restore runtime data from a backup created before any v3 data workflows.
