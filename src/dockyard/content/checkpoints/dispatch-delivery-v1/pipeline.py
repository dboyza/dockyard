"""Build, test, and publish a real image to this lab's loopback registry."""
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen

def command(args, **kwargs):
    completed = subprocess.run(args, text=True, capture_output=True, timeout=300, **kwargs)
    if completed.returncode:
        raise SystemExit(completed.stderr or completed.stdout)
    print(completed.stdout, end="")
    print(completed.stderr, end="")
    return completed.stdout.strip()

version = Path("VERSION").read_text().strip()
if not re.fullmatch(r"dispatch-[0-9]+", version):
    raise SystemExit("Use an explicit dispatch-N release version.")
registry = os.environ["DOCKYARD_REGISTRY"]
image = registry + "/dispatch:" + version
started = time.time()
command(["docker", "build", "--build-arg", "BASE_IMAGE=" + os.environ["DOCKYARD_PYTHON_IMAGE"], "--label", "org.opencontainers.image.version=" + version, "--label", "io.dockyard.lab=" + os.environ["DOCKYARD_LAB"], "-t", image, "."])
settings = json.loads(Path("pipeline.json").read_text())
tested = settings.get("run_tests") is True
if tested:
    command(["docker", "run", "--rm", "-i", "--network=none", "--label", "io.dockyard.lab=" + os.environ["DOCKYARD_LAB"], image, "python", "-"], input=Path("test_release.py").read_text())
command(["docker", "push", image])
request = Request("http://" + registry + "/v2/dispatch/manifests/" + version, headers={"Accept":"application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json"})
with urlopen(request, timeout=5) as response:
    digest = response.headers["Docker-Content-Digest"]
record = {"lab":os.environ["DOCKYARD_LAB"], "version":version, "image":registry + "/dispatch@" + digest, "digest":digest, "tested":tested, "started":started, "finished":time.time(), "source_sha256":{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (".dockerignore","Dockerfile","app.py","database.py","worker.py","maintenance.py","dashboard.html","VERSION","requirements.txt")}, "test_sha256":hashlib.sha256(Path("test_release.py").read_bytes()).hexdigest()}
Path("release.json").write_text(json.dumps(record, indent=2) + "\n")
print(record["image"])
