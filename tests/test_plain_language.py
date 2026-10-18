"""Learner-facing text stays short, plain, and consistently spelled."""

import json
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

from dockyard.catalog import CONTENT, YAML_LOADER, Catalog

ROOT = CONTENT.parents[2]
MAX_WORDS = 30
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
CODE_SPAN = re.compile(r"`[^`]*`")
FENCE = re.compile(r"```.*?```", re.DOTALL)
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
# Learner-facing text avoids these words and spellings; the exam objectives quote official wording.
AVOIDED = re.compile(
    r"\b(utili[sz]e[sd]?|leverag(e|es|ed|ing)|facilitat(e|es|ed|ing)|subsequently|prior to|"
    r"in order to|e\.g\.|i\.e\.|(?<![/\w])etc\.)"
    r"|—"
    r"|behaviour|authoris|recognis|initialis|neighbour|\blabelled(?!by)",
    re.IGNORECASE,
)
FILES_WITH_OFFICIAL_WORDING = {"objectives.json"}
DOCUMENTS = ["README.md", "docs/user-guide.md", "docs/platforms.md", "docs/terminals.md"]


def strings(node: object) -> Iterator[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from strings(item)
    elif isinstance(node, dict):
        for value in node.values():
            yield from strings(value)


def sentences(text: str) -> Iterator[str]:
    yield from SENTENCE_END.split(CODE_SPAN.sub("code", text))


def markdown_sentences(path: Path) -> Iterator[str]:
    text = LINK.sub(r"\1", FENCE.sub(" ", path.read_text()))
    for line in text.splitlines():
        if line.strip() and not line.startswith(("#", "|")):
            yield from sentences(line)


def unit_text() -> Iterator[tuple[str, str]]:
    for unit in Catalog().units.values():
        yield unit.id, unit.summary
        for outcome in unit.outcomes:
            yield unit.id, outcome
        yield unit.id, unit.prediction.question
        yield unit.id, unit.prediction.explanation
        for hint in unit.hints:
            yield unit.id, hint
        for note in (*unit.alternatives, *unit.failure_modes):
            yield unit.id, note
        for check in unit.checks:
            yield unit.id, check.title
            yield unit.id, check.explanation
            yield unit.id, check.diagnostic
            for case in check.cases:
                yield unit.id, case.diagnostic


def content_text() -> Iterator[tuple[str, str]]:
    for name in ("figures", "modules", "exams", "placement", "reference/glossary"):
        path = CONTENT / f"{name}.json"
        for text in strings(json.loads(path.read_text())):
            yield path.name, text
    shared = yaml.load((CONTENT / "diagnostics.yaml").read_text(), Loader=YAML_LOADER)  # noqa: S506
    for text in strings(shared):
        yield "diagnostics.yaml", text
    for unit_id, text in unit_text():
        yield unit_id, text
    for path in sorted(CONTENT.rglob("*.md")):
        for sentence in markdown_sentences(path):
            yield str(path.relative_to(CONTENT)), sentence


def test_sentences_stay_short():
    long = [
        f"{where}: {sentence}"
        for where, text in content_text()
        for sentence in sentences(text)
        if len(sentence.split()) > MAX_WORDS
    ]
    for document in DOCUMENTS:
        path = ROOT / document
        long += [
            f"{document}: {sentence}"
            for sentence in markdown_sentences(path)
            if len(sentence.split()) > MAX_WORDS
        ]
    assert not long, f"Split these into sentences of at most {MAX_WORDS} words:\n" + "\n".join(
        long[:20]
    )


@pytest.mark.parametrize("document", DOCUMENTS)
def test_documents_exist(document):
    assert (ROOT / document).exists()


def test_filler_words_and_british_spellings_are_avoided():
    found = []
    for where, text in content_text():
        if where not in FILES_WITH_OFFICIAL_WORDING and (match := AVOIDED.search(text)):
            found.append(f"{where}: {match.group(0)!r} in {text[:80]!r}")
    for document in DOCUMENTS:
        for sentence in markdown_sentences(ROOT / document):
            if match := AVOIDED.search(sentence):
                found.append(f"{document}: {match.group(0)!r} in {sentence[:80]!r}")
    assert not found, "\n".join(found[:20])
