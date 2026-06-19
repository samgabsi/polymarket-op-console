# v3.5 Simulation Lab Guide

Version: v3.5.0-real

The Simulation Lab is a local-first replay, scenario, and process-evaluation workspace. It is designed to help the operator review decisions, thesis quality, alert behavior, portfolio risk posture, governance discipline, and no-trade choices without touching live execution.

## What simulation is

Simulation is a descriptive training and review layer. It can reconstruct best-effort local historical state, compare what was known then with what is known now, generate simulated pre-trade packets, test alert/governance/risk behavior, and create process-quality backtests.

## What simulation is not

Simulation is not live trading, not paper trading, not financial advice, not a prediction engine, and not an execution system. It does not place orders, cancel orders, approve orders, sign orders, arm live trading, or bypass backend safety gates.

## Live, paper, demo, simulation, and replay

- Live: real execution path guarded by backend gates.
- Paper: local non-live trading workflow.
- Demo: clearly fake records for screenshots/manual QA.
- Simulation: hypothetical/local scenario output.
- Replay: best-effort reconstruction of local state at a selected time.

## Replay sessions

Replay sessions record the target time, included subsystems, selected market/thesis scope, assumptions, status, and notes. Sessions can be created, updated, archived, run, and exported. Running a session creates a local report only.

## Historical state reconstruction

The system uses local timestamps from audit, strategy, research, monitoring, portfolio, governance, analytics, workflow, and data-health records. It labels data as known at replay time, created after replay time, unknown, or hypothetical assumption. Reconstruction is best-effort and should not be treated as perfect historical truth.

## Assumptions

Every simulation records assumptions such as hypothetical fill percentage, hypothetical price, hypothetical resolution, hypothetical thesis outcome, missing-data handling mode, and local-only replay mode. Assumptions are visible in API outputs, UI panels, and exports.

## Simulation types

- Pre-trade replay: reconstructs a simulated pre-trade packet from local state.
- Thesis replay: compares thesis health then versus now.
- Alert simulation: tests how local alert rules may have behaved.
- Portfolio/risk simulation: previews hypothetical exposure and concentration warnings.
- Governance simulation: checks checklist/rule/near-miss posture.
- No-trade simulation: documents why doing nothing may be the process-correct action.
- Process-quality backtesting: evaluates process discipline, not profit or prediction accuracy.

## What-I-knew-then vs what-I-know-now

Comparison views separate data known at replay time from later-added information to reduce hindsight confusion.

## Exports

Simulation exports include JSON, Markdown, sessions CSV, and findings CSV. Exports include timestamps, app version, simulation type, assumptions, known/unavailable data, findings, limitations, and safety statements.

## Safety boundary

Simulation outputs are workflow guidance only. Live order submission still requires existing backend risk gates, human approval, warning acknowledgement, typed confirmation phrase, Live Armed mode, read-only disabled, and kill switch disabled.

## Known limitations

Simulation quality depends on locally recorded data. Missing historical records remain unknown/unavailable. Simulation does not infer true P&L, fills, balances, wallet state, or outcomes unless explicit safe data exists.
