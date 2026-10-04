"""The Kubernetes versions practice environments use, read from compatibility.json.

Lessons that rehearse an upgrade start on the previous minor version and finish on
the current one; every other native cluster starts on the current version.
"""

from __future__ import annotations

import json
from typing import Literal

from dockyard.catalog import CONTENT

_COMPATIBILITY = json.loads((CONTENT / "compatibility.json").read_text())

# Native kubeadm clusters, kubectl, and the upgrade target.
KUBERNETES: str = _COMPATIBILITY["kubernetes"]
# Where upgrade lessons begin: the latest patch of the previous minor version.
KUBERNETES_PREVIOUS: str = _COMPATIBILITY["kubernetes_previous"]
# The minor version, as Pod Security Admission and similar settings name it.
KUBERNETES_MINOR = "v" + ".".join(KUBERNETES.split(".")[:2])

Role = Literal["current", "previous"]


def native(role: Role) -> str:
    """The exact Kubernetes version for a lesson's starting cluster."""
    return KUBERNETES_PREVIOUS if role == "previous" else KUBERNETES


def pinned(version: str) -> bool:
    return version in {KUBERNETES, KUBERNETES_PREVIOUS}
