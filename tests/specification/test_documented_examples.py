"""Executable specification for every example in the property reference."""

from __future__ import annotations

import sympy as sp

import funcprops as fp
from examples.property_examples import EXAMPLES, STATISTICAL_SPECIAL_FUNCTION_EXAMPLES


def test_every_public_property_has_a_documented_example():
    documented = {case.property_name for case in EXAMPLES}
    assert documented == set(fp.api.__all__)


def test_documented_examples_have_unique_ids():
    ids = [case.example_id for case in EXAMPLES]
    assert len(ids) == len(set(ids))


def test_every_documented_example_executes_and_matches_its_expectation():
    x, y = sp.symbols("x y", real=True)
    for case in EXAMPLES:
        namespace = {"fp": fp, "sp": sp, "x": x, "y": y}
        exec(case.code, namespace)
        assert eval(case.check, namespace), case.example_id


def test_statistical_special_function_examples_execute_and_match_expectations():
    x, y = sp.symbols("x y", real=True)
    for case in STATISTICAL_SPECIAL_FUNCTION_EXAMPLES:
        namespace = {"fp": fp, "sp": sp, "x": x, "y": y}
        exec(case.code, namespace)
        assert eval(case.check, namespace), case.example_id


def test_statistical_special_function_documentation_contains_canonical_examples():
    from pathlib import Path

    page = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "statistical_special_functions.md"
    )
    text = page.read_text()
    for case in STATISTICAL_SPECIAL_FUNCTION_EXAMPLES:
        assert f"<!-- example-id: {case.example_id} -->" in text
        assert case.expected in text
