"""Record the immutable before-maintenance comparison for a fresh owned lab."""

import json
import uuid

from dockyard.native import current
from dockyard.probes.kubernetes import sql
from dockyard.probes.maintenance import certificate, observed
from dockyard.workspace import atomic_write


def record() -> None:
    r = current()
    version = r.kubectl(["get", "--raw=/version"])
    r.require(version)
    job = uuid.uuid4().hex
    marker = uuid.uuid4().hex
    r.require(
        r.kubectl(
            [
                "create",
                "configmap",
                "maintenance-sentinel",
                "-n",
                "default",
                "--from-literal=marker=" + marker,
            ]
        )
    )
    sql(
        "INSERT INTO jobs(id,title,status) VALUES ('" + job + "','maintenance-preserved','done')",
        workload="statefulset/db",
    )
    serial, ca = certificate(r)
    baseline = {
        "version": json.loads(version.stdout)["gitVersion"],
        "namespace_uid": observed(r, ["get", "namespace", "dispatch"])["metadata"]["uid"],
        "nodes": {
            n["metadata"]["name"]: n["metadata"]["uid"]
            for n in observed(r, ["get", "nodes"])["items"]
        },
        "marker": marker,
        "marker_uid": observed(r, ["get", "configmap", "maintenance-sentinel", "-n", "default"])[
            "metadata"
        ]["uid"],
        "job_id": job,
        "serial": serial,
        "ca": ca,
    }
    atomic_write(r.root / "data/maintenance-baseline.json", json.dumps(baseline).encode())
    print(
        "Recorded original namespace, nodes, API version, "
        "public certificate identity, and persisted test job."
    )


if __name__ == "__main__":
    record()
