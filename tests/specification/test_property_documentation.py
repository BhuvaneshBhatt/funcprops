"""Structural specification for the property reference documentation."""

from __future__ import annotations

from pathlib import Path

import funcprops as api
from examples.property_examples import examples_for

PUBLIC_QUERIES = {name for name, *_ in api.properties()}

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "properties"
REQUIRED = (
    "## Mathematical definition",
    "## API and return values",
    "## Domains, assumptions, and parameters",
    "## Executable examples",
    "## Applications",
    "## How funcprops proves it",
    "## Known limitations",
    "## Related properties",
)


def test_every_public_property_has_one_canonical_page():
    expected = {f"{name.removeprefix('function_')}.md" for name in PUBLIC_QUERIES}
    actual = {path.name for path in DOCS.glob("*.md") if path.name != "index.md"}
    assert actual == expected


def test_property_pages_follow_the_common_reference_template():
    for name in PUBLIC_QUERIES:
        text = (DOCS / f"{name.removeprefix('function_')}.md").read_text()
        for heading in REQUIRED:
            assert heading in text, (name, heading)
        assert "UNKNOWN" in text
        assert "Application:" in text
        for case in examples_for(name):
            assert f"<!-- example-id: {case.example_id} -->" in text
            assert case.expected in text


def test_property_index_links_every_public_query():
    text = (DOCS / "index.md").read_text()
    for name in PUBLIC_QUERIES:
        assert f"`{name}`" in text
        assert f"({name.removeprefix('function_')}.md)" in text
