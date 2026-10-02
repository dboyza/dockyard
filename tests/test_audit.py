"""The structural audit passes the shipped curriculum and reports real breakage."""

import copy
import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

from dockyard import cli
from dockyard.audit import curriculum
from dockyard.catalog import CONTENT, Catalog, figure_references
from dockyard.reference import library

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def catalog():
    return Catalog()


def test_shipped_curriculum_passes(catalog):
    report = curriculum(catalog)
    assert report["status"] == "pass", report["issues"]
    assert (report["course_units"], report["incidents"], report["exams"]) == (100, 12, 4)


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


def test_figure_blocks_name_exactly_one_figure():
    text = "Intro.\n\n```figure\nport-publishing\n```\n\n```sh\ndocker ps\n```\n"
    assert figure_references(text) == ["port-publishing"]
    for broken in ("```figure\n```", "```figure\none\ntwo\n```", "```figure one\n```"):
        with pytest.raises(ValueError, match="exactly one figure"):
            figure_references(broken)


def test_catalog_rejects_a_lesson_that_embeds_an_unknown_figure(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(CONTENT, content)
    concept = content / "units/m00-first-container/concept.md"
    concept.write_text(concept.read_text() + "\n```figure\nno-such-figure\n```\n")
    with pytest.raises(ValueError, match="unknown figure: no-such-figure"):
        Catalog(content)


def test_audit_requires_a_figure_in_every_lesson(catalog):
    broken = copy.copy(catalog)
    lesson = catalog.units["m00-first-container"]
    plain = lesson.model_copy(update={"concept": "## Words only\n\nNo picture here.\n"})
    broken.units = {**catalog.units, lesson.id: plain}
    assert (
        "m00-first-container: a lesson must explain its central idea with a figure."
        in (curriculum(broken)["issues"])
    )


def test_reference_library_rejects_a_primer_that_embeds_an_unknown_figure(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(CONTENT, content)
    primer = content / "reference/primers/http.md"
    primer.write_text(primer.read_text() + "\n```figure\nno-such-figure\n```\n")
    with pytest.raises(ValueError, match="http primer embeds an unknown figure: no-such-figure"):
        library(Catalog(content))


def test_audit_requires_a_figure_in_every_primer(tmp_path):
    content = tmp_path / "content"
    shutil.copytree(CONTENT, content)
    (content / "reference/primers/dns.md").write_text("# Names and DNS\n\nWords only.\n")
    assert (
        "dns primer: a primer must explain its central idea with a figure."
        in (curriculum(Catalog(content))["issues"])
    )


def test_every_figure_is_used_by_some_lesson_or_primer(catalog):
    texts = [
        text
        for unit in catalog.units.values()
        for text in (unit.concept, unit.brief, unit.debrief, *unit.hints)
    ]
    texts += [primer["content"] for primer in library(catalog)["primers"]]
    used = {figure for text in texts for figure in figure_references(text)}
    assert set(catalog.figures) == used


def test_generated_browser_contracts_are_current():
    spec = importlib.util.spec_from_file_location(
        "generate_types", ROOT / "scripts/generate_types.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.DESTINATION.read_text() == module.contracts(), (
        "Run .venv/bin/python scripts/generate_types.py"
    )
