"""Terminal adapters preserve command boundaries and portable existing-shell access."""

import json
import os
import shlex
import subprocess
import sys

import pytest

from dockyard import terminals
from dockyard.process import ProcessResult


@pytest.mark.parametrize("name", [entry[0] for entry in terminals.POSIX])
def test_posix_adapters_preserve_literal_arguments(name, tmp_path):
    command = [
        "/path with spaces/python",
        "-m",
        "dockyard",
        "--data-dir",
        '/profile with $dollar and "quotes"',
        "lab",
        "shell",
        "m01-processes",
    ]
    args = terminals.launch_argv(
        terminals.Terminal(name, name, "/bin/terminal"),
        command,
        str(tmp_path),
        tmp_path / "launch.command",
    )
    assert args[-len(command) :] == command
    assert "sh" not in args and "-c" not in args


def test_windows_terminal_targets_exact_distribution_and_rejects_separators(monkeypatch, tmp_path):
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu Test")
    terminal = terminals.Terminal("windows-terminal", "Windows Terminal", "/mnt/c/wt.exe")
    args = terminals.launch_argv(
        terminal,
        ["/home/test/python", "-m", "dockyard"],
        "/home/test/lab with spaces",
        tmp_path / "entry",
    )
    assert args[args.index("--distribution") + 1] == "Ubuntu Test"
    assert args[args.index("--cd") + 1] == "/home/test/lab with spaces"
    assert args[-3:] == ["/home/test/python", "-m", "dockyard"]
    with pytest.raises(ValueError, match="copied lab command"):
        terminals.launch_argv(terminal, ["/tmp/unsafe;argument"], "/tmp", tmp_path / "entry")


@pytest.mark.parametrize("name", ["iterm", "ghostty-macos"])
def test_applescript_receives_data_as_arguments_not_source(name, tmp_path):
    dangerous = '/tmp/quoted " path $(touch unwanted)'
    command = ["/bin/python", dangerous]
    args = terminals.launch_argv(
        terminals.Terminal(name, name, "/Applications/app"), command, dangerous, tmp_path / "entry"
    )
    assert dangerous not in args[2]
    assert shlex.split(args[-1]) == command
    assert "write text" not in args[2]  # A new session, never input into an existing shell.


def test_automatic_selection_and_missing_preference(monkeypatch):
    options = [
        terminals.Terminal("terminal", "Terminal", "/app"),
        terminals.Terminal("wezterm", "WezTerm", "/bin/wezterm"),
    ]
    monkeypatch.setenv("TERM_PROGRAM", "WezTerm")
    assert terminals.choose(options).id == "wezterm"
    assert terminals.choose(options, "terminal").id == "terminal"
    assert terminals.choose([]) is None
    with pytest.raises(ValueError, match="unavailable"):
        terminals.choose(options, "/arbitrary/program")


def test_headless_discovery_does_not_offer_unusable_linux_gui(monkeypatch):
    monkeypatch.setattr(terminals.platform, "system", lambda: "Linux")
    monkeypatch.setattr(terminals.host, "is_wsl", lambda: False)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(terminals.shutil, "which", lambda name: "/usr/bin/" + name)
    assert terminals.available() == []


def test_private_launcher_executes_exact_command_and_rejects_symlinks(tmp_path, monkeypatch):
    # The terminal shim executes its -e command, proving actual argv rather than only string shape.
    executable = tmp_path / "terminal"
    executable.write_text('#!/bin/sh\nshift\nexec "$@"\n')
    executable.chmod(0o700)
    output = tmp_path / "received.json"
    literal = 'spaces "quotes"; $literal $(not-executed)'
    command = [
        sys.executable,
        "-c",
        "import json,sys; from pathlib import Path; "
        "Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]))",
        str(output),
        literal,
    ]
    terminal = terminals.Terminal("xterm", "xterm", str(executable))
    terminals.launch(terminal, command, str(tmp_path), dict(os.environ), tmp_path / "shell")
    assert json.loads(output.read_text()) == [literal]
    entry = tmp_path / "shell/launch.command"
    assert entry.stat().st_mode & 0o777 == 0o700
    output.unlink()
    subprocess.run([str(entry)], check=True)
    assert json.loads(output.read_text()) == [literal]
    entry.unlink()
    entry.symlink_to(output)
    with pytest.raises(ValueError, match="symbolic link"):
        terminals.launch(terminal, command, str(tmp_path), dict(os.environ), tmp_path / "shell")
    assert json.loads(output.read_text()) == [literal]


def test_terminal_failure_is_reported_with_copy_recovery(tmp_path):
    terminal = terminals.Terminal("xterm", "xterm", "/usr/bin/false")
    with pytest.raises(ValueError, match="Copy the lab command"):
        terminals.launch(
            terminal, ["/bin/true"], str(tmp_path), dict(os.environ), tmp_path / "shell"
        )


def test_automation_denial_is_reported_before_saving_success(tmp_path, monkeypatch):
    monkeypatch.setattr(
        terminals, "run", lambda *args, **kwargs: ProcessResult((), 1, "", "Not authorized", 1)
    )
    with pytest.raises(ValueError, match="Automation permission"):
        terminals.launch(
            terminals.Terminal("iterm", "iTerm2", "/Applications/iTerm.app"),
            ["/bin/true"],
            str(tmp_path),
            dict(os.environ),
            tmp_path / "shell",
        )
