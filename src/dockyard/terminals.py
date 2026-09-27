"""Known terminal launch adapters; arbitrary shell commands are never accepted by the API."""

from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from dockyard import host
from dockyard.process import run
from dockyard.workspace import atomic_write


@dataclass(frozen=True)
class Terminal:
    id: str
    label: str
    executable: str


# Each adapter's command boundary is explicit, rather than guessing what $TERMINAL accepts.
POSIX = (
    ("xdg-terminal-exec", "System default terminal"),
    ("wezterm", "WezTerm"),
    ("ghostty", "Ghostty"),
    ("kitty", "kitty"),
    ("alacritty", "Alacritty"),
    ("gnome-terminal", "GNOME Terminal"),
    ("kgx", "GNOME Console"),
    ("konsole", "Konsole"),
    ("xfce4-terminal", "Xfce Terminal"),
    ("tilix", "Tilix"),
    ("mate-terminal", "MATE Terminal"),
    ("foot", "foot"),
    ("xterm", "xterm"),
    ("x-terminal-emulator", "System terminal alternative"),
)


def available() -> list[Terminal]:
    found = []
    if host.is_wsl():
        for name, label, binary in (
            ("windows-terminal", "Windows Terminal", "wt.exe"),
            ("wezterm-windows", "WezTerm (Windows)", "wezterm.exe"),
            ("alacritty-windows", "Alacritty (Windows)", "alacritty.exe"),
        ):
            executable = shutil.which(binary)
            if name == "wezterm-windows" and not executable:
                candidate = Path("/mnt/c/Program Files/WezTerm/wezterm.exe")
                executable = str(candidate) if candidate.is_file() else None
            if executable:
                found.append(Terminal(name, label, executable))
    if platform.system() == "Darwin":
        for name, label, bundle in (
            ("terminal", "Terminal", "Terminal.app"),
            ("iterm", "iTerm2", "iTerm.app"),
            ("ghostty-macos", "Ghostty", "Ghostty.app"),
        ):
            for root in (
                Path("/System/Applications/Utilities"),
                Path("/Applications"),
                Path.home() / "Applications",
            ):
                candidate = root / bundle
                if candidate.is_dir():
                    found.append(Terminal(name, label, str(candidate)))
                    break
    desktop = platform.system() == "Darwin" or bool(
        os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    )
    if desktop:
        for name, label in POSIX:
            if name == "ghostty" and platform.system() == "Darwin":
                continue
            executable = shutil.which(name)
            if not executable and platform.system() == "Darwin":
                bundles = {"wezterm": "WezTerm", "kitty": "kitty", "alacritty": "Alacritty"}
                if name in bundles:
                    candidate = (
                        Path("/Applications") / (bundles[name] + ".app/Contents/MacOS") / name
                    )
                    executable = str(candidate) if candidate.is_file() else None
            if executable:
                found.append(Terminal(name, label, executable))
    return found


def choose(options: list[Terminal], preference: str = "auto") -> Terminal | None:
    if preference != "auto":
        selected = next((item for item in options if item.id == preference), None)
        if selected is None:
            raise ValueError(
                "That terminal is unavailable. Choose another or copy the lab command."
            )
        return selected
    current = {
        "Apple_Terminal": "terminal",
        "iTerm.app": "iterm",
        "WezTerm": "wezterm",
        "ghostty": "ghostty-macos" if platform.system() == "Darwin" else "ghostty",
    }.get(os.environ.get("TERM_PROGRAM", ""))
    if host.is_wsl() and os.environ.get("WT_SESSION"):
        current = "windows-terminal"
    return next((item for item in options if item.id == current), options[0] if options else None)


def launch_argv(
    terminal: Terminal, command: list[str], workspace: str, launcher: Path
) -> list[str]:
    name, executable = terminal.id, terminal.executable
    if name in {"windows-terminal", "wezterm-windows", "alacritty-windows"}:
        distribution = os.environ.get("WSL_DISTRO_NAME")
        if not distribution:
            raise ValueError("WSL_DISTRO_NAME is unavailable. Run the copied command inside WSL.")
        command = ["wsl.exe", "--distribution", distribution, "--cd", workspace, "--exec", *command]
        workspace = "C:\\"
    if name == "terminal":
        return ["/usr/bin/open", "-a", executable, str(launcher)]
    if name == "iterm":
        script = """on run argv
    tell application "iTerm2"
        activate
        create window with default profile command (item 1 of argv)
    end tell
end run"""
        return ["/usr/bin/osascript", "-e", script, shlex.join(command)]
    if name == "ghostty-macos":
        script = """on run argv
    tell application "Ghostty"
        activate
        set cfg to new surface configuration
        set initial working directory of cfg to item 1 of argv
        set command of cfg to item 2 of argv
        new window with configuration cfg
    end tell
end run"""
        return ["/usr/bin/osascript", "-e", script, workspace, shlex.join(command)]
    if name == "windows-terminal":
        # Windows Terminal also parses command separators; preserve unusual paths via copy.
        if any(";" in arg for arg in command):
            raise ValueError("Use the copied lab command for paths containing semicolons.")
        return [
            executable,
            "-w",
            "new",
            "new-tab",
            "--startingDirectory",
            workspace,
            "--",
            *command,
        ]
    if name.startswith("wezterm"):
        domain = ["--domain", "local"] if name.endswith("-windows") else []
        return [
            executable,
            "start",
            "--always-new-process",
            *domain,
            "--cwd",
            workspace,
            "--",
            *command,
        ]
    if name.startswith("alacritty"):
        return [executable, "--working-directory", workspace, "-e", *command]
    if name == "kitty":
        return [executable, "--directory", workspace, *command]
    if name == "ghostty":
        return [executable, "--working-directory=" + workspace, "-e", *command]
    if name == "gnome-terminal":
        return [executable, "--working-directory=" + workspace, "--", *command]
    if name == "kgx":
        return [executable, "--working-directory=" + workspace, "--", *command]
    if name == "konsole":
        return [executable, "--workdir", workspace, "-e", *command]
    if name == "mate-terminal":
        return [executable, "--disable-factory", "--working-directory=" + workspace, "-x", *command]
    if name in {"xfce4-terminal", "tilix"}:
        return [
            executable,
            "--working-directory=" + workspace,
            "-e" if name == "tilix" else "-x",
            *command,
        ]
    if name == "foot":
        return [executable, "--working-directory=" + workspace, *command]
    if name in {"xterm", "x-terminal-emulator"}:
        return [executable, "-e", *command]
    if name == "xdg-terminal-exec":
        return [executable, *command]
    raise ValueError("Unknown terminal adapter.")


def launch(
    terminal: Terminal,
    command: list[str],
    workspace: str,
    environment: dict[str, str],
    directory: Path,
) -> None:
    if directory.is_symlink():
        raise ValueError("The terminal directory is a symbolic link; preserved.")
    directory.mkdir(parents=True, exist_ok=True)
    launcher = directory / "launch.command"
    if launcher.is_symlink():
        raise ValueError("The terminal launcher is a symbolic link; preserved.")
    atomic_write(launcher, ("#!/bin/sh\nexec " + shlex.join(command) + "\n").encode(), mode=0o700)
    args = launch_argv(terminal, command, workspace, launcher)
    if terminal.id in {"iterm", "ghostty-macos"}:
        result = run(args, cwd=Path(workspace), env=environment, timeout=30, output_limit=2000)
        if not result.ok:
            raise ValueError(
                "The terminal could not open. Check macOS Automation permission or copy "
                "the lab command instead. " + result.stderr.strip()
            )
        return
    if terminal.id.startswith("wezterm"):
        domain = ["--domain-name", "local"] if terminal.id.endswith("-windows") else []
        split = args.index("--cwd")
        result = run(
            [terminal.executable, "cli", "--no-auto-start", "spawn", *domain, *args[split:]],
            env=environment,
            timeout=8,
        )
        if result.ok:
            return
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            args,
            cwd=workspace,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=errors,
            start_new_session=True,
        )
        try:
            code = process.wait(timeout=0.4)
        except subprocess.TimeoutExpired:
            threading.Thread(target=process.wait, daemon=True).start()
            return
        if code:
            errors.seek(0)
            detail = errors.read(2000).decode(errors="replace").strip()
            raise ValueError("The terminal could not open. Copy the lab command instead. " + detail)
