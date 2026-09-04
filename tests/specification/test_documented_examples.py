"""Executable specification for every example in the property reference."""

from __future__ import annotations

import sympy as sp

import funcprops as fp
from examples.property_examples import EXAMPLES


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
