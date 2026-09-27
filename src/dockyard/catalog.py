"""Load the canonical authored curriculum and reject broken contracts at startup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from dockyard.models import Exam, Unit
from dockyard.workspace import safe_relative

CONTENT = Path(__file__).parent / "content"


class Catalog:
    def __init__(self, root: Path = CONTENT):
        self.root = root
        self.modules: list[dict[str, Any]] = json.loads((root / "modules.json").read_text())
        self.units: dict[str, Unit] = {}
        for path in sorted((root / "units").glob("*/unit.yaml")):
            raw = yaml.safe_load(path.read_text())
            for field in ("concept", "brief", "debrief"):
                relative = safe_relative(raw[field])
                raw[field] = path.parent.joinpath(*relative.parts).read_text()
            for field in ("starter", "reference"):
                folder = path.parent / field
                inherited: dict[str, str] = {}
                if field == "starter" and raw.get("checkpoint"):
                    checkpoint = root / "checkpoints" / str(safe_relative(raw["checkpoint"]))
                    if not checkpoint.is_dir():
                        raise ValueError(f"Unknown checkpoint: {raw['checkpoint']}")
                    inherited = {
                        file.relative_to(checkpoint).as_posix(): file.read_text()
                        for file in sorted(checkpoint.rglob("*"))
                        if file.is_file()
                    }
                raw[field] = {
                    **inherited,
                    **{
                        file.relative_to(folder).as_posix(): file.read_text()
                        for file in sorted(folder.rglob("*"))
                        if file.is_file()
                    },
                }
            unit = Unit.model_validate(raw)
            if unit.id in self.units:
                raise ValueError(f"Duplicate unit: {unit.id}")
            for file_name in [*unit.starter, *unit.reference]:
                safe_relative(file_name)
            self.units[unit.id] = unit
        exam_path = root / "exams.json"
        self.exams: dict[str, Exam] = {}
        if exam_path.exists():
            for item in json.loads(exam_path.read_text()):
                exam = Exam.model_validate(item)
                if exam.id in self.exams:
                    raise ValueError("Duplicate exam identity.")
                self.exams[exam.id] = exam
        placement = root / "placement.json"
        self.placement: list[dict[str, str]] = (
            json.loads(placement.read_text()) if placement.exists() else []
        )
        for benchmark in self.placement:
            for key in ("unit_id", "start_unit"):
                if benchmark[key] not in self.units:
                    raise ValueError("Placement points to an unknown unit.")
        for unit in self.units.values():
            for prerequisite in unit.prerequisites:
                if prerequisite not in self.units:
                    raise ValueError(f"{unit.id} has an unknown prerequisite: {prerequisite}")

    def get(self, unit_id: str) -> Unit:
        try:
            return self.units[unit_id]
        except KeyError as error:
            raise ValueError("That course unit does not exist.") from error

    def index(self) -> dict[str, Any]:
        return {
            "modules": self.modules,
            "placement": self.placement,
            "exams": [exam.model_dump(mode="json") for exam in self.exams.values()],
            "units": [
                {
                    **unit.model_dump(
                        mode="json",
                        exclude={
                            "reference",
                            "starter",
                            "checks",
                            "prepare",
                            "concept",
                            "debrief",
                            "hints",
                        },
                    ),
                    "search_text": " ".join(
                        f"{unit.id} {unit.title} {unit.summary} {' '.join(unit.outcomes)} "
                        f"{unit.concept} {unit.brief}".lower().split()
                    ),
                }
                for unit in sorted(self.units.values(), key=lambda item: (item.module, item.order))
            ],
        }
