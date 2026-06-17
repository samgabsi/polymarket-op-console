# Validation Report — v3.0.0-real

Validation targets:

- Syntax checks.
- Unit tests.
- Route smoke tests.
- Startup smoke test.
- Version consistency check.
- Package cleanliness check.
- Backup/export safety checks.

Expected commands:

```bash
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/check_release_package.py .
```

Safety confirmations:

- No real order placement occurs during validation.
- No real order cancellation occurs during validation.
- Backup/export defaults exclude or redact secrets.
