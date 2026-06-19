# Manual QA Checklist — v3.9.0-real

- Open `/v3/cockpit`, `/v3/cockpit/layouts`, `/v3/cockpit/focus`, `/v3/cockpit/review`, `/v3/cockpit/tasks`, `/v3/cockpit/dependencies`, `/v3/cockpit/source`, `/v3/cockpit/packets`, `/v3/cockpit/command-palette`, `/v3/cockpit/shortcuts`, and `/v3/cockpit/settings`.
- Confirm cockpit pages show safety statements.
- Confirm layouts, panels, focus modes, shortcuts, command-palette actions, source context, dependencies, and packets render with empty states.
- Confirm command-palette forbidden live actions are rejected by API.
- Confirm shortcuts are navigation/local workflow only.
- Confirm v3.7 task routes and v3.8 workspace routes still render.
- Confirm v2 live controls still require backend gates.
- Confirm no screenshots or runtime cockpit records are included in the release ZIP.
