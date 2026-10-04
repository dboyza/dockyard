"""Pinned Calico images, derived from compatibility.json so a release's packaging can change.

Each image key named ``calico_<name>`` pins ``quay.io/calico/<name>`` at the pinned
Calico version, with underscores in the key standing for hyphens in the name.
"""

from __future__ import annotations

import json
import re

from dockyard.catalog import CONTENT
from dockyard.runtimes.docker import RuntimeErrorBase

UPSTREAM = re.compile(r"quay\.io/calico/[a-z0-9-]+:[A-Za-z0-9._-]+")


def upstream_images() -> dict[str, str]:
    """The upstream reference each pinned Calico image replaces, by compatibility key."""
    compatibility = json.loads((CONTENT / "compatibility.json").read_text())
    version = compatibility["calico"]
    return {
        key: f"quay.io/calico/{key.removeprefix('calico_').replace('_', '-')}:v{version}"
        for key in compatibility["images"]
        if key.startswith("calico_")
    }


def require_pinned(manifest: str) -> None:
    """Refuse a manifest that still names an upstream Calico image Dockyard has not pinned."""
    if leftover := sorted(set(UPSTREAM.findall(manifest))):
        raise RuntimeErrorBase(
            "The Calico manifest uses images that are not pinned: " + ", ".join(leftover)
        )
