import json
import time

from dockyard.native import current

r = current()
primary = "d" + r.lab.id[:10] + "-cp1"
result = r.guest(primary, ["sudo", "crictl", "ps", "-o", "json"])
r.require(result)
container = next(
    c["id"]
    for c in json.loads(result.stdout)["containers"]
    if c.get("labels", {}).get("io.kubernetes.container.name") == "kube-apiserver"
)
r.require(r.guest(primary, ["sudo", "crictl", "stop", container], timeout=60))
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    result = r.kubectl(["get", "--raw=/readyz"], timeout=10)
    if result.ok and result.stdout.strip() == "ok":
        break
    time.sleep(1)
else:
    raise RuntimeError("The API did not recover within two minutes.")
