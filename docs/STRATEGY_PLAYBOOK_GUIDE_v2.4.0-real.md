# Strategy / Playbook Guide — v2.4.0-real

`v2.4.0-real` adds the Strategy / Playbook Intelligence Layer. It is a local-first research and decision-quality workspace for building market theses before any trade ticket reaches live execution.

## What it is

The strategy layer helps the operator create structured research artifacts:

- Market theses
- Evidence items
- Watchlist items
- Transparent scorecards
- Entry criteria
- Exit criteria
- Invalidation criteria
- Trade rationale
- Post-trade reviews

Each object is stored locally as an append-only strategy event and can be exported for offline review.

## What it is not

The strategy layer is not an autonomous trader. It does not place orders, sign orders for submission, cancel orders, arm live mode, bypass risk checks, or weaken human approval. A thesis is not an order. A score is not a trade recommendation. A watchlist item is not an order. Creating a ticket draft from a thesis only prepares safe context for the existing trade-ticket workflow.

## Strategy workspace

Open:

```text
/v2-live/strategy
```

The workspace shows summary cards, active theses, watchlist items, evidence, scorecards, post-trade reviews, export links, and local API results.

## Creating a thesis

Use the Create Thesis form to enter:

- Market title and market ID/slug
- Outcome under consideration
- Thesis summary
- Probability estimate
- Confidence level
- Key assumptions, entry criteria, exit criteria, and invalidation criteria
- Maximum acceptable exposure
- Tags and operator notes

Recommended status flow:

```text
draft -> watching -> ready_for_ticket -> ticket_created -> active -> closed
```

Use `invalidated` when the thesis no longer holds and `archived` when it should be hidden from active review.

## Adding evidence

Evidence items support manual source tracking:

- Title
- Source URL
- Source type
- Observed date
- Relevance score
- Credibility score
- Direction: supports, weakly supports, neutral, weakly contradicts, contradicts
- Notes
- Linked thesis ID
- Stale/archive status

This release does not scrape paywalled or private content. Store notes and URLs only when you are allowed to use them.

## Scoring a market

Scorecards use visible criteria instead of hidden automation:

- Liquidity
- Spread
- Market clarity
- Information quality
- Evidence strength
- Counter-evidence strength
- Catalyst clarity
- Time-to-resolution
- Risk/reward
- Operator confidence
- Execution readiness
- Downside risk
- Ambiguity risk

The scorecard reports total score, weighted score, blockers, warnings, and operational next action such as “Continue researching,” “Watchlist only,” “Ready for paper rehearsal,” or “Ready to draft ticket.” These are workflow labels, not financial advice.

## Watchlists

Watchlist items track markets that are not yet ready for a ticket. Use them for target entry price, target exit price, invalidation condition, priority, status, tags, and last reviewed timestamp.

## Entry, exit, and invalidation criteria

Before drafting a ticket, define:

Entry criteria:

- Price threshold
- Spread threshold
- Liquidity threshold
- Evidence threshold
- Catalyst observed
- Operator review required

Exit criteria:

- Target price
- Time-based exit
- Evidence changed
- Market conditions changed
- Risk limit reached
- Manual review

Invalidation criteria:

- Key assumption failed
- Contradictory evidence appeared
- Market changed materially
- Liquidity disappeared
- Thesis became stale
- Operator confidence dropped

## Creating a ticket draft from a thesis

The Strategy page includes a Draft Ticket action for theses. It returns a safe ticket draft payload containing market/outcome/rationale/criteria context. It does not submit an order and does not call live execution endpoints.

The existing trade-ticket flow still requires:

- Risk checks
- Human approval
- Warning acknowledgement
- Typed confirmation phrase
- Live Armed mode
- Read-only disabled
- Kill switch disabled
- Backend submit gates

## Post-trade review

Post-trade reviews link the original thesis to an action or order reference where available. Use reviews to capture what went right, what went wrong, whether the thesis was valid, whether execution followed the plan, whether risk rules were followed, lessons learned, and follow-up actions.

## Exports

Available exports:

```text
/api/v2/live/strategy/export.json
/api/v2/live/strategy/export.md
/api/v2/live/strategy/evidence.csv
/api/v2/live/strategy/watchlist.csv
/api/v2/live/strategy/scorecards.csv
```

Exports redact secrets and are research artifacts only.

## Known limitations

- The strategy layer is local-first and does not sync between machines.
- It does not scrape research sources.
- It does not generate autonomous orders.
- It does not infer P&L when data is unavailable.
- Runtime strategy data is excluded from release ZIPs.
