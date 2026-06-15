# Configuration Console v1.9.0-real

The v1.9.0 configuration console at `/settings/configuration` is a streamlined GUI for schema-backed `.env` configuration.

It preserves the v1.8 centralized config registry, safe `.env` read/write behavior, validation, diff preview, backups, audits, sanitized export, and secret masking, while making the UI easier to navigate.

## Modes

### Simple Mode

Simple Mode is the default. It shows the most common operator-facing settings and hides advanced/dangerous controls.

Use Simple Mode for:

- local/demo setup
- host training caps
- data and training settings
- paper workflow settings
- common server/LAN controls

### Advanced Mode

Advanced Mode exposes all schema-backed settings, including raw env keys, dangerous/live-related controls, advanced values, and detailed validation metadata.

Advanced Mode does not weaken safety gates.

## Search and filters

The console supports:

- search by env key
- search by human label
- search by description/help text
- category filtering
- changed-from-default filtering
- restart-required filtering
- warnings filtering
- blockers filtering
- secrets filtering
- advanced filtering
- dangerous filtering
- live-related filtering
- training-related filtering
- LAN-related filtering

## Setting rows

Each setting row shows:

- human label
- env key
- current effective value
- saved `.env` value when different
- default value
- guided control
- help text
- validation details
- warning/blocker badges
- restart badge
- advanced/danger/live-related badges
- copy env key button

Text entry is used only where constrained controls are not practical, such as custom paths, URLs, hostnames, labels, and explicit advanced values.

## Diff preview

Before saving, the console groups changes into:

- safe changes
- warning changes
- dangerous/live-related changes
- restart-required changes
- blocked changes

Secrets remain masked.

## Saving

Saving creates runtime-only backups under `data/config_backups/` and runtime-only audit records under `data/config_audit/`. Runtime data is excluded from release ZIPs.
