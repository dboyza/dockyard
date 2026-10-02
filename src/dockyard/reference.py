"""Local background primers and glossary with resolvable course links."""

from __future__ import annotations

import json
from typing import Any

from dockyard.catalog import Catalog, figure_references
from dockyard.workspace import safe_relative


def library(catalog: Catalog) -> dict[str, Any]:
    root = catalog.root / "reference"
    primers = json.loads((root / "primers.json").read_text())
    glossary = json.loads((root / "glossary.json").read_text())
    identifiers = {item["id"] for item in primers}
    if len(identifiers) != len(primers) or len({item["id"] for item in glossary}) != len(glossary):
        raise ValueError("Reference entries must have unique identifiers.")
    for item in primers:
        filename = safe_relative(item["id"] + ".md")
        item["content"] = (root / "primers").joinpath(*filename.parts).read_text()
        for figure in figure_references(item["content"]):
            if figure not in catalog.figures:
                raise ValueError(f"The {item['id']} primer embeds an unknown figure: {figure}")
    for item in glossary:
        if item["primer"] not in identifiers or not set(item["units"]) <= catalog.units.keys():
            raise ValueError("Reference links must identify available primers and course units.")
    terms = {item["id"] for item in glossary}
    for drawing in catalog.figures.values():
        if unknown := set(drawing.terms) - terms:
            names = ", ".join(sorted(unknown))
            raise ValueError(f"{drawing.id} names unknown glossary terms: {names}")
    return {"primers": primers, "glossary": sorted(glossary, key=lambda item: item["term"].lower())}
