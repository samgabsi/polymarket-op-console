# v3 UI/UX Redesign Guide — v3.3.0-real

v3.3.0-real is a product-quality redesign release. It keeps the v3 Operator Intelligence OS local-first and human-controlled while making the interface faster, cleaner, smoother, and easier to operate.

## What changed visually

- A new v3 app shell with persistent grouped navigation.
- A stronger command center hierarchy focused on Safety, Attention Queue, Workbench Shortcuts, Intelligence Summary, Recent Activity, and Safe Next Actions.
- A shared design system for cards, metric tiles, badges, tables, filters, reports, warning panels, danger zones, and empty states.
- Improved table readability with captions, result filtering, sticky headers, and expandable details where practical.
- More obvious safety status language around live armed state, read-only state, kill switch state, and fake demo data.

## New navigation model

The v3 sidebar groups the product into operator tasks:

1. **Operate** — Command Center, Live Controls, Trade Ticket, Audit.
2. **Analyze** — Analytics, Portfolio, Monitoring, Graph, Search.
3. **Build Thesis** — Strategy, Research, Evidence, Watchlists.
4. **Govern** — Governance, Reviews, Data / Backup, Settings.
5. **Output** — Workflows, Briefs, Reports, Docs.

Existing v2 routes remain available for detailed workflows.

## Command center redesign

The command center is now the flagship view. It prioritizes safety posture, operator attention items, workbench shortcuts, analytics context, and recent activity. It is designed to be readable within seconds.

## Search redesign

Global local search now has a more prominent input, clearer filter affordances, index-health links, result counts, better snippets, and local-only safety language.

## Graph redesign

The graph is presented as a stable table/tree style relationship explorer. This avoids brittle visualization while still exposing node filters, relationship filters, graph exports, and local decision-context links.

## Workflow redesign

Workflow cards now make clear what each workflow does, whether it is read-only, what output it creates, and what sections the generated packet/report includes.

## Packet/report redesign

Generated packets and reports are framed as structured drafts with summaries, blockers, warnings, unknown/unavailable data, source sections, operator review actions, export controls, and explicit safety statements.

## Forms and tables improvements

The redesign emphasizes grouped fields, clearer labels, helper text, safer action separation, result counts, readable row spacing, status badges, and local table filtering where practical.

## Safety UX improvements

Safety is more visible, not less. The redesign uses distinct status treatments for read-only, live armed, kill switch, warning, danger, blocked, unknown/unavailable, and fake demo data states. UI convenience controls do not bypass backend gates.

## Performance improvements

The v3 shell avoids deep scans on page load, uses lightweight summaries, supports local client-side filtering on rendered tables, and keeps expensive graph/search/analytics rebuilds operator-triggered.

## Accessibility improvements

The redesign adds or strengthens semantic landmarks, skip links, visible focus states, form labels, table captions, reduced reliance on color alone, touch-friendly spacing, and responsive behavior.

## Demo mode UX

Demo data remains fake and secret-free. Demo indicators are visible and demo scripts never place/cancel orders or arm live trading.

## Screenshot QA workflow

Run the screenshot helper in dry-run mode first:

```bash
PYTHONPATH=. python scripts/capture_v3_screenshots.py --dry-run
```

Screenshots should be reviewed manually before publication and are not included in the release ZIP by default.

## Known limitations

Live browser screenshot QA still requires a local browser automation environment. The redesign keeps the existing server-rendered architecture and intentionally avoids adding a heavy frontend framework.
