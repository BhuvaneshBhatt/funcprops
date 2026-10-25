"""Domain and pole preservation in exact transcendental substitutions."""

import pytest
import sympy as sp

from funcprops import range as function_range
from funcprops import sign
from funcprops.real_analysis.common import condition_to_set
from funcprops.results import Sign
from funcprops.transcendental.algebraize import (
    algebraize,
    algebraize_common_subexprs,
    algebraize_trig_circle,
    algebraize_trigonometric,
)

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        (sp.Interval(1, 2), Sign.POSITIVE),
        (sp.Interval(-2, -1), Sign.NEGATIVE),
        (sp.Interval(0, 1), Sign.SIGN_CHANGING),
    ],
)
def test_sign_algebraization_respects_requested_domain(domain, expected):
    assert sign(sp.exp(x) - 2, x, domain=domain) is expected


@pytest.mark.parametrize("expr", [x + sp.exp(x), x * sp.exp(x)])
def test_exponential_generator_does_not_leave_original_variable(expr):
    assert not algebraize(expr, x).changed


@pytest.mark.parametrize(
    ("source", "image"),
    [
        (sp.Interval(0, 1), sp.Interval(0, sp.tan(sp.Rational(1, 2)))),
        (sp.Interval.open(0, 1), sp.Interval.open(0, sp.tan(sp.Rational(1, 2)))),
        (sp.Interval(-sp.pi / 2, sp.pi / 2), sp.Interval(-1, 1)),
        (sp.Interval.open(-sp.pi, sp.pi), sp.S.Reals),
        (
            sp.Union(sp.Interval(-sp.pi / 2, -sp.pi / 4), sp.Interval(0, sp.pi / 4)),
            sp.Union(sp.Interval(-1, 1 - sp.sqrt(2)), sp.Interval(0, -1 + sp.sqrt(2))),
        ),
        (sp.FiniteSet(0, sp.pi / 2), sp.FiniteSet(0, 1)),
        ((x >= 0) & (x <= 1), sp.Interval(0, sp.tan(sp.Rational(1, 2)))),
    ],
)
def test_half_angle_auxiliary_domain_is_exact(source, image):
    result = algebraize_trigonometric(sp.sin(x) + sp.cos(x), x, source_domain=source)
    assert result.changed and result.exact
    auxiliary = result.substitutions[0][0]
    assert condition_to_set(result.constraints, auxiliary) == image


@pytest.mark.parametrize(
    "source",
    [sp.Interval(4, 5), sp.Interval(-sp.pi, sp.pi), sp.FiniteSet(sp.pi)],
)
def test_half_angle_declines_domains_outside_its_chart(source):
    assert not algebraize_trigonometric(sp.sin(x), x, source_domain=source).changed


@pytest.mark.parametrize(
    "expr", [x + sp.sin(x), sp.log(x) + sp.sin(x), sp.sin(x) + sp.tan(x)]
)
def test_trig_substitution_declines_residual_phase_dependence(expr):
    assert not algebraize_trigonometric(expr, x).changed
    assert not algebraize_trig_circle(expr, x).changed


def test_half_angle_inverse_agrees_on_chart():
    result = algebraize_trigonometric(sp.sin(x) + 2 * sp.cos(x), x)
    auxiliary = result.substitutions[0][0]
    for phase in (0, sp.pi / 4, -sp.pi / 3):
        value = result.expression.subs(auxiliary, sp.tan(phase / 2))
        expected = (sp.sin(x) + 2 * sp.cos(x)).subs(x, phase)
        assert sp.simplify(value - expected) == 0


def test_circle_relation_preserves_original_poles():
    quotient = sp.Mul(sp.sin(x), sp.Pow(sp.sin(x), -1, evaluate=False), evaluate=False)
    result = algebraize_trig_circle(quotient, x)
    assert result.changed and result.exact and result.expression == 1
    s = result.substitutions[0][0]
    c = result.substitutions[1][0]
    assert sp.simplify(result.constraints.subs({s: 0, c: 1})) is sp.S.false
    assert sp.simplify(result.constraints.subs({s: 1, c: 0})) is sp.S.true


def test_half_angle_preserves_original_poles_after_cancellation():
    quotient = sp.Mul(sp.sin(x), sp.Pow(sp.sin(x), -1, evaluate=False), evaluate=False)
    result = algebraize_trigonometric(quotient, x)
    assert result.changed and result.exact and result.expression == 1
    u = result.substitutions[0][0]
    assert sp.simplify(result.constraints.subs(u, 0)) is sp.S.false
    assert sp.simplify(result.constraints.subs(u, 1)) is sp.S.true


def test_exponential_pole_survives_cancellation():
    term = sp.exp(x) - 1
    quotient = sp.Mul(term, sp.Pow(term, -1, evaluate=False), evaluate=False)
    expr = sp.Add(sp.exp(x), quotient, evaluate=False)
    result = algebraize(expr, x)
    assert result.changed and result.exact
    u = result.substitutions[0][0]
    assert sp.simplify(result.constraints.subs(u, 1)) is sp.S.false
    assert sp.simplify(result.constraints.subs(u, 2)) is sp.S.true
    image = function_range(expr, x, y, constraints=sp.Interval(0, 1))
    assert condition_to_set(image, y) == sp.Interval.Lopen(2, 1 + sp.E)


def test_common_subexpression_lifting_remains_uncertified():
    inner = sp.sin(x) + sp.cos(x)
    result = algebraize_common_subexprs(inner**2 + sp.exp(inner), x)
    assert result.exact is False


@pytest.mark.parametrize(
    ("expr", "valid", "invalid"),
    [
        (sp.sqrt(sp.exp(x) - 2), 3, 0),
        (sp.sqrt(sp.sin(x)), sp.pi / 2, -sp.pi / 2),
        (sp.sqrt(sp.cos(x)) + sp.sin(x), 0, sp.pi / 2 + sp.pi / 4),
    ],
)
def test_radical_substitutions_preserve_real_domain(expr, valid, invalid):
    result = algebraize(expr, x, allow_trig=True)
    assert result.changed and result.exact
    aux, generator = result.substitutions[0]
    assert (
        sp.simplify(result.constraints.subs(aux, generator.subs(x, valid))) is sp.S.true
    )
    assert (
        sp.simplify(result.constraints.subs(aux, generator.subs(x, invalid)))
        is sp.S.false
    )


def test_circle_radical_restricts_to_real_branch():
    result = algebraize_trig_circle(sp.sqrt(sp.cos(x)) + sp.sin(x), x)
    assert result.changed and result.exact
    s = result.substitutions[0][0]
    c = result.substitutions[1][0]
    assert sp.simplify(result.constraints.subs({s: 0, c: 1})) is sp.S.true
    assert sp.simplify(result.constraints.subs({s: 0, c: -1})) is sp.S.false


@pytest.mark.parametrize(
    ("expr", "excluded"),
    [
        (sp.coth(x), True),
        (sp.csch(x), True),
        (sp.tanh(x), False),
        (sp.sech(x), False),
    ],
)
def test_hyperbolic_chart_preserves_real_poles(expr, excluded):
    result = algebraize(expr, x)
    assert result.changed and result.exact
    u = result.substitutions[0][0]
    assert (sp.simplify(result.constraints.subs(u, 1)) is sp.S.false) is excluded


def test_contour_trig_lifting_declines_residual_parameter():
    from funcprops.integration import _trig_algebraization

    assert _trig_algebraization(x + sp.sin(x), x) is None
    formula, circle, cosine, sine = _trig_algebraization(
        sp.cos(2 * x) + sp.I * sp.sin(2 * x), x
    )
    assert circle == sp.Eq(cosine**2 + sine**2, 1)
    assert sp.expand(formula - (2 * cosine**2 - 1 + 2 * sp.I * cosine * sine)) == 0
