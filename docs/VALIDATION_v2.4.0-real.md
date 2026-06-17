# Validation Report — v2.4.0-real

Generated for the packaged v2.4.0-real release candidate.

## Commands run

```text
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/check_release_package.py .
```

## Results

```text
compileall: PASS
pytest: PASS — 25 passed
check_versions.py: PASS — expected 2.4.0-real
smoke_startup.py: PASS — no 5xx route failures; no network mutation; no order placement; no cancellation
check_release_package.py: PASS after cache/runtime cleanup
```

## Warning

Starlette emits existing `TemplateResponse` deprecation warnings during tests. They do not block this release.

## Safety confirmation

- No real order placement occurred.
- No real order cancellation occurred.
- Strategy ticket drafts do not submit, sign, arm, or cancel orders.
- Strategy exports redact secrets.
- Existing live submit gates, read-only gate, kill switch gate, and paper/live separation remain in place.

## Known limitations

- Strategy storage is local-first and not synchronized between devices.
- No visual browser screenshot QA was performed in this environment.
- Strategy scorecards provide transparent operator workflow guidance, not financial advice or automated trading decisions.
