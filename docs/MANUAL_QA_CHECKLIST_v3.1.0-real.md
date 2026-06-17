# Manual QA Checklist — v3.3.0-real

1. Log in as admin.
2. Open `/v3` and confirm version `v3.3.0-real` is visible.
3. Open `/v3/search`, `/v3/graph`, `/v3/workflows`, `/v3/briefs`, `/v3/settings`, and `/v3/docs`.
4. Confirm `/v2-live`, `/v2-live/strategy`, `/v2-live/research`, `/v2-live/monitoring`, `/v2-live/portfolio`, `/v2-live/governance`, and `/v2-live/data` still render.
5. Create safe demo data with `python scripts/create_v3_demo_data.py`.
6. Confirm demo data is clearly fake and secret-free.
7. Generate pre-trade packet, market brief, thesis health, portfolio brief, and operator review outputs.
8. Confirm all outputs say they do not place/cancel/approve/arm orders.
9. Run `python scripts/capture_v3_screenshots.py --dry-run`.
10. Run `python scripts/validate_v3_release.py --quick`.
11. Clear demo data with `python scripts/clear_v3_demo_data.py`.
12. Confirm no real orders were placed or cancelled and live trading was not armed.
