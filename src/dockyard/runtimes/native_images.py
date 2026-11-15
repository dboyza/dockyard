"""Transfer native images into verified guests without host mounts."""

from __future__ import annotations

import hashlib
import threading

from dockyard import host
from dockyard.images import PINNED, ImageStore
from dockyard.process import run
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime


def load(runtime: LinuxRuntime, image: str, cancel: threading.Event) -> None:
    """Import the lab's own practice image, or a pinned image from its private archive."""
    practice = "dockyard-" + runtime.lab.id[:12] + ":practice"
    name = next((key for key, value in PINNED.items() if value == image), None)
    if image != practice and name is None:
        raise RuntimeErrorBase("Only the current lab image or a pinned dependency can be imported.")
    built = None
    if name is not None:
        archive = ImageStore(runtime.tools, runtime.env).ensure_archive(
            name, cancel, runtime.report
        )
    else:
        directory = runtime.root / "data/native-images"
        if directory.is_symlink():
            raise RuntimeErrorBase(
                "The native image staging directory is a symbolic link; preserved."
            )
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        archive = built = directory / (hashlib.sha256(image.encode()).hexdigest()[:24] + ".tar")
        if archive.is_symlink():
            raise RuntimeErrorBase("The native image staging file is a symbolic link; preserved.")
        runtime.report("Transferring this lab's image to its nodes")
        runtime.require(
            run(
                [
                    "docker",
                    "image",
                    "save",
                    "--platform=linux/" + host.architecture(),
                    "-o",
                    str(archive),
                    image,
                ],
                env=runtime.env,
                timeout=180,
                cancel=cancel,
            )
        )
        archive.chmod(0o600)
    try:
        for entry in runtime.discover():
            guest = entry["name"]
            target = "/tmp/dockyard-" + runtime.lab.id + "-image.tar"
            runtime.copy_to(guest, archive, target, cancel=cancel)
            runtime.require(
                runtime.guest(
                    guest,
                    [
                        "sudo",
                        "ctr",
                        "-n",
                        "k8s.io",
                        "images",
                        "import",
                        "--platform",
                        "linux/" + host.architecture(),
                        target,
                    ],
                    timeout=180,
                    cancel=cancel,
                )
            )
            runtime.require(runtime.guest(guest, ["rm", "-f", "--", target], cancel=cancel))
    finally:
        if built is not None:
            built.unlink(missing_ok=True)
