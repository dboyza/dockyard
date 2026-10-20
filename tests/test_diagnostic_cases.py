"""Each recognisable failure gets its own advice, and reconciliation evidence is observed."""

import threading

import pytest

from dockyard.catalog import Catalog
from dockyard.models import CheckStatus, Command, Criterion, DiagnosticCase, Lab, Runtime
from dockyard.probes import kubernetes
from dockyard.process import ProcessResult
from dockyard.service import Service


def lab(tmp_path) -> Lab:
    return Lab(
        id="0123456789abcdef0123456789abcdef",
        unit_id="m02-dockerfile",
        revision=1,
        runtime=Runtime.DOCKER,
        state="ready",
        workspace=str(tmp_path),
        created_at="now",
        updated_at="now",
        resources={"port": "41000"},
    )


def evaluate(tmp_path, criterion: Criterion, returncode: int, stdout: str, stderr: str = ""):
    observation = ProcessResult(
        args=tuple(criterion.command.args),
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        duration=0.1,
    )
    return Service(tmp_path)._criterion(
        criterion,
        lab(tmp_path),
        threading.Event(),
        {criterion.command.model_dump_json(): observation},
    )


def inspect_check(**overrides) -> Criterion:
    fields = {
        "id": "published-port",
        "title": "Published",
        "explanation": "Read the binding",
        "command": Command(args=["docker", "inspect", "{{container}}"]),
        "expectation": "json",
        "json_path": ["0", "HostConfig", "PortBindings", "8080/tcp", "0", "HostPort"],
        "expected": "{{port}}",
        "diagnostic": "general advice",
        "cases": [
            DiagnosticCase(observed="no such object: {{container}}$", diagnostic="missing"),
            DiagnosticCase(observed=r"^\(absent\) ", diagnostic="not published"),
        ],
    }
    return Criterion(**(fields | overrides))


def test_the_first_matching_case_replaces_the_general_diagnostic(tmp_path):
    evidence = evaluate(
        tmp_path, inspect_check(), 1, "[]", "error: no such object: dockyard-0123456789ab"
    )
    assert evidence.status == CheckStatus.FAIL
    assert evidence.diagnostic == "missing"


def test_placeholders_in_a_case_match_literally(tmp_path):
    # Another lab's container, or a name that merely starts with this one, is not this lab's.
    evidence = evaluate(
        tmp_path, inspect_check(), 1, "[]", "error: no such object: dockyard-0123456789ab-registry"
    )
    assert evidence.diagnostic == "general advice"


def test_an_absent_field_is_named_and_the_document_kept_as_details(tmp_path):
    document = '[{"HostConfig": {"PortBindings": {}}}]'
    evidence = evaluate(tmp_path, inspect_check(), 0, document)
    assert evidence.status == CheckStatus.FAIL
    assert evidence.observed == "(absent) 0.HostConfig.PortBindings.8080/tcp.0.HostPort"
    assert evidence.details == document
    assert evidence.diagnostic == "not published"


def test_diagnostics_name_real_values_but_keep_shell_variables_in_commands(tmp_path):
    case = DiagnosticCase(
        observed="no such object",
        diagnostic='No container named {{container}}; run docker logs "$DOCKYARD_CONTAINER".',
    )
    evidence = evaluate(tmp_path, inspect_check(cases=[case]), 1, "[]", "no such object: x")
    assert evidence.diagnostic == (
        'No container named dockyard-0123456789ab; run docker logs "$DOCKYARD_CONTAINER".'
    )


def test_the_shared_missing_container_advice_names_the_real_container(tmp_path):
    criterion = next(
        item
        for item in Catalog().get("m01-processes").checks
        if any("no such" in case.observed for case in item.cases)
    )
    evidence = evaluate(
        tmp_path, criterion, 1, "[]", "Error: No such object: dockyard-0123456789ab"
    )
    assert "named dockyard-0123456789ab, the name in $DOCKYARD_CONTAINER" in evidence.diagnostic
    assert "{{" not in evidence.diagnostic


def test_unmatched_failures_and_passes_keep_the_general_diagnostic(tmp_path):
    wrong = '[{"HostConfig": {"PortBindings": {"8080/tcp": [{"HostPort": "9"}]}}}]'
    assert evaluate(tmp_path, inspect_check(), 0, wrong).diagnostic == "general advice"
    right = '[{"HostConfig": {"PortBindings": {"8080/tcp": [{"HostPort": "41000"}]}}}]'
    passed = evaluate(
        tmp_path, inspect_check(cases=[DiagnosticCase(observed=".", diagnostic="x")]), 0, right
    )
    assert passed.status == CheckStatus.PASS
    assert passed.diagnostic == "general advice"


def test_runtime_cases_follow_each_criterions_own_cases():
    unit = Catalog().get("m02-dockerfile")
    response = next(check for check in unit.checks if check.id == "application-response")
    patterns = [case.observed for case in response.cases]
    assert patterns[0] == "Empty reply from server"
    assert any("no such (object|container)" in pattern for pattern in patterns[1:])
    kubernetes_unit = Catalog().get("m07-reconciliation")
    assert all(not check.cases for check in kubernetes_unit.checks)


def event(reason: str, message: str, uid: str = "rs-1") -> dict[str, object]:
    return {
        "reason": reason,
        "message": message,
        "involvedObject": {"kind": "ReplicaSet", "uid": uid},
    }


def pods(*names: str) -> list[dict[str, object]]:
    return [{"metadata": {"name": name}} for name in names]


@pytest.mark.parametrize(
    ("events", "current", "replaced"),
    [
        # Scaling from zero creates two Pods and replaces nothing.
        (
            [
                event("SuccessfulCreate", "Created pod: a"),
                event("SuccessfulCreate", "Created pod: b"),
            ],
            ("a", "b"),
            False,
        ),
        # A deleted Pod and its replacement.
        (
            [
                event("SuccessfulCreate", "Created pod: a"),
                event("SuccessfulCreate", "Created pod: b"),
                event("SuccessfulCreate", "Created pod: c"),
            ],
            ("b", "c"),
            True,
        ),
        # Scaling down and up again is the ReplicaSet deleting a Pod itself.
        (
            [
                event("SuccessfulCreate", "Created pod: a"),
                event("SuccessfulCreate", "Created pod: b"),
                event("SuccessfulDelete", "Deleted pod: a"),
                event("SuccessfulCreate", "Created pod: c"),
            ],
            ("b", "c"),
            False,
        ),
        # Another Deployment's ReplicaSet does not count.
        (
            [
                event("SuccessfulCreate", "Created pod: x", uid="other"),
                event("SuccessfulCreate", "Created pod: b"),
                event("SuccessfulCreate", "Created pod: c"),
            ],
            ("b", "c"),
            False,
        ),
        # A replacement only counts once both copies are back.
        (
            [
                event("SuccessfulCreate", "Created pod: a"),
                event("SuccessfulCreate", "Created pod: b"),
            ],
            ("b",),
            False,
        ),
    ],
)
def test_replacement_needs_a_pod_removed_by_someone_other_than_its_replicaset(
    monkeypatch, events, current, replaced
):
    monkeypatch.setattr(kubernetes, "get", lambda kind, *args, **kwargs: {"items": events})
    observed, details = kubernetes.replacement({"rs-1"}, pods(*current))
    assert observed is replaced
    assert details["replacement"]["current_pods"] == sorted(current)
