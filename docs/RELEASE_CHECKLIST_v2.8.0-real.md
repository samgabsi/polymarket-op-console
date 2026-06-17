# Release Checklist — v2.8.0-real

- [ ] Confirm `VERSION` is `2.8.0-real`.
- [ ] Confirm README title is v2.8.0-real.
- [ ] Run syntax checks.
- [ ] Run unit tests.
- [ ] Run route smoke tests.
- [ ] Run startup smoke test.
- [ ] Run package cleanliness check.
- [ ] Run secret scan.
- [ ] Complete manual browser QA checklist.
- [ ] Confirm no real order placement occurred.
- [ ] Confirm no real cancellation occurred.
- [ ] Confirm no live trading was armed.
- [ ] Confirm governance exports redact secrets.
- [ ] Build ZIP: `polymarket-gamma-starter-v2.8.0-real.zip`.
- [ ] Create Git tag: `git tag v2.8.0-real`.
- [ ] Create GitHub release title: `Polymarket Gamma Starter v2.8.0-real`.
- [ ] Upload `polymarket-gamma-starter-v2.8.0-real.zip`.

## Draft release body

v2.8.0-real adds the Review / Governance / Operator Decision Journal Layer: decision journal, pre-trade checklists, reviews, governance rules, near-miss tracking, mistake-pattern tracking, exports, docs, and tests. It preserves all live safety gates and does not add autonomous execution.

## Rollback note

If visual QA or release smoke tests fail, keep v2.7.0-real as the known prior package and do not publish v2.8.0-real until corrected.
