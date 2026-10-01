"""Every public property query must have direct behavioral test coverage."""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

import funcprops.api as api

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "tests"


def _direct_property_calls(path: Path) -> Counter[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "funcprops" or node.module.startswith("funcprops."):
                for alias in node.names:
                    if alias.name in api.__all__:
                        imported[alias.asname or alias.name] = alias.name

    calls: Counter[str] = Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Attribute) and target.attr in api.__all__:
            calls[target.attr] += 1
        elif isinstance(target, ast.Name) and target.id in imported:
            calls[imported[target.id]] += 1
    return calls


def test_every_public_property_query_has_direct_behavioral_coverage():
    counts: Counter[str] = Counter()
    for path in TESTS.rglob("test_*.py"):
        if path == Path(__file__):
            continue
        counts.update(_direct_property_calls(path))

    missing = sorted(name for name in api.__all__ if counts[name] == 0)
    assert missing == []
