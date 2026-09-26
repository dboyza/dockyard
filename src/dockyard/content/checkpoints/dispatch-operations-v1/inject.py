"""Author the declared teaching faults only inside this lab's recorded guests."""

import sys

from dockyard.native import current

runtime = current()
primary = "d" + runtime.lab.id[:10] + "-cp1"
worker = "d" + runtime.lab.id[:10] + "-worker"
mode = sys.argv[1]
if mode in {"runtime", "mission"}:
    runtime.require(
        runtime.guest(
            worker,
            ["sudo", "tee", "/etc/crictl.yaml"],
            input_text="runtime-endpoint: unix:///run/containerd/retired.sock\nimage-endpoint: unix:///run/containerd/retired.sock\ntimeout: 2\ndebug: false\n",
        )
    )
if mode in {"kubelet", "mission"}:
    runtime.require(runtime.guest(worker, ["sudo", "systemctl", "stop", "kubelet"]))
if mode in {"certificates", "mission"}:
    runtime.require(
        runtime.guest(primary, ["sh", "-c", 'sed -i "s/:6443/:7443/g" "$HOME/.kube/operator.conf"'])
    )
print("Prepared the declared native teaching fault.")
