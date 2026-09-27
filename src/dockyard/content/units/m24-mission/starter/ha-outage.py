"""Create the owned cluster's explicit one-member outage and endpoint routing fault."""

import json
import time
from dockyard.native import current
from dockyard.runtimes.native_cluster import load_balancer_configuration

runtime = current()
names = [entry["name"] for entry in runtime.discover()]
if len(names) != 4:
    raise RuntimeError("This fixture needs three control planes and one worker")
primary, worker = names[0], names[-1]
runtime.require(runtime.guest(primary, ["sudo", "mkdir", "-p", "/var/lib/dockyard/ha-outage"]))
for component in ("kube-apiserver", "etcd"):
    runtime.require(
        runtime.guest(
            primary,
            [
                "sudo",
                "mv",
                "/etc/kubernetes/manifests/" + component + ".yaml",
                "/var/lib/dockyard/ha-outage/" + component + ".yaml",
            ],
        )
    )
for attempt in range(40):
    observed = runtime.guest(primary, ["sudo", "crictl", "ps", "-o", "json"])
    runtime.require(observed)
    running = {
        entry.get("labels", {}).get("io.kubernetes.container.name")
        for entry in json.loads(observed.stdout)["containers"]
    }
    if not running & {"kube-apiserver", "etcd"}:
        break
    time.sleep(2)
else:
    raise RuntimeError("The primary static components did not stop")
runtime.require(
    runtime.guest(
        worker,
        ["sudo", "tee", "/etc/haproxy/haproxy.cfg"],
        input_text=load_balancer_configuration([primary]),
    )
)
runtime.require(runtime.guest(worker, ["sudo", "haproxy", "-c", "-f", "/etc/haproxy/haproxy.cfg"]))
runtime.require(runtime.guest(worker, ["sudo", "systemctl", "restart", "haproxy"]))
print("Primary API and etcd stopped; endpoint currently selects only that unavailable backend.")
