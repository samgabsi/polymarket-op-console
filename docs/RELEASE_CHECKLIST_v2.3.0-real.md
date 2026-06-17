# Release Checklist — v2.3.0-real

## Required checks

- [ ] Version file says `2.3.0-real`.
- [ ] README title says `Polymarket Gamma Starter v2.3.0-real`.
- [ ] `python -m compileall -q app tests` passes.
- [ ] `PYTHONPATH=. python -m pytest -q` passes.
- [ ] `python scripts/check_versions.py` passes.
- [ ] `python scripts/check_release_package.py .` passes.
- [ ] Manual QA checklist is completed.
- [ ] No screenshots show secrets.
- [ ] Verification report confirms no order placement or cancellation.

## Suggested Git commands

```bash
git status
git add .
git commit -m "Release v2.3.0-real"
git tag v2.3.0-real
git push origin main
git push origin v2.3.0-real
```

## GitHub release draft

Title: `Polymarket Gamma Starter v2.3.0-real`

Body:

```text
v2.3.0-real hardens the v2 Live operator console for release/demo use. It adds explicit live read-only verification, demo readiness checks, manual browser QA, release checklist, startup/package validation scripts, and redacted report exports while preserving fail-closed live-trading safety gates.
```

Assets:

- `polymarket-gamma-starter-v2.3.0-real.zip`
- Optional redacted verification report
- Optional screenshots with no secrets

Rollback note: keep prior `v2.2.0-real` artifact available until v2.3 QA is completed.
