"""Bounded, cancellable subprocess execution without shell interpolation."""

from __future__ import annotations

import os
import selectors
import signal
import subprocess
import threading
import time
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False
    canceled: bool = False
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not (self.timed_out or self.canceled)


def run(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    timeout: float = 30,
    cancel: threading.Event | None = None,
    input_text: str | None = None,
    output_limit: int = 1_000_000,
) -> ProcessResult:
    """Drain both pipes while enforcing a deadline, output bound, and group cancellation."""
    if not args or timeout <= 0 or output_limit < 1:
        raise ValueError("A command, positive timeout, and positive output limit are required.")
    started = time.monotonic()
    process = subprocess.Popen(
        list(args),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        bufsize=0,
    )
    assert process.stdout is not None and process.stderr is not None
    buffers: dict[str, bytearray] = {"stdout": bytearray(), "stderr": bytearray()}
    pending = memoryview((input_text or "").encode())
    timed_out = canceled = truncated = terminated = False
    terminate_time = 0.0
    with selectors.DefaultSelector() as selector:
        for stream, name in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        if process.stdin is not None:
            if pending:
                os.set_blocking(process.stdin.fileno(), False)
                selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
            else:
                process.stdin.close()
        try:
            while selector.get_map() or process.poll() is None:
                now = time.monotonic()
                if not terminated:
                    canceled = cancel is not None and cancel.is_set()
                    timed_out = now - started >= timeout
                    if canceled or timed_out:
                        terminated = True
                        terminate_time = now
                        _signal_group(process.pid, signal.SIGTERM)
                elif now - terminate_time >= 0.5:
                    _signal_group(process.pid, signal.SIGKILL)
                for key, _ in selector.select(0.05):
                    descriptor = key.fd
                    if key.data == "stdin":
                        try:
                            sent = os.write(descriptor, pending[:65536])
                            pending = pending[sent:]
                        except BrokenPipeError:
                            pending = memoryview(b"")
                        if not pending:
                            selector.unregister(key.fileobj)
                            assert process.stdin is not None
                            process.stdin.close()
                    else:
                        try:
                            chunk = os.read(descriptor, 65536)
                        except BlockingIOError:
                            continue
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        buffer = buffers[key.data]
                        room = max(0, output_limit - len(buffer))
                        buffer.extend(chunk[:room])
                        truncated |= len(chunk) > room
                # A descendant can retain a pipe after its parent exits.
                # The same deadline and process-group cleanup still apply.
                if terminated and time.monotonic() - terminate_time > 2:
                    break
        finally:
            if process.poll() is None or terminated:
                _signal_group(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
            for final_stream in (process.stdin, process.stdout, process.stderr):
                if final_stream is not None:
                    final_stream.close()
    return ProcessResult(
        args=tuple(args),
        returncode=process.returncode,
        stdout=buffers["stdout"].decode(errors="replace"),
        stderr=buffers["stderr"].decode(errors="replace"),
        duration=time.monotonic() - started,
        timed_out=timed_out,
        canceled=canceled,
        truncated=truncated,
    )


def _signal_group(pid: int, sig: signal.Signals) -> None:
    with suppress(ProcessLookupError):
        os.killpg(pid, sig)
