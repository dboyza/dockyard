"""Record actual package inventory and findings from a pinned offline database."""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from dockyard.runtimes.scanner import SCANNER, ready

phase = sys.argv[1]
if phase not in ("before", "after"):
    raise SystemExit("Use before or after.")
cache = Path(os.environ["TRIVY_CACHE_DIR"])
if not ready(cache):
    raise SystemExit("Prepare the lab to restore its pinned scanner database before scanning.")
image = os.environ["DOCKYARD_IMAGE"]
archive = Path(os.environ["DOCKYARD_STORAGE"]) / ("scan-" + phase + ".tar")
archive.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(
    ["docker", "image", "save", "--platform=linux/arm64", "--output", str(archive), image],
    check=True,
    timeout=120,
)
archive.chmod(0o600)
with tarfile.open(archive) as source:
    manifest = json.load(source.extractfile("manifest.json"))
    configuration = source.extractfile(manifest[0]["Config"]).read()
configuration_id = "sha256:" + hashlib.sha256(configuration).hexdigest()
identity = subprocess.check_output(
    ["docker", "image", "inspect", "--platform=linux/arm64", "--format", "{{.Id}}", image],
    text=True,
).strip()
common = [
    "trivy",
    "image",
    "--disable-telemetry",
    "--skip-version-check",
    "--skip-db-update",
    "--skip-java-db-update",
    "--skip-check-update",
    "--skip-vex-repo-update",
    "--offline-scan",
    "--cache-dir",
    str(cache),
    "--input",
    str(archive),
]
for output_format, name, extra in [
    ("json", "scan", ["--scanners", "vuln"]),
    ("cyclonedx", "sbom", []),
]:
    subprocess.run(
        common + extra + ["--format", output_format, "--output", name + "-" + phase + ".json"],
        check=True,
        timeout=120,
    )
record = {
    "lab": os.environ["DOCKYARD_LAB"],
    "phase": phase,
    "image_manifest": identity,
    "image_configuration": configuration_id,
    "database": SCANNER["database"],
    "at": time.time(),
    "reports": {
        name: hashlib.sha256(Path(name + "-" + phase + ".json").read_bytes()).hexdigest()
        for name in ("scan", "sbom")
    },
}
Path("scan-evidence-" + phase + ".json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
