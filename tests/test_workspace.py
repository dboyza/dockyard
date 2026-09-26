import pytest

from dockyard.workspace import WorkspaceError, reset, snapshot, write_files


def test_reset_preserves_the_complete_previous_workspace(tmp_path):
    work = tmp_path / "lab"
    write_files(work, {"main.py": "learner draft"})
    (work / ".git").mkdir()
    (work / ".git/config").write_text("learner git data")
    backup = reset(work, {"main.py": "starter"}, tmp_path / "backups")
    assert (backup / "main.py").read_text() == "learner draft"
    assert (backup / ".git/config").read_text() == "learner git data"
    assert (work / "main.py").read_text() == "starter"


def test_a_bad_manifest_does_not_partially_overwrite_files(tmp_path):
    write_files(tmp_path, {"first.txt": "keep"})
    with pytest.raises(WorkspaceError):
        write_files(tmp_path, {"first.txt": "replace", "../escape.txt": "bad"}, overwrite=True)
    assert (tmp_path / "first.txt").read_text() == "keep"


def test_symlinks_cannot_leak_external_files_into_snapshots(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("private")
    work = tmp_path / "lab"
    work.mkdir()
    (work / "linked.txt").symlink_to(secret)
    with pytest.raises(WorkspaceError):
        snapshot(work)


def test_snapshot_digest_changes_for_paths_and_contents(tmp_path):
    write_files(tmp_path, {"a": "draft"})
    before, _ = snapshot(tmp_path)
    (tmp_path / "a").rename(tmp_path / "b")
    renamed, files = snapshot(tmp_path)
    assert before != renamed
    assert files == {"b": b"draft"}
    (tmp_path / "b").write_text("edited")
    assert snapshot(tmp_path)[0] != renamed
