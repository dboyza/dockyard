"""Pinned images live where they are used: Docker for host steps, private archives for clusters."""

import threading

import pytest

from dockyard import cache, images
from dockyard.catalog import Catalog
from dockyard.images import PINNED, ImageStore, alias, cluster_images, host_images
from dockyard.process import ProcessResult
from dockyard.service import Service
from dockyard.toolchain import platform_manifest


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
    # kind's own network plugin needs no extra images.
    assert set(cluster_images(workloads)) == {"postgres", "redis", "busybox"}
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


@pytest.fixture(autouse=True)
def private_registry(tmp_path, monkeypatch):
    """Profiles publish their Docker needs here instead of the real per-user registry."""
    from dockyard import capacity

    root = tmp_path / "registry"
    root.mkdir(mode=0o700)
    monkeypatch.setattr(capacity, "registry_directory", lambda: root)
    return root


def docker_listing(references):
    rows = [
        {
            "Repository": reference.partition("@")[0],
            "Tag": "<none>",
            "Digest": reference.partition("@")[2],
        }
        for reference in references
    ]
    return result(stdout="\n".join(cache.json.dumps(row) for row in rows))


def test_a_sweep_never_removes_what_another_profile_needs_or_did_not_pull(
    tmp_path, monkeypatch, private_registry
):
    monkeypatch.setenv("DOCKER_HOST", "unix:///nonexistent/docker.sock")
    learner, test = Service(tmp_path / "learner"), Service(tmp_path / "test")
    for service in (learner, test):
        service.tools, service.shared_tools = service.directory / "tools", False
    python = images.digest_reference(PINNED["python"])
    postgres = images.digest_reference(PINNED["postgres"])
    removed = []

    def run(args, **kwargs):
        if args[1:3] == ["image", "ls"]:
            return docker_listing([python, postgres])
        removed.append(args[3])
        return result()

    monkeypatch.setattr(cache, "run", run)
    # The learner is studying Compose and pulled both images for it.
    learner.store.set_setting("last_unit", "m05-services")
    cache.record_pulls(learner, ["python", "postgres"])
    # A record another profile is midway through writing is skipped, not fatal.
    (private_registry / "images-partial.json").write_text("{")
    assert cache.sweep(learner)["removed"] == []
    # A second profile that found them already present removes nothing.
    assert cache.sweep(test)["removed"] == [] and removed == []
    # Even an image the second profile pulled stays while the learner needs it.
    cache.record_pulls(test, ["python"])
    cache.sweep(test)
    assert removed == []
    # Once the learner moves on, the learner's own sweep removes what it pulled.
    learner.store.set_setting("last_unit", "m00-first-container")
    cache.sweep(learner)
    assert removed == [postgres]


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


def test_every_pinned_image_has_a_name_and_a_recorded_download_size():
    sizes = cache.json.loads((cache.CONTENT / "download-sizes.json").read_text())
    for name, reference in PINNED.items():
        assert images.label(name)
        assert set(sizes["images"][reference]) == {"arm64", "amd64"}, name
    for platform in ("darwin-arm64", "linux-arm64", "linux-amd64"):
        for name, entry in platform_manifest(platform).items():
            assert sizes["files"][entry["sha256"]] > 0, f"{platform}/{name}"


def test_an_estimate_counts_only_what_is_still_missing(tmp_path, monkeypatch):
    service = Service(tmp_path)
    service.tools = tmp_path / "tools"
    monkeypatch.setenv("DOCKER_HOST", "unix:///nonexistent/docker.sock")
    monkeypatch.setattr(images.host, "architecture", lambda: "arm64")
    monkeypatch.setattr(cache.host, "architecture", lambda: "arm64")
    held = {"python", "kind", "postgres"}
    monkeypatch.setattr(ImageStore, "on_host", lambda self, name: name in held)
    monkeypatch.setattr(cache, "run", lambda args, **kwargs: result())
    unit = service.catalog.get("m08-workloads")
    first = cache.estimate(service, unit)
    # Docker already holds PostgreSQL, so its archive needs no download.
    assert "the PostgreSQL image" not in first["items"]
    assert first["items"][0] == "kubectl" and "the Redis image" in first["items"]
    store = ImageStore(service.tools, {})
    store.directory.mkdir(parents=True)
    for name in cluster_images(unit):
        store.archive_path(name).write_bytes(b"archive")
    for name in ("kind", "kubectl"):
        path = service.tools / cache.MANIFEST[name]["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"tool")
    assert cache.estimate(service, unit) == {"bytes": 0, "items": [], "docker_ready": True}
    # An image Docker itself must hold is still a download, even with an archive of it.
    balanced = cache.estimate(service, service.catalog.get("m10-services"))
    assert "the BusyBox image" in balanced["items"]
    # Without Docker, every image this lesson uses there is still to download.
    monkeypatch.setattr(
        cache,
        "docker_environment",
        lambda service: (_ for _ in ()).throw(cache.LabError("Docker is unavailable.")),
    )
    offline = cache.estimate(service, unit)
    assert offline["items"] == ["the Kubernetes node image", "the Python image"]
    assert offline["docker_ready"] is False
