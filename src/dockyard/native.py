"""Explicit native-lab helpers available from the real learner shell."""

from __future__ import annotations

import argparse
import os
import threading
from pathlib import Path

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
        "prepare-storage", help="Create the native checkpoint's guest-local database directory"
    )
    actions.add_parser(
        "refresh-client",
        help="Copy this lab's current native admin client to its private host kubeconfig",
    )
    image = actions.add_parser(
        "load-image", help="Import the current lab image or one pinned dependency"
    )
    image.add_argument("image")
    args = parser.parse_args()
    runtime = current()
    cancel = threading.Event()
    if args.action == "prepare-storage":
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
    elif args.action == "refresh-client":
        runtime.export_kubeconfig(cancel)
        print("Refreshed the current lab's private Kubernetes client.")
    else:
        load(runtime, args.image, cancel)
        print("Imported the image into this lab's native nodes.")


if __name__ == "__main__":
    main()
