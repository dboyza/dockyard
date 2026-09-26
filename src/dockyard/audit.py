"""Structural release checks, separate from actual runtime and teaching-quality evidence."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from dockyard.catalog import Catalog
from dockyard.models import Exam, UnitKind
from dockyard.reference import library


def curriculum(catalog: Catalog) -> dict[str, Any]:
    issues: list[str] = []
    units = catalog.units
    course = [unit for unit in units.values() if unit.kind != UnitKind.INCIDENT]
    incidents = [unit for unit in units.values() if unit.kind == UnitKind.INCIDENT]
    for module in range(1, 25):
        members = [unit for unit in course if unit.module == module]
        kinds = Counter(unit.kind for unit in members)
        if kinds != {UnitKind.LESSON: 3, UnitKind.MISSION: 1}:
            issues.append(f"Module {module}: requires three lessons and one independent mission.")
        if members and sorted(unit.order for unit in members) != [1, 2, 3, 4]:
            issues.append(f"Module {module}: course ordering must be unique positions 1 through 4.")
    if len(incidents) != 12:
        issues.append(
            f"Incident inventory: {len(incidents)} authored; 12 distinct scenarios required."
        )
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identity: str) -> None:
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
    objectives = json.loads((catalog.root / "objectives.json").read_text())["objectives"]
    known = {entry["id"] for entry in objectives}
    if len(known) != len(objectives):
        issues.append("Objective identifiers are not unique.")
    for unit in units.values():
        for objective in {
            item for item in unit.objectives if item.startswith(("cka.", "ckad."))
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
    exams_path = catalog.root / "exams.json"
    exams = (
        [Exam.model_validate(item) for item in json.loads(exams_path.read_text())]
        if exams_path.exists()
        else []
    )
    if Counter(exam.track for exam in exams) != {"CKA": 2, "CKAD": 2}:
        issues.append("Exam inventory: two original CKA and two original CKAD exams are required.")
    if len({exam.id for exam in exams}) != len(exams):
        issues.append("Exam identifiers are not unique.")
    for exam in exams:
        if exam.minutes != 120:
            issues.append(f"{exam.id}: the release default must be 120 minutes.")
        for task in exam.tasks:
            if task.unit_id not in units:
                issues.append(f"{exam.id}: unknown task {task.unit_id}.")
    library(catalog)
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
