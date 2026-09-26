"""Explicit native-lab helpers available from the real learner shell."""

from __future__ import annotations

import argparse
import os
import threading
from pathlib import Path

import yaml

from dockyard.models import Runtime
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime
from dockyard.runtimes.native_images import load
from dockyard.service import Service


def current() -> LinuxRuntime:
    service = Service(Path(os.environ["DOCKYARD_DATA"]))
    lab = service.store.lab(os.environ["DOCKYARD_UNIT"])
    if (
        lab is None
        or lab.runtime != Runtime.LINUX
        or lab.id != os.environ["DOCKYARD_LAB"]
        or Path(lab.workspace).resolve() != Path(os.environ["DOCKYARD_WORKSPACE"]).resolve()
    ):
        raise RuntimeErrorBase("This terminal no longer identifies the current native lab.")
    return LinuxRuntime(lab, service.environment(lab), service.store.save_lab, service.tools)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser(
        "stage-upgrade", help="Stage verified 1.35.8 packages without installing them"
    )
    waited = actions.add_parser(
        "wait-upgraded-node", help="Observe upgraded node and API readiness before the next node"
    )
    waited.add_argument("guest")
    actions.add_parser(
        "expose-app", help="Connect the private browser endpoint to the native NodePort"
    )
    actions.add_parser(
        "prepare-storage", help="Create the native checkpoint's guest-local database directory"
    )
    actions.add_parser(
        "refresh-client",
        help="Copy this lab's current native admin client to its private host kubeconfig",
    )
    actions.add_parser("init-config", help="Print this lab's kubeadm initialization configuration")
    joined = actions.add_parser("join-config", help="Print a private CA-pinned join configuration")
    joined.add_argument("guest")
    actions.add_parser("network-manifest", help="Print the pinned native Calico VXLAN manifest")
    actions.add_parser(
        "lb-config", help="Print the recorded HA topology's TCP load balancer configuration"
    )
    image = actions.add_parser(
        "load-image", help="Import the current lab image or one pinned dependency"
    )
    image.add_argument("image")
    args = parser.parse_args()
    runtime = current()
    cancel = threading.Event()
    if args.action in {"init-config", "join-config", "network-manifest", "lb-config"}:
        from dockyard.runtimes import native_cluster

        names = native_cluster.topology(runtime)
        if args.action == "init-config":
            if len(names) != 2:
                raise RuntimeErrorBase("The learner initialization helper expects two guests.")
            print(
                yaml.safe_dump_all(
                    native_cluster.initialization(runtime, names[0], cancel, "1.35.8")
                )
            )
        elif args.action == "join-config":
            print(yaml.safe_dump(native_cluster.join_configuration(runtime, args.guest, cancel)))
        elif args.action == "lb-config":
            if len(names) != 4:
                raise RuntimeErrorBase("This lab does not have three control-plane guests.")
            print(native_cluster.load_balancer_configuration(names[:-1]))
        else:
            print(native_cluster.network_manifest(runtime, cancel))
    elif args.action == "wait-upgraded-node":
        from dockyard.runtimes.native_maintenance import wait_node

        wait_node(runtime, args.guest, cancel)
        print("The upgraded node and private API remained ready with settled components.")
    elif args.action == "stage-upgrade":
        from dockyard.runtimes.native_maintenance import stage_upgrade

        print(stage_upgrade(runtime, cancel))
    elif args.action == "prepare-storage":
        worker = "d" + runtime.lab.id[:10] + "-worker"
        runtime.require(
            runtime.guest(
                worker,
                [
                    "sudo",
                    "install",
                    "-d",
                    "-m",
                    "0770",
                    "-o",
                    "70",
                    "-g",
                    "70",
                    "/var/lib/dockyard/postgres",
                ],
                cancel=cancel,
            )
        )
        print("Prepared the owned worker's local database directory.")
    elif args.action == "expose-app":
        from dockyard.runtimes.native_gateway import prepare

        prepare(runtime, cancel)
        print("Connected the owned worker NodePort to the private browser endpoint.")
    elif args.action == "refresh-client":
        runtime.export_kubeconfig(cancel)
        print("Refreshed the current lab's private Kubernetes client.")
    else:
        load(runtime, args.image, cancel)
        print("Imported the image into this lab's native nodes.")


if __name__ == "__main__":
    main()
