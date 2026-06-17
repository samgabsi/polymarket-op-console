# Release Notes — v2.8.0-real

v2.8.0-real adds the Review / Governance / Operator Decision Journal Layer.

## Added

- `/v2-live/governance` workspace
- `app/live_governance.py` local-first governance data layer
- Structured decision journal entries
- Pre-trade governance checklists
- Post-trade, daily, weekly, and process reviews
- Governance rules
- Rule violation / near-miss tracking
- Mistake-pattern tracking
- Governance exports in JSON, Markdown, and CSV formats
- Governance audit events in the Live v2 audit ledger
- Governance status panel on the Trade Ticket page
- v2.8 documentation, manual QA checklist, release checklist, and validation report

## Safety

Governance records do not place orders, cancel orders, approve orders, sign orders, arm live trading, or bypass backend gates. Existing risk checks, human approval, warning acknowledgement, typed confirmation, Live Armed mode, read-only gate, kill switch gate, and backend submit gates remain intact.
