# Release Checklist — v2.6.0-real

- [ ] Confirm `VERSION` is `2.6.0-real`.
- [ ] Run syntax checks.
- [ ] Run unit tests.
- [ ] Run route smoke tests.
- [ ] Run `scripts/check_versions.py`.
- [ ] Run `scripts/smoke_startup.py`.
- [ ] Run `scripts/check_release_package.py .`.
- [ ] Run secret scan.
- [ ] Complete manual QA checklist.
- [ ] Confirm no real order placement occurred.
- [ ] Confirm no real cancellation occurred.
- [ ] Create Git tag: `git tag v2.6.0-real`.
- [ ] Create GitHub release title: `Polymarket Gamma Starter v2.6.0-real`.
- [ ] Upload ZIP artifact.
- [ ] Keep rollback note to v2.5.0-real.
