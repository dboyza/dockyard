"""Compound operating scenarios with an intact before-change state record."""

from __future__ import annotations

import json
import os
import sys

from dockyard.fixtures.maintenance import record
from dockyard.native import current


def prepare(mode: str) -> None:
    record()
    runtime = current()
    if mode in {"triage", "mission"}:
        runtime.require(
            runtime.kubectl(
                [
                    "patch",
                    "service",
                    "dispatch",
                    "--type=merge",
                    "-p",
                    json.dumps({"spec": {"selector": {"track": "retired"}}}),
                ]
            )
        )
        runtime.require(runtime.kubectl(["scale", "deployment/worker", "--replicas=0"]))
        runtime.require(
            runtime.kubectl(
                [
                    "wait",
                    "--for=delete",
                    "pod",
                    "-l",
                    "app=worker",
                    "--timeout=90s",
                ],
                timeout=100,
            )
        )
    if mode in {"decisions", "mission"}:
        runtime.require(
            runtime.kubectl(
                [
                    "patch",
                    "role",
                    "dispatch-pod-reader",
                    "--type=merge",
                    "-p",
                    json.dumps(
                        {"rules": [{"apiGroups": ["*"], "resources": ["*"], "verbs": ["*"]}]}
                    ),
                ]
            )
        )
        runtime.require(runtime.kubectl(["scale", "deployment/dispatch", "--replicas=1"]))
        runtime.require(
            runtime.kubectl(
                [
                    "rollout",
                    "status",
                    "deployment/dispatch",
                    "--timeout=90s",
                ],
                timeout=100,
            )
        )
    if mode == "handoff":
        runtime.require(
            runtime.kubectl(
                [
                    "set",
                    "image",
                    "deployment/dispatch",
                    "api=" + os.environ["DOCKYARD_IMAGE"] + "-missing",
                ]
            )
        )
    print("Prepared the operating scenario while preserving its original state record.")


if __name__ == "__main__":
    if sys.argv[1:] not in (["triage"], ["decisions"], ["handoff"], ["mission"]):
        raise SystemExit("Choose triage, decisions, handoff, or mission.")
    prepare(sys.argv[1])
