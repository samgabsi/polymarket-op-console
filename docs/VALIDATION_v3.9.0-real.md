# Validation — v3.9.0-real

Recommended validation before release:

- `python -m compileall -q app scripts tests`
- `python scripts/check_versions.py`
- `python scripts/smoke_startup.py`
- `python scripts/validate_v3_release.py`
- `python scripts/validate_v3_ux_release.py`
- `python scripts/capture_v3_screenshots.py --dry-run`
- `python scripts/check_release_package.py .`
- targeted pytest suites for v2, v3, tasks, workspace, and cockpit.

Validation should confirm no real order placement, no real cancellation, no live arming, no task/review completion trade approval, no command-palette or keyboard-shortcut live mutation, no secrets, and no runtime artifacts in the ZIP.
