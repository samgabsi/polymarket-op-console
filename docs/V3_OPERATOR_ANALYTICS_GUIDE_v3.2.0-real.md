# v3 Operator Analytics Guide — v3.3.0-real

v3.3.0-real adds a local-first analytics and learning layer to the v3 Operator Intelligence OS. It is designed to help the operator review process quality over time across decisions, theses, evidence, alerts, governance records, portfolio/risk process signals, confidence calibration, mistake patterns, strengths, and review follow-through.

## What analytics are

Analytics are descriptive summaries derived from local application records. They measure workflow quality, review coverage, stale evidence, alert follow-through, governance discipline, and calibration sample sizes.

## What analytics are not

Analytics are not orders, trade recommendations, predictions, guarantees, alpha signals, or financial advice. Analytics never submit, cancel, approve, sign, or arm live orders.

## Decision quality metrics

Decision metrics summarize decision journal records: total decisions, decisions by type, reviewed vs unreviewed decisions, follow-up completion, linked theses/evidence, counter-evidence coverage, checklist completion, no-trade decisions, emergency decisions, unresolved decisions, overdue follow-ups, and unknown outcome counts.

## Thesis quality metrics

Thesis metrics summarize evidence coverage, counter-evidence coverage, unresolved research questions, alert/exposure/review linkages, exit criteria, invalidation criteria, stale states, and whether thesis quality is strong, incomplete, stale, blocked, needs review, or unknown.

## Evidence usefulness metrics

Evidence metrics summarize source type, freshness, stale or expired evidence, thesis linkage, contradiction records, and sources needing refresh. They reflect local metadata and operator records only.

## Alert usefulness metrics

Alert metrics summarize triggered, acknowledged, snoozed, ignored, repeated, critical, stale-evidence, concentration, and readiness/safety alerts. Recommendations are workflow tuning suggestions only.

## Governance discipline metrics

Governance metrics summarize checklist completion, post-trade/daily/weekly review completion, rule violations, near misses, mistake patterns, process improvements, governance rules, decisions without review, and overdue actions.

## Confidence calibration

Calibration buckets group recorded confidence values and show sample size, reviewed outcomes, unknown outcomes, and caution signals. Small samples are explicitly labeled as needing more data. Calibration is descriptive and should not be treated as statistically predictive.

## Mistake pattern analytics

Mistake pattern analytics summarize recurring patterns, active vs resolved status, frequency, corrective actions, and links to operator records. The tone is operational and supportive, not punitive.

## Strength pattern analytics

v3.2 also records positive process patterns such as completed checklists, counter-evidence coverage, alert acknowledgements, stale evidence resolution, and follow-through. The system should show what is working, not only what is broken.

## Review follow-through analytics

Review analytics summarize daily, weekly, and post-trade review creation, completed items, overdue items, missed/met follow-ups, unresolved actions, and process-improvement completion.

## Learning reports

The Learning Report can be generated for a daily, weekly, monthly, or custom review period. It includes decision review status, thesis quality, evidence usefulness, alert usefulness, governance discipline, portfolio/risk process signals, confidence calibration, recurring mistakes, recurring strengths, overdue follow-ups, suggested process improvements, unknown/unavailable data, and a safety statement.

## Integration

Analytics appear in:

- `/v3/analytics`
- the v3 command center analytics snapshot
- global local search
- decision graph analytics nodes
- pre-trade packets
- thesis health reports
- portfolio risk briefs
- operator review packets
- JSON, Markdown, and CSV exports

## Exports

v3.2 supports redacted exports for analytics snapshots, learning reports, and CSV metric tables. Exports do not include secrets and do not contain live-trading authorizations.

## Known limitations

Analytics are only as complete as the local records. Unknown outcomes, missing fills, missing balances, or absent review records are displayed as unknown/unavailable rather than invented. External AI/model calls are not required for analytics.
