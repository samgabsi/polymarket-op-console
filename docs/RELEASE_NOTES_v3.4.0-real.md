# Release Notes — v3.5.0-real

v3.5.0-real adds the Advanced Backtesting, Replay, Simulation Lab, and Process Evaluation Layer.

## Highlights

- Added `/v3/simulation` workspace and simulation subroutes.
- Added `app/live_v3_simulation.py` local-first simulation engine.
- Added replay sessions, historical state reconstruction, and what-I-knew-then vs what-I-know-now labels.
- Added simulated pre-trade packets, thesis health replay, alert behavior simulation, portfolio/risk simulation, governance/checklist simulation, and no-trade simulation.
- Added process-quality backtesting that evaluates operator discipline without claiming profitability.
- Added simulation JSON, Markdown, sessions CSV, and findings CSV exports.
- Integrated simulation into command center, search, graph, workflow templates, analytics context, demo data, screenshot helper, and validation harness.

## Safety

No simulation workflow places orders, cancels orders, signs orders, approves orders, arms live trading, or bypasses backend gates.
