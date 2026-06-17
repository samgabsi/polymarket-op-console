# Validation Report — v3.0.0-real

Validation should include:

- `python -m compileall -q app tests scripts`
- `PYTHONPATH=. python -m pytest -q`
- `PYTHONPATH=. python scripts/check_versions.py`
- `PYTHONPATH=. python scripts/smoke_startup.py`
- `python scripts/check_release_package.py .`

Safety assertions:

- No real order placement occurs.
- No real cancellation occurs.
- v3 workflows do not arm live trading.
- AI/model assistance is disabled by default.
- Exports and workflow outputs redact secrets.
