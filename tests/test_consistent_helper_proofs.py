"""Integration and adversarial replay tests for shared helper proof obligations."""

from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops.certified_balls import certified_real_ball
from funcprops.domain_tracking import smooth_domain_record
from funcprops.global_multivariate import affine_global_mapping, compose_global_maps
from funcprops.piecewise_proofs import complex_source_defined
from funcprops.results import TruthValue as T
from funcprops.work_budget import BudgetedResult

x = s.Symbol("x", real=True)
t = s.Symbol("t", real=True)
z = s.Symbol("z")
a = s.Symbol("a", real=True)


def test_bounded_precision_refinement_resolves_rounding():
    cutoff = s.Rational(str(s.E.evalf(60))) - s.Rational(1, 10) ** 59
    f = (s.E - cutoff) * s.exp(x)
    D = s.Interval(0, 1)
    low = fp.certify_inequality(f, 0, x, D, max_depth=0, max_precision=30)
    high = fp.certify_inequality(f, 0, x, D, max_depth=0, max_precision=120)
    assert low.classification is T.UNKNOWN and not low.verify()
    assert high.classification is T.TRUE and high.verify()
    assert 30 < high.evidence.precision <= 120
    capped = fp.certify_inequality(
        f, 0, x, D, max_depth=0, max_precision=240, max_refinements=0
    )
    assert capped.classification is T.UNKNOWN
    assert not replace(high.evidence, upper=high.evidence.lower - 1).verify()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"precision": 1},
        {"precision": 40, "max_precision": 30},
        {"max_refinements": -1},
        {"max_refinements": True},
    ],
)
def test_invalid_refinement_caps_reject(kwargs):
    with pytest.raises(ValueError):
        certified_real_ball(s.exp(x), x, s.Interval(0, 1), relation=">", **kwargs)


@pytest.mark.parametrize(
    "premise,expected", [(s.Ne(a, 0), T.TRUE), (s.Eq(a, 0), T.FALSE), (a > 0, T.TRUE)]
)
def test_affine_parameter_assumptions_specialize(premise, expected):
    c = affine_global_mapping((a * x,), (x,), assumptions=premise)
    assert c.classification is expected and c.verify() and c.complete
    assert c.assumptions == premise
    assert not replace(c, assumptions=s.S.true).verify()


def test_unknown_and_contradictory_guard_contexts_do_not_certify():
    c = affine_global_mapping((a * x,), (x,), assumptions=False)
    assert c.classification is T.UNKNOWN and not c.certified and not c.complete
    with pytest.raises(ValueError, match="coordinates"):
        affine_global_mapping((a * x,), (x,), assumptions=x > 0)
    q = s.Symbol("q")
    conditional = affine_global_mapping((q * x,), (x,), assumptions=s.Q.real(q))
    assert conditional.cases and conditional.certified and conditional.complete


def test_composition_keeps_component_assumptions():
    c = affine_global_mapping((a * x,), (x,), assumptions=s.Ne(a, 0))
    identity = affine_global_mapping((x,), (x,))
    combined = compose_global_maps((c, identity))
    assert combined.classification is T.TRUE and combined.verify()
    assert combined.assumptions == s.Ne(a, 0)
    assert not replace(combined, assumptions=s.S.true).verify()


def test_specialization_happens_before_case_product_budget():
    parameters = s.symbols("a0:9", real=True)
    parts = tuple(
        affine_global_mapping((parameter * x,), (x,)) for parameter in parameters
    )
    assert not compose_global_maps(parts).certified
    c = compose_global_maps(
        parts, assumptions=s.And(*(s.Ne(parameter, 0) for parameter in parameters))
    )
    assert c.classification is T.TRUE and c.certified and c.complete


@pytest.mark.parametrize("exponent", [s.pi, s.sqrt(2), s.I, s.Rational(1, 3)])
def test_constant_power_continuation_and_reversal(exponent):
    contour = fp.ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    c = fp.analytic_continue(z**exponent, z, contour, return_certificate=True)
    assert c.verify() and c.complete and c.certified
    expected = z**exponent * s.exp(2 * s.pi * s.I * exponent)
    assert s.simplify(c.continued - expected) == 0
    assert not replace(c, substitutions=()).verify()
    backward = fp.analytic_continue(z**exponent, z, contour.reversed())
    assert s.simplify(backward - z**exponent * s.exp(-2 * s.pi * s.I * exponent)) == 0


def test_power_parameter_requires_finite_constant_exponent():
    contour = fp.ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    q = s.Symbol("q", complex=True)
    assert fp.analytic_continue(z**q, z, contour, return_certificate=True).verify()
    assert fp.analytic_continue(z**z, z, contour) is None
    assert fp.analytic_continue(z ** s.Symbol("unknown"), z, contour) is None


def test_piecewise_inequality_branch_and_singleton_assembly():
    f = s.Piecewise((s.exp(x), x < 0), (2, s.Eq(x, 0)), (x * x + 1, True))
    c = fp.certify_inequality(f, 0, x, s.Interval(-1, 1))
    assert c.source == "piecewise-assembly" and c.verify() and c.complete
    assert not replace(c, evidence=c.evidence[:-1]).verify()
    wrong = replace(c.evidence[0], domain=s.Interval(-1, s.Rational(-1, 2)))
    assert not replace(c, evidence=(wrong, *c.evidence[1:])).verify()


def test_piecewise_counterexample_and_jump_remain_distinct():
    f = s.Piecewise((x * x + 1, x < 0), (-2, True))
    c = fp.certify_inequality(f, 0, x, s.Interval(-1, 1))
    assert c.classification is T.FALSE and c.verify()
    assert fp.certify_piecewise_regular(f, x, s.Interval(-1, 1)) is None
    assert fp.verify_real_root_interval(f, x, s.Interval(-1, 1)).root_count is None


def test_corner_regular_assembly_is_not_a_global_c1_claim():
    f = s.Piecewise((-x, x < 0), (x, True))
    D = s.Interval(-1, 1)
    c = fp.certify_piecewise_regular(f, x, D)
    assert c.verify() and c.complete
    assert fp.verify_certificate(c, expr=f, var=x)
    assert not fp.verify_certificate(c, expr=f + 1, var=x)
    assert smooth_domain_record(f, x, D, 1) is None
    assert not replace(c, seams=()).verify()
    spike = s.Piecewise((3, s.Eq(x, -1)), (f, True))
    assert fp.certify_piecewise_regular(spike, x, D) is None


def square():
    gamma = s.Piecewise(
        (1 + s.I - 2 * t, t <= 1),
        (-1 + s.I - 2 * s.I * (t - 1), t <= 2),
        (-1 - s.I + 2 * (t - 2), t <= 3),
        (1 - s.I + 2 * s.I * (t - 3), True),
    )
    return fp.ParametricContour(gamma, (t, 0, 4))


def test_piecewise_polygon_winding_and_continuation():
    contour = square()
    c = fp.winding_number(contour, 0, return_certificate=True)
    assert c.winding == 1 and c.certified and c.complete
    assert fp.winding_number(contour.reversed(), 0) == -1
    assert fp.winding_number(contour, 1 + s.I) is None
    continued = fp.analytic_continue(s.log(z), z, contour, return_certificate=True)
    assert (
        continued.verify()
        and s.simplify(continued.continued - s.log(z)) == 2 * s.pi * s.I
    )


def test_inactive_complex_source_holes_and_undefined_conditions():
    f = s.Piecewise((1 + s.I, x <= 0), (s.log(x) + s.I, True))
    assert complex_source_defined(f, x, s.Interval(-1, 1))
    bad_condition = s.Gt(s.Pow(x, -1, evaluate=False), 0, evaluate=False)
    assert not complex_source_defined(
        s.Piecewise((1, bad_condition), (2, True)), x, s.Interval(-1, 1)
    )


@pytest.mark.parametrize(
    "operation,args,kwargs",
    [
        (fp.solve, (x - 1, x), {"domain": s.S.Reals, "return_certificate": True}),
        (fp.inverse, (x + 1, x), {"return_certificate": True}),
        (fp.analytic_continue, (z**s.pi, z, square()), {"return_certificate": True}),
        (fp.classify_singularity, (1 / z, z, 0), {"return_certificate": True}),
        (fp.winding_number, (square(), 0), {"return_certificate": True}),
        (fp.argument_principle, (z, z, square()), {"return_certificate": True}),
        (fp.certify_inequality, (s.exp(x), 0, x, s.Interval(0, 1)), {}),
        (fp.certify_global_minimum, (x * x, x), {}),
    ],
)
def test_budget_expiry_is_context_bound_and_incomplete(operation, args, kwargs):
    result = operation(*args, **kwargs, work_budget=1e-6)
    assert isinstance(result, BudgetedResult)
    assert not result.complete and not result.certified and not result.verify()
    assert result.operation == operation.__name__
    assert result.query[0] == args[0]


def test_budget_success_and_error_transport():
    c = fp.solve(x - 1, x, domain=s.S.Reals, return_certificate=True, work_budget=10)
    assert c.complete and c.verify() and c.solutions == s.FiniteSet(1)
    contour = fp.ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    c = fp.analytic_continue(
        z**s.pi, z, contour, return_certificate=True, work_budget=10
    )
    assert c.certified
    assert fp.solve(x - 1, x, work_budget=1e-6) is None
    with pytest.raises(TypeError):
        fp.solve(x - 1, 1, work_budget=10)
    with pytest.raises(ValueError):
        fp.solve(x - 1, x, work_budget=True)
