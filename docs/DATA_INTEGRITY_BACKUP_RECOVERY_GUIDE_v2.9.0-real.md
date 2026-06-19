# Data Integrity / Backup / Recovery Guide — v3.0.0-real

## What this layer is

The v2.9 data layer is a local-first durability and recovery workspace for the Polymarket OP Console runtime data. It helps the operator inspect health, validate records, create redacted backups, preview restores, run controlled imports/exports, inspect migration status, and produce recovery reports.

## What this layer is not

It is not an execution system, trading strategy, predictor, or autonomous agent. A backup does not place or cancel orders. A restore does not authorize live trading. A migration does not approve trading. Live submit still requires every existing backend gate.

## Runtime data location

Runtime data is kept under local data paths such as `data/live_v2/`. The release ZIP must not include real runtime audit ledgers, strategy records, research data, monitoring data, portfolio data, governance data, backup bundles, restore reports, logs, or screenshots with secrets.

## Data health checks

Use `/v2-live/data` or `/api/v2/live/data/health/run` to inspect runtime data. Checks cover missing subsystem paths, invalid JSON/JSONL, duplicate IDs, empty/oversized files, required field warnings, and secret-like content.

## Secret scanning

The secret scanner reports only path and pattern class. It never prints secret values. Default backup/export workflows redact content and exclude known secret-bearing files such as real `.env` files and local credentials.

## Backup bundles

Backups include a manifest, app version, selected subsystems, file inventory, checksums, schema versions, redaction policy, restore instructions, and a safety statement. Default backups are redacted.

## Restore workflow

Restore is deliberate:

1. Validate the bundle.
2. Preview restore impact.
3. Confirm explicitly with `RESTORE DATA`.
4. Apply restore.
5. Validate restored data.

Restore does not place orders, cancel orders, arm live trading, or change live mode without explicit operator action.

## Import/export bundles

Exports create redacted operator-controlled bundles. Imports must be previewed before apply. Apply requires explicit confirmation and is conservative by default.

## Schema migrations

The migration registry reports known schema versions and whether a migration is needed. Dry-run does not mutate data. Apply requires explicit confirmation and should be preceded by a backup.

## Recovery reports

Reports are available as JSON, Markdown, and CSV check output. Reports include safety statements and never reveal secret values.

## Known limitations

- Runtime backup/restore is local-first and not cloud-synced.
- The current migration registry provides future-compatible scaffolding; most current v2.9 data uses the current schema.
- The backup system defaults to redacted text-file backup behavior and skips unsafe binary/secret content.
