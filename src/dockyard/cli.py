"""Launch the workbench and operate its labs from an ordinary terminal."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path
from types import FrameType

from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.service import LabError, Service


def default_directory() -> Path:
    configured = os.environ.get("DOCKYARD_DATA")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / "Library/Application Support/Dockyard"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="dockyard", description="Learn containers in a real lab.")
    result.add_argument("--data-dir", type=Path, default=default_directory())
    commands = result.add_subparsers(dest="command")
    launch = commands.add_parser("launch", help="Open the local learning workbench")
    launch.add_argument("--port", type=int, default=8768)
    launch.add_argument("--no-open", action="store_true")
    commands.add_parser("doctor", help="Inspect local tool and runtime readiness")
    commands.add_parser("catalog", help="List the authored curriculum")
    lab = commands.add_parser("lab", help="Manage and check a dedicated practice lab")
    operations = lab.add_subparsers(dest="action", required=True)
    for action in ("prepare", "shell", "check", "status", "reset", "stop", "resume", "clean"):
        operation = operations.add_parser(action)
        operation.add_argument("unit", nargs="?", default=os.environ.get("DOCKYARD_UNIT"))
        if action in {"reset", "clean"}:
            operation.add_argument("--yes", action="store_true")
    return result


def launch(service: Service, port: int, open_browser: bool) -> None:
    import uvicorn

    from dockyard.web import create_app

    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        listener.bind(("127.0.0.1", port))
    except OSError:
        listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    actual_port = listener.getsockname()[1]
    origin = f"http://127.0.0.1:{actual_port}"
    app, nonce = create_app(service, origin)
    url = f"{origin}/#session={nonce}"
    print(f"Dockyard is starting at {origin}", flush=True)
    if open_browser:
        timer = threading.Timer(0.8, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    else:
        print(f"One-time browser sign-in (valid for five minutes): {url}", flush=True)

    class WorkbenchServer(uvicorn.Server):
        def handle_exit(self, sig: int, frame: FrameType | None) -> None:
            service.shutdown()
            super().handle_exit(sig, frame)

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=actual_port,
        log_level="warning",
        access_log=False,
        timeout_graceful_shutdown=5,
    )
    try:
        WorkbenchServer(config).run(sockets=[listener])
    finally:
        listener.close()


def main() -> None:
    arguments = parser().parse_args()
    service = Service(arguments.data_dir)
    try:
        if arguments.command in {None, "launch"}:
            launch(
                service, getattr(arguments, "port", 8768), not getattr(arguments, "no_open", False)
            )
        elif arguments.command == "doctor":
            print(json.dumps(service.doctor(), indent=2))
        elif arguments.command == "catalog":
            for unit in service.catalog.units.values():
                print(f"{unit.id:28} {unit.title}")
        elif arguments.command == "lab":
            if not arguments.unit:
                raise LabError("Name a unit, or run this command inside its Dockyard lab shell.")
            if arguments.action in {"reset", "clean"} and not arguments.yes:
                raise LabError(
                    "This changes the current lab. Review its scope, then repeat with --yes."
                )
            if arguments.action == "shell":
                lab = service.store.lab(arguments.unit)
                if not lab or not Path(lab.workspace).is_dir():
                    raise LabError("Prepare the lab before opening its shell.")
                env = service.environment(lab)
                env["ZDOTDIR"] = str(service.write_shell_rc(lab))
                os.chdir(lab.workspace)
                os.execvpe("/bin/zsh", ["/bin/zsh", "-i"], env)
            elif arguments.action == "status":
                lab = service.store.lab(arguments.unit)
                print(
                    json.dumps(service.public_lab(lab), indent=2)
                    if lab
                    else "This lab is not prepared."
                )
            else:
                result = service.perform(arguments.unit, arguments.action)
                print(json.dumps(result, indent=2))
                if arguments.action == "check" and result.get("status") != "pass":
                    raise SystemExit(1)
    except KeyboardInterrupt:
        print("Dockyard stopped. Your work and lab resources are preserved.")
    except (RuntimeErrorBase, ValueError, FileNotFoundError) as error:
        print(f"Dockyard: {error}", file=sys.stderr)
        raise SystemExit(2) from error
