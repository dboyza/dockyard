"""Embedded lab shells: each is a real PTY on this computer, streamed to the signed-in browser."""

from __future__ import annotations

import fcntl
import os
import signal
import struct
import subprocess
import sys
import termios
import threading
import uuid
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any

from dockyard.store import timestamp

SCROLLBACK = 512 * 1024
PER_UNIT = 6
TOTAL = 24
# Runs as the new session leader so the shell gets a controlling terminal and job control.
ACQUIRE = (
    "import fcntl, os, sys, termios\n"
    "fcntl.ioctl(0, termios.TIOCSCTTY, 0)\n"
    "os.execvpe(sys.argv[1], sys.argv[1:], os.environ)\n"
)
# Variables that describe the backend's own terminal rather than this one.
FOREIGN = (
    "TERM_PROGRAM_VERSION", "TERM_SESSION_ID", "TMUX", "TMUX_PANE", "STY", "VTE_VERSION",
    "WT_SESSION", "WT_PROFILE_ID", "COLUMNS", "LINES",
)  # fmt: skip
FOREIGN_PREFIXES = ("ITERM_", "LC_TERMINAL", "KITTY_", "GHOSTTY_", "WEZTERM_", "ALACRITTY_")

Listener = Callable[[bytes | None], None]


class ConsoleError(ValueError):
    pass


@dataclass
class Console:
    id: str
    unit_id: str
    lab_id: str
    number: int
    process: subprocess.Popen[bytes]
    fd: int
    created_at: str
    buffer: bytearray = field(default_factory=bytearray)
    listeners: set[Listener] = field(default_factory=set)
    exit_code: int | None = None
    ended_by: str | None = None
    ended: bool = False

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "lab_id": self.lab_id,
            "number": self.number,
            "created_at": self.created_at,
            "alive": not self.ended,
            "exit_code": self.exit_code,
            "ended_by": self.ended_by,
        }


def terminal_environment(base: dict[str, str]) -> dict[str, str]:
    env = {
        key: value
        for key, value in base.items()
        if key not in FOREIGN and not key.startswith(FOREIGN_PREFIXES)
    }
    env.update(
        TERM="xterm-256color",
        COLORTERM="truecolor",
        TERM_PROGRAM="Dockyard",
        DOCKYARD_TERMINAL="embedded",
    )
    if not any(env.get(name) for name in ("LC_ALL", "LC_CTYPE", "LANG")):
        env["LC_CTYPE"] = "UTF-8" if sys.platform == "darwin" else "C.UTF-8"
    return env


def trim(buffer: bytearray) -> None:
    """Drop the oldest output, cutting at a line break so replay starts cleanly."""
    excess = len(buffer) - SCROLLBACK
    if excess <= 0:
        return
    newline = buffer.find(b"\n", excess)
    del buffer[: newline + 1 if 0 <= newline < excess + 4096 else excess]


class Consoles:
    def __init__(self) -> None:
        self._items: dict[str, Console] = {}
        self._lock = threading.Lock()

    def public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [item.public() for item in self._items.values()]

    def open(
        self,
        unit_id: str,
        lab_id: str,
        command: list[str],
        workspace: str,
        environment: dict[str, str],
        size: tuple[int, int],
    ) -> dict[str, Any]:
        with self._lock:
            mine = [item for item in self._items.values() if item.unit_id == unit_id]
            if sum(not item.ended for item in mine) >= PER_UNIT:
                raise ConsoleError(f"This lab already has {PER_UNIT} shells. Close one first.")
            if sum(not item.ended for item in self._items.values()) >= TOTAL:
                raise ConsoleError("Too many shells are open. Close some in other labs first.")
            ended = [item.id for item in self._items.values() if item.ended]
            for old in ended[: max(0, len(ended) - TOTAL)]:
                self._items.pop(old)
            taken = {item.number for item in mine}
            number = next(n for n in range(1, len(taken) + 2) if n not in taken)
            master, slave = os.openpty()
            try:
                resize(master, *size)
                process = subprocess.Popen(
                    [sys.executable, "-c", ACQUIRE, *command],
                    cwd=workspace,
                    env=terminal_environment(environment),
                    stdin=slave,
                    stdout=slave,
                    stderr=slave,
                    start_new_session=True,
                )
            except BaseException:
                os.close(master)
                raise
            finally:
                os.close(slave)
            console = Console(
                uuid.uuid4().hex, unit_id, lab_id, number, process, master, timestamp()
            )
            self._items[console.id] = console
        threading.Thread(target=self._pump, args=(console,), daemon=True).start()
        return console.public()

    def _pump(self, console: Console) -> None:
        while True:
            try:
                data = os.read(console.fd, 65536)
            except OSError:
                data = b""
            if not data:
                break
            with self._lock:
                console.buffer += data
                trim(console.buffer)
                listeners = list(console.listeners)
            for listener in listeners:
                listener(data)
        code = console.process.wait()
        os.close(console.fd)
        with self._lock:
            console.exit_code = code
            console.ended = True
            listeners = list(console.listeners)
            console.listeners.clear()
        for listener in listeners:
            listener(None)

    def attach(self, console_id: str, listener: Listener) -> tuple[bytes, bool]:
        """Return the scrollback and whether later output will stream to the listener."""
        with self._lock:
            console = self._get(console_id)
            if not console.ended:
                console.listeners.add(listener)
            return bytes(console.buffer), not console.ended

    def detach(self, console_id: str, listener: Listener) -> None:
        with self._lock:
            console = self._items.get(console_id)
            if console:
                console.listeners.discard(listener)

    def write(self, console_id: str, data: bytes) -> None:
        with self._lock:
            console = self._get(console_id)
            if console.ended:
                return
        view = memoryview(data)
        try:
            while view:
                view = view[os.write(console.fd, view) :]
        except OSError:
            return

    def resize(self, console_id: str, cols: int, rows: int) -> None:
        with self._lock:
            console = self._get(console_id)
            if not console.ended:
                resize(console.fd, cols, rows)

    def end(self, console_id: str, reason: str | None = None) -> None:
        with self._lock:
            console = self._get(console_id)
            if console.ended:
                return
            console.ended_by = reason
        hang_up(console.process)

    def remove(self, console_id: str) -> None:
        self.end(console_id)
        with self._lock:
            self._items.pop(console_id, None)

    def end_lab(self, lab_id: str, reason: str) -> None:
        with self._lock:
            owned = [item.id for item in self._items.values() if item.lab_id == lab_id]
        for console_id in owned:
            self.end(console_id, reason)

    def shutdown(self) -> None:
        with self._lock:
            owned = list(self._items)
        for console_id in owned:
            self.end(console_id, "Dockyard stopped.")

    def _get(self, console_id: str) -> Console:
        console = self._items.get(console_id)
        if console is None:
            raise ConsoleError("That shell is no longer available. Open a new one.")
        return console


def resize(fd: int, cols: int, rows: int) -> None:
    cols, rows = max(2, min(cols, 1000)), max(1, min(rows, 500))
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))


def hang_up(process: subprocess.Popen[bytes]) -> None:
    """Hang up the shell's session the way closing a terminal window does."""
    try:
        os.killpg(process.pid, signal.SIGHUP)
    except ProcessLookupError:
        return

    def escalate() -> None:
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)

    threading.Thread(target=escalate, daemon=True).start()
