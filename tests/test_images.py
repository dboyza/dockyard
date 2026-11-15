"""Pinned images live where they are used: Docker for host steps, private archives for clusters."""

import threading

from dockyard import cache, images
from dockyard.catalog import Catalog
from dockyard.images import PINNED, ImageStore, alias, cluster_images, host_images
from dockyard.process import ProcessResult
from dockyard.service import Service


def result(code=0, stdout="", stderr=""):
    return ProcessResult((), code, stdout, stderr, 0.0)


def test_each_runtime_keeps_only_what_docker_itself_runs_on_the_host():
    catalog = Catalog()
    first = catalog.get("m00-first-container")
    assert host_images(first) == ["python"] and cluster_images(first) == []
    compose = catalog.get("m05-services")
    assert set(host_images(compose)) == {"python", "postgres", "redis"}
    workloads = catalog.get("m08-workloads")
    assert set(host_images(workloads)) == {"python", "kind"}
    assert set(cluster_images(workloads)) == {
        "calico_calico",
        "calico_node",
        "calico_third_party_cni_plugins",
        "postgres",
        "redis",
        "busybox",
    }
    # The load balancer lesson reaches its address from a container on this computer.
    assert "busybox" in host_images(catalog.get("m10-services"))
    delivery = catalog.get("m16-gitops")
    assert {"git", "registry"} <= set(host_images(delivery))
    assert not {"git", "registry", "python"} & set(cluster_images(delivery))
    native = catalog.get("m22-storage")
    assert host_images(native) == ["python"]
    assert {name for name in PINNED if name.startswith("csi_")} <= set(cluster_images(native))


def test_every_image_a_unit_declares_is_kept_somewhere():
    for unit in Catalog().units.values():
        assert set(unit.images) <= set(host_images(unit)) | set(cluster_images(unit)), unit.id


def test_an_archive_is_made_without_leaving_names_in_docker(tmp_path, monkeypatch):
    calls = []

    def run(args, **kwargs):
        calls.append(args[1:])
        if args[1:3] == ["image", "inspect"]:
            return result(1, stderr="No such image")
        if args[1:3] == ["image", "save"]:
            (tmp_path / "image-archives").joinpath(args[args.index("--output") + 1]).write_bytes(
                b"archive"
            )
        return result()

    monkeypatch.setattr(images, "run", run)
    store = ImageStore(tmp_path, {})
    messages = []
    path = store.ensure_archive("redis", threading.Event(), messages.append)
    assert path.read_bytes() == b"archive" and path.stat().st_mode & 0o777 == 0o600
    assert messages == ["Downloading the Redis image"]
    commands = [call[:2] if call[0] == "image" else call[:1] for call in calls]
    assert (
        commands
        == [["image", "inspect"], ["pull"], ["tag"], ["image", "save"]] + [["image", "rm"]] * 2
    )
    # Both the alias and the digest pulled only for the archive are removed again.
    assert [call[2] for call in calls[-2:]] == [alias("redis"), PINNED["redis"]]
    calls.clear()
    assert store.ensure_archive("redis", threading.Event(), messages.append) == path
    assert calls == []


def test_an_image_docker_already_holds_stays_after_archiving(tmp_path, monkeypatch):
    removed = []

    def run(args, **kwargs):
        if args[1:3] == ["image", "inspect"]:
            return result(stdout="arm64\n")
        if args[1:3] == ["image", "save"]:
            (tmp_path / "image-archives").joinpath(args[args.index("--output") + 1]).write_bytes(
                b"archive"
            )
        if args[1:3] == ["image", "rm"]:
            removed.append(args[3])
        return result()

    monkeypatch.setattr(images, "run", run)
    monkeypatch.setattr(images.host, "architecture", lambda: "arm64")
    ImageStore(tmp_path, {}).ensure_archive("postgres", threading.Event(), lambda message: None)
    assert removed == [alias("postgres")]


def test_downloads_are_kept_for_labs_the_current_module_and_prefetched_scopes(tmp_path):
    service = Service(tmp_path)
    assert cache.needed(service) == (set(), set())
    service.store.set_setting("last_unit", "m08-workloads")
    host, cluster = cache.needed(service)
    assert host == {"python", "kind"} and "postgres" in cluster and "traefik" not in cluster
    service.store.set_setting("kept-scopes", ["module:10", "module:99"])
    assert "traefik" in cache.needed(service)[1]
    # An incident is not part of a module's sequence, so it keeps nothing ready.
    service.store.set_setting("kept-scopes", [])
    service.store.set_setting("last_unit", "i05-readiness-port")
    assert cache.needed(service) == (set(), set())


def test_a_sweep_keeps_what_is_needed_and_never_raises(tmp_path, monkeypatch):
    service = Service(tmp_path)
    # A source checkout shares its tools between profiles and never sweeps them.
    assert service.shared_tools and cache.sweep(service) is None
    service.tools, service.shared_tools = tmp_path / "tools", False
    monkeypatch.setenv("DOCKER_HOST", "unix:///nonexistent/docker.sock")
    store = ImageStore(service.tools, {})
    store.directory.mkdir(parents=True)
    kept, stale = store.archive_path("postgres"), store.directory / "postgres-old-arm64.tar"
    kept.write_bytes(b"1")
    stale.write_bytes(b"22")
    python = images.digest_reference(PINNED["python"])
    old = "python@sha256:" + "ab" * 32
    service.store.set_setting("host-images", [python, old])
    service.store.set_setting("last_unit", "m08-workloads")
    removed = []

    def run(args, **kwargs):
        if args[1:3] == ["image", "ls"]:
            rows = [
                {"Repository": "python", "Tag": "<none>", "Digest": reference.partition("@")[2]}
                for reference in (python, old)
            ] + [{"Repository": "ubuntu", "Tag": "<none>", "Digest": "sha256:" + "cd" * 32}]
            return result(stdout="\n".join(cache.json.dumps(row) for row in rows))
        removed.append(args[3])
        return result()

    monkeypatch.setattr(cache, "run", run)
    outcome = cache.sweep(service)
    # The superseded pin goes; the current pin and the archive a module needs stay.
    assert removed == [old] and outcome["removed"] == [old, stale.name]
    assert kept.exists() and not stale.exists()
    assert service.store.setting("host-images") == [python]
    service.store.set_setting("keep-downloads", True)
    assert cache.sweep(service) is None
    service.store.set_setting("keep-downloads", False)
    monkeypatch.setattr(cache, "run", lambda args, **kwargs: result(1, stderr="daemon down"))
    assert cache.sweep(service) is None
