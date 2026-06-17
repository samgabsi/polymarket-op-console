# Validation Report — v2.6.0-real

Validation should include:

```bash
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/check_release_package.py .
```

Expected result:

- all tests pass
- version reports v2.6.0-real
- startup smoke test passes
- package cleanliness check passes
- no real order placement occurs
- no real cancellation occurs

Monitoring-specific safety assertions:

- alert rules do not submit orders
- alert evaluation does not cancel orders
- acknowledgement/snooze does not arm live trading
- exports redact secrets
