from __future__ import annotations

import ast
from pathlib import Path

import sympy as sp

from funcprops.exactness import certify_equal, certify_identity_equal, certify_zero


def test_certified_zero_is_three_valued():
    x = sp.symbols("x")
    assert certify_zero(sp.S.Zero) is True
    assert certify_zero(sp.S.One) is False
    assert certify_zero(x) is None


def test_certified_equality_distinguishes_identity_and_assumptions():
    x, a = sp.symbols("x a", real=True)
    assert certify_equal(x, a, assumptions=sp.Eq(x, a)) is True
    assert certify_equal(x, a) is None
    assert certify_identity_equal((x + 1) ** 2, x**2 + 2 * x + 1) is True


def test_proof_code_avoids_simplify_zero_comparisons():
    root = Path(__file__).parents[1] / "src" / "funcprops"
    offenders = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            values = [node.left, *node.comparators]
            has_zero = any(isinstance(v, ast.Constant) and v.value == 0 for v in values)
            if not has_zero:
                continue
            if any(
                isinstance(v, ast.Call)
                and isinstance(v.func, ast.Attribute)
                and v.func.attr == "simplify"
                for v in values
            ):
                offenders.append(f"{path.relative_to(root)}:{node.lineno}")
    assert offenders == []
