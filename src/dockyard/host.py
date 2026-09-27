"""Host capabilities shared by paths, pinned tools, shells, and VM providers."""

from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path


def architecture(machine: str | None = None) -> str:
    value = (machine or platform.machine()).lower()
    if value in {"arm64", "aarch64"}:
        return "arm64"
    if value in {"amd64", "x86_64"}:
        return "amd64"
    raise ValueError(f"Unsupported processor architecture: {value}. Use ARM64 or x86-64.")


def platform_key() -> str:
    system = platform.system()
    arch = architecture()
    if system == "Darwin" and arch == "arm64":
        return "darwin-arm64"
    if system == "Linux":
        if is_wsl() and not any(
            value in platform.release().lower() for value in ("wsl2", "microsoft-standard")
        ):
            raise ValueError("WSL 1 cannot run these labs. Convert the distribution to WSL 2.")
        return "linux-" + arch
    raise ValueError("Use Apple Silicon macOS, Linux, or Windows through WSL 2.")


def is_wsl() -> bool:
    return platform.system() == "Linux" and "microsoft" in platform.release().lower()


def default_directory() -> Path:
    if configured := os.environ.get("DOCKYARD_DATA"):
        return Path(configured).expanduser()
    if platform.system() == "Darwin":
        return Path.home() / "Library/Application Support/Dockyard"
    data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    if not data.is_absolute():
        data = Path.home() / ".local/share"
    return data / "dockyard"


def temporary_root() -> Path:
    # Keep a single per-user capacity registry even when processes have different TMPDIRs.
    return Path("/private/tmp" if platform.system() == "Darwin" else "/tmp")


def vm_type() -> str:
    return "vz" if platform.system() == "Darwin" else "qemu"


def guest_architecture() -> str:
    return "aarch64" if architecture() == "arm64" else "x86_64"


def native_blocker() -> str | None:
    if platform.system() != "Linux":
        return None
    missing = [
        name
        for name in ("qemu-system-" + guest_architecture(), "qemu-img", "ssh")
        if not shutil.which(name)
    ]
    if missing:
        return "Native VM labs need these host tools: " + ", ".join(missing) + "."
    if not os.access("/dev/kvm", os.R_OK | os.W_OK):
        return (
            "Native VM labs need readable and writable /dev/kvm. Enable hardware "
            "virtualization and KVM access; WSL 2 additionally needs nested virtualization. "
            "Docker and kind labs remain available."
        )
    return None


def shell() -> str:
    candidates = ("zsh", "bash") if platform.system() == "Darwin" else ("bash", "zsh")
    for name in candidates:
        if executable := shutil.which(name):
            return executable
    raise ValueError("Install Bash or Zsh to use the real lesson shell.")


def wezterm() -> str | None:
    if is_wsl():
        if found := shutil.which("wezterm.exe"):
            return found
        installed = Path("/mnt/c/Program Files/WezTerm/wezterm.exe")
        if installed.is_file():
            return str(installed)
    return shutil.which("wezterm")


def docker_plugin_blocker(environment: dict[str, str]) -> str | None:
    from dockyard.process import run

    missing = []
    for plugin in ("buildx", "compose"):
        if not run(["docker", plugin, "version"], env=environment, timeout=5).ok:
            missing.append(plugin)
    if missing:
        return "Install Docker's " + " and ".join(missing) + " plugins before preparing labs."
    return None
