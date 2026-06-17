# Validation — v3.3.0-real

Validation performed for the packaged v3.3.0-real release candidate:

```text
python -m compileall -q app tests scripts
PASS

PYTHONPATH=. python -m pytest -q
60 passed

PYTHONPATH=. python scripts/check_versions.py
PASS

PYTHONPATH=. python scripts/smoke_startup.py
PASS

python scripts/validate_v3_release.py --quick
PASS

python scripts/check_release_package.py .
PASS after cleanup of validation caches/runtime data

Secret scan
PASS
```

Warnings observed: Starlette emitted existing `TemplateResponse` deprecation warnings during tests. They do not block this release.

Safety confirmations:

- No real order placement occurred.
- No real order cancellation occurred.
- v3 workflows did not arm live trading.
- Demo data is fake and secret-free.
- AI/model assistance is disabled by default.
- Screenshots are not included in the release ZIP.

Known validation limitation: browser screenshot automation was not executed in this environment. The screenshot helper includes a safe dry-run path and visual QA checklist for local review.
