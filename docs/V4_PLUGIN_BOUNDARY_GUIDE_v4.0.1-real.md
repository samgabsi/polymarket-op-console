# V4 Plugin Boundary Guide — v4.0.1-real

## Summary

v4.0.1-real introduces plugin manifests as a metadata-only extension boundary. This is not executable plugin support.

## Plugin Manifests Are Metadata Only

A plugin manifest can describe a future local UI extension, workflow extension, export extension, diagnostic extension, research helper, or disabled placeholder. The app validates manifest fields and forbidden capabilities but does not execute arbitrary plugin code.

## Forbidden Behaviors

Plugins cannot:

- Place orders.
- Cancel orders.
- Approve trades.
- Sign transactions.
- Arm live trading.
- Disable kill switch protections.
- Bypass read-only mode.
- Load remote code.
- Execute arbitrary code.
- Access secrets by default.
- Use network access by default.

## Required Manifest Fields

Each manifest should include plugin ID, title, description, version, app compatibility, enabled flag, plugin type, allowed routes, allowed API namespaces, allowed storage namespaces, safety class, capabilities, forbidden capabilities, no-live-mutation flag, no-secret-access flag, no-network-by-default flag, operator notes, and audit metadata.

## Future Extension Plan

Future releases may use this boundary to add local extension registration, but code execution must remain explicitly reviewed, test-covered, local-first, and separated from live mutation endpoints.

## Known Limitations

v4.0.1-real validates and displays manifests only. It does not provide executable plugins or dynamic route loading.
