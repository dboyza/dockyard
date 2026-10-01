"""The CLI explains itself and prints readable summaries by default."""

import pytest

from dockyard import __version__
from dockyard.cli import parser, print_cache, print_doctor, print_lab


def test_version_and_lab_actions_are_documented(capsys):
    with pytest.raises(SystemExit):
        parser().parse_args(["--version"])
    assert capsys.readouterr().out.strip() == f"dockyard {__version__}"
    with pytest.raises(SystemExit):
        parser().parse_args(["lab", "--help"])
    help_text = capsys.readouterr().out
    for action in ("prepare", "shell", "check", "stop", "resume", "clean"):
        assert action in help_text
    assert "VMs" in help_text


def test_doctor_summary_names_each_dependency(capsys):
    print_doctor(
        {
            "wsl": False,
            "system": "Linux",
            "architecture": "x86_64",
            "host_memory_gib": 16.0,
            "memory_free_percent": 40,
            "free_disk_gib": 120.5,
            "docker_ready": False,
            "docker_version": None,
            "docker_error": "Docker is not running.",
            "docker_tools_error": None,
            "terminal": None,
            "native_vm_blocker": "KVM is unavailable.",
            "vm_budget_gib": 8,
            "tools": {"kind": None},
        }
    )
    out = capsys.readouterr().out
    assert "not available: Docker is not running." in out
    assert "blocked: KVM is unavailable." in out
    assert "copy lab commands" in out
    assert "not installed yet" in out


def test_lab_and_cache_summaries(capsys):
    print_lab("m01-processes", None)
    print_lab(
        "m01-processes",
        {"state": "ready", "workspace": "/tmp/work", "error": None},
    )
    print_cache(
        {
            "scope": "module:1",
            "units": [
                {"unit_id": "a", "status": "cached", "missing": [], "limitations": []},
                {"unit_id": "b", "status": "missing", "missing": ["kind"], "limitations": []},
            ],
            "private_cache_gib": 1.5,
            "soft_budget_gib": 40,
            "free_disk_gib": 100,
        }
    )
    out = capsys.readouterr().out
    assert "not prepared. Run: dockyard lab prepare m01-processes" in out
    assert "dockyard lab shell m01-processes" in out
    assert "1 of 2 activities" in out and "missing: kind" in out


def test_frontend_and_python_versions_match():
    import json
    from pathlib import Path

    package = json.loads((Path(__file__).parents[1] / "frontend/package.json").read_text())
    assert package["version"] == __version__


def test_clean_all_needs_confirmation_and_reports_nothing_to_clean(tmp_path, monkeypatch, capsys):
    import sys

    from dockyard import cli

    monkeypatch.setattr(
        sys, "argv", ["dockyard", "--data-dir", str(tmp_path), "lab", "clean", "--all"]
    )
    cli.main()
    assert capsys.readouterr().out.strip() == "No labs to clean."


def test_lab_status_without_a_unit_lists_labs(tmp_path, monkeypatch, capsys):
    import sys

    from dockyard import cli

    monkeypatch.delenv("DOCKYARD_UNIT", raising=False)
    monkeypatch.setattr(sys, "argv", ["dockyard", "--data-dir", str(tmp_path), "lab", "status"])
    cli.main()
    assert capsys.readouterr().out.startswith("No labs yet.")


def test_progress_import_previews_readably_then_merges(tmp_path, monkeypatch, capsys):
    import sys

    from dockyard import cli

    archive = tmp_path / "backup.zip"
    source, target = tmp_path / "source", tmp_path / "target"

    def run(*args: str) -> str:
        monkeypatch.setattr(sys, "argv", ["dockyard", "--data-dir", *args])
        cli.main()
        return capsys.readouterr().out

    run(str(source), "progress", "export", str(archive))
    preview = run(str(target), "progress", "import", str(archive))
    assert "Activities" in preview and "repeat this command with --yes" in preview
    assert not (target / "imports").exists()
    merged = run(str(target), "progress", "import", str(archive), "--yes")
    assert "Merged." in merged and "progress database was saved" in merged
    assert "already imported" in run(str(target), "progress", "import", str(archive), "--yes")
