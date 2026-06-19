# Validation — v4.0.1-real

v4.0.1-real validation focuses on package identity, internal naming, version consistency, startup/import safety, route smoke checks, package cleanliness, and the existing no-live-mutation boundaries.

Expected validation commands:

```bash
python -m compileall -q app scripts tests
python scripts/check_versions.py
python scripts/smoke_startup.py
python scripts/validate_v3_release.py --quick
python scripts/validate_v3_ux_release.py --quick
python scripts/capture_v3_screenshots.py --dry-run
python scripts/check_release_package.py .
```

Safety confirmations:

- No real order placement.
- No real cancellation.
- No live arming.
- Plugin manifests remain metadata-only.
- Platform diagnostics remain local and non-mutating.
- Command-palette and keyboard shortcuts remain safe local/navigation actions only.
