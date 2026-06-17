# Validation Report — v2.7.0-real

Validation targets:

- Syntax checks
- Unit tests
- Route smoke tests
- Import checks
- Version consistency
- Secret scan
- Package cleanliness
- Startup smoke test
- Portfolio export safety test

Expected commands:

```bash
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/check_release_package.py .
```

Expected safety result:

- No real order placement.
- No real cancellation.
- No live trading armed.
- Portfolio warnings, scenarios, and planned-impact previews do not call execution endpoints.

Known warning:

- Starlette may emit existing TemplateResponse deprecation warnings during tests. They do not block the release.
