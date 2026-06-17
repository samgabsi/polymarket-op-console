# Validation Report — v2.5.0-real

Generated for the packaged v2.5.0-real release candidate.

## Commands run

```text
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/check_release_package.py .
grep -RInE '(PRIVATE_KEY|API_KEY|SECRET|PASSPHRASE|TOKEN)\\s*=\\s*[A-Za-z0-9_./+-]{16,}' .
```

## Results

```text
compileall: PASS
pytest: PASS — 30 passed
check_versions.py: PASS — expected 2.5.0-real
smoke_startup.py: PASS — app imports and safe routes respond without network mutation
check_release_package.py: PASS after removing local validation caches/runtime audit data
secret scan: PASS — only CHANGE_ME_LOCAL_ONLY placeholders found in docs/.env.example
```

## Warnings

Starlette emits existing `TemplateResponse` deprecation warnings during tests. These warnings do not block this release and predate the research layer.

## Safety confirmation

- No real order placement occurred.
- No real order cancellation occurred.
- No live trading was armed.
- No private key, API key, secret, passphrase, or auth token was required.
- Research candidate conversion created strategy evidence only.
- Live submit gates remain unchanged.

## Known limitations

- Visual browser screenshot QA was not automated in this environment.
- Research data is local-first and not synced between devices.
- External scraping is intentionally not included by default.
- Research scores are workflow guidance only and are not financial advice.
