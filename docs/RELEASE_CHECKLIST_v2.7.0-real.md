# Release Checklist — v2.7.0-real

- [ ] Confirm `VERSION` is `2.7.0-real`.
- [ ] Confirm README title is v2.7.0-real.
- [ ] Run `python -m compileall -q app tests`.
- [ ] Run `PYTHONPATH=. python -m pytest -q`.
- [ ] Run `PYTHONPATH=. python scripts/check_versions.py`.
- [ ] Run `PYTHONPATH=. python scripts/smoke_startup.py`.
- [ ] Run `python scripts/check_release_package.py .`.
- [ ] Perform manual browser QA for `/v2-live/portfolio`.
- [ ] Verify no secrets in screenshots or exports.
- [ ] Confirm portfolio planned-impact preview does not submit orders.
- [ ] Confirm scenarios do not submit or cancel orders.
- [ ] Confirm existing kill switch/read-only/live submit gates still block as expected.
- [ ] Create Git tag: `git tag v2.7.0-real`.
- [ ] Create GitHub release title: `Polymarket OP Console v2.7.0-real`.
- [ ] Upload `polymarket-op-console-v2.7.0-real.zip`.
- [ ] Keep prior v2.6.0-real ZIP available for rollback.
