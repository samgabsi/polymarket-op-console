# Setup Wizard v1.9.0-real

The setup wizard at `/setup/wizard` provides card-based presets for common operator modes.

Each preset card shows:

- preset name
- plain-English description
- safety level
- recommended use case
- enabled keys
- disabled keys
- LAN exposure impact
- internet/data impact
- host-training impact
- live-readiness impact
- whether live trading remains disabled
- restart expectation

## Presets

- Locked-down safe mode
- Local demo mode
- LAN demo mode
- Paper trading only
- Data ingestion mode
- Training and backtesting mode
- 100K host training mode
- Live-readiness review mode
- Manual live execution readiness mode

## Final review

The wizard requires a final review step with:

- grouped diff preview
- warnings
- blockers
- restart-required keys
- backup notice
- explicit review checkbox

No preset is saved until the operator confirms and submits the apply action.

## 100K host training through the GUI

Open `/setup/wizard`, select `100K host training mode`, preview the diff, review warnings, and apply if the machine can safely handle local batch processing.

This enables local host training jobs and row caps while preserving:

```text
TRAINING_OUTPUTS_MANUAL_REVIEW_ONLY=true
TRAINING_ALLOW_LIVE_EXECUTION=false
```
