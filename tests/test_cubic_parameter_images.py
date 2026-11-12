"""Guarded cubic extrema preserve degree loss, poles and endpoint ownership."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x, y, a, b, c, d = sp.symbols("x y a b c d", real=True)


@pytest.mark.parametrize(
    "domain", [sp.Interval(-1, 1), sp.Interval.open(-1, 1), sp.Interval.Ropen(-1, 1)]
)
def test_cubic_family(domain):
    r = fp.analyze_parameter_range(x**3 + a * x, x, (a,), domain, value=y)
    assert r.complete and r.verify() and not r.certified
    for av in [0, -3, -sp.Rational(3, 4), -1, -4, 1]:
        image = r.specialize({a: av})
        if av in (-sp.Rational(3, 4), -1):
            bound = (
                sp.Rational(1, 4) if av == -sp.Rational(3, 4) else 2 / (3 * sp.sqrt(3))
            )
            expected = sp.Interval(-bound, bound)
        else:
            bound = {0: 1, -3: 2, -4: 3, 1: 2}[av]
            reverse = av < -2
            expected = sp.Interval(
                -bound,
                bound,
                domain.right_open if reverse else domain.left_open,
                domain.left_open if reverse else domain.right_open,
            )
        assert image == expected
        for value in [-4, -1, -sp.Rational(1, 4), 0, sp.Rational(1, 4), 1, 4]:
            assert sp.simplify(
                r.condition.subs({a: av, y: value})
            ) == expected.contains(value)
    assert not replace(r, transitions=()).verify()


def test_cubic_degree_loss():
    r = fp.analyze_parameter_range(
        a * x**3 + b * x * x + c * x + d, x, (a, b, c, d), sp.Interval(-1, 1), value=y
    )
    for values in [
        (0, 0, 0, 2),
        (0, 0, 1, 0),
        (0, 1, 0, 0),
        (1, 0, -1, 0),
        (-1, 1, 0, 1),
    ]:
        subs = dict(zip((a, b, c, d), values, strict=True))
        image = r.specialize(subs)
        for value in [-2, -1, 0, 1, 2]:
            assert sp.simplify(r.condition.subs({**subs, y: value})) == image.contains(
                value
            )


def test_cubic_coefficient_pole():
    r = fp.analyze_parameter_range(x**3 / a + x, x, (a,), sp.Interval(-1, 1), value=y)
    assert r.verify() and r.specialize({a: 0}) is sp.S.EmptySet
    assert r.condition.subs({a: 0, y: 0}) is sp.false


def test_outer_output_guards():
    for head, bad in [(sp.exp, -1), (sp.tanh, 2), (sp.erf, 2), (sp.erfc, -1)]:
        r = fp.analyze_parameter_range(
            head(x**3 + a * x), x, (a,), sp.Interval(-1, 1), value=y
        )
        assert r.verify() and r.condition.subs({a: 0, y: bad}) is sp.false


def test_cubic_dispatch():
    condition = fp.range(x**3 + a * x, x, y, domain=sp.Interval(-1, 1))
    assert condition.subs({a: 0, y: 1}) is sp.true
    assert sp.simplify(condition.subs({a: -1, y: 1})) is sp.false


def test_guarded_output_sets():
    condition = fp.range(sp.exp(x * x + a * x), x, y, domain=sp.Interval.open(-1, 1))
    assert fp.condition_to_real_set(condition.subs(a, 0), y) == sp.Interval.Ropen(
        1, sp.E
    )
    assert condition.subs({a: 0, y: -1}) is sp.false
