"""Cache cleanup selects only references Dockyard created."""

import json

from dockyard import cache
from dockyard.process import ProcessResult
from dockyard.service import COMPATIBILITY, Service


def test_only_dockyard_aliases_and_pinned_digests_are_selected(tmp_path, monkeypatch):
    python = COMPATIBILITY["images"]["python"]
    python_digest = python.partition("@")[2]
    kind_name, _, kind_digest = COMPATIBILITY["images"]["kind"].partition("@")
    old = "sha256:" + "ab" * 32
    rows = [
        {"Repository": "dockyard-cache/python", "Tag": python_digest[7:23], "Digest": "<none>"},
        {"Repository": "python", "Tag": "<none>", "Digest": python_digest},
        {"Repository": "python", "Tag": "3.14", "Digest": python_digest},
        {"Repository": kind_name.rpartition(":")[0], "Tag": "<none>", "Digest": kind_digest},
        {"Repository": "dockyard-cache/metrics-server", "Tag": "ab" * 8, "Digest": "<none>"},
        {"Repository": "registry.k8s.io/metrics-server", "Tag": "<none>", "Digest": old},
        {"Repository": "ubuntu", "Tag": "<none>", "Digest": "sha256:" + "cd" * 32},
        {"Repository": "my-app", "Tag": "latest", "Digest": "<none>"},
    ]
    listed = ProcessResult((), 0, "\n".join(json.dumps(row) for row in rows), "", 0.0)
    monkeypatch.setattr(cache, "run", lambda *args, **kwargs: listed)
    monkeypatch.setenv("DOCKER_HOST", "unix:///nonexistent/docker.sock")
    selected = cache.pulled_references(Service(tmp_path))
    assert selected == [
        "dockyard-cache/metrics-server:" + "ab" * 8,
        "dockyard-cache/python:" + python_digest[7:23],
        f"{kind_name.rpartition(':')[0]}@{kind_digest}",
        f"python@{python_digest}",
        f"registry.k8s.io/metrics-server@{old}",
    ]
