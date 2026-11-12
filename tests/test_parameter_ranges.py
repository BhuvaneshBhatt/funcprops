"""Parameter strata are checked by image membership, including boundary ownership."""

from dataclasses import replace
from itertools import product

import pytest
import sympy as sp

import funcprops as fp

x, y, a, b, c = sp.symbols("x y a b c", real=True)


def test_quadratic_family():
    result = fp.analyze_parameter_range(
        x * x + a * x, x, (a,), sp.Interval(-1, 1), value=y, certified=True
    )
    assert result.complete and result.certified and result.verify()
    assert fp.verify_certificate(result, expr=x * x + a * x, var=x)
    assert set(result.transitions) == {
        sp.Eq(-2 * a, 0),
        sp.Eq(a - 2, 0),
        sp.Eq(a + 2, 0),
    }
    for av, expected in [
        (-3, sp.Interval(-2, 4)),
        (-2, sp.Interval(-1, 3)),
        (0, sp.Interval(0, 1)),
        (2, sp.Interval(-1, 3)),
        (3, sp.Interval(-2, 4)),
    ]:
        assert result.specialize({a: av}) == expected
        for v in (-3, -2, -1, 0, 1, 2, 3, 4, 5):
            assert result.condition.subs({a: av, y: v}) == expected.contains(v)
    assert not fp.analyze_parameter_range(
        x * x + a * x, x, (a,), sp.Interval(-1, 1)
    ).certified


@pytest.mark.parametrize(
    "D",
    [
        sp.Interval(-1, 1),
        sp.Interval.open(-1, 1),
        sp.Interval.Ropen(-1, 1),
        sp.FiniteSet(-1, 0, 1),
    ],
)
def test_degree_loss(D):
    result = fp.analyze_parameter_range(a * x * x + b * x + c, x, (a, b, c), D, value=y)
    assert result.verify()
    for av, bv, cv in product((-1, 0, 1), repeat=3):
        expression = av * x * x + bv * x + cv
        image = fp.condition_to_real_set(fp.range(expression, x, y, domain=D), y)
        assert result.specialize({a: av, b: bv, c: cv}) == image
        for value in (-3, -2, -1, 0, 1, 2, 3):
            assert result.condition.subs(
                {a: av, b: bv, c: cv, y: value}
            ) == image.contains(value)


@pytest.mark.parametrize(
    "head",
    [
        sp.exp,
        sp.log,
        sp.sinh,
        sp.asinh,
        sp.tanh,
        sp.atanh,
        sp.atan,
        sp.asin,
        sp.acos,
        sp.acosh,
        sp.erf,
        sp.erfc,
    ],
)
def test_outer_branches(head):
    result = fp.analyze_parameter_range(
        head(x * x + a * x), x, (a,), sp.Interval(-1, 1), value=y
    )
    assert result.verify()
    for av in (-3, 0, 3):
        inner = fp.analyze_parameter_range(
            x * x + a * x, x, (a,), sp.Interval(-1, 1)
        ).specialize({a: av})
        from funcprops.real_analysis.image_rules import exact_image

        assert result.specialize({a: av}) == exact_image(head(x), x, inner)


def test_open_vertex_and_coefficient_pole():
    result = fp.analyze_parameter_range(
        sp.exp(x * x + a * x), x, (a,), sp.Interval.open(-1, 1), value=y
    )
    assert result.specialize({a: 0}) == sp.Interval.Ropen(1, sp.E)
    assert result.specialize({a: 2}) == sp.Interval.open(sp.exp(-1), sp.exp(3))
    result = fp.analyze_parameter_range(
        x * x / a, x, (a,), sp.Interval.open(-1, 1), value=y
    )
    assert result.verify() and result.specialize({a: 0}) is sp.S.EmptySet
    assert result.specialize({a: 1}) == sp.Interval.Ropen(0, 1)
    assert result.specialize({a: -1}) == sp.Interval.Lopen(-1, 0)
    assert result.condition.subs({a: 0, y: 1}) is sp.false


def test_parameter_guard():
    result = fp.analyze_parameter_range(
        sp.exp(x * x + a * x),
        x,
        (a,),
        sp.Interval(-1, 1),
        value=y,
        parameter_domain=a >= 0,
    )
    assert result.specialize({a: -1}) is sp.S.EmptySet
    assert result.specialize({a: 0}) == sp.Interval(1, sp.E)
    assert (
        fp.parameter_range(x * x + a * x, x, (a,), sp.Interval(-1, 1), value=y)
        == fp.analyze_parameter_range(
            x * x + a * x, x, (a,), sp.Interval(-1, 1), value=y
        ).condition
    )


def test_parameter_mutations():
    r = fp.analyze_parameter_range(
        x * x + a * x, x, (a,), sp.Interval.open(-1, 1), value=y
    )
    for bad in (
        replace(r, condition=sp.true),
        replace(r, transitions=()),
        replace(r, domain=sp.Interval(-1, 1)),
        replace(r, expression=x * x + a * x + 1),
        replace(r, parameters=(b,)),
        replace(r, complete=False),
    ):
        assert not bad.verify()


def test_declines():
    held = sp.Add(
        x * x,
        sp.Mul(0, sp.Pow(x - a, -1, evaluate=False), evaluate=False),
        evaluate=False,
    )
    for expression in (sp.sin(x) + a * x, x**4 + a * x, held):
        result = fp.analyze_parameter_range(expression, x, (a,), sp.Interval(-1, 1))
        assert not result.complete and result.condition is None
    with pytest.raises(ValueError):
        fp.analyze_parameter_range(x * x + a * x, x, (a,), sp.Interval(0, a))
    with pytest.raises(ValueError):
        fp.analyze_parameter_range(x * x + a * x, x, (a,), sp.Interval(-1, 1), value=a)


def test_intrinsic_assumptions():
    positive = sp.Symbol("positive_parameter", positive=True)
    r = fp.analyze_parameter_range(
        x * x + positive * x, x, (positive,), sp.Interval(-1, 1), value=y
    )
    assert r.verify() and r.specialize({positive: -1}) is sp.S.EmptySet
    assert r.specialize({positive: 1}) == sp.Interval(-sp.Rational(1, 4), 2)
    positive_x = sp.Symbol("positive_x", positive=True)
    r = fp.analyze_parameter_range(
        positive_x * positive_x + a * positive_x,
        positive_x,
        (a,),
        sp.Interval(-1, 1),
        value=y,
    )
    assert not r.complete


def test_source_coefficient_grammar():
    held = sp.Add(x * x, sp.Mul(0, sp.log(a), evaluate=False), evaluate=False)
    for expression in (x * x + sp.I * a * x, x * x + sp.sqrt(2) * a * x, held):
        result = fp.analyze_parameter_range(
            expression, x, (a,), sp.Interval(-1, 1), value=y
        )
        assert not result.complete and result.condition is None
