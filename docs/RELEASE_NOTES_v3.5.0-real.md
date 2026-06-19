# Release Notes — v3.5.0-real

v3.5.0-real adds the Read-Only Market Data Snapshot Collector, Replay Dataset Builder, and Data Quality Layer.

## Highlights

- `/v3/datasets` workspace and dataset subroutes.
- `app/live_v3_datasets.py` local-first dataset engine.
- Read-only snapshot collection for market metadata, order book structures, and local subsystem state.
- Snapshot validation, payload hashing, duplicate detection, and redaction status.
- Dataset manifests with quality scoring, replay readiness, simulation readiness, warnings, limitations, and provenance.
- JSON, Markdown, and CSV dataset exports.
- Command center, search, graph, analytics, simulation, workflow, demo, screenshot, and validation integration.

## Safety

Dataset and snapshot workflows are read-only, local-first, non-autonomous, and do not place orders, cancel orders, arm live trading, or bypass backend gates.
