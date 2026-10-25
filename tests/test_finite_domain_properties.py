"""Exact images, finite signs, work budgets and separable curvature."""

import inspect
import time

import pytest
import sympy as sp

import funcprops as fp
from funcprops.real_analysis.common import condition_to_set
from funcprops.real_analysis.image_rules import exact_image
from funcprops.real_analysis.piecewise import combine_piecewise_sign
from funcprops.results import Convexity, Sign

x, y, z = sp.symbols("x y z", real=True)
a = sp.Symbol("a", real=True)


@pytest.mark.parametrize(
    ("expr", "points", "expected"),
    [
        (x - 1, sp.FiniteSet(0, 2), Sign.SIGN_CHANGING),
        (x**2, sp.FiniteSet(0, 2), Sign.NONNEGATIVE),
        (x - 1, sp.FiniteSet(1), Sign.ZERO),
        (1 / x, sp.FiniteSet(0, 1), Sign.POSITIVE),
        ((x + sp.I) ** 2, sp.FiniteSet(0), Sign.NEGATIVE),
    ],
)
def test_exact_finite_sign(expr, points, expected):
    assert fp.sign(expr, x, domain=points) is expected
    boolean = sp.Or(*(sp.Eq(x, p) for p in points))
    assert fp.sign(expr, x, domain=boolean) is expected


@pytest.mark.parametrize(
    ("assumption", "expected"),
    [
        (sp.Eq(a, 0), Sign.ZERO),
        (a > 0, Sign.SIGN_CHANGING),
        (a < 0, Sign.SIGN_CHANGING),
    ],
)
def test_finite_parameter_sign_strata(assumption, expected):
    assert (
        fp.sign(a * x, x, domain=sp.FiniteSet(-1, 1), assumptions=assumption)
        is expected
    )


def test_weak_signs_do_not_prove_a_change():
    assert combine_piecewise_sign((Sign.NONNEGATIVE, Sign.NONPOSITIVE)) is Sign.UNKNOWN
    assert combine_piecewise_sign((Sign.NONNEGATIVE, Sign.NEGATIVE)) is Sign.UNKNOWN


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        (sp.sqrt(sp.sin(x)), sp.Interval(0, 1)),
        (sp.sqrt(sp.cos(x)), sp.Interval(0, 1)),
        (sp.sin(sp.exp(x)), sp.Interval(-1, 1)),
        (sp.log(sp.sin(x)), sp.Interval(-sp.oo, 0)),
        (sp.exp(sp.sin(x)), sp.Interval(sp.exp(-1), sp.E)),
    ],
)
def test_certified_composition_images(expr, expected):
    assert condition_to_set(fp.range(expr, x, y), y) == expected


@pytest.mark.parametrize(
    ("q", "source", "expected"),
    [
        (sp.Rational(1, 2), sp.Interval(-1, 4), sp.Interval(0, 2)),
        (sp.Rational(1, 3), sp.Interval(-1, 8), sp.Interval(0, 2)),
        (sp.Rational(-1, 2), sp.Interval(0, 4), sp.Interval(sp.Rational(1, 2), sp.oo)),
        (2, sp.Interval.open(-2, 1), sp.Interval.Ropen(0, 4)),
        (3, sp.Interval(-2, 1), sp.Interval(-8, 1)),
        (
            -1,
            sp.Interval(-1, 1),
            sp.Union(sp.Interval(-sp.oo, -1), sp.Interval(1, sp.oo)),
        ),
        (-2, sp.Interval(-1, 1), sp.Interval(1, sp.oo)),
        (sp.Rational(1, 2), sp.FiniteSet(-1, 0, 4), sp.FiniteSet(0, 2)),
    ],
)
def test_principal_power_components(q, source, expected):
    assert exact_image(x**q, x, source) == expected


@pytest.mark.parametrize(
    ("head", "source", "expected"),
    [
        (sp.floor, sp.Interval.open(0, 1), sp.FiniteSet(0)),
        (sp.ceiling, sp.Interval.open(0, 1), sp.FiniteSet(1)),
        (sp.floor, sp.Interval(0, 1), sp.FiniteSet(0, 1)),
        (sp.ceiling, sp.Interval(0, 1), sp.FiniteSet(0, 1)),
        (sp.floor, sp.Interval.Ropen(-2, -1), sp.FiniteSet(-2)),
        (sp.ceiling, sp.Interval.Lopen(-2, -1), sp.FiniteSet(-1)),
        (sp.floor, sp.Interval.open(0, sp.oo), sp.Range(0, sp.oo)),
        (sp.ceiling, sp.Interval.open(0, sp.oo), sp.Range(1, sp.oo)),
        (sp.floor, sp.Interval.open(-sp.oo, 0), sp.Range(-sp.oo, 0)),
    ],
)
def test_discrete_interval_endpoint_attainment(head, source, expected):
    image = condition_to_set(fp.range(head(x), x, y, constraints=source), y)
    if isinstance(expected, sp.FiniteSet):
        assert set(image) == set(expected)
    else:
        assert image == expected


@pytest.mark.parametrize(
    ("head", "expected"),
    [(sp.floor, sp.Range(0, sp.oo)), (sp.ceiling, sp.Range(1, sp.oo))],
)
def test_discrete_exponential_image(head, expected):
    assert condition_to_set(fp.range(head(sp.exp(x)), x, y), y) == expected


def test_disconnected_composition_preserves_gaps_and_endpoints():
    source = sp.Union(sp.Interval(0, 1), sp.Interval(2, 3))
    expected = sp.Union(sp.Interval(1, sp.E), sp.Interval(sp.exp(2), sp.exp(3)))
    image = condition_to_set(fp.range(sp.exp(x), x, y, constraints=source), y)
    assert image == expected
    source = sp.Union(
        sp.Interval(sp.log(2), sp.log(3)), sp.Interval(sp.log(5), sp.log(6))
    )
    image = condition_to_set(fp.range(sp.floor(sp.exp(x)), x, y, constraints=source), y)
    assert set(image) == {sp.Integer(2), sp.Integer(3), sp.Integer(5), sp.Integer(6)}


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        (sp.exp(x) + sp.exp(y), Convexity.STRICTLY_CONVEX),
        (x**4 + y**4, Convexity.STRICTLY_CONVEX),
        (sp.exp(x) + x**2 + sp.exp(y) + y**2, Convexity.STRONGLY_CONVEX),
        (sp.log(x) + sp.log(y), Convexity.STRICTLY_CONCAVE),
        (sp.exp(x) + y, Convexity.CONVEX),
        (-sp.exp(x) - sp.exp(y), Convexity.STRICTLY_CONCAVE),
    ],
)
def test_separable_multivariate_curvature(expr, expected):
    assert fp.convexity(expr, (x, y)) is expected
    assert fp.convexity(expr, (x, y), return_result=True).primary is expected


def test_multivariate_domain_must_be_proved_convex():
    expr = x**2 + y**2
    assert fp.convexity(expr, (x, y), domain=sp.Or(x < -1, x > 1)) is Convexity.UNKNOWN
    assert (
        fp.convexity(expr, (x, y), domain=(x >= 1) & (x <= 2) & (y > 0))
        is Convexity.STRONGLY_CONVEX
    )
    assert fp.convexity(sp.I + expr, (x, y)) is Convexity.UNKNOWN


@pytest.mark.parametrize("seconds", [0, -1, float("inf"), float("nan"), True])
def test_invalid_work_budget(seconds):
    with pytest.raises(ValueError):
        fp.range(sp.exp(x), x, y, work_budget=seconds)


def test_successful_budgeted_queries_preserve_results():
    assert (
        fp.sign(x - 1, x, domain=sp.FiniteSet(0, 2), work_budget=5)
        is Sign.SIGN_CHANGING
    )
    assert condition_to_set(
        fp.range(sp.sin(sp.exp(x)), x, y, work_budget=5), y
    ) == sp.Interval(-1, 1)
    assert "work_budget" in inspect.signature(fp.range).parameters


def test_exhausted_budget_is_unknown_and_incomplete():
    start = time.monotonic()
    result = fp.range(sp.sin(sp.exp(x)), x, y, work_budget=0.001, return_result=True)
    assert time.monotonic() - start < 3
    assert result.complete is False and result.certified is False
    assert result.source == "work-budget-exhausted"
    assert result.primary.func == sp.Function("UnknownRange")
    assert fp.as_detailed_result(result).complete is False


def test_constant_range_on_empty_domain_is_empty():
    assert fp.range(1, x, y, constraints=sp.S.EmptySet) is sp.S.false
    assert fp.range(sp.I, x, y) is sp.S.false


def test_restricted_positive_axis_range():
    image = condition_to_set(
        fp.range(sp.besselk(0, x), x, y, constraints=sp.Interval(1, 2)), y
    )
    assert image == sp.Interval(sp.besselk(0, 2), sp.besselk(0, 1))
    assert fp.range(sp.besselk(0, x), x, y, constraints=x > 0) == (y > 0)


def test_parameterized_power_full_axis_theorem_requires_full_axis():
    from funcprops.real_analysis.range import _parameterized_elementary_range

    assert _parameterized_elementary_range(x**a, x, y, (x >= 1) & (x <= 2)) is None
    result = _parameterized_elementary_range(x**a, x, y, x > 0).as_piecewise()
    assert result.subs(a, 2) == (y > 0)
    assert result.subs(a, 0) == sp.Eq(y, 1)


@pytest.mark.parametrize(
    ("right", "expected"),
    [
        (1, fp.Monotonicity.NONDECREASING),
        (-1, fp.Monotonicity.NONINCREASING),
        (0, fp.Monotonicity.CONSTANT),
    ],
)
def test_constant_piecewise_branches_are_not_a_constant_function(right, expected):
    expr = sp.Piecewise((0, x < 0), (right, True))
    assert fp.monotonicity(expr, x) is expected


def test_piecewise_gap_reset():
    expr = sp.Piecewise((x, x < 0), (x - 10, True))
    source = sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2))
    assert fp.monotonicity(expr, x, domain=source) is fp.Monotonicity.NOT_MONOTONE


def test_product_box_and_nonconvex_multivariate_sets():
    box = sp.ProductSet(sp.Interval(1, 2), sp.Interval(0, 1))
    assert fp.convexity(sp.exp(x) + sp.exp(y), (x, y), domain=box) in (
        Convexity.STRICTLY_CONVEX,
        Convexity.STRONGLY_CONVEX,
    )
    points = sp.FiniteSet(sp.Tuple(0, 0), sp.Tuple(1, 1))
    assert fp.convexity(x * x + y * y, (x, y), domain=points) is Convexity.UNKNOWN


def test_constant_range_retains_parameter_domain_nonemptiness():
    b = sp.Symbol("b", real=True)
    image = fp.range(1, x, y, constraints=(x > a) & (x < b))
    assert sp.simplify(image.subs({a: 2, b: 1})) is sp.S.false
    assert image.subs({a: 0, b: 1}) == sp.Eq(y, 1)
    assert fp.range(1, x, y, constraints=sp.FiniteSet(sp.I)) is sp.S.false


def test_independent_parameter_guards():
    assert condition_to_set(a > 0, x) is None


def test_finite_weak_parameter_signs_retain_zero_case():
    assert (
        fp.sign(a**2 * x, x, domain=sp.FiniteSet(-1, 1), assumptions=sp.Eq(a, 0))
        is Sign.ZERO
    )
    assert (
        fp.sign(a**2 * x, x, domain=sp.FiniteSet(-1, 1), assumptions=a > 0)
        is Sign.SIGN_CHANGING
    )


def test_complex_intermediate_images():
    assert fp.range((x + sp.I) ** 2, x, y, constraints=sp.FiniteSet(0)) == sp.Eq(y, -1)
    assert fp.range(
        sp.exp(sp.I * x), x, y, constraints=sp.FiniteSet(0, sp.pi)
    ) == sp.Or(sp.Eq(y, 1), sp.Eq(y, -1))
    result = fp.range(sp.exp(sp.I * x), x, y, work_budget=3)
    assert result != (y > 0)


def test_convexity_replay_rejects_tampered_classification_and_subject():
    from dataclasses import replace

    from funcprops.real_analysis.advanced_convexity import ConvexityCertificate

    result = fp.convexity(sp.exp(x) + sp.exp(y), (x, y), return_result=True)
    cert = next(
        item for item in result.evidence if isinstance(item, ConvexityCertificate)
    )
    assert fp.verify_convexity_certificate(sp.exp(x) + sp.exp(y), (x, y), cert)
    assert not fp.verify_convexity_certificate(
        sp.exp(x) + sp.exp(y), (x, y), replace(cert, classification=Convexity.CONCAVE)
    )
    assert not fp.verify_convexity_certificate(x * y, (x, y), cert)
    fake = ConvexityCertificate(
        Convexity.STRICTLY_CONVEX, sp.S.Reals, "unverified-label"
    )
    assert not fp.verify_convexity_certificate(sp.sin(x), x, fake)


def test_separable_certificate_retains_natural_domain():
    from funcprops.real_analysis.advanced_convexity import ConvexityCertificate

    result = fp.convexity(sp.log(x) + sp.log(y), (x, y), return_result=True)
    cert = next(
        item for item in result.evidence if isinstance(item, ConvexityCertificate)
    )
    assert cert.domain == (x > 0) & (y > 0)


def test_curvature_domain_premises():
    from funcprops.real_analysis.advanced_convexity import ConvexityCertificate

    expr = sp.Piecewise((x * x, x < 0), (x * x - 10, True))
    cert = ConvexityCertificate(
        Convexity.STRONGLY_CONVEX,
        sp.S.Reals,
        "second-derivative",
        modulus=sp.Integer(1),
    )
    assert not fp.verify_convexity_certificate(expr, x, cert)
    nonconvex = sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2))
    cert = ConvexityCertificate(
        Convexity.STRONGLY_CONVEX, nonconvex, "second-derivative", modulus=sp.Integer(1)
    )
    assert not fp.verify_convexity_certificate(x * x, x, cert)


def test_curvature_modulus_cannot_verify_wrong_kind_of_conclusion():
    from funcprops.real_analysis.advanced_convexity import ConvexityCertificate

    for claimed in (Convexity.NEITHER, Convexity.AFFINE, Convexity.UNKNOWN):
        cert = ConvexityCertificate(
            claimed, sp.S.Reals, "second-derivative", modulus=sp.Integer(1)
        )
        assert not fp.verify_convexity_certificate(x * x, x, cert)


def test_replay_rejects_mutated_indexed_and_monotonic_evidence():
    from dataclasses import replace

    p = fp.monotonic_partition(
        x**3 - 3 * x, x, domain=sp.Interval(-2, 2), return_result=True
    )
    assert fp.verify_monotonic_partition(x**3 - 3 * x, x, p)
    assert not fp.verify_monotonic_partition(x**3 - 3 * x, x, replace(p, cells=()))
    d = fp.monotonic_decomposition(sp.acos(sp.exp(x)), x, return_result=True)
    assert fp.verify_monotonic_decomposition(d)
    assert not fp.verify_monotonic_decomposition(replace(d, direction=-d.direction))
    g = fp.zero_geometry(sp.besselj(0, x), x)[0]
    assert fp.verify_zero_geometry(g)
    assert not fp.verify_zero_geometry(replace(g, count=1))
    assert not fp.verify_certificate(g, expr=sp.cos(x), var=x)
    order = fp.extremum_ordering_theorems(sp.airyai(x), x)[0]
    assert fp.verify_extremum_ordering(order)
    assert not fp.verify_extremum_ordering(
        replace(order, magnitude_direction="increasing")
    )
    k = sp.Symbol("k", integer=True, positive=True)
    template = fp.IndexedZero("BesselJ", k, 0, 0, "positive")
    tail = fp.indexed_tail_inversion(
        template, fp.IndexedZero("BesselJ", 3, 0, 0, "positive")
    )
    assert fp.verify_indexed_tail_inversion(tail)
    assert not fp.verify_indexed_tail_inversion(replace(tail, first_index=100))


def test_root_index_cannot_capture_phase_parameter():
    n = sp.Symbol("n", integer=True)
    family = fp.affine_trig_root_family(sp.sin(x + n), x)
    assert family.verify()
    assert family.index != n and n in family.formula.free_symbols
    g = fp.zero_geometry(sp.sin(x + n), x)[0]
    assert fp.verify_zero_geometry(g)


def test_parameter_dependent_order_does_not_use_fixed_order_theorems():
    from funcprops.real_analysis.special_functions import positive_axis_range_strata

    assert not fp.zero_geometry(sp.besselj(x, x), x)
    assert not fp.extremum_ordering_theorems(sp.besselj(x, x), x)
    assert not positive_axis_range_strata(sp.besseli(x, x), x, y)


def test_bessel_y_zero_order_first_maximum_is_first_critical_point():
    cert = fp.extremum_ordering_theorems(sp.bessely(0, x), x)[0]
    assert cert.global_max_index == 1
    assert fp.verify_extremum_ordering(cert)


def test_indexed_order_parameter_binding():
    k = sp.Symbol("k", integer=True, positive=True)
    g = fp.zero_geometry(sp.besselj(k, x), x)[0]
    assert g.indexed_family[0].index != k
    assert g.indexed_family[0].args[2] == k
    assert fp.verify_zero_geometry(g)


def test_replay_rejects_mutated_root_extremum_and_bracket_conclusions():
    from dataclasses import replace

    roots = fp.transcendental_roots(
        sp.sin(x), x, sp.Interval(0, 2 * sp.pi), allow_numerical=False
    )
    c = roots.certificates[0]
    assert fp.verify_root_certificate(c)
    assert not fp.verify_root_certificate(replace(c, root_count=100))
    assert not fp.verify_root_certificate(replace(c, expression=sp.exp(x)))
    c = fp.extremum_geometry(sp.airyai(x), x)[0]
    assert fp.verify_extremum_family(c)
    assert not fp.verify_extremum_family(replace(c, alternating=not c.alternating))
    c = fp.symbolic_extremum_range(x**2, x, sp.Interval(-1, 2))
    assert fp.verify_extremum_range(c)
    assert not fp.verify_extremum_range(replace(c, upper=100))
    k = sp.Symbol("k", integer=True, positive=True)
    template = fp.IndexedZero("BesselJ", k, 0, 0, "positive")
    c = fp.indexed_tail_integer_bracket(template, 10)
    assert fp.verify_integer_bracket(c)
    assert not fp.verify_integer_bracket(replace(c, lower=100, upper=101))


def test_unbound_payloads_cannot_be_verified_from_labels():
    from funcprops.transcendental.extrema import ExtremumRange
    from funcprops.transcendental.roots import RootCertificate
    from funcprops.transcendental.zero_geometry import CertifiedIntegerBracket

    assert not fp.verify_root_certificate(RootCertificate(sp.S.Reals, 100, "solveset"))
    assert not fp.verify_extremum_range(
        ExtremumRange(0, 100, True, True, sp.S.Reals, True)
    )
    assert not fp.verify_integer_bracket(CertifiedIntegerBracket(100, 101))
