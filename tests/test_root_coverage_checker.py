from dataclasses import replace

import pytest
import sympy as sp

from funcprops import (
    CoverageRectangle,
    RootCoverageCertificate,
    complex_root_coverage,
    replay_status,
    root_coverage,
    specialize_root_coverage,
    verify_certificate,
)
from funcprops.domain_tracking import track_domain
from funcprops.root_coverage import _leaf

x = sp.Symbol("x", real=True)
z = sp.Symbol("z")


@pytest.mark.parametrize(
    "f,D,n,m",
    [
        (x, sp.Interval(-1, 1), 1, 1),
        (x**2, sp.Interval(-1, 1), 1, 2),
        ((x - 1) ** 3 * (x + 1) ** 2, sp.Interval(-2, 2), 2, 5),
        (x, sp.Interval.open(0, 1), 0, 0),
        (x, sp.Interval(0, 1), 1, 1),
        (x**2 - 2, sp.Interval(-2, 2), 2, 2),
        (1 / x, sp.Interval(-1, 1), 0, 0),
        (sp.Integer(1), sp.S.Reals, 0, 0),
        (sp.S.Zero, sp.Interval(-1, 1), sp.oo, None),
        (sp.S.Zero, sp.FiniteSet(0, 1), 2, None),
    ],
)
def test_exact_counts_and_multiplicities(f, D, n, m):
    r = root_coverage(f, x, D)
    assert (
        r.complete and r.certified and r.root_count == n and r.multiplicity_count == m
    )
    assert r.unresolved is sp.S.EmptySet
    assert verify_certificate(r, expr=f, var=x)


def test_transcendental_compact_simple_root():
    r = root_coverage(sp.exp(x) - 2, x, sp.Interval(0, 2))
    assert r.complete and r.root_count == 1 and r.verify()
    assert any(p.method == "interval" for p in r.regions)


def test_adaptive_transcendental_partition_and_endpoint_ownership():
    r = root_coverage(sp.sin(x), x, sp.Interval(-4, 4), max_depth=6)
    assert r.complete and r.root_count == 3 and r.verify()
    for i, a in enumerate(r.regions):
        for b in r.regions[i + 1 :]:
            assert sp.Intersection(a.region, b.region) is sp.S.EmptySet


@pytest.mark.parametrize(
    "kwargs", [{"max_cells": 0}, {"max_cells": 1, "max_depth": 0}, {"max_depth": 0}]
)
def test_budget_exhaustion_retains_unresolved(kwargs):
    r = root_coverage(sp.sin(x), x, sp.Interval(-4, 4), **kwargs)
    assert not r.complete and r.root_count is None and r.unresolved is not sp.S.EmptySet
    assert r.verify()
    assert not replace(r, complete=True).verify()
    status = replay_status(r)
    assert status.certified and status.complete is False


def test_tangent_transcendental_root_remains_unresolved():
    r = root_coverage(sp.sin(x) ** 2, x, sp.Interval(-1, 1), max_depth=3, max_cells=20)
    assert not r.complete and r.unresolved.contains(0) is sp.S.true
    assert r.verify()


def test_deleted_region_is_a_gap():
    r = root_coverage(sp.sin(x), x, sp.Interval(-4, 4))
    bad = replace(r, regions=r.regions[1:])
    assert not bad.verify()


def test_duplicate_region_double_count_rejected():
    r = root_coverage(x, x, sp.Interval(-1, 1))
    assert not replace(
        r, regions=r.regions * 2, root_count=2, multiplicity_count=2
    ).verify()


def test_missing_single_endpoint_is_a_gap():
    D = sp.Interval(-1, 1)
    left = _leaf(x, x, sp.Interval.Ropen(-1, 0), "exact-rational")
    right = _leaf(x, x, sp.Interval.Lopen(0, 1), "exact-rational")
    r = RootCoverageCertificate(
        x,
        x,
        track_domain(x, x, D),
        (left, right),
        complete=True,
        root_count=0,
        multiplicity_count=0,
    )
    assert not r.verify()
    point = _leaf(x, x, sp.FiniteSet(0), "exact-rational")
    good = replace(r, regions=(left, point, right), root_count=1, multiplicity_count=1)
    assert good.verify()


def test_unresolved_cannot_overlap_proved_root():
    r = root_coverage(x, x, sp.Interval(-1, 1))
    assert not replace(
        r,
        unresolved=sp.FiniteSet(0),
        complete=False,
        root_count=None,
        multiplicity_count=None,
    ).verify()


@pytest.mark.parametrize(
    "field,value",
    [
        ("root_count", 99),
        ("multiplicity_count", 99),
        ("expression", x + 1),
        ("complete", 1),
    ],
)
def test_coverage_mutations(field, value):
    r = root_coverage(x, x, sp.Interval(-1, 1))
    assert not replace(r, **{field: value}).verify()


def test_leaf_proof_is_bound_to_source_and_region():
    r = root_coverage(x, x, sp.Interval(-1, 1))
    p = r.regions[0]
    for bad in [
        replace(p, root_count=0),
        replace(p, roots=()),
        replace(p, region=sp.Interval(1, 2)),
        replace(p, expression=x + 5),
    ]:
        assert not bad.verify()
        assert not replace(r, regions=(bad,)).verify()
    assert not verify_certificate(r, expr=x + 1, var=x)


def test_source_hole_is_excluded_not_an_invented_zero():
    f = sp.Mul(x**2, sp.Pow(x, -1, evaluate=False), evaluate=False)
    r = root_coverage(f, x, sp.Interval(-1, 1))
    assert r.complete and r.root_count == 0 and r.verify()
    assert r.domain.contains(0) is sp.S.false
    assert not replace(r, domain_record=track_domain(x, x, sp.Interval(-1, 1))).verify()


def test_periodic_exhaustive_family_covers_infinite_domain():
    r = root_coverage(sp.sin(x), x)
    assert r.complete and r.root_count is sp.oo and r.verify()
    assert r.regions[0].method == "periodic-family"
    assert not replace(r, regions=(replace(r.regions[0], witness=None),)).verify()


def test_periodic_search_cannot_replace_unknown_infinite_coverage():
    r = root_coverage(sp.sin(x), x, use_families=False)
    assert not r.complete and r.unresolved is sp.S.Reals and r.verify()


def test_strict_tail_exclusion_and_threshold_binding():
    f = (x + 1) * sp.exp(x)
    D = sp.Interval(1, sp.oo)
    r = root_coverage(f, x, D)
    assert r.complete and r.root_count == 0 and r.verify()
    p = r.regions[0]
    assert p.method == "tail"
    bad = replace(p, region=sp.Interval(-2, sp.oo))
    assert not bad.verify()
    assert not replace(p, witness=replace(p.witness, threshold=10)).verify()


def test_unproved_infinite_tail_remains_unresolved():
    r = root_coverage(sp.exp(x) - x, x, sp.Interval(0, sp.oo))
    assert not r.complete and r.root_count is None and r.verify()


def test_empty_effective_domain_is_complete():
    r = root_coverage(1 / x, x, sp.FiniteSet(0))
    assert r.complete and r.root_count == 0 and r.verify()


def test_unsupported_definition_domain_is_not_complete():
    r = root_coverage(sp.gamma(x), x, sp.Interval(1, 2))
    assert not r.complete and r.reason and not r.certified


@pytest.mark.parametrize("value,count", [(1, 2), (0, 1), (-1, 0)])
def test_parameter_specialization_preserves_guard(value, count):
    a = sp.Symbol("a", real=True)
    r = specialize_root_coverage(x * x - a, x, {a: value}, sp.Interval(-2, 2))
    assert r.complete and r.verify() and r.coverage.root_count == count
    assert r.guard == sp.Eq(a, value)
    assert replay_status(r).certified
    assert not replace(r, substitutions=((a, sp.Integer(value + 1)),)).verify()


def test_parameter_specialization_cannot_hide_pole():
    a = sp.Symbol("a", real=True)
    f = sp.Mul(x, a, sp.Pow(a, -1, evaluate=False), evaluate=False)
    r = specialize_root_coverage(f, x, {a: 0}, sp.Interval(-1, 1))
    assert not r.complete and not r.certified


def test_unresolved_parameter_root_count_stays_partial():
    a = sp.Symbol("a", real=True)
    r = root_coverage(x * x - a, x, sp.Interval(-2, 2), max_depth=1, max_cells=3)
    assert not r.complete and r.root_count is None


def test_invalid_budgets_rejected():
    for kwargs in [{"max_depth": True}, {"max_cells": -1}, {"max_cells": 1.5}]:
        with pytest.raises(ValueError):
            root_coverage(x, x, **kwargs)


@pytest.mark.parametrize(
    "f,count,multiplicity",
    [(z * z + 1, 2, 2), ((z - 1) ** 2, 1, 2), (sp.Integer(1), 0, 0)],
)
def test_complex_polynomial_contour_coverage(f, count, multiplicity):
    r = complex_root_coverage(f, z, -2 - 2 * sp.I, 2 + 2 * sp.I)
    assert (
        r.complete
        and r.root_count == count
        and r.multiplicity_count == multiplicity
        and r.verify()
    )
    assert replay_status(r).certified
    assert not verify_certificate(r, expr=f + 1, var=z)


def test_complex_boundary_root_is_unresolved():
    r = complex_root_coverage(z - 1, z, -1 - sp.I, 1 + sp.I)
    assert not r.complete and r.unresolved and r.verify()
    assert not replace(r, complete=True).verify()


def test_complex_tiling_count_additivity_and_gap_rejection():
    target = complex_root_coverage(z * z + 1, z, -2 - 2 * sp.I, 2 + 2 * sp.I)
    left = complex_root_coverage(z * z + 1, z, -2 - 2 * sp.I, -1 + 2 * sp.I)
    right = complex_root_coverage(z * z + 1, z, -1 - 2 * sp.I, 2 + 2 * sp.I)
    r = replace(target, regions=left.regions + right.regions)
    assert r.verify()
    assert not replace(r, regions=right.regions).verify()
    assert not replace(
        r, regions=target.regions * 2, root_count=4, multiplicity_count=4
    ).verify()


def test_complex_source_hole_not_canceled_into_polynomial():
    f = sp.Mul(z**2, sp.Pow(z, -1, evaluate=False), evaluate=False)
    r = complex_root_coverage(f, z, -2 - 2 * sp.I, 2 + 2 * sp.I)
    assert not r.complete and r.verify()


def test_complex_invalid_rectangle_rejected():
    with pytest.raises(ValueError):
        complex_root_coverage(z, z, 1 + sp.I, -1 - sp.I)
    assert not CoverageRectangle(sp.S.Zero, sp.I).valid()


def test_tail_helper_cannot_capture_user_parameter():
    from funcprops.asymptotic_tails import TailSignCertificate, certify_tail_sign

    y = sp.Symbol("_tail_y", nonnegative=True)
    f = x - y
    assert f.subs({x: 1, y: 2}) < 0
    assert certify_tail_sign(f, x, threshold=1) is None
    forged = TailSignCertificate(f, x, 1, sp.S.One, 1, "polynomial-leading-term")
    assert not forged.verify()
    r = root_coverage(f, x, sp.Interval(1, sp.oo))
    assert not r.complete and r.root_count is None and r.verify()


def test_counts_cannot_be_booleans():
    r = root_coverage(x + 5, x, sp.Interval(-1, 1))
    assert not replace(r, root_count=False).verify()
    assert not replace(r, multiplicity_count=False).verify()
    assert not replace(r.regions[0], multiplicity_count=False).verify()
    c = complex_root_coverage(z + 5, z, -1 - sp.I, 1 + sp.I)
    assert not replace(c, root_count=False).verify()


def test_inconsistent_parameter_guard_is_not_a_certificate():
    a = sp.Symbol("a", positive=True)
    r = specialize_root_coverage(x - a, x, {a: -1}, sp.Interval(-2, 2))
    assert r.guard is sp.S.false and not r.certified and not r.complete


@pytest.mark.parametrize("f", [z + sp.I, z + sp.sqrt(2), sp.sin(z), 1 / z])
def test_unsupported_complex_contour_family_is_explicitly_unresolved(f):
    r = complex_root_coverage(f, z, -2 - 2 * sp.I, 2 + 2 * sp.I)
    assert not r.complete and r.root_count is None and r.verify()


def test_exact_nonrational_constant_uses_interval_proof():
    r = root_coverage(x + sp.pi, x, sp.Interval(-4, 4))
    assert r.complete and r.root_count == 1 and r.verify()
