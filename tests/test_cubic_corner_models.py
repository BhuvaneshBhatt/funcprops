"""Exact derivative-root oracles exercise low-dimensional cubic degree strata."""

from itertools import product

import pytest
import sympy as sp

import funcprops as fp

x, y, a, b, c = sp.symbols("x y a b c", real=True)


@pytest.mark.parametrize(
    "domain", [sp.Interval(-1, 1), sp.Interval.open(-1, 1), sp.Interval.Ropen(-1, 1)]
)
def test_coefficient_corners(domain):
    family = fp.analyze_parameter_range(
        a * x**3 + b * x * x + c * x, x, (a, b, c), domain, value=y
    )
    assert family.verify()
    for av, bv, cv in product((-1, 0, 1), repeat=3):
        polynomial = sp.Poly(av * x**3 + bv * x * x + cv * x, x)
        points = [
            (domain.start, not domain.left_open),
            (domain.end, not domain.right_open),
            (sp.S.Zero, True),
        ]
        if polynomial.degree() > 0:
            points.extend(
                (p, True)
                for p in polynomial.diff().real_roots()
                if domain.contains(p) is sp.true
            )
        sites = [(sp.simplify(polynomial.eval(p)), owned) for p, owned in points]
        low, high = min(v for v, _ in sites), max(v for v, _ in sites)
        expected = sp.Interval(
            low,
            high,
            not any(v == low and own for v, own in sites),
            not any(v == high and own for v, own in sites),
        )
        for value in (-2, -1, -sp.Rational(1, 4), 0, sp.Rational(1, 4), 1, 2):
            actual = sp.simplify(family.condition.subs({a: av, b: bv, c: cv, y: value}))
            assert actual == expected.contains(value), (av, bv, cv, value)
