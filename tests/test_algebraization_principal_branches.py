"""Adversarial principal-power guards and fresh contour coordinates."""

import pytest
import sympy as sp

from funcprops import domain, sign
from funcprops import range as function_range
from funcprops.integration import _trig_algebraization
from funcprops.real_analysis.common import condition_to_set
from funcprops.results import Sign
from funcprops.transcendental.algebraize import (
    algebraize,
    algebraize_trig_circle,
    algebraize_trigonometric,
)

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    "q", [sp.Rational(1, 3), sp.Rational(2, 3), sp.Rational(-1, 3)]
)
@pytest.mark.parametrize("family", ["exp", "half_angle", "circle"])
def test_principal_odd_power_auxiliary_guard(q, family):
    base = sp.exp(x) - 2 if family == "exp" else sp.sin(x)
    expr = base**q
    result = {
        "exp": algebraize,
        "half_angle": algebraize_trigonometric,
        "circle": algebraize_trig_circle,
    }[family](expr, x)
    assert result.changed and result.exact
    for phase in (-sp.pi / 2, 0, sp.pi / 2):
        substitutions = {a: g.subs(x, phase) for a, g in result.substitutions}
        guard = sp.simplify(result.constraints.subs(substitutions))
        value = base.subs(x, phase)
        expected = value > 0 if q < 0 else value >= 0
        assert guard is sp.simplify(expected)


@pytest.mark.parametrize(
    "q", [sp.Rational(1, 3), sp.Rational(2, 3), sp.Rational(-1, 3)]
)
@pytest.mark.parametrize("base", [x, sp.exp(x) - 2, sp.sin(x)])
def test_real_domain_matches_sympy_principal_power(q, base):
    guard = domain(base**q, x)
    for phase in (0, sp.pi / 2, -sp.pi / 2):
        value = (base**q).subs(x, phase)
        expected = value.is_real is True and value.is_finite is True
        assert (sp.simplify(guard.subs(x, phase)) is sp.S.true) == expected


@pytest.mark.parametrize("q", [sp.Rational(1, 3), sp.Rational(2, 3)])
def test_range_and_sign_use_principal_real_domain(q):
    expr = (sp.exp(x) - 2) ** q
    assert function_range(expr, x, y, constraints=sp.FiniteSet(0)) is sp.S.false
    image = function_range(expr, x, y, constraints=sp.FiniteSet(sp.log(2), sp.log(3)))
    assert condition_to_set(image, y) == sp.FiniteSet(0, 1)
    assert sign(expr, x, domain=sp.FiniteSet(sp.log(3))) in (
        Sign.POSITIVE,
        Sign.NONNEGATIVE,
    )


@pytest.mark.parametrize("exponent", [sp.pi, sp.Symbol("a", real=True)])
@pytest.mark.parametrize("family", ["exp", "half_angle", "circle"])
def test_cancellation_cannot_hide_unsupported_power(exponent, family):
    base = sp.exp(x) - 2 if family == "exp" else sp.sin(x)
    power = sp.Pow(base, exponent, evaluate=False)
    quotient = sp.Mul(power, sp.Pow(power, -1, evaluate=False), evaluate=False)
    result = {
        "exp": algebraize,
        "half_angle": algebraize_trigonometric,
        "circle": algebraize_trig_circle,
    }[family](quotient, x)
    assert not result.changed


def test_contour_coordinates_cannot_capture_user_parameters():
    coefficient = sp.Symbol("_contour_cos", real=True)
    gamma = coefficient + sp.cos(x) + sp.I * sp.sin(x)
    expression, relation, cosine, sine = _trig_algebraization(gamma, x)
    assert cosine != coefficient and sine != coefficient
    assert coefficient in expression.free_symbols
    assert coefficient not in relation.free_symbols
    restored = expression.subs({cosine: sp.cos(x), sine: sp.sin(x)})
    assert sp.simplify(restored - gamma) == 0


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (sp.Interval(0, sp.log(3)), sp.Interval(2, 3)),
        (sp.Interval.open(sp.log(2), sp.log(3)), sp.Interval.open(2, 3)),
        (sp.Interval(sp.log(2), sp.oo), sp.Interval(2, sp.oo)),
        (
            sp.Union(sp.Interval(-1, 0), sp.Interval(sp.log(3), sp.log(4))),
            sp.Interval(3, 4),
        ),
    ],
)
def test_principal_branch_intersects_restricted_auxiliary_domain(source, expected):
    result = algebraize((sp.exp(x) - 2) ** sp.Rational(1, 3), x, domain=source)
    assert result.changed and result.exact
    auxiliary = result.substitutions[0][0]
    assert condition_to_set(result.constraints, auxiliary) == expected


def test_explicit_real_root_keeps_negative_base_domain():
    expr = sp.real_root(sp.exp(x) - 2, 3)
    assert sp.simplify(domain(expr, x).subs(x, 0)) is sp.S.true
    assert expr.subs(x, 0) == -1


@pytest.mark.parametrize("q", [sp.Rational(1, 3), sp.Rational(1, 2)])
def test_proven_nonreal_power_does_not_form_real_comparison(q):
    expr = (sp.exp(x) + sp.I) ** q
    assert expr.is_real is False
    assert not algebraize(expr, x).changed
    assert domain(expr, x) is sp.S.false
