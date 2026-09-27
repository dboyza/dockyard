"""Launch the workbench and operate its labs from an ordinary terminal."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import textwrap
import threading
import webbrowser
from pathlib import Path
from types import FrameType

from dockyard.runtimes.docker import RuntimeErrorBase
from dockyard.service import LabError, Service
from dockyard.store import BusyError


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
    audit = commands.add_parser("audit", help="Check curriculum structure and release coverage")
    audit.add_argument("--json", action="store_true")
    progress = commands.add_parser(
        "progress", help="Export or safely merge personal learning history"
    )
    transfers = progress.add_subparsers(dest="transfer", required=True)
    exported = transfers.add_parser(
        "export", help="Save progress, evidence, checkpoints, and portable drafts"
    )
    exported.add_argument("destination", type=Path)
    imported = transfers.add_parser(
        "import", help="Preview a portable progress bundle before merging"
    )
    imported.add_argument("source", type=Path)
    imported.add_argument("--yes", action="store_true", help="Merge after validating the preview")
    cache = commands.add_parser("cache", help="Inspect and prefetch pinned lesson dependencies")
    caches = cache.add_subparsers(dest="cache_action", required=True)
    for name in ("status", "prepare"):
        command = caches.add_parser(name)
        command.add_argument(
            "scope", nargs="?", default="all", help="all, unit:ID, module:1..24, or track:1..4"
        )
    portfolio = commands.add_parser("portfolio", help="Export a readable mission source portfolio")
    portfolio.add_argument("destination", type=Path)
    lab = commands.add_parser("lab", help="Manage and check a dedicated practice lab")
    operations = lab.add_subparsers(dest="action", required=True)
    for action in (
        "prepare",
        "shell",
        "check",
        "status",
        "reset",
        "retake",
        "stop",
        "resume",
        "clean",
    ):
        operation = operations.add_parser(action)
        operation.add_argument("unit", nargs="?", default=os.environ.get("DOCKYARD_UNIT"))
        if action != "shell":
            operation.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
        if action in {"reset", "retake", "clean"}:
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
        elif arguments.command == "audit":
            from dockyard.audit import curriculum

            report = curriculum(service.catalog)
            if arguments.json:
                print(json.dumps(report, indent=2))
            else:
                print(f"Curriculum: {report['status']}")
                print(
                    f"{report['course_units']} course units, "
                    f"{report['incidents']} incidents, {report['exams']} exams"
                )
                for issue in report["issues"]:
                    print("- " + issue)
                print(report["evidence_boundary"])
            if report["issues"]:
                raise SystemExit(1)
        elif arguments.command == "cache":
            from dockyard.cache import inventory, prepare

            report = (
                prepare(
                    service,
                    arguments.scope,
                    lambda message: print(message, file=sys.stderr, flush=True),
                )
                if arguments.cache_action == "prepare"
                else inventory(service, arguments.scope)
            )
            print(json.dumps(report, indent=2))
        elif arguments.command == "portfolio":
            from dockyard.progress_bundle import save_export
            from dockyard.projects import export_portfolio

            save_export(export_portfolio(service), arguments.destination)
            print(f"Saved Dispatch portfolio to {arguments.destination.resolve()}")
        elif arguments.command == "progress":
            from dockyard.archives import MAX_ARCHIVE
            from dockyard.progress_bundle import (
                export_bundle,
                import_bundle,
                preview_import,
                save_export,
            )

            if arguments.transfer == "export":
                save_export(export_bundle(service), arguments.destination)
                print(f"Saved portable progress to {arguments.destination.resolve()}")
            else:
                if not arguments.source.is_file() or arguments.source.stat().st_size > MAX_ARCHIVE:
                    raise ValueError("Choose a progress archive no larger than 64 MiB.")
                body = arguments.source.read_bytes()
                preview = preview_import(service, body)
                if arguments.yes:
                    print(json.dumps(import_bundle(service, body, preview["digest"]), indent=2))
                else:
                    print(json.dumps(preview, indent=2))
                    print("Review this merge, then repeat with --yes to import.")
        elif arguments.command == "catalog":
            for unit in service.catalog.units.values():
                print(f"{unit.id:28} {unit.title}")
        elif arguments.command == "lab":
            if not arguments.unit:
                raise LabError("Name a unit, or run this command inside its Dockyard lab shell.")
            if arguments.action in {"reset", "retake", "clean"} and not arguments.yes:
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
                if arguments.action == "check" and not arguments.json:
                    print(f"\n{result['status'].upper()}  {arguments.unit}")
                    print(f"Assessment {result['id'][:12]} · revision {result['revision']}")
                    for evidence in result["evidence"]:
                        print(f"  {evidence['status'].upper():7} {evidence['title']}")
                        if evidence["status"] != "pass":
                            print(
                                textwrap.fill(
                                    evidence["diagnostic"],
                                    width=88,
                                    initial_indent="          ",
                                    subsequent_indent="          ",
                                )
                            )
                    print("\nEvidence is saved in the workbench. Use --json for full observations.")
                else:
                    print(json.dumps(result, indent=2))
                if arguments.action == "check" and result.get("status") != "pass":
                    raise SystemExit(1)
    except KeyboardInterrupt:
        print("Dockyard stopped. Your work and lab resources are preserved.")
        raise SystemExit(130) from None
    except (BusyError, RuntimeErrorBase, ValueError, FileNotFoundError) as error:
        print(f"Dockyard: {error}", file=sys.stderr)
        raise SystemExit(2) from error
