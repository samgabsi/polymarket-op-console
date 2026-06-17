# Research Intake Guide — v2.5.0-real

`v2.5.0-real` adds a local-first Research Intake and Source Workflow Layer at `/v2-live/research`.

## What it is

The research layer is a structured workflow for capturing source material, writing review notes, scoring source quality, tracking freshness, creating evidence candidates, and converting reviewed candidates into strategy evidence.

It feeds the v2.4 Strategy / Playbook layer.

## What it is not

- It is not autonomous trading.
- It is not a web scraper.
- It does not scrape private, authenticated, paywalled, or restricted content unless the operator explicitly provides content and authorizes the workflow.
- It does not place orders.
- It does not sign orders for submission.
- It does not cancel orders.
- It does not arm live trading.
- It does not bypass risk, approval, warning, confirmation, read-only, or kill-switch gates.
- Research scores are workflow guidance, not financial advice.

## Core objects

### Sources

A source is a raw research input such as a news article, official announcement, market page, social post, analyst note, data source, or operator note.

A source supports title, URL, source type, publisher, date published, date observed, market linkage, thesis linkage, credibility rating, relevance rating, freshness status, tags, notes, and status.

### Research queue

The research queue tracks what needs review. Queue items include priority, source reference, research question, desired output, status, tags, and notes.

### Source notes

Source notes capture the operator's summary, key claims, supporting details, contradicting details, uncertainty, and interpretation.

### Evidence candidates

Evidence candidates are reviewed claims that may become strategy evidence. They include direction, credibility, relevance, freshness, evidence strength, contradiction strength, uncertainty, notes, and thesis linkage.

A source is not evidence until it is reviewed and converted by the operator.

## Workflow

1. Add a source.
2. Add or update a research queue item.
3. Write source notes.
4. Create an evidence candidate.
5. Assign direction, credibility, relevance, freshness, and uncertainty.
6. Link the candidate to a thesis.
7. Convert the candidate into strategy evidence.
8. Re-run thesis comparison.
9. Update the thesis manually if appropriate.
10. Draft a ticket only after the strategy layer has enough reviewed evidence.

## Evidence direction

- `supports`
- `weakly_supports`
- `neutral`
- `weakly_contradicts`
- `contradicts`

## Scoring

Scores are deliberately simple and transparent:

- source credibility
- source relevance
- evidence relevance
- evidence strength
- evidence freshness
- contradiction strength
- uncertainty level

The app may produce workflow guidance such as:

- Review source before using
- Good candidate for evidence
- Needs corroboration
- Potentially stale
- Contradicts active thesis
- Archive or monitor
- Link to thesis before scoring

These are not trade recommendations.

## Freshness and staleness

Freshness status can be:

- fresh
- aging
- stale
- expired
- unknown

Use stale warnings to avoid relying on old or expired claims in active theses, scorecards, and trade-ticket rationale.

## Thesis comparison

The thesis comparison panel summarizes:

- thesis summary
- supporting evidence count
- contradicting evidence count
- neutral evidence count
- stale evidence count
- average credibility
- average relevance
- strongest supporting evidence
- strongest contradicting evidence
- unresolved research questions
- recommended next research action

The comparison does not change a thesis automatically. The operator must explicitly update theses and scorecards.

## Strategy integration

Converting an evidence candidate creates a strategy evidence item in the v2.4 Strategy / Playbook layer. It does not create, submit, approve, sign, or cancel an order.

The Strategy workspace can use converted evidence for thesis review, scorecards, and ticket rationale.

## Trade-ticket relationship

The trade ticket may display strategy and research freshness warnings when linked to a thesis. Those warnings do not bypass any execution gate.

Live order submission still requires:

- risk checks
- human approval
- warning acknowledgement
- typed confirmation phrase
- Live Armed mode
- read-only disabled
- kill switch disabled
- backend submit gates

## Exports

Available exports:

- `/api/v2/live/research/export.json`
- `/api/v2/live/research/export.md`
- `/api/v2/live/research/sources.csv`
- `/api/v2/live/research/queue.csv`
- `/api/v2/live/research/evidence-candidates.csv`
- `/api/v2/live/research/stale.csv`

Exports are redacted and include a safety statement that research output does not place orders.

## Known limitations

- Storage is local-first JSONL event storage.
- Research data is not synced between devices.
- External page scraping is not implemented by default.
- Freshness requires operator review unless future integrations are added.
- Research scores are workflow guidance only.
