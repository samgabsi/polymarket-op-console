# Validation — v3.5.0-real

Expected validation commands:

```bash
python -m compileall -q app tests scripts
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
PYTHONPATH=. python scripts/validate_v3_release.py
PYTHONPATH=. python scripts/validate_v3_ux_release.py
PYTHONPATH=. python scripts/capture_v3_screenshots.py --dry-run
python scripts/check_release_package.py .
```

Validation must confirm no real order placement, no real cancellation, no live arming, secret-safe exports, and no runtime simulation data in the release ZIP.
