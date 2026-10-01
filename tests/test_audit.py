"""The structural audit passes the shipped curriculum and reports real breakage."""

import copy
import sys

import pytest

from dockyard import cli
from dockyard.audit import curriculum
from dockyard.catalog import Catalog
from dockyard.reference import library


@pytest.fixture(scope="module")
def catalog():
    return Catalog()


def test_shipped_curriculum_passes(catalog):
    report = curriculum(catalog)
    assert report["status"] == "pass", report["issues"]
    assert (report["course_units"], report["incidents"], report["exams"]) == (96, 12, 4)


def test_audit_reports_a_missing_mission_and_an_unknown_remediation(catalog):
    broken = copy.copy(catalog)
    broken.units = {k: v for k, v in catalog.units.items() if k != "m03-mission"}
    broken.exams = copy.deepcopy(catalog.exams)
    first = next(iter(broken.exams.values()))
    first.tasks[0].remediation = ["no-such-lesson"]
    issues = curriculum(broken)["issues"]
    assert any(issue.startswith("Module 3:") for issue in issues)
    assert any("unknown remediation unit" in issue for issue in issues)
    assert "A prerequisite names m03-mission, which does not exist." in issues


def test_reference_library_links_resolve(catalog):
    reference = library(catalog)
    primers = {item["id"] for item in reference["primers"]}
    assert all(item["content"].strip() for item in reference["primers"])
    for term in reference["glossary"]:
        assert term["primer"] in primers
        assert set(term["units"]) <= catalog.units.keys()


def test_catalog_and_audit_commands(tmp_path, monkeypatch, capsys):
    for arguments in (["catalog"], ["audit"]):
        monkeypatch.setattr(sys, "argv", ["dockyard", "--data-dir", str(tmp_path), *arguments])
        cli.main()
    out = capsys.readouterr().out
    assert "Module 24 · Operational handoff" in out
    assert "Curriculum: pass" in out
