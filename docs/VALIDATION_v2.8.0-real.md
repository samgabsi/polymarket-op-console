# Validation Report — v2.8.0-real

## Commands run

```bash
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/check_release_package.py .
```

## Results

- Syntax checks: PASS
- Unit/route/export/safety tests: PASS — 48 passed
- Version consistency: PASS
- Startup smoke test: PASS
- Package cleanliness check: PASS after cleanup of local validation caches/runtime data
- Secret scan: PASS — no real secrets detected; only `CHANGE_ME_LOCAL_ONLY` placeholders are present in examples/docs
- Governance export safety: PASS

## Warning

Starlette emits existing `TemplateResponse` deprecation warnings during tests. They do not block the release.

## Safety confirmation

- No real order placement occurred.
- No real cancellation occurred.
- No live trading was armed.
- Governance records do not place orders, cancel orders, approve orders, sign orders, arm live trading, or bypass backend gates.
- Governance exports are redacted and do not include secrets.

## Known limitations

- Visual browser screenshot QA was not performed in this environment.
- Governance storage is local-first and not synced across devices.
- Governance guidance is workflow guidance only and not financial advice.
