# Validation Report — v2.2.0-real

Generated for the Browser-Polished Interactive Operator Console build.

## Commands run

```bash
python -m compileall -q app tests
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python - <<'PY'
from app.main import app
from app.config import APP_VERSION
routes = {route.path for route in app.routes}
required = {
    '/v2-live', '/v2-live/markets', '/v2-live/trade-ticket', '/v2-live/orders',
    '/v2-live/positions', '/v2-live/risk', '/v2-live/audit', '/v2-live/settings',
    '/v2-live/emergency', '/v2-live/docs', '/api/v2/live/ui/preferences/schema'
}
assert APP_VERSION == '2.2.0-real'
assert not (required - routes)
PY
```

## Results

- Syntax/import compile check: PASS
- Unit and route/template tests: PASS, `14 passed`
- Route smoke test: PASS, app version `2.2.0-real`, 496 routes discovered, required Live v2 browser routes present
- Document/example secret placeholder scan: PASS, no real secrets detected
- Source-tree cleanliness check before packaging: PASS, runtime data/cache folders removed from release tree

## Warning

Starlette emitted existing `TemplateResponse` deprecation warnings during route tests. This warning does not affect runtime behavior or the v2.2 release scope.

## Safety validation

- No real order placement occurred.
- No real order cancellation occurred.
- No wallet signing occurred.
- No private trading endpoint was called during tests.
- Paper/default/fail-closed behavior remains intact.

## Known limitations

Browser screenshots were not automated in this environment. Use `docs/MANUAL_QA_CHECKLIST_v2.2.0-real.md` for manual visual QA before demos or release publication.
