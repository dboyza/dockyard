"""Run the browser's copied command in a real PTY against its prepared lab."""

import json
import os
import pty
import select
import shlex
import signal
import sys
import time
from contextlib import suppress
from pathlib import Path

from dockyard.service import Service

profile, command = sys.argv[1:]
service = Service(Path(profile))
lab = service.store.lab("m01-processes")
assert lab is not None
marker = Path(profile) / "terminal-proof.json"
pid, descriptor = pty.fork()
if pid == 0:
    os.execv("/bin/sh", ["sh", "-c", command])
try:
    # Use the installed interpreter by absolute path, independent of host dotfiles.
    code = (
        "import os,json; from pathlib import Path; "
        f"Path({str(marker)!r}).write_text(json.dumps("
        "{'cwd':os.getcwd(),'tty':os.isatty(0),'unit':os.environ.get('DOCKYARD_UNIT')}))"
    )
    os.write(descriptor, (shlex.join([sys.executable, "-c", code]) + "\nexit\n").encode())
    deadline = time.monotonic() + 15
    while not marker.exists() and time.monotonic() < deadline:
        readable, _, _ = select.select([descriptor], [], [], 0.2)
        if readable:
            try:
                os.read(descriptor, 65536)
            except OSError:
                break
    result = json.loads(marker.read_text())
    assert result == {"cwd": lab.workspace, "tty": True, "unit": lab.unit_id}, result
finally:
    os.close(descriptor)
    with suppress(ProcessLookupError):
        os.kill(pid, signal.SIGTERM)
    os.waitpid(pid, 0)
