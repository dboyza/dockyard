import pytest

from dockyard.cache import dependencies, select
from dockyard.catalog import Catalog
from dockyard.service import Service
from dockyard.versions import KUBERNETES, KUBERNETES_PREVIOUS


def test_prefetch_scopes_cover_the_course_and_reject_ambiguous_input(tmp_path):
    service = Service(tmp_path)
    assert len(select(service, "all")) == 147
    assert {unit.module for unit in select(service, "track:0")} == {0}
    assert {unit.module for unit in select(service, "module:2")} == {2}
    assert {unit.module for unit in select(service, "track:2")} == set(range(7, 13))
    assert {unit.module for unit in select(service, "track:5")} == set(range(25, 31))
    assert [unit.id for unit in select(service, "unit:exam-cka-a")] == ["exam-cka-a"]
    for invalid in ["module:31", "track:6", "module:-1", "../tools", "unit:no-unit"]:
        with pytest.raises(ValueError):
            select(service, invalid)


def test_advanced_prefetch_includes_adjacent_packages_and_reports_network_gaps():
    catalog = Catalog()
    admin = dependencies(catalog.get("exam-cka-b"))
    assert {"limactl", "lima-guestagent", "ubuntu-node", "kubectl", "helm", "calico"} <= set(
        admin["tools"]
    )
    versions = {
        entry["version"] for name, entry in admin["packages"].items() if name.startswith("kubeadm")
    }
    assert versions == {
        f"ubuntu24-kubernetes{KUBERNETES_PREVIOUS}",
        f"ubuntu24-kubernetes{KUBERNETES}",
    }
    assert any("control-plane" in message for message in admin["limitations"])
    application = dependencies(catalog.get("exam-ckad-a"))
    # Docker holds what the learner builds from; cluster-only images stay private archives.
    assert set(application["host_images"]) == {"kind", "python"}
    assert {"postgres", "redis", "busybox"} <= set(application["cluster_images"])
    assert not any(name.startswith("calico_") for name in application["cluster_images"])
    assert any("Python package index" in message for message in application["limitations"])
    assert dependencies(catalog.get("m01-processes"))["limitations"] == []
