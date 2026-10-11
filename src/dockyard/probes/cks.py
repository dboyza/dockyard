"""Observe CKS hardening outcomes on native clusters: benchmarks, endpoints, and binaries."""

from __future__ import annotations

import base64
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from contextlib import suppress
from pathlib import Path
from typing import Any

import yaml

from dockyard.fixtures.cks import BINARIES, STAGED, release_checksums
from dockyard.fixtures.recovery import etcd
from dockyard.native import current
from dockyard.probes.bootstrap import ERRORS
from dockyard.probes.kubernetes import available
from dockyard.probes.maintenance import observed, preserved
from dockyard.probes.native import workflow
from dockyard.probes.security import connections
from dockyard.runtimes.linux import LinuxRuntime

# kube-bench 0.16 maps Kubernetes versions only up to 1.34, so the benchmark is named.
BENCHMARK = "cis-1.12"


def kube_bench(runtime: LinuxRuntime, guest: str, target: str, checks: list[str]) -> dict[str, str]:
    """Run the named benchmark checks on one guest and return each check's status."""
    result = runtime.guest(
        guest,
        [
            "sudo",
            "kube-bench",
            "run",
            "--targets",
            target,
            "--benchmark",
            BENCHMARK,
            "--check",
            ",".join(checks),
            "--json",
        ],
        timeout=120,
    )
    runtime.require(result)
    report = json.loads(result.stdout)
    return {
        item["test_number"]: item["status"]
        for control in report["Controls"]
        for group in control["tests"]
        for item in group["results"]
    }


def kubelet_config(runtime: LinuxRuntime, node: str) -> dict[str, Any]:
    """The configuration the running kubelet reports, not the file on disk."""
    value = runtime.kubectl(["get", "--raw", f"/api/v1/nodes/{node}/proxy/configz"], timeout=20)
    runtime.require(value)
    return dict(json.loads(value.stdout)["kubeletconfig"])


def begin(
    names: tuple[str, ...], full: bool = True
) -> tuple[LinuxRuntime, dict[str, Any], dict[str, Any]]:
    """Start a result with every outcome false, after checking the cluster is the original.

    Exams combine several of these observations, so they pass full=False and check the
    cluster's preservation and the job workflow once for the whole exam instead.
    """
    shared = ("preserved", "workflow") if full else ()
    result: dict[str, Any] = dict.fromkeys((*shared[:1], *names, *shared[1:]), False)
    details: dict[str, Any] = {}
    result["_details"] = details
    r = current()
    if full:
        baseline = json.loads((r.root / "data/maintenance-baseline.json").read_text())
        result["preserved"] = preserved(r, baseline, details)
    return r, result, details


def kubelet_hardened(r: LinuxRuntime, checks: dict[str, Any], details: dict[str, Any]) -> bool:
    """Whether kube-bench passes the checks on the worker and the running kubelet agrees."""
    statuses = kube_bench(r, r.worker, "node", sorted(checks))
    running = kubelet_config(r, "lima-" + r.worker)
    observed_settings = {check: read(running) for check, (read, _) in checks.items()}
    details["kubelet"] = {"benchmark": statuses, "running": observed_settings}
    return statuses == dict.fromkeys(checks, "PASS") and all(
        observed_settings[check] == wanted for check, (_, wanted) in checks.items()
    )


def profiling_off(r: LinuxRuntime, component: str, check: str, details: dict[str, Any]) -> bool:
    """Whether a control-plane component passes its profiling check and runs with it off."""
    statuses = kube_bench(r, r.primary, "master", [check])
    pods = observed(r, ["get", "pods", "-n", "kube-system", "-l", "component=" + component])
    command = pods["items"][0]["spec"]["containers"][0]["command"]
    ready = all(
        status.get("ready") for status in pods["items"][0]["status"].get("containerStatuses", [])
    )
    details[component] = {"benchmark": statuses, "ready": ready}
    return statuses == {check: "PASS"} and "--profiling=false" in command and ready


def pprof_gone(r: LinuxRuntime, details: dict[str, Any]) -> bool:
    # With profiling off, the API server no longer serves its pprof handlers.
    ready = r.kubectl(["get", "--raw=/readyz"], timeout=20)
    pprof = r.kubectl(["get", "--raw=/debug/pprof/"], timeout=20)
    details["pprof_served"] = pprof.ok
    return ready.ok and not pprof.ok and "NotFound" in pprof.stderr + pprof.stdout


CLIENTS = ("trusted-client", "untrusted-client")


def metadata_blocked(r: LinuxRuntime, details: dict[str, Any]) -> bool:
    # The service must really be there, or an unreachable endpoint proves nothing.
    served = all(
        r.guest(guest, ["curl", "-sf", "http://169.254.169.254/latest/meta-data/"]).ok
        for guest in (r.primary, r.worker)
    )
    reached = {c: connections(c, "frontend", [("169.254.169.254", 80)]) for c in CLIENTS}
    details["metadata"] = {"served_on_nodes": served, "reached_from": reached}
    return served and not any(any(v) for v in reached.values())


def kubelets_blocked(r: LinuxRuntime, ports: list[int], details: dict[str, Any]) -> bool:
    nodes = observed(r, ["get", "nodes"])["items"]
    addresses = [
        next(a["address"] for a in n["status"]["addresses"] if a["type"] == "InternalIP")
        for n in nodes
    ]
    targets = [(address, port) for address in addresses for port in ports]
    reached = {c: connections(c, "frontend", targets) for c in CLIENTS}
    details["kubelet_ports"] = {"targets": targets, "reached_from": reached}
    return len(addresses) == 2 and not any(any(v) for v in reached.values())


def checksums(runtime: LinuxRuntime, guest: str, pattern: str) -> dict[str, str]:
    """SHA-512 of each file matching a guest path pattern, keyed by file name."""
    listing = runtime.guest(guest, ["sudo", "sh", "-c", f"sha512sum {pattern} 2>/dev/null || true"])
    runtime.require(listing)
    return {
        line.split()[1].rsplit("/", 1)[-1]: line.split()[0]
        for line in listing.stdout.splitlines()
        if len(line.split()) == 2
    }


def staged_binaries(r: LinuxRuntime, altered: str, details: dict[str, Any]) -> tuple[bool, bool]:
    """Whether every staged file is genuine, and whether the genuine ones were kept."""
    official = release_checksums()
    staged = checksums(r, r.primary, STAGED + "/*")
    installed = {
        guest: checksums(r, guest, " ".join(f"/usr/bin/{name}" for name in BINARIES))
        for guest in (r.primary, r.worker)
    }
    mismatched = sorted(name for name, value in staged.items() if official.get(name) != value)
    details["staged"] = {"present": sorted(staged), "not_matching": mismatched}
    kept = all(staged.get(name) == official[name] for name in BINARIES if name != altered) and all(
        found == official for found in installed.values()
    )
    return not mismatched, kept


def unauthenticated(r: LinuxRuntime, path: str) -> int:
    """The HTTP status the API server returns to a request without credentials."""
    configuration = yaml.safe_load((r.root / "kubeconfig").read_text())
    authority = base64.b64decode(
        configuration["clusters"][0]["cluster"]["certificate-authority-data"]
    ).decode()
    context = ssl.create_default_context(cadata=authority)
    url = f"https://127.0.0.1:{int(r.lab.resources['api_port'])}{path}"
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context)
    )
    try:
        with opener.open(url, timeout=10) as response:
            return int(response.status)
    except urllib.error.HTTPError as error:
        return int(error.code)


# Default bindings that Kubernetes and kubeadm create for discovery and cluster joining.
DEFAULT_BINDING_PREFIXES = ("system:", "kubeadm:")
ANONYMOUS_SUBJECTS = {"system:anonymous", "system:unauthenticated"}


def anonymous_grants(r: LinuxRuntime) -> list[str]:
    """Bindings, other than the built-in defaults, that grant anything to anonymous callers."""
    found = []
    for kind in ("clusterrolebindings", "rolebindings"):
        args = ["get", kind] + (["--all-namespaces"] if kind == "rolebindings" else [])
        for binding in observed(r, args)["items"]:
            name = binding["metadata"]["name"]
            subjects = {subject.get("name") for subject in binding.get("subjects") or []}
            if subjects & ANONYMOUS_SUBJECTS and not name.startswith(DEFAULT_BINDING_PREFIXES):
                found.append(f"{kind}/{binding['metadata'].get('namespace', '')}/{name}")
    return found


def anonymous(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("grants", "restricted", "health"), full)
    with suppress(*ERRORS):
        grants = anonymous_grants(r)
        details["grants"] = grants
        result["grants"] = not grants
    with suppress(*ERRORS):
        statuses = {
            path: unauthenticated(r, path)
            for path in ("/api/v1/namespaces/dispatch/configmaps", "/version", "/readyz", "/livez")
        }
        details["unauthenticated_status"] = statuses
        # 401 means the request is no longer treated as the anonymous user at all.
        result["restricted"] = (
            statuses["/api/v1/namespaces/dispatch/configmaps"] == 401
            and statuses["/version"] == 401
        )
        result["health"] = statuses["/readyz"] == 200 and statuses["/livez"] == 200
    if full:
        result["workflow"] = workflow()
    return result


def can(r: LinuxRuntime, subject: str, verb: str, resource: str, namespace: str) -> bool:
    """kubectl auth can-i for a subject; the exit status carries the answer."""
    answer = r.kubectl(["auth", "can-i", verb, resource, "-n", namespace, "--as", subject])
    return answer.ok and answer.stdout.strip() == "yes"


REPORTS_DEFAULT = "system:serviceaccount:reports:default"
BUILDER = "system:serviceaccount:reports:report-builder"
SETTINGS_REQUEST = (
    "import json,ssl,urllib.request; a='/var/run/secrets/kubernetes.io/serviceaccount/'; "
    "q=urllib.request.Request('https://kubernetes.default.svc/api/v1/namespaces/reports/"
    "configmaps/report-settings',headers={'Authorization':'Bearer '+open(a+'token').read()}); "
    "print(json.load(urllib.request.urlopen(q,context=ssl.create_default_context(cafile=a+'ca.crt'),"
    "timeout=5))['data']['title'])"
)


def bound_to(r: LinuxRuntime, namespace: str, account: str) -> list[str]:
    """Bindings anywhere that name a ServiceAccount as a subject."""
    found = []
    for kind in ("clusterrolebindings", "rolebindings"):
        args = ["get", kind] + (["--all-namespaces"] if kind == "rolebindings" else [])
        for binding in observed(r, args)["items"]:
            for subject in binding.get("subjects") or []:
                if (
                    subject.get("kind") == "ServiceAccount"
                    and subject.get("name") == account
                    and subject.get("namespace") == namespace
                ):
                    found.append(f"{kind}/{binding['metadata']['name']}")
    return found


def tokens(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("default", "legacy", "builder"), full)
    with suppress(*ERRORS):
        account = observed(r, ["get", "serviceaccount", "default", "-n", "reports"])
        bindings = bound_to(r, "reports", "default")
        # Pods still terminating after a restart are on their way out; judge the live ones.
        viewers = [
            pod
            for pod in observed(r, ["get", "pods", "-n", "reports", "-l", "app=report-viewer"])[
                "items"
            ]
            if not pod["metadata"].get("deletionTimestamp")
        ]
        # An automounted token appears as a projected volume holding a serviceAccountToken.
        mounted = [
            pod["metadata"]["name"]
            for pod in viewers
            if any(
                source.get("serviceAccountToken")
                for volume in pod["spec"].get("volumes", [])
                for source in volume.get("projected", {}).get("sources", [])
            )
        ]
        details["default"] = {
            "automount": account.get("automountServiceAccountToken"),
            "bindings": bindings,
            "viewer_pods_with_token": mounted,
        }
        result["default"] = (
            account.get("automountServiceAccountToken") is False
            and not bindings
            and bool(viewers)
            and not mounted
            and not can(r, REPORTS_DEFAULT, "get", "configmaps", "reports")
        )
    with suppress(*ERRORS):
        secrets = observed(
            r,
            [
                "get",
                "secrets",
                "-n",
                "reports",
                "--field-selector",
                "type=kubernetes.io/service-account-token",
            ],
        )["items"]
        details["legacy_tokens"] = [item["metadata"]["name"] for item in secrets]
        result["legacy"] = not secrets
    with suppress(*ERRORS):
        deployment = observed(r, ["get", "deployment", "report-builder", "-n", "reports"])
        allowed = can(r, BUILDER, "get", "configmap/report-settings", "reports")
        excess = {
            check: can(r, BUILDER, verb, resource, "reports")
            for check, (verb, resource) in {
                "list_secrets": ("list", "secrets"),
                "create_pods": ("create", "pods"),
                "update_settings": ("update", "configmap/report-settings"),
                # Every namespace holds kube-root-ca.crt, so this shows the Role names its object.
                "read_other_configmaps": ("get", "configmap/kube-root-ca.crt"),
            }.items()
        }
        reply = r.kubectl(
            [
                "exec",
                "-n",
                "reports",
                "deployment/report-builder",
                "--",
                "python",
                "-c",
                SETTINGS_REQUEST,
            ],
            timeout=30,
        )
        details["builder"] = {
            "service_account": deployment["spec"]["template"]["spec"].get("serviceAccountName"),
            "can_read_settings": allowed,
            "excess": excess,
            "reads_settings": reply.ok,
        }
        result["builder"] = (
            deployment["spec"]["template"]["spec"].get("serviceAccountName") == "report-builder"
            and deployment.get("status", {}).get("availableReplicas", 0) >= 1
            and allowed
            and not any(excess.values())
            and reply.ok
            and reply.stdout.strip() == "Daily Dispatch summary"
        )
    if full:
        result["workflow"] = workflow()
    return result


DEPLOYER = "system:serviceaccount:ci:deployer"


def can_as(
    r: LinuxRuntime, identity: list[str], verb: str, resource: str, namespace: str | None
) -> bool:
    scope = ["-n", namespace] if namespace else []
    answer = r.kubectl(["auth", "can-i", verb, resource, *scope, *identity])
    return answer.ok and answer.stdout.strip() == "yes"


def access_matches(
    r: LinuxRuntime,
    identity: list[str],
    expected: dict[tuple[str, str, str | None], bool],
    details: dict[str, Any],
    key: str,
) -> bool:
    """Compare what an identity may do with what it should be able to do."""
    observed_access = {
        f"{verb} {resource} in {namespace or 'cluster'}": can_as(
            r, identity, verb, resource, namespace
        )
        for verb, resource, namespace in expected
    }
    wanted = {
        f"{verb} {resource} in {namespace or 'cluster'}": allowed
        for (verb, resource, namespace), allowed in expected.items()
    }
    details[key] = {name: value for name, value in observed_access.items() if value != wanted[name]}
    return observed_access == wanted


DEPLOYER_ACCESS = {
    ("patch", "deployments.apps", "dispatch"): True,
    ("update", "deployments.apps", "dispatch"): True,
    ("list", "deployments.apps", "dispatch"): True,
    ("get", "secrets", "dispatch"): False,
    ("delete", "pods", "dispatch"): False,
    ("patch", "deployments.apps", "kube-system"): False,
    ("create", "clusterrolebindings", None): False,
    ("delete", "nodes", None): False,
}
OPERATOR_ACCESS = {
    ("list", "pods", "dispatch"): True,
    ("get", "pods/log", "dispatch"): True,
    ("list", "deployments.apps", "dispatch"): True,
    ("get", "secrets", "dispatch"): False,
    ("delete", "pods", "dispatch"): False,
    ("patch", "deployments.apps", "dispatch"): False,
    ("create", "pods/exec", "dispatch"): False,
    ("list", "pods", "kube-system"): False,
    ("list", "nodes", None): False,
}


def rbac(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("deployer", "operators"), full)
    with suppress(*ERRORS):
        result["deployer"] = access_matches(
            r, ["--as", DEPLOYER], DEPLOYER_ACCESS, details, "deployer_differences"
        )
    with suppress(*ERRORS):
        result["operators"] = access_matches(
            r,
            ["--as", "alex", "--as-group", "dispatch-operators"],
            OPERATOR_ACCESS,
            details,
            "operator_differences",
        )
    if full:
        result["workflow"] = workflow()
    return result


AUDITOR_ACCESS = {
    ("list", "pods", "dispatch"): True,
    ("list", "deployments.apps", "frontend"): True,
    ("get", "pods/log", "frontend"): True,
    ("get", "secrets", "dispatch"): False,
    ("delete", "pods", "frontend"): False,
    ("patch", "deployments.apps", "dispatch"): False,
    ("list", "pods", "kube-system"): False,
    ("list", "pods", "ci"): False,
    ("list", "nodes", None): False,
}


def access(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("anonymous", "tokens", "auditors"), full)
    with suppress(*ERRORS):
        grants = anonymous_grants(r)
        statuses = {
            path: unauthenticated(r, path)
            for path in ("/api/v1/namespaces/dispatch/pods", "/version", "/readyz")
        }
        details["anonymous"] = {"grants": grants, "unauthenticated_status": statuses}
        result["anonymous"] = (
            not grants
            and statuses["/api/v1/namespaces/dispatch/pods"] == 401
            and statuses["/version"] == 401
            and statuses["/readyz"] == 200
        )
    with suppress(*ERRORS):
        secrets = observed(
            r,
            [
                "get",
                "secrets",
                "--all-namespaces",
                "--field-selector",
                "type=kubernetes.io/service-account-token",
            ],
        )["items"]
        # kube-system belongs to the platform's own components, outside this review.
        legacy = [
            f"{item['metadata']['namespace']}/{item['metadata']['name']}"
            for item in secrets
            if item["metadata"]["namespace"] != "kube-system"
        ]
        details["legacy_tokens"] = legacy
        result["tokens"] = not legacy
    with suppress(*ERRORS):
        result["auditors"] = access_matches(
            r,
            ["--as", "sam", "--as-group", "auditors"],
            AUDITOR_ACCESS,
            details,
            "auditor_differences",
        )
    if full:
        result["workflow"] = workflow()
    return result


def service_closed(r: LinuxRuntime, guest: str, unit: str, port: int) -> dict[str, Any]:
    """Whether a systemd service is stopped, will not start at boot, and its port is closed."""
    state = r.guest(guest, ["systemctl", "is-active", unit]).stdout.strip()
    enabled = r.guest(guest, ["systemctl", "is-enabled", unit]).stdout.strip()
    listening = r.guest(guest, ["ss", "-ltnH", f"sport = :{port}"])
    r.require(listening)
    return {
        "active": state,
        "enabled": enabled,
        "listening": bool(listening.stdout.strip()),
        # A deleted unit reports as not found, which also satisfies the requirement.
        "closed": state != "active"
        and enabled not in {"enabled", "static", "alias", "linked"}
        and not listening.stdout.strip(),
    }


def account_retired(r: LinuxRuntime, guest: str, user: str) -> dict[str, Any]:
    """Whether a user can no longer log in with a shell or use sudo."""
    entry = r.guest(guest, ["getent", "passwd", user])
    shell = entry.stdout.strip().rsplit(":", 1)[-1] if entry.ok else ""
    rules = r.guest(guest, ["sudo", "sudo", "-l", "-U", user])
    may_sudo = rules.ok and "may run the following" in rules.stdout
    return {
        "exists": entry.ok,
        "shell": shell,
        "sudo": may_sudo,
        "retired": (not entry.ok or shell in {"/usr/sbin/nologin", "/sbin/nologin", "/bin/false"})
        and not may_sudo,
    }


def footprint(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("service", "account"), full)
    with suppress(*ERRORS):
        details["service"] = service_closed(r, r.worker, "report-share", 8081)
        result["service"] = details["service"]["closed"]
    with suppress(*ERRORS):
        details["account"] = account_retired(r, r.worker, "backup")
        result["account"] = details["account"]["retired"]
    if full:
        result["workflow"] = workflow()
    return result


def exec_in(r: LinuxRuntime, namespace: str, target: str, script: str) -> tuple[bool, str]:
    result = r.kubectl(["exec", "-n", namespace, target, "--", "sh", "-c", script], timeout=30)
    return result.ok, result.stdout.strip()


def profile_loaded(r: LinuxRuntime, profile: str) -> dict[str, Any]:
    """Whether a profile is loaded in enforce mode, and installed for boot, on every node."""
    nodes = {}
    for guest in (r.primary, r.worker):
        loaded = r.guest(guest, ["sudo", "cat", "/sys/kernel/security/apparmor/profiles"])
        installed = r.guest(guest, ["test", "-f", f"/etc/apparmor.d/{profile}"])
        nodes[guest] = {
            "enforced": loaded.ok and f"{profile} (enforce)" in loaded.stdout.splitlines(),
            "installed_for_boot": installed.ok,
        }
    return {
        "nodes": nodes,
        "ok": all(n["enforced"] and n["installed_for_boot"] for n in nodes.values()),
    }


def apparmor(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("loaded", "confined", "working"), full)
    with suppress(*ERRORS):
        details["loaded"] = profile_loaded(r, "dockyard-processor")
        result["loaded"] = details["loaded"]["ok"]
    with suppress(*ERRORS):
        details["confined"] = apparmor_confined(
            r, "processing", "deployment/processor", "dockyard-processor"
        )
        result["confined"] = details["confined"]["ok"]
    with suppress(*ERRORS):
        deployment = observed(r, ["get", "deployment", "processor", "-n", "processing"])
        result["working"] = available(deployment, 1) and results_growing(r)
    if full:
        result["workflow"] = workflow()
    return result


CHMOD_ATTEMPT = (
    "python -c \"import os; open('/tmp/probe','w').close(); os.chmod('/tmp/probe', 0o755)\""
)


def seccomp_mode(r: LinuxRuntime, target: str, namespace: str = "processing") -> str:
    """The Seccomp field of the container's main process: 0 off, 2 filtering."""
    _, status = exec_in(r, namespace, target, "grep '^Seccomp:' /proc/1/status")
    return status.split()[-1] if status else ""


def results_growing(
    r: LinuxRuntime,
    namespace: str = "processing",
    target: str = "deployment/processor",
    folder: str = "/data/results",
) -> bool:
    """Whether a workload keeps adding files to its output folder."""
    kind, name = target.split("/", 1)
    selector = observed(r, ["get", kind, name, "-n", namespace])["spec"]["selector"]["matchLabels"]
    labels = ",".join(f"{key}={value}" for key, value in selector.items())
    pods = observed(r, ["get", "pods", "-n", namespace, "-l", labels])["items"]
    # Count twice in one serving Pod; replicas and Pods ending a rollout hold different files.
    serving = sorted(
        pod["metadata"]["name"]
        for pod in pods
        if not pod["metadata"].get("deletionTimestamp")
        and any(
            c["type"] == "Ready" and c["status"] == "True"
            for c in pod["status"].get("conditions", [])
        )
    )
    if not serving:
        return False
    count = f"ls {folder} | wc -l"
    ok, output = exec_in(r, namespace, f"pod/{serving[0]}", f"{count}; sleep 6; {count}")
    counts = output.split()
    return ok and len(counts) == 2 and int(counts[1]) > int(counts[0])


def apparmor_confined(r: LinuxRuntime, namespace: str, target: str, profile: str) -> dict[str, Any]:
    """Whether a root workload runs under a profile that refuses writes to /etc."""
    _, current = exec_in(r, namespace, target, "cat /proc/1/attr/apparmor/current")
    # The workload runs as root, so only AppArmor can refuse this write.
    wrote, _ = exec_in(r, namespace, target, "echo probe > /etc/dockyard-probe")
    return {
        "profile": current,
        "root_wrote_etc": wrote,
        "ok": current == f"{profile} (enforce)" and not wrote,
    }


def seccomp(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("installed", "processor", "intake"), full)
    with suppress(*ERRORS):
        path = "/var/lib/kubelet/seccomp/profiles/no-chmod.json"
        valid = "import json,sys; json.load(open(sys.argv[1]))"
        installed = {
            guest: r.guest(guest, ["sudo", "python3", "-c", valid, path]).ok
            for guest in (r.primary, r.worker)
        }
        details["installed"] = installed
        result["installed"] = all(installed.values())
    with suppress(*ERRORS):
        deployment = observed(r, ["get", "deployment", "processor", "-n", "processing"])
        profile = deployment["spec"]["template"]["spec"]["containers"][0].get(
            "securityContext", {}
        ).get("seccompProfile") or deployment["spec"]["template"]["spec"].get(
            "securityContext", {}
        ).get("seccompProfile", {})
        changed, _ = exec_in(r, "processing", "deployment/processor", CHMOD_ATTEMPT)
        mode = seccomp_mode(r, "deployment/processor")
        details["processor"] = {"profile": profile, "seccomp": mode, "chmod_allowed": changed}
        result["processor"] = (
            profile.get("type") == "Localhost"
            and mode == "2"
            and not changed
            and available(deployment, 1)
            and results_growing(r)
        )
    with suppress(*ERRORS):
        deployment = observed(r, ["get", "deployment", "intake", "-n", "processing"])
        mode = seccomp_mode(r, "deployment/intake")
        details["intake"] = {"seccomp": mode}
        result["intake"] = mode == "2" and available(deployment, 1)
    if full:
        result["workflow"] = workflow()
    return result


def confine(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("footprint", "apparmor", "seccomp", "working"), full)
    with suppress(*ERRORS):
        service = service_closed(r, r.primary, "debug-share", 2222)
        account = account_retired(r, r.primary, "contractor")
        details["footprint"] = {"service": service, "account": account}
        result["footprint"] = service["closed"] and account["retired"]
    with suppress(*ERRORS):
        loaded = profile_loaded(r, "dockyard-renderer")
        confined = apparmor_confined(r, "rendering", "deployment/renderer", "dockyard-renderer")
        details["apparmor"] = {"loaded": loaded, "confined": confined}
        result["apparmor"] = loaded["ok"] and confined["ok"]
    with suppress(*ERRORS):
        mode = seccomp_mode(r, "deployment/renderer", "rendering")
        details["seccomp"] = mode
        result["seccomp"] = mode == "2"
    with suppress(*ERRORS):
        deployment = observed(r, ["get", "deployment", "renderer", "-n", "rendering"])
        result["working"] = available(deployment, 1) and results_growing(
            r, "rendering", "deployment/renderer", "/output"
        )
    if full:
        result["workflow"] = workflow()
    return result


ETCDCTL = [
    "etcdctl",
    "--endpoints=https://127.0.0.1:2379",
    "--cacert=/etc/kubernetes/pki/etcd/ca.crt",
    "--cert=/etc/kubernetes/pki/etcd/server.crt",
    "--key=/etc/kubernetes/pki/etcd/server.key",
]


def stored_encrypted(r: LinuxRuntime, namespace: str, name: str) -> bool:
    """Whether etcd holds this Secret encrypted. Only the storage prefix is examined."""
    value = etcd(
        r, [*ETCDCTL, "get", f"/registry/secrets/{namespace}/{name}", "--print-value-only"]
    )
    # Encrypted values begin with k8s:enc:PROVIDER:v1:KEY; plain ones with k8s and a NUL byte.
    return value.startswith("k8s:enc:") and not value.startswith("k8s:enc:identity")


def encryption_configured(r: LinuxRuntime) -> dict[str, Any]:
    """Whether the API server encrypts Secrets with a real provider first. Keys stay unread."""
    pods = observed(r, ["get", "pods", "-n", "kube-system", "-l", "component=kube-apiserver"])
    command = pods["items"][0]["spec"]["containers"][0]["command"]
    flag = next((c for c in command if c.startswith("--encryption-provider-config=")), "")
    if not flag:
        return {"flag": False, "ok": False}
    raw = r.guest(r.primary, ["sudo", "cat", flag.split("=", 1)[1]])
    r.require(raw)
    config = yaml.safe_load(raw.stdout)
    secrets_rule = next(
        rule for rule in config["resources"] if "secrets" in rule.get("resources", [])
    )
    first = next(iter(secrets_rule["providers"][0]))
    ready = r.kubectl(["get", "--raw=/readyz"], timeout=20).ok
    return {
        "flag": True,
        "first_provider": first,
        "ready": ready,
        "ok": first != "identity" and ready,
    }


def encryption(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("configured", "encrypted"), full)
    with suppress(*ERRORS):
        details["configured"] = encryption_configured(r)
        result["configured"] = details["configured"]["ok"]
    with suppress(*ERRORS):
        stored = {}
        for namespace in ("dispatch", "frontend"):
            for item in observed(r, ["get", "secrets", "-n", namespace])["items"]:
                name = item["metadata"]["name"]
                stored[f"{namespace}/{name}"] = stored_encrypted(r, namespace, name)
        details["encrypted"] = stored
        result["encrypted"] = bool(stored) and all(stored.values())
    if full:
        result["workflow"] = workflow()
    return result


FELIX = ["felixconfigurations.crd.projectcalico.org", "default"]


def interface_bytes(r: LinuxRuntime, guest: str, interface: str) -> int | None:
    """Bytes received plus sent on a guest interface, or None when it does not exist."""
    result = r.guest(
        guest,
        [
            "cat",
            f"/sys/class/net/{interface}/statistics/rx_bytes",
            f"/sys/class/net/{interface}/statistics/tx_bytes",
        ],
    )
    if not result.ok:
        return None
    return sum(int(value) for value in result.stdout.split())


def wireguard(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("enabled", "nodes", "traffic"), full)
    with suppress(*ERRORS):
        felix = observed(r, ["get", *FELIX])
        details["enabled"] = felix.get("spec", {}).get("wireguardEnabled")
        result["enabled"] = felix.get("spec", {}).get("wireguardEnabled") is True
    with suppress(*ERRORS):
        nodes = observed(r, ["get", "nodes"])["items"]
        keys = {
            n["metadata"]["name"]: bool(
                n["metadata"].get("annotations", {}).get("projectcalico.org/WireguardPublicKey")
            )
            for n in nodes
        }
        interfaces = {
            guest: interface_bytes(r, guest, "wireguard.cali") is not None
            for guest in (r.primary, r.worker)
        }
        details["nodes"] = {"public_keys": keys, "interfaces": interfaces}
        result["nodes"] = len(keys) == 2 and all(keys.values()) and all(interfaces.values())
    # The trusted client runs on the control plane and Dispatch on the worker, so the
    # workflow's requests cross nodes; encrypted traffic must pass through wireguard.cali.
    before = None
    with suppress(*ERRORS):
        before = interface_bytes(r, r.worker, "wireguard.cali")
    result["workflow"] = workflow()
    with suppress(*ERRORS):
        after = interface_bytes(r, r.worker, "wireguard.cali")
        details["traffic"] = {"before": before, "after": after}
        result["traffic"] = (
            result["workflow"] and before is not None and after is not None and after > before
        )
    return result


PREVIEW_REQUEST = (
    'python -c "import urllib.request; '
    "urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)\""
)


def sandbox(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("runtimeclass", "node", "sandboxed"), full)
    runtime_class: dict[str, Any] = {}
    with suppress(*ERRORS):
        runtime_class = observed(r, ["get", "runtimeclass", "gvisor"])
        selector = runtime_class.get("scheduling", {}).get("nodeSelector", {})
        details["runtimeclass"] = {"handler": runtime_class.get("handler"), "selector": selector}
        result["runtimeclass"] = runtime_class.get("handler") == "runsc" and bool(selector)
    with suppress(*ERRORS):
        # The worker's CRI must know a runsc handler, and its node must match the selector.
        info = r.guest(r.worker, ["sudo", "crictl", "info"])
        r.require(info)
        handlers = (
            json.loads(info.stdout).get("config", {}).get("containerd", {}).get("runtimes", {})
        )
        labels = observed(r, ["get", "node", "lima-" + r.worker])["metadata"].get("labels", {})
        selector = runtime_class.get("scheduling", {}).get("nodeSelector", {})
        details["node"] = {
            "handlers": sorted(handlers),
            "labels_match": selector.items() <= labels.items(),
        }
        result["node"] = (
            "runsc" in handlers and bool(selector) and selector.items() <= labels.items()
        )
    with suppress(*ERRORS):
        deployment = observed(r, ["get", "deployment", "template-preview", "-n", "untrusted"])
        spec = deployment["spec"]["template"]["spec"]
        _, kernel = exec_in(
            r, "untrusted", "deployment/template-preview", "dmesg 2>/dev/null | head -3"
        )
        served, _ = exec_in(
            r,
            "untrusted",
            "deployment/template-preview",
            PREVIEW_REQUEST,
        )
        details["sandboxed"] = {
            "runtime_class": spec.get("runtimeClassName"),
            "gvisor_kernel_messages": "gVisor" in kernel,
            "serving": served,
        }
        # Inside gVisor, dmesg shows gVisor's own start-up messages instead of the host kernel's.
        result["sandboxed"] = (
            spec.get("runtimeClassName") == "gvisor"
            and available(deployment, 1)
            and "gVisor" in kernel
            and served
        )
    if full:
        result["workflow"] = workflow()
    return result


def gvisor_workload(
    r: LinuxRuntime, namespace: str, name: str, runtime_class: str
) -> dict[str, Any]:
    """Whether a Deployment uses a runsc RuntimeClass and really runs inside gVisor."""
    handler = observed(r, ["get", "runtimeclass", runtime_class]).get("handler")
    deployment = observed(r, ["get", "deployment", name, "-n", namespace])
    used = deployment["spec"]["template"]["spec"].get("runtimeClassName")
    _, kernel = exec_in(r, namespace, f"deployment/{name}", "dmesg 2>/dev/null | head -3")
    return {
        "handler": handler,
        "runtime_class": used,
        "gvisor": "gVisor" in kernel,
        "ok": handler == "runsc"
        and used == runtime_class
        and available(deployment, 1)
        and "gVisor" in kernel,
    }


def isolate(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("sandbox", "encryption", "wireguard"), full)
    with suppress(*ERRORS):
        details["sandbox"] = gvisor_workload(r, "plugins", "plugin-runner", "sandboxed")
        result["sandbox"] = details["sandbox"]["ok"]
    with suppress(*ERRORS):
        configured = encryption_configured(r)
        stored = {
            name: stored_encrypted(r, namespace, name)
            for namespace, name in (
                ("plugins", "plugin-credentials"),
                ("dispatch", "dispatch-database"),
            )
        }
        details["encryption"] = {"configured": configured, "stored": stored}
        result["encryption"] = configured["ok"] and all(stored.values())
    before = None
    with suppress(*ERRORS):
        felix = observed(r, ["get", *FELIX])
        before = interface_bytes(r, r.worker, "wireguard.cali")
        details["wireguard_enabled"] = felix.get("spec", {}).get("wireguardEnabled")
    result["workflow"] = workflow()
    with suppress(*ERRORS):
        after = interface_bytes(r, r.worker, "wireguard.cali")
        details["wireguard_bytes"] = {"before": before, "after": after}
        result["wireguard"] = (
            details.get("wireguard_enabled") is True
            and result["workflow"]
            and before is not None
            and after is not None
            and after > before
        )
    return result


EXPORTER = "system:serviceaccount:telemetry:metrics-exporter"


def apiserver_flags(r: LinuxRuntime) -> dict[str, str]:
    pods = observed(r, ["get", "pods", "-n", "kube-system", "-l", "component=kube-apiserver"])
    command = pods["items"][0]["spec"]["containers"][0]["command"]
    return dict(item.split("=", 1) for item in command if item.startswith("--") and "=" in item)


def audit_events(r: LinuxRuntime, path: str) -> list[dict[str, Any]]:
    """Recent audit events. Callers project safe fields only; bodies are never reported."""
    tail = r.guest(r.primary, ["sudo", "tail", "-n", "4000", path], timeout=60)
    r.require(tail)
    events = []
    for line in tail.stdout.splitlines():
        with suppress(ValueError):
            events.append(json.loads(line))
    return events


def audit(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("configured", "secrets", "finding"), full)
    flags: dict[str, str] = {}
    with suppress(*ERRORS):
        flags = apiserver_flags(r)
        required = (
            "--audit-policy-file",
            "--audit-log-path",
            "--audit-log-maxage",
            "--audit-log-maxbackup",
        )
        ready = r.kubectl(["get", "--raw=/readyz"], timeout=20).ok
        details["configured"] = {flag: flag in flags for flag in required} | {"ready": ready}
        result["configured"] = ready and all(flag in flags for flag in required)
    with suppress(*ERRORS):
        events = audit_events(r, flags["--audit-log-path"])
        secret_events = [
            e for e in events if (e.get("objectRef") or {}).get("resource") == "secrets"
        ]
        exporter = [
            e
            for e in secret_events
            if e.get("user", {}).get("username") == EXPORTER
            and e["objectRef"].get("name") == "dispatch-database"
        ]
        # Secret access must be recorded, but never with a request or response body.
        with_bodies = [e for e in secret_events if "requestObject" in e or "responseObject" in e]
        reads = [e for e in secret_events if e["objectRef"].get("name") == "dispatch-database"]
        details["secrets"] = {
            "secret_events": len(secret_events),
            "exporter_reads_logged": len(exporter),
            # Who read the database Secret and with what result; identities only, never bodies.
            "database_reads": sorted(
                {
                    f"{e.get('user', {}).get('username', '')} "
                    f"{(e.get('responseStatus') or {}).get('code', '')}"
                    for e in reads
                }
            ),
            "levels": sorted({e.get("level", "") for e in secret_events}),
            "events_with_bodies": len(with_bodies),
        }
        result["secrets"] = (
            bool(exporter)
            and not with_bodies
            and all(e.get("level") == "Metadata" for e in secret_events)
        )
    with suppress(*ERRORS):
        answer = Path("finding.txt").read_text().strip()
        details["finding"] = {"written": bool(answer)}
        result["finding"] = answer == EXPORTER
    if full:
        result["workflow"] = workflow()
    return result


def immutable(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("finding", "immutable", "working"), full)
    with suppress(*ERRORS):
        recorded = json.loads((r.root / "data/tampered-pod.json").read_text())["pod"]
        answer = Path("tampered-pod.txt").read_text().strip()
        details["finding"] = {"written": bool(answer)}
        result["finding"] = answer == recorded
    with suppress(*ERRORS):
        deployment = observed(r, ["get", "deployment", "uploader", "-n", "uploads"])
        pods = [
            pod
            for pod in observed(r, ["get", "pods", "-n", "uploads", "-l", "app=uploader"])["items"]
            if not pod["metadata"].get("deletionTimestamp")
        ]
        recorded = json.loads((r.root / "data/tampered-pod.json").read_text())["pod"]
        checks = {}
        for pod in pods:
            name = pod["metadata"]["name"]
            context = pod["spec"]["containers"][0].get("securityContext", {})
            # Root inside the container must be unable to change the image's files.
            changed, _ = exec_in(r, "uploads", name, "touch /usr/local/bin/probe-change")
            checks[name] = {
                "read_only_root": context.get("readOnlyRootFilesystem") is True,
                "no_escalation": context.get("allowPrivilegeEscalation") is False,
                "root_changed_files": changed,
            }
        details["immutable"] = {"pods": checks, "tampered_pod_still_running": recorded in checks}
        result["immutable"] = (
            available(deployment, 3)
            and len(checks) == 3
            and recorded not in checks
            and all(
                c["read_only_root"] and c["no_escalation"] and not c["root_changed_files"]
                for c in checks.values()
            )
        )
    with suppress(*ERRORS):
        result["working"] = results_growing(
            r, "uploads", "deployment/uploader", "/var/cache/uploads"
        )
    if full:
        result["workflow"] = workflow()
    return result


RULES_FILE = "/etc/falco/rules.d/dockyard.yaml"


def falco_running(r: LinuxRuntime, guest: str) -> dict[str, Any]:
    active = r.guest(guest, ["systemctl", "is-active", "falco"]).stdout.strip()
    enabled = r.guest(guest, ["systemctl", "is-enabled", "falco"]).stdout.strip()
    return {"active": active, "enabled": enabled, "ok": active == "active" and enabled == "enabled"}


def falco_alerts(r: LinuxRuntime, guest: str, minutes: int = 5) -> str:
    """Recent Falco output from the systemd journal on a guest."""
    journal = r.guest(
        guest,
        [
            "sudo",
            "journalctl",
            "-u",
            "falco",
            "--since",
            f"-{minutes}min",
            "--no-pager",
            "-o",
            "cat",
        ],
    )
    r.require(journal)
    return journal.stdout


def falco(
    full: bool = True, namespace: str = "billing", workload: str = "report-sync"
) -> dict[str, Any]:
    r, result, details = begin(("running", "rule", "alert", "finding"), full)
    with suppress(*ERRORS):
        details["running"] = falco_running(r, r.worker)
        result["running"] = details["running"]["ok"]
    with suppress(*ERRORS):
        # Validate together with the default rules, whose macros custom rules usually use.
        valid = r.guest(
            r.worker,
            ["sudo", "falco", "-V", "/etc/falco/falco_rules.yaml", "-V", RULES_FILE],
            timeout=60,
        )
        details["rule"] = {"valid": valid.ok}
        result["rule"] = valid.ok
    with suppress(*ERRORS):
        # The spawner starts a shell every fifteen seconds; give one alert time to appear.
        output = ""
        for _ in range(3):
            output = falco_alerts(r, r.worker)
            if namespace in output and workload in output:
                break
            time.sleep(10)
        lines = [line for line in output.splitlines() if workload in line]
        details["alert"] = {"alert_lines_for_workload": len(lines)}
        result["alert"] = bool(lines) and any(namespace in line for line in lines)
    with suppress(*ERRORS):
        answer = Path("finding.txt").read_text().strip()
        pods = {
            pod["metadata"]["name"]
            for pod in observed(r, ["get", "pods", "-n", "billing"])["items"]
        }
        details["finding"] = {"written": bool(answer)}
        result["finding"] = answer in {"billing/report-sync"} | {f"billing/{p}" for p in pods}
    if full:
        result["workflow"] = workflow()
    return result


CATALOG = "system:serviceaccount:storefront:catalog"


def intrusion(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("finding", "revoked", "isolated", "evidence"), full)
    recorded = json.loads((r.root / "data/intrusion-pod.json").read_text())
    with suppress(*ERRORS):
        answer = Path("finding.txt").read_text().strip()
        details["finding"] = {"written": bool(answer)}
        result["finding"] = answer in {"storefront/catalog", f"storefront/{recorded['name']}"}
    with suppress(*ERRORS):
        access = {
            "get_secret": can(r, CATALOG, "get", "secrets/dispatch-database", "dispatch"),
            "list_secrets": can(r, CATALOG, "list", "secrets", "dispatch"),
        }
        details["revoked"] = access
        result["revoked"] = not any(access.values())
    with suppress(*ERRORS):
        pods = observed(r, ["get", "pods", "-n", "storefront", "-l", "app=catalog"])["items"]
        alive = {
            pod["metadata"]["uid"]: pod["status"].get("phase")
            for pod in pods
            if not pod["metadata"].get("deletionTimestamp")
        }
        details["evidence"] = {"original_pod_running": alive.get(recorded["uid"]) == "Running"}
        result["evidence"] = alive.get(recorded["uid"]) == "Running"
    with suppress(*ERRORS):
        # Reached from the compromised Pod itself: the API, the metadata service, and DNS.
        api = observed(r, ["get", "service", "kubernetes", "-n", "default"])["spec"]["clusterIP"]
        dns = observed(r, ["get", "service", "kube-dns", "-n", "kube-system"])["spec"]["clusterIP"]
        reached = connections(
            "catalog", "storefront", [(api, 443), ("169.254.169.254", 80), (dns, 53)]
        )
        details["isolated"] = {"api": reached[0], "metadata": reached[1], "dns": reached[2]}
        result["isolated"] = not any(reached)
    if full:
        result["workflow"] = workflow()
    return result


def benchmark(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("kubelet", "apiserver"), full)
    with suppress(*ERRORS):
        result["kubelet"] = kubelet_hardened(
            r,
            {
                "4.2.1": (lambda c: c["authentication"]["anonymous"]["enabled"], False),
                "4.2.2": (lambda c: c["authorization"]["mode"], "Webhook"),
            },
            details,
        )
    with suppress(*ERRORS):
        result["apiserver"] = profiling_off(r, "kube-apiserver", "1.2.15", details) and pprof_gone(
            r, details
        )
    if full:
        result["workflow"] = workflow()
    return result


def endpoints(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("metadata", "kubelet"), full)
    with suppress(*ERRORS):
        result["metadata"] = metadata_blocked(r, details)
    with suppress(*ERRORS):
        result["kubelet"] = kubelets_blocked(r, [10250], details)
    if full:
        result["workflow"] = workflow()
    return result


def binaries(full: bool = True, altered: str = "kubectl") -> dict[str, Any]:
    r, result, details = begin(("clean", "kept"), full)
    with suppress(*ERRORS):
        result["clean"], result["kept"] = staged_binaries(r, altered, details)
    if full:
        result["workflow"] = workflow()
    return result


def mission(full: bool = True) -> dict[str, Any]:
    r, result, details = begin(("benchmark", "endpoints", "binaries"), full)
    with suppress(*ERRORS):
        # A read-only port of 0 turns off the kubelet's unauthenticated read-only API.
        kubelet = kubelet_hardened(r, {"4.2.4": (lambda c: c.get("readOnlyPort", 0), 0)}, details)
        result["benchmark"] = kubelet and profiling_off(
            r, "kube-controller-manager", "1.3.2", details
        )
    with suppress(*ERRORS):
        result["endpoints"] = metadata_blocked(r, details) and kubelets_blocked(
            r, [10250, 10255], details
        )
    with suppress(*ERRORS):
        clean, kept = staged_binaries(r, "kubeadm", details)
        result["binaries"] = clean and kept
    if full:
        result["workflow"] = workflow()
    return result


def combined(parts: dict[str, tuple[dict[str, Any], tuple[str, ...]]]) -> dict[str, Any]:
    """Each exam task passes when every named outcome of its lesson observation passed."""
    result: dict[str, Any] = {}
    details: dict[str, Any] = {}
    for task, (observed_result, keys) in parts.items():
        result[task] = all(observed_result.get(key) is True for key in keys)
        details[task] = observed_result.get("_details", {})
    result["_details"] = details
    return result


def exam_a() -> dict[str, Any]:
    r = current()
    baseline = json.loads((r.root / "data/maintenance-baseline.json").read_text())
    shared: dict[str, Any] = {}
    result = combined(
        {
            "kubelet": (benchmark(False), ("kubelet",)),
            "anonymous": (anonymous(False), ("grants", "restricted", "health")),
            "rbac": (rbac(False), ("deployer",)),
            "apparmor": (apparmor(False), ("loaded", "confined", "working")),
            "encryption": (encryption(False), ("configured", "encrypted")),
            "egress": (endpoints(False), ("metadata", "kubelet")),
            "binaries": (binaries(False, altered="kubelet"), ("clean", "kept")),
            "audit": (audit(False), ("configured", "secrets", "finding")),
        }
    )
    result["preserved"] = preserved(r, baseline, shared)
    result["workflow"] = workflow()
    result["_details"]["preserved"] = shared.get("preserved")
    return result


def exam_b() -> dict[str, Any]:
    r = current()
    baseline = json.loads((r.root / "data/maintenance-baseline.json").read_text())
    shared: dict[str, Any] = {}
    # WireGuard's traffic check runs the job workflow itself; its answer is reused.
    tunnel = wireguard(False)
    result = combined(
        {
            "seccomp": (seccomp(False), ("installed", "processor", "intake")),
            "sandbox": (sandbox(False), ("runtimeclass", "node", "sandboxed")),
            "detect": (
                falco(False, namespace="storefront", workload="catalog"),
                ("running", "rule", "alert"),
            ),
            "contain": (intrusion(False), ("finding", "revoked", "isolated", "evidence")),
            "immutable": (immutable(False), ("finding", "immutable", "working")),
            "tokens": (tokens(False), ("default", "legacy", "builder")),
            "footprint": (footprint(False), ("service", "account")),
            "wireguard": (tunnel, ("enabled", "nodes", "traffic")),
        }
    )
    result["preserved"] = preserved(r, baseline, shared)
    result["workflow"] = tunnel.get("workflow") is True
    result["_details"]["preserved"] = shared.get("preserved")
    return result


def main() -> None:
    probes = {
        "benchmark": benchmark,
        "endpoints": endpoints,
        "binaries": binaries,
        "mission": mission,
        "anonymous": anonymous,
        "tokens": tokens,
        "rbac": rbac,
        "access": access,
        "footprint": footprint,
        "apparmor": apparmor,
        "seccomp": seccomp,
        "confine": confine,
        "encryption": encryption,
        "wireguard": wireguard,
        "sandbox": sandbox,
        "isolate": isolate,
        "audit": audit,
        "immutable": immutable,
        "falco": falco,
        "intrusion": intrusion,
        "exam-a": exam_a,
        "exam-b": exam_b,
    }
    try:
        print(json.dumps(probes[sys.argv[1]](), sort_keys=True))
    except (*ERRORS,) as error:
        print(json.dumps({"error": str(error)}))
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
