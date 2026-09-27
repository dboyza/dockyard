"""Prepare original CKA operations tasks on native kubeadm machines."""

from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

from dockyard.fixtures.exam import apply, deployment
from dockyard.fixtures.maintenance import record
from dockyard.fixtures.recovery import etcd
from dockyard.native import current
from dockyard.probes.kubernetes import get, kubectl
from dockyard.workspace import atomic_write


def prepare() -> None:
    r = current()
    record()
    worker = "d" + r.lab.id[:10] + "-worker"
    status = json.loads(
        etcd(
            r,
            [
                "etcdctl",
                "--endpoints=https://127.0.0.1:2379",
                "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
                "--cert=/etc/kubernetes/pki/etcd/server.crt",
                "--key=/etc/kubernetes/pki/etcd/server.key",
                "endpoint",
                "status",
                "-w",
                "json",
            ],
        )
    )[0]["Status"]
    claim = get("pvc", "data-db-0")
    volume = get("pv", claim["spec"]["volumeName"])
    atomic_write(
        r.root / "data/exam-backup.json",
        json.dumps(
            {
                "revision": status["header"]["revision"],
                "claim_uid": claim["metadata"]["uid"],
                "volume_uid": volume["metadata"]["uid"],
            }
        ).encode(),
    )
    apply(
        {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"name": "incident-observer", "namespace": "dispatch"},
        }
    )
    # A dedicated scheduling requirement is separate from the existing application.
    kubectl("label", "node", "lima-" + worker, "dockyard.io/pool=batch", "--overwrite")
    kubectl("taint", "node", "lima-" + worker, "dockyard.io/batch=true:NoSchedule", "--overwrite")
    batch = deployment("batch-audit", ["python", "-c", "import time; time.sleep(86400)"])
    batch["spec"]["template"]["spec"]["nodeSelector"] = {"dockyard.io/pool": "retired"}
    apply(batch)
    # The chart renders a real running configuration consumer, with its original wrong value.
    chart = Path("ops-chart")
    (chart / "templates").mkdir(parents=True, exist_ok=True)
    (chart / "Chart.yaml").write_text("apiVersion: v2\nname: operations-report\nversion: 0.1.0\n")
    (chart / "values.yaml").write_text(
        yaml.safe_dump({"image": os.environ["DOCKYARD_IMAGE"], "environment": "staging"})
    )
    reporter = deployment(
        "operations-report",
        [
            "python",
            "-u",
            "-c",
            "import os,http.server; from pathlib import Path; "
            "Path('/tmp/environment').write_text(os.environ['REPORT_ENV']); os.chdir('/tmp'); "
            "http.server.ThreadingHTTPServer(('0.0.0.0',8080),http.server.SimpleHTTPRequestHandler).serve_forever()",
        ],
    )
    reporter["spec"]["template"]["spec"]["tolerations"] = [
        {
            "key": "dockyard.io/batch",
            "operator": "Equal",
            "value": "true",
            "effect": "NoSchedule",
        }
    ]
    container = reporter["spec"]["template"]["spec"]["containers"][0]
    container["image"] = "{{ .Values.image }}"
    container["env"] = [{"name": "REPORT_ENV", "value": "{{ .Values.environment }}"}]
    (chart / "templates/report.yaml").write_text(yaml.safe_dump(reporter, sort_keys=False))
    # kubelet nodes stay healthy while the workload network and placement are wrong.
    kubectl(
        "patch",
        "deployment",
        "trusted-client",
        "-n",
        "frontend",
        "--type=merge",
        "-p",
        json.dumps({"spec": {"template": {"spec": {"dnsPolicy": "Default"}}}}),
    )
    kubectl(
        "patch",
        "statefulset",
        "db",
        "--type=merge",
        "-p",
        json.dumps(
            {
                "spec": {
                    "template": {
                        "spec": {
                            "nodeSelector": {"kubernetes.io/hostname": "lima-dockyard-unavailable"}
                        }
                    }
                }
            }
        ),
    )
    kubectl("delete", "pod", "db-0", "--wait=true", "--timeout=90s", timeout=100)
    r.require(r.guest(worker, ["sudo", "sysctl", "-w", "net.ipv4.ip_forward=0"]))
    print("Prepared the native operations assessment and retained original identities.")


if __name__ == "__main__":
    prepare()
