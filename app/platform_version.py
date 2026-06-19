from __future__ import annotations

from typing import Any

from .config import APP_VERSION, APP_VERSION_SHORT
from .platform_safety import safety_flags

RELEASE_TITLE = "Polymarket OP Console Rename and Package Identity Update"
RELEASE_FAMILY = "v4-platform-stabilization-rename-patch"
RELEASE_STAGE = "stable rename/package-identity patch"
COMPATIBILITY_NOTES = [
    "Preserves v2 live/paper controls and all v3 command center, analytics, simulation, dataset, freshness, task, workspace, and cockpit routes.",
    "Local JSON/JSONL runtime data remains lazily created and excluded from release ZIPs.",
    "Plugin manifests remain metadata-only and do not execute arbitrary code.",
    "No migration helper mutates live trading state or deletes user runtime data automatically.",
    "Software identity has been renamed to Polymarket OP Console and package slug to polymarket-op-console.",
    "GitHub repository identity is https://github.com/samgabsi/polymarket-op-console.",
]
DOCS_INDEX = [
    "docs/RELEASE_NOTES_v4.0.1-real.md",
    "docs/VALIDATION_v4.0.1-real.md",
    "docs/V4_PLATFORM_ARCHITECTURE_GUIDE_v4.0.1-real.md",
    "docs/V4_PLUGIN_BOUNDARY_GUIDE_v4.0.1-real.md",
    "docs/V4_PLATFORM_DIAGNOSTICS_GUIDE_v4.0.1-real.md",
    "docs/V4_STORAGE_COMPATIBILITY_GUIDE_v4.0.1-real.md",
    "docs/RELEASE_CHECKLIST_v4.0.1-real.md",
]


def version_metadata() -> dict[str, Any]:
    return safety_flags({
        "version": APP_VERSION,
        "version_short": APP_VERSION_SHORT,
        "release_family": RELEASE_FAMILY,
        "release_title": RELEASE_TITLE,
        "release_stage": RELEASE_STAGE,
        "release_date": "operator-defined",
        "compatibility_notes": COMPATIBILITY_NOTES,
        "docs_index": DOCS_INDEX,
        "changelog_reference": "CHANGELOG.md#v401-real--polymarket-op-console-rename-and-package-identity-update",
        "safety_posture": "fail-closed, local-first, human-in-the-loop, no autonomous live mutation",
    })
