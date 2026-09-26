"""Versioned curriculum and observed assessment contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{1,79}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Runtime(StrEnum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    LINUX = "linux"


class UnitKind(StrEnum):
    LESSON = "lesson"
    MISSION = "mission"
    INCIDENT = "incident"


class CheckStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    STALE = "stale"


class Prediction(Contract):
    question: str
    options: list[str] = Field(min_length=2)
    correct: int = Field(ge=0)
    explanation: str

    @model_validator(mode="after")
    def valid_answer(self) -> Prediction:
        if self.correct >= len(self.options):
            raise ValueError("Prediction answer must refer to an existing option.")
        return self


class Command(Contract):
    """Packaged operations only; never accepted as a browser request body."""

    args: list[str] = Field(min_length=1)
    timeout: float = Field(default=30, gt=0, le=900)
    stdin: str | None = None
    allowed_exit_codes: list[int] = Field(default_factory=lambda: [0])


class Criterion(Contract):
    id: Identifier
    title: str
    explanation: str
    command: Command
    expectation: Literal["contains", "equals", "matches", "json", "absent"] = "contains"
    expected: str
    json_path: list[str | int] = Field(default_factory=list)
    diagnostic: str
    points: int = Field(default=1, ge=1)


class Unit(Contract):
    id: Identifier
    revision: int = Field(default=1, ge=1)
    module: int = Field(ge=1, le=24)
    order: int = Field(ge=1)
    title: str
    summary: str
    kind: UnitKind = UnitKind.LESSON
    runtime: Runtime
    minutes: int = Field(ge=5)
    outcomes: list[str] = Field(min_length=1)
    prerequisites: list[Identifier] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    concept: str
    brief: str
    debrief: str
    prediction: Prediction
    hints: list[str] = Field(min_length=3)
    sources: list[str] = Field(min_length=1)
    starter: dict[str, str]
    reference: dict[str, str]
    prepare: list[Command] = Field(default_factory=list)
    checks: list[Criterion] = Field(min_length=1)
    capabilities: list[str] = Field(default_factory=list)
    checkpoint: str | None = None

    @model_validator(mode="after")
    def unique_checks(self) -> Unit:
        if len({check.id for check in self.checks}) != len(self.checks):
            raise ValueError("Criterion identifiers must be unique within a unit.")
        return self


class Evidence(Contract):
    criterion: str
    title: str
    status: CheckStatus
    expected: str
    observed: str
    diagnostic: str
    points: int = 1


class Assessment(Contract):
    id: str
    unit_id: str
    revision: int
    lab_id: str
    status: CheckStatus
    started_at: str
    finished_at: str
    file_digest: str
    evidence: list[Evidence]
    independent: bool
    hints_used: int = Field(default=0, ge=0)
    reference_revealed: bool = False


class Lab(Contract):
    id: str
    unit_id: str
    revision: int
    runtime: Runtime
    state: Literal[
        "absent", "preparing", "ready", "checking", "stopping", "stopped", "failed", "cleaning"
    ]
    workspace: str
    created_at: str
    updated_at: str
    resources: dict[str, str] = Field(default_factory=dict)
    error: str | None = None


class ExamTask(Contract):
    unit_id: str
    weight: int = Field(ge=1)


class Exam(Contract):
    id: Identifier
    title: str
    track: Literal["CKA", "CKAD"]
    minutes: int = 120
    tasks: list[ExamTask] = Field(min_length=1)
    reference_policy: str
