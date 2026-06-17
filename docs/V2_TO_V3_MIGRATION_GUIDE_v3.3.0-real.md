# V2 to V3 Migration Guide — v3.3.0-real

v3.3.0-real is compatible with the existing v2-live routes and local-first data model.

## What changed

The v3 interface has been redesigned with grouped navigation, a new command center layout, improved search/graph/workflow/report pages, and stronger safety visibility.

## What remained compatible

- Existing `/v2-live/*` routes remain available.
- Local strategy, research, monitoring, portfolio, governance, data, v3, and analytics records continue to be used.
- Backend safety gates remain the authority for live submission.

## After upgrade

1. Start the app.
2. Open `/v3`.
3. Run `PYTHONPATH=. python scripts/validate_v3_ux_release.py --quick`.
4. Run visual QA before publishing screenshots.

## Rollback

Keep the previous ZIP and runtime data backups. v3.3 does not require cloud services or autonomous migration to run.
