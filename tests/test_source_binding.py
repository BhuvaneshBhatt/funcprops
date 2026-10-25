"""Exact image attainment and nested proof-dispatch regressions."""

from dataclasses import replace
from itertools import pairwise

import pytest
import sympy as sp

import funcprops as fp
from funcprops import analytic_contours as ac
from funcprops.certified_optimization import GlobalMinimumCertificate
from funcprops.component_optimization import ComponentMinimumResult
from funcprops.domain_tracking import DomainRecord
from funcprops.enclosures import EnclosureResult
from funcprops.real_analysis.image_rules import exact_image

x, y = sp.symbols("x y", real=True)
z = sp.Symbol("z")


@pytest.mark.parametrize("function,offset", [(sp.sin, sp.pi / 2), (sp.cos, 0)])
@pytest.mark.parametrize(
    "left_open,right_open", [(True, True), (True, False), (False, True), (False, False)]
)
@pytest.mark.parametrize("turn", [-2, 0, 3])
def test_one_period_images_preserve_extremum_attainment(
    function, offset, left_open, right_open, turn
):
    start = offset + turn * 2 * sp.pi
    source = sp.Interval(start, start + 2 * sp.pi, left_open, right_open)
    expected = sp.Interval(-1, 1, right_open=left_open and right_open)
    assert exact_image(function(x), x, source) == expected


@pytest.mark.parametrize(
    "function,offset",
    [(sp.sin, sp.pi / 2), (sp.cos, 0), (sp.sin, -sp.pi / 2), (sp.cos, sp.pi)],
)
def test_composed_one_period_ranges_do_not_add_missing_values(function, offset):
    upper_missing = function(offset) == 1
    expected = sp.Interval(-1, 1, left_open=not upper_missing, right_open=upper_missing)
    source = sp.Interval.open(sp.exp(offset), sp.exp(offset + 2 * sp.pi))
    result = fp.range(function(sp.log(x)), x, y, domain=source)
    assert result.as_set() == expected
    wider = sp.Interval.open(sp.exp(offset), sp.exp(offset + 2 * sp.pi + 1))
    assert fp.range(function(sp.log(x)), x, y, domain=wider).as_set() == sp.Interval(
        -1, 1
    )


@pytest.mark.parametrize("function,offset", [(sp.sin, sp.pi / 2), (sp.cos, 0)])
@pytest.mark.parametrize("left_open,right_open", [(True, False), (False, True)])
def test_composed_one_period_closed_endpoint_attains_the_peak(
    function, offset, left_open, right_open
):
    domain = sp.Interval(
        sp.exp(offset), sp.exp(offset + 2 * sp.pi), left_open, right_open
    )
    assert fp.range(function(sp.log(x)), x, y, domain=domain).as_set() == sp.Interval(
        -1, 1
    )


@pytest.mark.parametrize("periods", [2, 3])
@pytest.mark.parametrize("function,offset", [(sp.sin, sp.pi / 2), (sp.cos, 0)])
def test_interior_periodic_extremum_is_not_lost_at_an_open_endpoint(
    function, offset, periods
):
    domain = sp.Interval.open(offset, offset + periods * 2 * sp.pi)
    assert fp.range(function(x), x, y, domain=domain).as_set() == sp.Interval(-1, 1)


@pytest.mark.parametrize(
    "expression,domain,expected",
    [
        (
            sp.cosh(sp.log(x)),
            sp.Interval.Lopen(1 / sp.E, sp.E),
            sp.Interval(1, sp.cosh(1)),
        ),
        ((sp.exp(x) - 2) ** 2, sp.Interval.Lopen(0, sp.log(3)), sp.Interval(0, 1)),
        (
            (sp.exp(x) ** 2 - 1) ** 2,
            sp.Interval.open(sp.log(sp.Rational(1, 2)), sp.log(sp.Rational(3, 2))),
            sp.Interval.Ropen(0, sp.Rational(25, 16)),
        ),
    ],
)
def test_algebraized_and_composed_ranges_retain_attained_values(
    expression, domain, expected
):
    assert fp.range(expression, x, y, domain=domain).as_set() == expected


def test_disconnected_range_attainment():
    domain = sp.Interval.open(sp.exp(sp.pi / 2), sp.exp(5 * sp.pi / 2))
    expression = sp.sin(sp.log(x))
    assert (
        fp.surjective(expression, x, domain=domain, codomain=sp.Interval(-1, 1))
        is fp.TruthValue.FALSE
    )
    assert (
        fp.surjective(expression, x, domain=domain, codomain=sp.Interval.Ropen(-1, 1))
        is fp.TruthValue.TRUE
    )
    domain = sp.Union(domain, sp.FiniteSet(sp.exp(sp.pi / 2)))
    assert fp.range(expression, x, y, domain=domain).as_set() == sp.Interval(-1, 1)


def assert_rejected(record):
    assert not record.verify()
    assert fp.verify_certificate(record) is False
    assert fp.replay_status(record).certified is False


def forged_contour():
    class LyingBox(ac.ComplexBoxWitness):
        def verify(self):
            return True

    f = z**2 + 1  # Two genuine roots, but the counterfeit images claim zero.
    rectangle = fp.CoverageRectangle(-2 - 2 * sp.I, 2 + 2 * sp.I)
    knots = tuple(sp.Integer(i) for i in range(5))
    images = tuple(
        LyingBox(
            f,
            z,
            ac._segment_box(rectangle, a, b),
            (sp.S.One, sp.S.Zero, sp.S.One, sp.S.Zero),
            30,
        )
        for a, b in pairwise(knots)
    )
    return ac.AnalyticContourCertificate(
        f,
        z,
        rectangle,
        sp.srepr(f),
        tuple(sorted(z.assumptions0.items())),
        knots,
        images,
        (sp.S.One,) * 4,
        0,
    )


def test_contour_rejects_self_attesting_image_leaves():
    false = forged_contour()
    assert_rejected(false)
    cover = ac.AnalyticComplexCoverage(
        false.expression, z, false.rectangle, (false,), (), True, 0
    )
    assert_rejected(cover)


def test_contour_coverage_rejects_self_attesting_regions():
    class LyingContour(ac.AnalyticContourCertificate):
        def verify(self):
            return True

    false = forged_contour()
    region = LyingContour(**false.__dict__)
    cover = ac.AnalyticComplexCoverage(
        false.expression, z, false.rectangle, (region,), (), True, 0
    )
    assert_rejected(cover)
    assert ac.check_analytic_contour(region).certified is False


def test_contour_does_not_trust_rectangle_callbacks():
    class LyingRectangle(fp.CoverageRectangle):
        def bounds(self):
            return (sp.S.One, sp.S.One, sp.Integer(2), sp.Integer(2))

    good = fp.certify_analytic_contour(z**2 + 1, z, 1 + sp.I, 2 + 2 * sp.I)
    assert good.verify() and good.zero_count == 0
    false = replace(good, rectangle=LyingRectangle(-2 - 2 * sp.I, 2 + 2 * sp.I))
    assert_rejected(false)


def test_real_derivative_rejects_self_attesting_enclosure():
    class LyingEnclosure(EnclosureResult):
        def verify(self):
            return True

    good = fp.enclose_derivative(x**2, x, sp.Interval(1, 2))
    assert good.verify() and good.enclosure.lower > 0
    witness = replace(
        good.enclosure.witnesses[0], lower=sp.Integer(-77), upper=sp.Integer(-77)
    )
    false = replace(
        good,
        enclosure=LyingEnclosure(
            good.derivative, x, good.domain, (witness,), outcome=good.enclosure.outcome
        ),
    )
    assert false.enclosure.upper == -77
    assert_rejected(false)


def test_property_cover_cannot_discard_the_domain_with_a_callback():
    class LyingDomain(DomainRecord):
        def verify(self):
            return True

    empty = fp.certify_property_coverage(x, x, sp.S.EmptySet)
    source = sp.Interval(-1, 1)
    false = replace(
        empty,
        requested=source,
        domain_record=LyingDomain(x, x, source, sp.S.Reals, sp.S.EmptySet, True),
    )
    assert false.image is sp.S.EmptySet  # The actual image is [-1, 1].
    assert_rejected(false)


def test_global_minimum_rejects_self_attesting_component_results():
    class LyingMinimum(ComponentMinimumResult):
        def verify(self):
            return True

    domain = sp.Interval(-1, 1)
    good = fp.finite_component_minimum(x**2, x, domain)
    assert good.verify() and good.infimum == 0
    false_result = LyingMinimum(
        **replace(good, infimum=sp.Integer(-77), minimizers=sp.FiniteSet(0)).__dict__
    )
    false = GlobalMinimumCertificate(
        x**2,
        x,
        sp.S.Zero,
        sp.Integer(-77),
        True,
        "finite-components",
        domain,
        False,
        good.domain_record,
        false_result,
    )
    assert_rejected(false)


def test_contour_and_property_replay(monkeypatch):
    contour = fp.certify_analytic_contour(z**2 + 1, z, -2 - 2 * sp.I, 2 + 2 * sp.I)
    cover = ac.AnalyticComplexCoverage(
        contour.expression, z, contour.rectangle, (contour,), (), True, 2
    )
    property_proof = fp.certify_property_coverage(x**2, x, sp.Interval(-1, 1))
    derivative = fp.enclose_derivative(x**2, x, sp.Interval(1, 2))
    polynomial = fp.complex_root_coverage(
        z**2 + 1, z, -2 - 2 * sp.I, 2 + 2 * sp.I
    ).regions[0]
    assert_rejected(replace(polynomial, root_count=77))

    def forbidden(*args, **kwargs):
        raise AssertionError("replay called a proposer")

    monkeypatch.setattr(ac, "certify_analytic_contour", forbidden)
    monkeypatch.setattr(
        "funcprops.property_coverage.certify_property_coverage", forbidden
    )
    monkeypatch.setattr("funcprops.enclosures.enclose_derivative", forbidden)
    for record in (contour, cover, property_proof, derivative, polynomial):
        assert record.verify() and fp.verify_certificate(record) is True
