# Validation Report — v2.3.0-real

Generated for the packaged v2.3.0-real release candidate.

## Commands run

```bash
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python scripts/check_versions.py
PYTHONPATH=. python scripts/smoke_startup.py
python scripts/check_release_package.py .
```

## Results

- Compile check: PASS
- Unit/route tests: PASS, `20 passed`
- Version consistency script: PASS, expected `2.3.0-real`
- Startup smoke script: PASS for UI routes; protected API routes returned authentication/authorization responses when unauthenticated, not server errors
- Package cleanliness script: PASS, no blocked cache/runtime/secret paths detected after cleanup

## Warnings

Starlette emitted existing `TemplateResponse` deprecation warnings during tests. They do not block this release and were present in prior validation.

## Safety confirmation

- No real order placement occurred.
- No real order cancellation occurred.
- Verification harness did not arm live trading.
- Verification harness did not mutate settings.
- Tests used mocked/local-safe paths only.
- Release ZIP excludes runtime data, caches, virtual environments, node modules, `.git`, and real `.env` files.

## Known limitations

- Browser screenshot automation is optional and requires Playwright if used locally.
- Real live read-only network checks require operator-supplied credentials/configuration and explicit `POLYMARKET_LIVE_ALLOW_REAL_NETWORK=true` plus `POLYMARKET_LIVE_NETWORK_READONLY=true`.
- The harness reports skipped/unavailable when credentials, wallet, or read-only network gates are absent rather than inventing success.
