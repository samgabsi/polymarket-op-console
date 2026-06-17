# V2 to V3 Migration Guide — v3.3.0-real

v3.2 preserves v2 compatibility while polishing the v3 operator layer.

## What changed

- Current app version is `v3.3.0-real`.
- `/v3` remains the unified command center.
- v3.2 adds safer demo fixtures, visual QA docs, screenshot helper dry-run support, search/graph filters, and workflow templates.

## What remains compatible

Existing `/v2-live/*` routes remain available for detailed strategy, research, monitoring, portfolio, governance, data integrity, and live-trading control-plane workflows.

## How local data is reused

v3 reads local v2 runtime data and builds local search/graph/packet views. It does not require external services.

## After upgrade

1. Start the app.
2. Open `/v3`.
3. Run `python scripts/validate_v3_release.py --quick`.
4. Optionally create safe demo data for screenshots.
5. Review the visual QA checklist.

## Rollback guidance

Keep the prior release ZIP. Runtime data should be backed up before production-like usage. v3.2 does not require silent migrations to use the command center.
