# Validation — v3.3.0-real

Expected validation commands:

```bash
python -m compileall -q app tests scripts
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/validate_v3_release.py --quick
python scripts/check_release_package.py .
```

Validation must confirm:

- App imports successfully.
- Version reports `3.3.0-real`.
- v2 routes still render.
- v3 routes still render.
- `/v3/analytics` renders.
- Analytics APIs respond.
- Learning reports export safely.
- Secret scan passes.
- No real order placement occurred.
- No real order cancellation occurred.
- Analytics workflows do not arm live trading.
- Analytics are descriptive and not autonomous.
