# Validation — v4.0.0-real

## Validation Scope

This release validates platform stabilization, metadata-only plugin manifests, route inventory, storage compatibility, diagnostics, export safety, package cleanliness, and preservation of existing v2/v3 behavior.

## Required Commands

```bash
python -m compileall -q app scripts tests
python scripts/check_versions.py
python scripts/smoke_startup.py
python scripts/validate_v3_release.py
python scripts/validate_v3_ux_release.py
python scripts/capture_v3_screenshots.py --dry-run
python scripts/check_release_package.py .
python -m pytest -q tests/test_live_v3_platform.py
```

## Safety Confirmations

- No real order placement occurs during validation.
- No real cancellation occurs during validation.
- Task, cadence, guided, cockpit, platform, and plugin workflows do not arm live trading.
- Platform diagnostics do not mutate live trading state.
- Plugin manifests are metadata only and do not execute code.
- Command-palette actions do not place or cancel orders.
- Keyboard shortcuts do not place or cancel orders.
- Task completion does not approve trades.
- Guided review completion does not approve trades.
- Cockpit and platform workflows are local-first and non-autonomous by default.
- Demo data is fake and secret-free.
- Screenshots are not included in the release ZIP unless explicitly reviewed and intended.

## Known Limitations

- Plugin support is manifest-only in v4.0.0-real; it intentionally does not load executable extension code.
- Platform settings are lightweight/non-destructive and do not automatically migrate runtime data.
- Route protected/authenticated status is summarized from application route patterns and auth middleware behavior.
