# Release Notes — v3.0.0-real

v3.0.0-real adds the Data Integrity / Backup / Migration / Recovery Layer.

## Highlights

- `/v2-live/data` workspace.
- Runtime inventory for local-first data.
- Data health checks.
- Redacted secret scanning.
- Redacted backup bundles with manifests and checksums.
- Restore preview and explicit-confirmation restore apply.
- Controlled import/export bundles.
- Migration registry, dry-run, and explicit-confirmation apply path.
- Recovery reports in JSON, Markdown, and CSV.
- Data workflow audit events.

## Safety

No data workflow places orders, cancels orders, arms live trading, approves orders, signs orders for submission, or bypasses backend gates. Backup/export defaults exclude secrets.
