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
from datetime import datetime
from pathlib import Path
from types import FrameType
from typing import TYPE_CHECKING, Any

from dockyard.runtimes.docker import RuntimeErrorBase

if TYPE_CHECKING:
    from dockyard.service import Service
from dockyard.store import BusyError

STALE_NOTE = (
    "\nThe lab changed while it was being checked, for example because Pods were still "
    "starting or stopping. Wait for rollouts to finish, then check again."
)


def default_directory() -> Path:
    from dockyard.host import default_directory as directory

    return directory()


EXAMPLES = """\
examples:
  dockyard                              open the workbench in your browser
  dockyard doctor                       check Docker, disk, memory, and terminals
  dockyard lab prepare m01-processes    create a lesson's lab
  dockyard lab shell m01-processes      open a shell inside that lab
  dockyard lab check m01-processes      check your work
  dockyard cache prepare module:7       download what module 7 needs ahead of time
  dockyard progress export backup.zip   back up your progress
"""

LAB_ACTIONS = {
    "prepare": "Create the lab and its workspace",
    "shell": "Open a shell inside the lab, with its settings loaded",
    "check": "Check your work and print the results",
    "status": "Show whether the lab exists and where its files are",
    "reset": "Back up your files and restore the starting state",
    "retake": "Start a fresh attempt without earlier hints",
    "stop": "Stop the lab's containers, cluster, or VMs, keeping everything",
    "resume": "Start a stopped lab again",
    "clean": "Remove the lab's resources; your files and progress stay",
}


def parser() -> argparse.ArgumentParser:
    from dockyard import __version__

    result = argparse.ArgumentParser(
        prog="dockyard",
        description="Learn containers, Docker, and Kubernetes in real labs on this computer.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    result.add_argument("--version", action="version", version=f"dockyard {__version__}")
    result.add_argument(
        "--data-dir",
        type=Path,
        default=default_directory(),
        metavar="PATH",
        help="where progress and labs are stored (default: %(default)s)",
    )
    commands = result.add_subparsers(dest="command", metavar="COMMAND")
    launch = commands.add_parser("launch", help="open the workbench in your browser (the default)")
    launch.add_argument(
        "--port", type=int, default=8768, help="local port to listen on (default: %(default)s)"
    )
    launch.add_argument(
        "--no-open", action="store_true", help="print the sign-in link instead of opening it"
    )
    doctor = commands.add_parser("doctor", help="check Docker, disk, memory, terminals, and tools")
    doctor.add_argument("--json", action="store_true", help="print machine-readable JSON")
    commands.add_parser("catalog", help="list every lesson, mission, incident, and exam")
    audit = commands.add_parser("audit", help="check the curriculum's structure")
    audit.add_argument("--json", action="store_true", help="print machine-readable JSON")
    progress = commands.add_parser("progress", help="back up or restore your progress")
    transfers = progress.add_subparsers(dest="transfer", required=True, metavar="ACTION")
    exported = transfers.add_parser(
        "export", help="save progress, results, notes, and saved mission files to a .zip"
    )
    exported.add_argument("destination", type=Path, help="the .zip file to write")
    imported = transfers.add_parser("import", help="preview a backup, then merge it with --yes")
    imported.add_argument("source", type=Path, help="the backup .zip to read")
    imported.add_argument("--yes", action="store_true", help="merge after showing the preview")
    imported.add_argument("--json", action="store_true", help="print machine-readable JSON")
    cache = commands.add_parser("cache", help="check or download what lessons need ahead of time")
    caches = cache.add_subparsers(dest="cache_action", required=True, metavar="ACTION")
    for name, text in (
        ("status", "show what is already downloaded"),
        ("prepare", "download what is missing"),
    ):
        command = caches.add_parser(name, help=text)
        command.add_argument(
            "scope",
            nargs="?",
            default="all",
            help="all (default), unit:ID, module:1-24, or track:1-4",
        )
        command.add_argument("--json", action="store_true", help="print machine-readable JSON")
    portfolio = commands.add_parser(
        "portfolio", help="export your passed missions' files as a readable portfolio"
    )
    portfolio.add_argument("destination", type=Path, help="the .zip file to write")
    lab = commands.add_parser("lab", help="prepare, check, and manage a lesson's lab")
    operations = lab.add_subparsers(dest="action", required=True, metavar="ACTION")
    for action, text in LAB_ACTIONS.items():
        operation = operations.add_parser(
            action, help=text[0].lower() + text[1:], description=text + "."
        )
        operation.add_argument(
            "unit",
            nargs="?",
            default=os.environ.get("DOCKYARD_UNIT"),
            help="activity ID, such as m01-processes (default: the current lab shell's"
            + ("; outside one, list every lab)" if action == "status" else ")"),
        )
        if action != "shell":
            operation.add_argument(
                "--json", action="store_true", help="print machine-readable JSON"
            )
        if action in {"reset", "retake", "clean"}:
            operation.add_argument("--yes", action="store_true", help="confirm the change")
        if action == "clean":
            operation.add_argument(
                "--all", action="store_true", help="clean every lab in this profile"
            )
    return result


LAB_STATE_NAMES = {
    "absent": "not prepared",
    "preparing": "preparing",
    "ready": "ready",
    "checking": "checking",
    "stopping": "stopping",
    "stopped": "stopped",
    "failed": "needs attention",
    "cleaning": "cleaning up",
}


def print_doctor(report: dict[str, Any]) -> None:
    from dockyard import __version__

    def line(label: str, value: str) -> None:
        print(f"  {label:<14}{value}")

    print(f"Dockyard {__version__}")
    if report.get("data_dir"):
        line("Data", report["data_dir"])
    line("System", f"{'WSL 2' if report['wsl'] else report['system']} {report['architecture']}")
    memory = report["host_memory_gib"]
    free = report["memory_free_percent"]
    line(
        "Memory",
        (f"{memory:g} GiB" if memory is not None else "not reported")
        + (f", {free}% available" if free is not None else ""),
    )
    line("Free disk", f"{report['free_disk_gib']:g} GiB")
    line(
        "Docker",
        f"ready ({report['docker_version']})"
        if report["docker_ready"]
        else f"not available: {report['docker_error'] or 'no response'}",
    )
    if report["docker_tools_error"]:
        line("Docker tools", report["docker_tools_error"])
    line("Terminal", report["terminal"] or "none found; copy lab commands into your own terminal")
    line(
        "VM labs",
        f"blocked: {report['native_vm_blocker']}"
        if report["native_vm_blocker"]
        else f"available (up to {report['vm_budget_gib']} GiB)",
    )
    for name, location in sorted(report["tools"].items()):
        line(name, location or "not installed yet")


def print_cache(report: dict[str, Any]) -> None:
    units = report["units"]
    ready = sum(1 for unit in units if unit["status"] == "cached")
    print(f"Scope {report['scope']}: {ready} of {len(units)} activities have everything cached")
    for unit in units:
        if unit["status"] != "cached":
            print(f"  {unit['unit_id']:<24} {unit['status']}")
            for item in unit["missing"]:
                print(f"    missing: {item}")
            for item in unit["limitations"]:
                print(f"    needs network: {item}")
    print(
        f"Private cache {report['private_cache_gib']:g} GiB of {report['soft_budget_gib']} GiB"
        f" suggested; {report['free_disk_gib']:g} GiB free on disk."
    )


def print_lab(unit_id: str, lab: dict[str, Any] | None) -> None:
    if not lab:
        print(f"{unit_id}: not prepared. Run: dockyard lab prepare {unit_id}")
        return
    print(f"{unit_id}: {LAB_STATE_NAMES.get(lab['state'], lab['state'])}")
    print(f"  Workspace  {lab['workspace']}")
    if lab.get("error"):
        print(
            textwrap.fill(
                lab["error"],
                width=88,
                initial_indent="  Problem    ",
                subsequent_indent="             ",
            )
        )
    if lab["state"] == "ready":
        print(f"  Next       dockyard lab shell {unit_id}")
    elif lab["state"] == "stopped":
        print(f"  Next       dockyard lab resume {unit_id}")
    elif lab["state"] == "absent":
        print(f"  Next       dockyard lab prepare {unit_id}")


def print_labs(labs: list[dict[str, Any]]) -> None:
    present = [lab for lab in labs if lab["state"] != "absent"]
    if not present:
        print("No labs yet. Start one with: dockyard lab prepare UNIT")
        return
    for lab in present:
        print(f"  {lab['unit_id']:24} {LAB_STATE_NAMES.get(lab['state'], lab['state'])}")
    print("Details: dockyard lab status UNIT")


def print_import(report: dict[str, Any], merged: bool) -> None:
    if report.get("already_imported"):
        print("This backup was already imported; nothing changed.")
        return
    created = datetime.fromisoformat(report["created_at"]).astimezone()
    print(f"Backup made {created:%Y-%m-%d %H:%M}")
    rows = (
        ("Activities", f"{report['progress_units']} ({report['new_progress_units']} new here)"),
        ("Check results", report["assessments"]),
        ("Exam attempts", report["exams"]),
        ("Mission files", report["checkpoints"]),
        ("Draft files", report["draft_files"]),
        ("Notes", f"{report['notes']} ({report['preserved_local_notes']} differ; yours are kept)"),
    )
    for label, value in rows:
        print(f"  {label:14} {value}")
    if report["older_revisions"]:
        print(f"  {report['older_revisions']} activities changed since; they need a new check.")
    if merged:
        print(f"Merged. Imported drafts are in {report['directory']}")
        print(f"Your earlier progress database was saved to {report['backup']}")
    else:
        print(textwrap.fill(report["policy"], width=88))
        print("To merge it, repeat this command with --yes.")


def open_local_browser(url: str) -> None:
    import shutil

    from dockyard import host
    from dockyard.process import run

    if host.is_wsl() and (opener := shutil.which("rundll32.exe")):
        result = run([opener, "url.dll,FileProtocolHandler", url], timeout=10)
        if result.ok:
            return
    if not webbrowser.open(url):
        print(f"Open this one-time local sign-in in your browser: {url}", flush=True)


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
        timer = threading.Timer(0.8, open_local_browser, args=(url,))
        timer.daemon = True
        timer.start()
    else:
        print(f"One-time browser sign-in (valid for five minutes): {url}", flush=True)
    print(
        "Keep this window open while you use Dockyard. Press Ctrl-C to stop; "
        "your work and labs are kept.",
        flush=True,
    )

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
    print("Dockyard stopped. Your work and labs are kept.", flush=True)


def main() -> None:
    if os.name == "nt":
        print("On Windows, run dockyard.ps1 to use Dockyard inside WSL 2.", file=sys.stderr)
        raise SystemExit(2)
    from dockyard.service import LabError, Service

    arguments = parser().parse_args()
    service = Service(arguments.data_dir)
    try:
        if arguments.command in {None, "launch"}:
            launch(
                service, getattr(arguments, "port", 8768), not getattr(arguments, "no_open", False)
            )
        elif arguments.command == "doctor":
            report = {**service.doctor(), "data_dir": str(service.directory)}
            if arguments.json:
                print(json.dumps(report, indent=2))
            else:
                print_doctor(report)
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
            if arguments.json:
                print(json.dumps(report, indent=2))
            else:
                print_cache(report)
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
                report = (
                    import_bundle(service, body, preview["digest"]) if arguments.yes else preview
                )
                if arguments.json:
                    print(json.dumps(report, indent=2))
                else:
                    print_import(report, arguments.yes)
        elif arguments.command == "catalog":
            kinds = {"lesson": "", "mission": "mission", "incident": "incident", "exam": "exam"}
            for module in service.catalog.modules:
                print(f"\nModule {module['id']:02d} · {module['title']}")
                members = sorted(
                    (u for u in service.catalog.units.values() if u.module == module["id"]),
                    key=lambda unit: unit.order,
                )
                for unit in members:
                    print(f"  {unit.id:24} {kinds[unit.kind]:9} {unit.title}")
        elif arguments.command == "lab" and getattr(arguments, "all", False):
            if arguments.unit:
                raise LabError("Use either a unit or --all, not both.")
            owned = [item for item in service.store.labs() if item.state != "absent"]
            plural = "lab" if len(owned) == 1 else "labs"
            if not owned:
                print("No labs to clean.")
                return
            if not arguments.yes:
                raise LabError(
                    f"This removes the resources of {len(owned)} {plural}. "
                    "Your files and progress stay. Repeat with --yes to continue."
                )
            for item in owned:
                print(f"Cleaning {item.unit_id}…", flush=True)
                service.perform(item.unit_id, "clean")
            print(f"Cleaned {len(owned)} {plural}.")
        elif arguments.command == "lab" and arguments.action == "status" and not arguments.unit:
            labs = [service.public_lab(item) for item in service.store.labs()]
            if arguments.json:
                print(json.dumps(labs, indent=2))
            else:
                print_labs(labs)
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
                from dockyard import host

                executable = host.shell()
                rc = service.write_shell_rc(lab)
                env["ZDOTDIR"] = str(rc)
                args = (
                    [executable, "--noprofile", "--rcfile", str(rc / ".bashrc"), "-i"]
                    if Path(executable).name == "bash"
                    else [executable, "-i"]
                )
                os.chdir(lab.workspace)
                os.execvpe(executable, args, env)
            elif arguments.action == "status":
                lab = service.store.lab(arguments.unit)
                public = service.public_lab(lab) if lab else None
                if arguments.json:
                    print(json.dumps(public, indent=2))
                else:
                    print_lab(arguments.unit, public)
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
                    if result["status"] == "stale":
                        print(STALE_NOTE)
                    print("\nEvidence is saved in the workbench. Use --json for full observations.")
                elif arguments.json:
                    print(json.dumps(result, indent=2))
                else:
                    lab = service.store.lab(arguments.unit)
                    print_lab(arguments.unit, service.public_lab(lab) if lab else None)
                if arguments.action == "check" and result.get("status") != "pass":
                    raise SystemExit(1)
    except KeyboardInterrupt:
        print("Dockyard stopped. Your work and labs are kept.")
        if arguments.command not in {None, "launch"}:
            raise SystemExit(130) from None
    except (BusyError, RuntimeErrorBase, ValueError, FileNotFoundError) as error:
        print(f"Dockyard: {error}", file=sys.stderr)
        raise SystemExit(2) from error
