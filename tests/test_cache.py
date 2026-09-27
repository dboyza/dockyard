import pytest

from dockyard.cache import dependencies, select
from dockyard.catalog import Catalog
from dockyard.service import Service


def test_prefetch_scopes_cover_the_course_and_reject_ambiguous_input(tmp_path):
    service = Service(tmp_path)
    assert len(select(service, "all")) == 112
    assert {unit.module for unit in select(service, "module:2")} == {2}
    assert {unit.module for unit in select(service, "track:2")} == set(range(7, 13))
    assert [unit.id for unit in select(service, "unit:exam-cka-a")] == ["exam-cka-a"]
    for invalid in ["module:25", "track:5", "module:-1", "../tools", "unit:no-unit"]:
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
    assert versions == {"ubuntu24-kubernetes1.34.12", "ubuntu24-kubernetes1.35.8"}
    assert any("control-plane" in message for message in admin["limitations"])
    application = dependencies(catalog.get("exam-ckad-a"))
    assert {"kind", "calico_cni", "python", "postgres", "redis"} <= set(application["images"])
    assert any("Python package index" in message for message in application["limitations"])
    assert dependencies(catalog.get("m01-processes"))["limitations"] == []
