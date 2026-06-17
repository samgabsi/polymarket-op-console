# Release Checklist — v2.5.0-real

- [ ] VERSION file says `2.5.0-real`.
- [ ] README title says `Polymarket Gamma Starter v2.5.0-real`.
- [ ] `python -m compileall -q app tests` passes.
- [ ] `PYTHONPATH=. python -m pytest -q` passes.
- [ ] `PYTHONPATH=. python scripts/check_versions.py` passes.
- [ ] `PYTHONPATH=. python scripts/smoke_startup.py` passes.
- [ ] `python scripts/check_release_package.py .` passes.
- [ ] Manual QA checklist completed.
- [ ] No secrets in package.
- [ ] No runtime audit, strategy, or research data in package.
- [ ] No real order placement occurred.
- [ ] No real cancellation occurred.

## Suggested Git commands

```bash
git add .
git commit -m "Release v2.5.0-real"
git tag v2.5.0-real
git push origin main
git push origin v2.5.0-real
```

## Suggested release title

```text
Polymarket Gamma Starter v2.5.0-real
```

## Suggested asset

```text
polymarket-gamma-starter-v2.5.0-real.zip
```

## Rollback note

If QA fails, do not publish the release. Roll back to v2.4.0-real and fix the research intake layer before tagging.
