# Manual QA Checklist — v3.3.0-real

1. Start the app locally.
2. Log in with a safe local account.
3. Open `/v3` and confirm version `v3.3.0-real`.
4. Confirm sidebar navigation groups render.
5. Confirm command center safety cards render.
6. Confirm `/v3/search`, `/v3/graph`, `/v3/workflows`, `/v3/briefs`, `/v3/analytics`, `/v3/settings`, and `/v3/docs` render.
7. Confirm v2 compatibility pages still render.
8. Run `PYTHONPATH=. python scripts/capture_v3_screenshots.py --dry-run`.
9. Run `PYTHONPATH=. python scripts/validate_v3_ux_release.py --quick`.
10. Confirm no real order placement/cancellation occurred.
11. Confirm screenshots are not bundled into the release ZIP.
