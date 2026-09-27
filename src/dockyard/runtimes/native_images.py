"""Transfer native images into verified guests without host mounts."""

from __future__ import annotations

import hashlib
import json
import threading

from dockyard import host
from dockyard.catalog import CONTENT
from dockyard.process import run
from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.runtimes.linux import LinuxRuntime


def load(runtime: LinuxRuntime, image: str, cancel: threading.Event) -> None:
    allowed = json.loads((CONTENT / "compatibility.json").read_text())["images"]
    practice = "dockyard-" + runtime.lab.id[:12] + ":practice"
    if image != practice and image not in allowed.values():
        raise RuntimeErrorBase("Only the current lab image or a pinned dependency can be imported.")
    directory = runtime.root / "data/native-images"
    if directory.is_symlink():
        raise RuntimeErrorBase("The native image staging directory is a symbolic link; preserved.")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = hashlib.sha256(image.encode()).hexdigest()[:24] + ".tar"
    archive = directory / name
    if archive.is_symlink():
        raise RuntimeErrorBase("The native image staging file is a symbolic link; preserved.")
    reference = image
    if image != practice:
        key = next(key for key, value in allowed.items() if value == image)
        reference = (
            "dockyard-cache/" + key.replace("_", "-") + ":" + image.split("sha256:")[-1][:16]
        )
        existing = run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", reference], env=runtime.env
        )
        source = run(["docker", "image", "inspect", "--format", "{{.Id}}", image], env=runtime.env)
        runtime.require(source)
        if existing.ok and existing.stdout.strip() != source.stdout.strip():
            raise RuntimeErrorBase("The local dependency alias has changed identity; preserved.")
        runtime.require(run(["docker", "tag", image, reference], env=runtime.env))
    runtime.report("Transferring the native-architecture image " + reference)
    runtime.require(
        run(
            [
                "docker",
                "image",
                "save",
                "--platform=linux/" + host.architecture(),
                "-o",
                str(archive),
                reference,
            ],
            env=runtime.env,
            timeout=180,
            cancel=cancel,
        )
    )
    archive.chmod(0o600)
    try:
        for entry in runtime.discover():
            name = entry["name"]
            target = "/tmp/dockyard-" + runtime.lab.id + "-image.tar"
            runtime.copy_to(name, archive, target, cancel=cancel)
            runtime.require(
                runtime.guest(
                    name,
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
            runtime.require(runtime.guest(name, ["rm", "-f", "--", target], cancel=cancel))
    finally:
        archive.unlink(missing_ok=True)
