"""Real outputs can require complex intermediate values on a real source."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_images.transfers import ComposedImage

x, y = sp.symbols("x y", real=True)
D = sp.Interval(-2, -sp.Rational(1, 2))


@pytest.mark.parametrize(
    "expression, expected",
    [
        (sp.Piecewise((sp.exp(x), x < 0), (1, True)), False),
        (sp.Piecewise((sp.Abs(sp.log(x)), x < 0), (1, True)), True),
    ],
)
def test_piecewise_operand_scan(expression, expected):
    from funcprops.real_analysis.domain import _has_complex_intermediates

    assert _has_complex_intermediates(expression, x) is expected


def known_endpoint(value, point):
    """Evaluate an implicit endpoint by its checked unique-root description."""
    if isinstance(value, fp.CriticalValue):
        root = value.root
        assert root.verify() and root.interval.contains(point) is sp.true
        assert sp.simplify(root.expression.subs(root.variable, point)) == 0
        return sp.simplify(value.function.expr.subs(value.function.variables[0], point))
    if value.is_Pow:
        return known_endpoint(value.base, point) ** value.exp
    return value


@pytest.mark.parametrize("opened", [False, True])
def test_absolute_log_image(opened):
    source = sp.Interval(D.start, D.end, opened, opened)
    f = sp.Abs(sp.log(x))
    expected = sp.Interval(sp.pi, sp.sqrt(sp.pi**2 + sp.log(2) ** 2), False, opened)
    r = fp.analyze_range(f, x, source)
    assert r.verify() and r.image.end == expected.end
    assert known_endpoint(r.image.start, -1) == sp.pi
    assert not r.image.left_open and r.image.right_open == opened
    condition = fp.range(f, x, y, domain=source)
    assert condition.subs(y, sp.pi) is sp.true
    assert condition.subs(y, 0) is sp.false
    assert sp.simplify(condition.subs(y, expected.end)) == (
        sp.false if opened else sp.true
    )


def test_cosine_log_image():
    f = sp.cos(sp.I * sp.log(x), evaluate=False)
    r = fp.analyze_range(f, x, D)
    assert r.verify() and r.image.start == -sp.Rational(5, 4)
    assert known_endpoint(r.image.end, -1) == -1
    assert not r.image.left_open and not r.image.right_open
    condition = fp.range(f, x, y, domain=D)
    assert condition.subs(y, -1) is sp.true
    assert condition.subs(y, -sp.Rational(5, 4)) is sp.true
    assert condition.subs(y, 0) is sp.false


def test_real_inner_domain_premise():
    f = sp.Abs(sp.log(x))
    r = fp.analyze_range(f, x, D)
    child = fp.analyze_range(sp.log(x), x, D)
    assert child.verify() and child.image is sp.S.EmptySet
    u = sp.Dummy("inner_value", real=True)
    bad = replace(
        r,
        transfer=ComposedImage(sp.Lambda(u, sp.Abs(u)), child),
        image=sp.S.EmptySet,
        inner=sp.S.EmptySet,
        outer=sp.S.EmptySet,
    )
    assert not bad.verify()


def test_complex_source_hole():
    hole = sp.Mul(x + 1, sp.Pow(x + 1, -1, evaluate=False), evaluate=False)
    f = sp.Mul(sp.Abs(sp.log(x)), hole, evaluate=False)
    r = fp.analyze_range(f, x, D)
    assert (
        r.image == sp.Interval.Lopen(sp.pi, sp.sqrt(sp.pi**2 + sp.log(2) ** 2))
        and r.verify()
    )
    assert not r.domain_record.effective.contains(-1)
    assert not replace(
        r, transfer=replace(r.transfer, analyses=r.transfer.analyses[:1])
    ).verify()


@pytest.mark.parametrize("order", [1, 2, 3])
@pytest.mark.parametrize("opened", [False, True])
def test_complex_log_models(order, opened):
    source = sp.Interval(D.start, D.end, opened, opened)
    f = sp.cos(order * sp.I * sp.log(x), evaluate=False)
    condition = fp.range(f, x, y, domain=source)
    stationary = (-1) ** order
    endpoint = ((-sp.S(2)) ** order + (-sp.S(2)) ** (-order)) / 2
    assert sp.simplify(condition.subs(y, stationary)) is sp.true
    assert sp.simplify(condition.subs(y, endpoint)) == (sp.false if opened else sp.true)
    assert sp.simplify(condition.subs(y, 2 * endpoint)) is sp.false


def test_real_formula_binding():
    from funcprops.real_images.transfers import RealFormulaImage

    r = fp.analyze_range(sp.Abs(sp.log(x)), x, D)
    child = fp.analyze_range(sp.pi, x, D)
    bad = replace(
        r,
        transfer=RealFormulaImage(sp.pi, child),
        image=child.image,
        inner=child.inner,
        outer=child.outer,
    )
    assert not bad.verify()
