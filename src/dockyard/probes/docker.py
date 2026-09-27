"""Cross-resource observations which cannot be expressed as one JSON field."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
import tarfile
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from dockyard import host
from dockyard.process import run


def inspect(kind: str, identity: str) -> dict[str, Any]:
    result = run(["docker", kind, "inspect", identity], timeout=10)
    if not result.ok:
        raise ValueError(result.stderr.strip())
    return dict(json.loads(result.stdout)[0])


def network() -> dict[str, Any]:
    name = os.environ["DOCKYARD_CONTAINER"]
    lab_id = os.environ["DOCKYARD_LAB"]
    api = inspect("container", name)
    peer = inspect("container", name + "-dependency")
    bridge = inspect("network", os.environ["DOCKYARD_NETWORK"])
    owned = (
        all(
            resource["Config"]["Labels"].get("io.dockyard.lab") == lab_id
            for resource in (api, peer)
        )
        and bridge["Labels"].get("io.dockyard.lab") == lab_id
    )
    peer_endpoints = peer["NetworkSettings"]["Networks"]
    api_endpoints = api["NetworkSettings"]["Networks"]
    network_name = os.environ["DOCKYARD_NETWORK"]
    shared = all(
        endpoints.get(network_name, {}).get("NetworkID") == bridge["Id"]
        for endpoints in (api_endpoints, peer_endpoints)
    )
    lookup = run(
        [
            "docker",
            "exec",
            name,
            "python",
            "-c",
            'import socket; print(socket.gethostbyname("dependency"))',
        ],
        timeout=10,
    )
    expected_ip = peer_endpoints.get(network_name, {}).get("IPAddress")
    dns = lookup.ok and bool(expected_ip) and lookup.stdout.strip() == expected_ip
    peer_private = not any(peer["NetworkSettings"]["Ports"].values())
    payload: dict[str, Any] = {}
    try:
        with urlopen(
            f"http://127.0.0.1:{os.environ['DOCKYARD_PORT']}/dependency", timeout=4
        ) as response:
            payload = json.load(response)
    except OSError as error:
        payload = {"error": str(error)}
    reached_peer = (
        payload.get("connected") is True
        and payload.get("dependency", {}).get("hostname") == peer["Config"]["Hostname"]
    )
    return {
        "owned": owned,
        "shared_bridge": shared,
        "dns": dns,
        "dependency_private": peer_private,
        "reached_peer": reached_peer,
        "response": payload,
        "observed_dns": lookup.stdout.strip(),
    }


def request(path: str, body: dict[str, str] | None = None, method: str = "GET") -> dict[str, Any]:
    data = json.dumps(body).encode() if body is not None else None
    address = f"http://127.0.0.1:{os.environ['DOCKYARD_PORT']}{path}"
    with urlopen(
        Request(address, data=data, method=method, headers={"Content-Type": "application/json"}),
        timeout=4,
    ) as response:
        return dict(json.load(response))


def storage(mode: str) -> dict[str, Any]:
    api = inspect("container", os.environ["DOCKYARD_CONTAINER"])
    mount: dict[str, Any] = next(
        (item for item in api["Mounts"] if item["Destination"] == "/data"), {}
    )
    expected_type = "bind" if mode == "bind" else "volume"
    valid_mount = mount.get("Type") == expected_type and mount.get("RW") is True
    if expected_type == "bind":
        valid_mount = (
            valid_mount
            and Path(str(mount.get("Source", ""))).resolve()
            == Path(os.environ["DOCKYARD_STORAGE"]).resolve()
        )
    else:
        volume = inspect("volume", os.environ["DOCKYARD_VOLUME"])
        valid_mount = (
            valid_mount
            and mount.get("Name") == volume["Name"]
            and volume["Labels"].get("io.dockyard.lab") == os.environ["DOCKYARD_LAB"]
        )
    result: dict[str, Any] = {"mount": valid_mount, "roundtrip": False, "durable": False}
    job: dict[str, Any] | None = None
    try:
        job = request(
            "/jobs", {"title": "Dockyard storage observation " + uuid.uuid4().hex}, "POST"
        )
        jobs = request("/jobs")["jobs"]
        result["roundtrip"] = job in jobs
        if not valid_mount:
            return result
        # Observe the same data through a separate short-lived reader and a read-only mount.
        source = os.environ["DOCKYARD_STORAGE"] if mode == "bind" else os.environ["DOCKYARD_VOLUME"]
        code = (
            'import json, sqlite3; c=sqlite3.connect("file:/data/jobs.db?mode=ro",uri=True); '
            'print(json.dumps(c.execute("SELECT id,title FROM jobs").fetchall()))'
        )
        reader = run(
            [
                "docker",
                "run",
                "--rm",
                "--label",
                "io.dockyard.lab=" + os.environ["DOCKYARD_LAB"],
                "--mount",
                f"type={expected_type},source={source},target=/data,readonly",
                os.environ["DOCKYARD_PYTHON_IMAGE"],
                "python",
                "-c",
                code,
            ],
            timeout=20,
        )
        rows = json.loads(reader.stdout) if reader.ok else []
        result["durable"] = [job["id"], job["title"]] in rows
        if mode == "recovery":
            seed = "recovery-" + os.environ["DOCKYARD_LAB"]
            result["restored"] = any(row[0] == seed for row in rows)
            archive = Path(os.environ["DOCKYARD_WORKSPACE"]) / "backup.tar"
            result["backup"] = False
            if archive.is_file() and archive.stat().st_size <= 16 * 1024 * 1024:
                with tarfile.open(archive, "r:") as package:
                    item = package.getmember("jobs.db")
                    if item.isfile() and item.size <= 8 * 1024 * 1024:
                        stream = package.extractfile(item)
                        if stream:
                            with sqlite3.connect(":memory:") as database:
                                database.deserialize(stream.read())
                                result["backup"] = (
                                    database.execute(
                                        "SELECT id FROM jobs WHERE id=?", (seed,)
                                    ).fetchone()
                                    is not None
                                )
        return result
    finally:
        if job and "id" in job:
            request("/jobs/" + str(job["id"]), method="DELETE")


def compose() -> dict[str, Any]:
    name = os.environ["DOCKYARD_CONTAINER"]
    lab_id = os.environ["DOCKYARD_LAB"]
    api = inspect("container", name)
    db = inspect("container", os.environ["DOCKYARD_PROJECT"] + "-db")
    redis = inspect("container", os.environ["DOCKYARD_PROJECT"] + "-queue")
    workers_result = run(
        [
            "docker",
            "container",
            "ls",
            "--quiet",
            "--filter",
            "label=io.dockyard.lab=" + lab_id,
            "--filter",
            "label=com.docker.compose.service=worker",
        ],
        timeout=10,
    )
    workers = [inspect("container", identity) for identity in workers_result.stdout.split()]
    resources = [api, db, redis, *workers]
    owned = all(
        resource["Config"]["Labels"].get("io.dockyard.lab") == lab_id for resource in resources
    )
    ready = request("/readyz").get("ready") is True
    private = all(
        not any(resource["NetworkSettings"]["Ports"].values()) for resource in [db, redis, *workers]
    )
    healthy = all(
        resource.get("State", {}).get("Health", {}).get("Status") == "healthy"
        for resource in [api, db, redis]
    )
    volume = inspect("volume", os.environ["DOCKYARD_VOLUME"])
    persistent = volume["Labels"].get("io.dockyard.lab") == lab_id and any(
        item.get("Name") == volume["Name"] and item.get("Destination") == "/var/lib/postgresql/data"
        for item in db["Mounts"]
    )
    config_result = run(["docker", "compose", "config", "--format", "json"], timeout=10)
    config = json.loads(config_result.stdout) if config_result.ok else {}
    services = config.get("services", {})
    guarded = all(
        services.get(service, {}).get("depends_on", {}).get(dependency, {}).get("condition")
        == "service_healthy"
        for service in ("api", "worker")
        for dependency in ("db", "queue")
    )
    title = "observe-" + uuid.uuid4().hex
    job = request("/jobs", {"title": title}, "POST")
    identity = str(job.get("id", ""))
    if not re.fullmatch(r"[0-9a-f]{32}", identity):
        raise ValueError("The API returned an unexpected job identity.")
    completed: dict[str, Any] = {}
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            completed = next((row for row in request("/jobs")["jobs"] if row["id"] == identity), {})
            if completed.get("status") == "done":
                break
            time.sleep(0.25)
        expected = {
            "normalized": title.upper(),
            "sha256": hashlib.sha256(title.encode()).hexdigest(),
        }
        processed = completed.get("result") == expected and completed.get("worker") in {
            worker["Config"]["Hostname"] for worker in workers
        }
        query = "SELECT row_to_json(j) FROM jobs j WHERE id='" + identity + "';"
        observed = run(
            [
                "docker",
                "exec",
                db["Id"],
                "psql",
                "-U",
                "dispatch",
                "-d",
                "dispatch",
                "-t",
                "-A",
                "-c",
                query,
            ],
            timeout=10,
        )
        stored = json.loads(observed.stdout) if observed.ok and observed.stdout.strip() else {}
        durable = stored.get("result") == expected and stored.get("status") == "done"
        return {
            "owned": owned,
            "ready": ready,
            "private": private,
            "healthy": healthy,
            "persistent": persistent,
            "guarded": guarded,
            "workers": len(workers),
            "scaled": len(workers) >= 2,
            "processed": processed,
            "durable": durable,
            "job": completed,
        }
    finally:
        request("/jobs/" + identity, method="DELETE")


def registry() -> dict[str, Any]:
    api = inspect("container", os.environ["DOCKYARD_CONTAINER"])
    registry_container = inspect("container", os.environ["DOCKYARD_CONTAINER"] + "-registry")
    address = "127.0.0.1:" + os.environ["DOCKYARD_REGISTRY_PORT"]
    selected = api["Config"]["Image"]
    pinned = bool(re.fullmatch(re.escape(address) + r"/dispatch@sha256:[0-9a-f]{64}", selected))
    served = False
    if pinned:
        digest = selected.split("@", 1)[1]
        target = f"http://{address}/v2/dispatch/manifests/{digest}"
        headers = {
            "Accept": (
                "application/vnd.oci.image.manifest.v1+json, "
                "application/vnd.docker.distribution.manifest.v2+json"
            )
        }
        with urlopen(Request(target, method="HEAD", headers=headers), timeout=4) as response:
            served = response.headers.get("Docker-Content-Digest") == digest
    bindings = registry_container["HostConfig"]["PortBindings"].get("5000/tcp", [])
    private = (
        len(bindings) == 1
        and bindings[0]["HostIp"] == "127.0.0.1"
        and bindings[0]["HostPort"] == os.environ["DOCKYARD_REGISTRY_PORT"]
    )
    owned = (
        registry_container["Config"]["Labels"].get("io.dockyard.lab") == os.environ["DOCKYARD_LAB"]
    )
    return {
        "pinned": pinned,
        "served": served,
        "private": private,
        "owned": owned,
        "selected": selected,
    }


def artifact() -> dict[str, Any]:
    api = inspect("container", os.environ["DOCKYARD_CONTAINER"])
    image = inspect("image", api["Image"])
    native = image["Architecture"] == host.architecture() and image["Os"] == "linux"
    clean = True
    with tempfile.TemporaryDirectory(prefix="dockyard-image-observation-") as temporary:
        archive = Path(temporary) / "image.tar"
        saved = run(["docker", "image", "save", "--output", str(archive), api["Image"]], timeout=45)
        if not saved.ok or archive.stat().st_size > 512 * 1024 * 1024:
            raise ValueError("Image observation requires a valid archive under 512 MiB.")
        with tarfile.open(archive) as outer:
            manifest_stream = outer.extractfile("manifest.json")
            if manifest_stream is None:
                raise ValueError("The image archive did not contain a manifest.")
            manifest = json.load(manifest_stream)
            for layer_name in manifest[0]["Layers"]:
                layer_stream = outer.extractfile(layer_name)
                if layer_stream is None:
                    raise ValueError("The image archive has a missing layer.")
                with tarfile.open(fileobj=layer_stream, mode="r|*") as layer:
                    for member in layer:
                        if Path(member.name).name in {".env", "training-secret.env"}:
                            clean = False
    return {"native": native, "excluded_secret": clean, "architecture": image["Architecture"]}


def hardened_container(identity: str) -> dict[str, Any]:
    api = inspect("container", identity)
    config = api["HostConfig"]
    program = (
        "import os, json; from pathlib import Path; "
        "print(json.dumps({'uid':os.getuid(), "
        "'memory':Path('/sys/fs/cgroup/memory.max').read_text().strip(), "
        "'cpu':Path('/sys/fs/cgroup/cpu.max').read_text().strip(), "
        "'pids':Path('/sys/fs/cgroup/pids.max').read_text().strip()}))"
    )
    observed = run(["docker", "exec", api["Id"], "python", "-c", program], timeout=10)
    live = json.loads(observed.stdout) if observed.ok else {}
    memory = config.get("Memory", 0)
    nano_cpus = config.get("NanoCpus", 0)
    pids = config.get("PidsLimit", 0) or 0
    cpu_parts = str(live.get("cpu", "")).split()
    cpu_live = (
        len(cpu_parts) == 2
        and cpu_parts[0] != "max"
        and 0 < int(cpu_parts[0]) / int(cpu_parts[1]) <= 1
    )
    probe = """import errno, os
try:
    open('/dockyard-readonly-observation', 'w').close()
    os.unlink('/dockyard-readonly-observation')
    print(False)
except OSError as error:
    print(error.errno == errno.EROFS)
"""
    filesystem = run(
        ["docker", "exec", "--user", "0", api["Id"], "python", "-c", probe], timeout=10
    )
    return {
        "nonroot": isinstance(live.get("uid"), int) and live["uid"] != 0,
        "readonly": bool(config.get("ReadonlyRootfs")) and filesystem.stdout.strip() == "True",
        "caps": "ALL" in (config.get("CapDrop") or []) and not config.get("Privileged"),
        "no_escalation": any(
            value in ("no-new-privileges", "no-new-privileges:true")
            for value in (config.get("SecurityOpt") or [])
        ),
        "memory": 32 * 1024**2 <= memory <= 256 * 1024**2 and live.get("memory") == str(memory),
        "cpu": 0 < nano_cpus <= 1_000_000_000 and cpu_live,
        "pids": 16 <= pids <= 256 and live.get("pids") == str(pids),
        "observed": live,
    }


def hardening() -> dict[str, Any]:
    return hardened_container(os.environ["DOCKYARD_CONTAINER"])


def recovery() -> dict[str, Any]:
    lab_id = os.environ["DOCKYARD_LAB"]
    db = inspect("container", os.environ["DOCKYARD_PROJECT"] + "-db")
    if db["Config"]["Labels"].get("io.dockyard.lab") != lab_id:
        raise ValueError("The database does not belong to this lab.")
    seed = "capstone-" + lab_id
    query = "SELECT id FROM jobs WHERE id='" + seed + "';"
    result = run(
        [
            "docker",
            "exec",
            db["Id"],
            "psql",
            "-U",
            "dispatch",
            "-d",
            "restored",
            "-t",
            "-A",
            "-c",
            query,
        ],
        timeout=10,
    )
    restored = result.ok and result.stdout.strip() == seed
    workers = run(
        [
            "docker",
            "container",
            "ls",
            "--quiet",
            "--filter",
            "label=io.dockyard.lab=" + lab_id,
            "--filter",
            "label=com.docker.compose.service=worker",
        ],
        timeout=10,
    )
    secured = bool(workers.stdout.strip())
    for identity in workers.stdout.split():
        observations = hardened_container(identity)
        secured = secured and all(
            observations[key]
            for key in ("nonroot", "readonly", "caps", "no_escalation", "memory", "cpu", "pids")
        )
    runbook = Path(os.environ["DOCKYARD_WORKSPACE"]) / "RUNBOOK.md"
    return {
        "restored": restored,
        "workers_hardened": secured,
        "runbook_present": runbook.is_file() and runbook.stat().st_size >= 100,
    }


def main() -> None:
    probes: dict[str, Callable[[], dict[str, Any]]] = {
        "network": network,
        "compose": compose,
        "registry": registry,
        "artifact": artifact,
        "hardening": hardening,
        "recovery": recovery,
        "storage-bind": lambda: storage("bind"),
        "storage-volume": lambda: storage("volume"),
        "storage-recovery": lambda: storage("recovery"),
    }
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in probes:
            raise ValueError("Unknown packaged observation.")
        print(json.dumps(probes[sys.argv[1]]()))
    except (ValueError, KeyError, OSError, sqlite3.Error, tarfile.TarError) as error:
        print(json.dumps({"observation_error": str(error)}))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
