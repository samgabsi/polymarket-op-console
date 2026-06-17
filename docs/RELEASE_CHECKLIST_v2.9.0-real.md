# Release Checklist — v3.0.0-real

- [ ] Confirm `VERSION` is `3.0.0-real`.
- [ ] Confirm README title is v3.0.0-real.
- [ ] Run unit tests.
- [ ] Run startup smoke test.
- [ ] Run package cleanliness check.
- [ ] Run manual browser QA for `/v2-live/data`.
- [ ] Confirm no runtime data is in the release ZIP.
- [ ] Confirm no secrets are in backup/export reports.
- [ ] Build ZIP: `polymarket-gamma-starter-v3.0.0-real.zip`.
- [ ] Create Git tag: `git tag v3.0.0-real`.
- [ ] Create GitHub release title: `Polymarket Gamma Starter v3.0.0-real`.
- [ ] Upload release ZIP.

Rollback note: keep v2.8.0-real as the previous known release if data backup/restore QA fails.
