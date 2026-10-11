"""Structural release checks, separate from actual runtime and teaching-quality evidence."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from dockyard.catalog import Catalog, figure_references
from dockyard.models import UnitKind
from dockyard.reference import library


def curriculum(catalog: Catalog) -> dict[str, Any]:
    issues: list[str] = []
    units = catalog.units
    course = [unit for unit in units.values() if unit.kind in {UnitKind.LESSON, UnitKind.MISSION}]
    incidents = [unit for unit in units.values() if unit.kind == UnitKind.INCIDENT]
    for module in sorted(item["id"] for item in catalog.modules):
        members = sorted(
            (unit for unit in course if unit.module == module), key=lambda unit: unit.order
        )
        kinds = Counter(unit.kind for unit in members)
        # Modules teach with three or more lessons; focused exercises close objective gaps.
        if kinds[UnitKind.LESSON] < 3 or kinds[UnitKind.MISSION] != 1:
            issues.append(
                f"Module {module}: requires at least three lessons and one independent mission."
            )
        if members and (
            [unit.order for unit in members] != list(range(1, len(members) + 1))
            or members[-1].kind != UnitKind.MISSION
        ):
            issues.append(
                f"Module {module}: units must take positions 1 onward, with the mission last."
            )
    if len(incidents) != 12:
        issues.append(
            f"Incident inventory: {len(incidents)} authored; 12 distinct scenarios required."
        )
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identity: str) -> None:
        if identity not in units:
            issues.append(f"A prerequisite names {identity}, which does not exist.")
            return
        if identity in visiting:
            issues.append(f"Prerequisite cycle reaches {identity}.")
            return
        if identity in visited:
            return
        visiting.add(identity)
        for parent in units[identity].prerequisites:
            visit(parent)
        visiting.remove(identity)
        visited.add(identity)

    for unit in units.values():
        visit(unit.id)
        if not unit.starter_failure_checks:
            issues.append(f"{unit.id}: no declared intended starter failure.")
        if "run.sh" not in unit.reference:
            issues.append(f"{unit.id}: no executable reference entry point.")
        if not unit.alternatives or not unit.failure_modes:
            issues.append(f"{unit.id}: acceptable alternatives and failure modes are required.")
        if unit.runtime == "linux" and unit.nodes not in {2, 3, 4}:
            issues.append(f"{unit.id}: unsupported native node topology.")
        if unit.kind == UnitKind.LESSON and not figure_references(unit.concept):
            issues.append(f"{unit.id}: a lesson must explain its central idea with a figure.")
        for check in unit.checks:
            # A learner may check straight after starting a service; give it a moment.
            args = check.command.args
            if args[0] == "curl" and not {"--retry", "--retry-all-errors"} <= set(args):
                issues.append(f"{unit.id}/{check.id}: a request check must retry briefly.")
    objectives = json.loads((catalog.root / "objectives.json").read_text())["objectives"]
    known = {entry["id"] for entry in objectives}
    if len(known) != len(objectives):
        issues.append("Objective identifiers are not unique.")
    for unit in units.values():
        for objective in {
            item for item in unit.objectives if item.startswith(("cka.", "ckad.", "cks."))
        } - known:
            issues.append(f"{unit.id}: unknown objective {objective}.")
    for objective in objectives:
        for role in ("explained_by", "practiced_by", "assessed_by"):
            mapped = objective.get(role, [])
            if not mapped:
                issues.append(f"{objective['id']}: {role} is empty.")
            for identity in mapped:
                if identity not in units:
                    issues.append(f"{objective['id']}: {role} points to missing {identity}.")
                elif role == "assessed_by" and units[identity].kind == UnitKind.LESSON:
                    issues.append(
                        f"{objective['id']}: {identity} is guided rather than independent."
                    )
    exams = list(catalog.exams.values())
    if Counter(exam.track for exam in exams) != {"CKA": 2, "CKAD": 2, "CKS": 2}:
        issues.append("Exam inventory: each of CKA, CKAD, and CKS needs two original exams.")
    if len({exam.id for exam in exams}) != len(exams):
        issues.append("Exam identifiers are not unique.")
    for exam in exams:
        if exam.minutes != 120:
            issues.append(f"{exam.id}: the release default must be 120 minutes.")
        exam_unit = units.get(exam.unit_id)
        if exam_unit is None or exam_unit.kind != UnitKind.EXAM:
            issues.append(f"{exam.id}: requires its own original exam environment.")
            continue
        assigned = [criterion for task in exam.tasks for criterion in task.criteria]
        if len(set(assigned)) != len(assigned) or set(assigned) != {c.id for c in exam_unit.checks}:
            issues.append(f"{exam.id}: tasks must assign every assessment criterion exactly once.")
        for task in exam.tasks:
            if any(identity not in units for identity in task.remediation):
                issues.append(f"{exam.id}/{task.id}: unknown remediation unit.")
    for primer in library(catalog)["primers"]:
        if not figure_references(primer["content"]):
            issues.append(
                f"{primer['id']} primer: a primer must explain its central idea with a figure."
            )
    return {
        "status": "pass" if not issues else "incomplete",
        "course_units": len(course),
        "incidents": len(incidents),
        "exams": len(exams),
        "objectives": len(objectives),
        "issues": issues,
        "evidence_boundary": (
            "Structural checks do not establish runtime success, "
            "distinct task design, or learning effectiveness."
        ),
    }
