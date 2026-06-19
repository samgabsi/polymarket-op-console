# Visual QA Checklist — v3.9.0-real

Use `python scripts/capture_v3_screenshots.py --dry-run` to verify route coverage. Capture real screenshots only in a local runtime folder after confirming no secrets are visible.

Cockpit routes to inspect: `/v3/cockpit`, `/v3/cockpit/layouts`, `/v3/cockpit/focus`, `/v3/cockpit/review`, `/v3/cockpit/tasks`, `/v3/cockpit/dependencies`, `/v3/cockpit/source`, `/v3/cockpit/packets`, `/v3/cockpit/command-palette`, `/v3/cockpit/shortcuts`, `/v3/cockpit/settings`.

Confirm responsive behavior, clear safety labels, empty states, warning states, unknown/unavailable states, readable multi-panel layout, and no dangerous action styling confusion.
