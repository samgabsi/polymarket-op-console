# Data Integrity / Backup / Recovery Guide — v3.5.0-real

v3.5 preserves the v2.9 data integrity layer. Runtime data health, backup bundles, restore previews, import/export bundles, migration registry, and recovery reports remain local-first and fail-closed. Simulation artifacts are runtime data under `data/live_v3/simulation` and must not be included in release ZIPs.
