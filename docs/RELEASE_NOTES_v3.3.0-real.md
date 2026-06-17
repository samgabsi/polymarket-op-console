# Release Notes — v3.3.0-real

v3.3.0-real is a complete operator UI/UX redesign, performance polish, and interaction-overhaul release.

## Highlights

- Complete v3 visual redesign.
- New design system CSS and lightweight interaction script.
- Grouped navigation model for Operate, Analyze, Build Thesis, Govern, and Output.
- Redesigned command center with safety posture, attention queue, workbench shortcuts, intelligence summary, recent activity, and safe next actions.
- Improved global search UX with filters, clearer result counts, and local-only framing.
- Improved graph UX with node/relationship filters and table/tree relationship explorer.
- Improved workflow cards and packet/report readability.
- Improved analytics dashboard layout.
- Stronger safety UX for live armed, read-only, kill switch, unknown/unavailable, danger, and fake-demo states.
- Responsive and accessibility polish.
- Updated screenshot helper and v3.3 UX validation harness.
- Updated docs/tests with no safety regression.

## Safety

The redesign does not place orders, cancel orders, arm live trading, approve trades, sign orders, or bypass backend gates. Live order submission still requires all existing backend controls.
