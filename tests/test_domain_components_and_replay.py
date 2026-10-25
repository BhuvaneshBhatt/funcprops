from dataclasses import replace

import pytest
import sympy as sp

from funcprops import (
    certify_global_minimum,
    convexity,
    finite_component_minimum,
    monotonicity,
    range,
    replay_status,
    sign,
    track_domain,
    verify_certificate,
)
from funcprops.certified_optimization import GlobalMinimumCertificate
from funcprops.proof_cache import property_proof_context
from funcprops.results import as_detailed_result

x, y = sp.symbols("x y", real=True)


def test_requested_natural_effective_domain():
    D = sp.Interval(-2, 3)
    r = track_domain(1 / x, x, D)
    assert r.requested == D
    assert r.natural == sp.S.Reals - sp.FiniteSet(0)
    assert r.effective == D - sp.FiniteSet(0)
    assert r.complete and r.certified and verify_certificate(r, expr=1 / x, var=x)


def test_cancellation_retains_source_hole():
    f = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    r = track_domain(f, x)
    assert r.effective == sp.S.Reals - sp.FiniteSet(0)
    assert r.exclusions == (sp.Ne(x, 0),)
    assert not GlobalMinimumCertificate(f, x, 1, 1, False, "convex-stationary").verify()
    optimum = finite_component_minimum(f, x)
    assert optimum.certified and optimum.minimizers == r.effective


def test_cancelled_tangent_retains_original_poles():
    f = sp.Add(sp.tan(x), -sp.tan(x), evaluate=False)
    r = track_domain(f, x)
    assert r.complete and r.certified
    assert r.effective.contains(sp.pi / 2) is sp.S.false
    assert r.effective.contains(0) is sp.S.true


@pytest.mark.parametrize("f", [sp.gamma(x), sp.floor(x), sp.Heaviside(x)])
def test_unsupported_domain_stays_unknown(f):
    r = track_domain(f, x)
    assert not r.complete and not r.certified
    assert r.natural is None and r.effective is None and r.reason


def test_parameter_pole_is_not_assumed_away():
    a = sp.Symbol("a", real=True)
    assert not track_domain(1 / (a * x), x).complete


def test_unknown_requested_parameter_condition():
    a = sp.Symbol("a", real=True)
    assert not track_domain(x**2, x, a > 0).complete


def test_proof_context_combines_domain_and_assumptions():
    context = property_proof_context(
        1 / x, x, domain=sp.Interval(-2, 2), assumptions=x > 0
    )
    r = context.domain_record()
    assert r.effective == sp.Interval.Lopen(0, 2)
    assert r.certified


def test_public_range_keeps_original_domain_record():
    D = sp.Interval(-1, 1)
    r = range(1 / x, x, y, domain=D, return_result=True)
    assert r.domain_record.requested == sp.Contains(x, D)
    assert r.domain_record.effective == D - sp.FiniteSet(0)


@pytest.mark.parametrize("query", [sign, monotonicity, convexity])
def test_public_properties_share_provenance(query):
    D = sp.Interval(1, 2)
    r = query(1 / x, x, domain=D, return_result=True)
    assert r.domain_record.expression == 1 / x
    assert r.domain_record.effective == D


def test_restricted_rewrite_preserves_source_expression():
    f = sp.Abs(x)
    r = sign(f, x, domain=x > 0, return_result=True)
    assert r.domain_record.expression == f
    assert r.domain_record.effective == sp.Interval.open(0, sp.oo)


def test_finite_component_endpoint_minimum():
    D = sp.Union(sp.Interval(-3, -2), sp.Interval(1, 2))
    r = finite_component_minimum(x**2, x, D)
    assert r.complete and r.certified and r.infimum == 1
    assert r.minimizers == sp.FiniteSet(1) and r.unique
    c = certify_global_minimum(x**2, x, D)
    assert c.verify() and c.point == 1 and c.requested_domain == D


def test_open_endpoint_infimum_not_minimum():
    r = finite_component_minimum(x**2, x, sp.Interval.open(1, 2))
    assert r.certified and r.infimum == 1 and not r.attained
    assert r.minimizers is sp.S.EmptySet
    assert certify_global_minimum(x**2, x, sp.Interval.open(1, 2)) is None


def test_mixed_points_and_intervals():
    D = sp.Union(sp.Interval(2, 3), sp.FiniteSet(-1, 0))
    r = finite_component_minimum((x + 1) ** 2, x, D)
    assert r.certified and r.infimum == 0 and r.minimizers == sp.FiniteSet(-1)


def test_pole_components_and_nonunique_minima():
    r = finite_component_minimum(x**2 + 1 / x**2, x)
    assert r.certified and r.infimum == 2
    assert r.minimizers == sp.FiniteSet(-1, 1) and not r.unique
    c = certify_global_minimum(x**2 + 1 / x**2, x)
    assert c.verify() and not c.unique


def test_unbounded_below_is_complete_without_minimum():
    r = finite_component_minimum(1 / x, x)
    assert r.certified and r.infimum == -sp.oo and not r.attained
    assert certify_global_minimum(1 / x, x) is None


def test_constant_open_component_has_all_points_as_minimizers():
    D = sp.Union(sp.Interval.open(-2, -1), sp.Interval.open(1, 2))
    r = finite_component_minimum(sp.Integer(3), x, D)
    assert r.certified and r.infimum == 3 and r.minimizers == D
    c = certify_global_minimum(sp.Integer(3), x, D)
    assert c.verify() and not c.unique


def test_boolean_requested_domain_retained():
    requested = sp.And(x >= 2, x <= 3)
    c = certify_global_minimum(x**2, x, requested)
    assert c.verify() and c.point == 2
    assert c.requested_domain == requested and c.domain == sp.Interval(2, 3)


def test_empty_effective_domain_has_no_minimum():
    r = finite_component_minimum(1 / x, x, sp.FiniteSet(0))
    assert r.certified and r.infimum == sp.oo and not r.attained
    assert certify_global_minimum(1 / x, x, sp.FiniteSet(0)) is None


def test_unsupported_optimization_has_explicit_incomplete_status():
    r = finite_component_minimum(sp.sin(x) + x, x)
    status = replay_status(r)
    assert not r.complete and r.infimum is None and r.reason
    assert status.supported and status.certified is False and status.complete is False


def test_curvature_route_works_for_elementary_transcendentals():
    c = certify_global_minimum(sp.exp(x) + sp.exp(-x), x, x > -1)
    assert c.verify() and c.point == 0 and c.value == 2
    assert c.requested_domain == (x > -1)


def test_result_projection_keeps_provenance_and_status():
    r = finite_component_minimum(x**2, x, sp.Interval(-1, 1))
    detail = as_detailed_result(r)
    assert detail.domain_record == r.domain_record
    assert detail.complete is True and detail.certified is True
    assert detail.has_certificate


def test_status_does_not_promote_certificate_presence():
    status = replay_status(object())
    assert not status.supported and status.certified is None and status.complete is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("infimum", -1),
        ("minimizers", sp.FiniteSet(99)),
        ("candidates", ()),
        ("expression", x**2 + 1),
        ("complete", 1),
    ],
)
def test_component_mutations_fail_replay(field, value):
    r = finite_component_minimum(x**2, x, sp.Interval(-1, 1))
    bad = replace(r, **{field: value})
    assert not bad.verify() and not replay_status(bad).certified


def test_domain_mutations_fail_replay():
    r = track_domain(1 / x, x)
    for bad in [
        replace(r, effective=sp.S.Reals),
        replace(r, exclusions=()),
        replace(r, complete=1),
    ]:
        assert not bad.verify() and not replay_status(bad).certified


def test_minimum_certificates_bind_source_and_metadata():
    c = certify_global_minimum(x**2, x, sp.Interval(-1, 1))
    assert verify_certificate(c, expr=x**2, var=x)
    assert not verify_certificate(c, expr=x**2 + 1, var=x)
    assert not verify_certificate(c, var=y)
    for bad in [
        replace(c, point=1),
        replace(c, unique=False),
        replace(c, coercive=True),
        replace(c, component_result=None),
        replace(c, domain=sp.S.Reals),
    ]:
        assert not bad.verify()
    status = replay_status(c)
    assert status.supported and status.certified and status.complete
    assert status.scope == "global-minimum-on-effective-domain"


def test_malformed_records_fail_safely():
    c = certify_global_minimum(x**2, x)
    assert not replace(c, domain_record=object()).verify()
    r = finite_component_minimum(x**2, x)
    assert not replace(r, domain_record=object()).verify()


def test_root_records_share_provenance_and_replay_status():
    from funcprops.transcendental.roots import transcendental_roots

    r = transcendental_roots(sp.sin(x), x)
    assert r.domain_record.expression == sp.sin(x)
    assert r.domain_record.effective is sp.S.Reals
    assert r.verify()
    status = replay_status(r, expr=sp.sin(x), var=x)
    assert status.supported and status.certified and status.complete
    assert status.scope == "real-root-data-on-requested-domain"
    assert not replay_status(r, expr=sp.cos(x), var=x).certified
    assert not replace(r, domain_record=track_domain(sp.cos(x), x)).verify()
    assert not replace(r, complete=1).verify()


def test_partial_root_data_can_be_certified_without_complete_coverage():
    from funcprops.transcendental.roots import transcendental_roots

    r = replace(transcendental_roots(sp.sin(x), x), complete=False)
    status = replay_status(r)
    assert status.certified is True and status.complete is False


def test_detailed_property_domain_record_includes_assumptions():
    r = sign(x, x, domain=sp.Interval(-2, 2), assumptions=x > 0, return_result=True)
    assert r.domain_record.effective == sp.Interval.Lopen(0, 2)


def test_coercivity_claim_on_finite_interval_cannot_replay():
    c = GlobalMinimumCertificate(
        x**2, x, 0, 0, True, "strict-convex-stationary", sp.Interval(-1, 1), True
    )
    assert not c.verify()


def test_periodic_pole_domain_replays_with_fresh_bound_indices():
    from funcprops.transcendental.roots import transcendental_roots

    r = transcendental_roots(sp.tan(x), x)
    assert r.domain_record.certified and r.verify()
    assert replay_status(r).certified


@pytest.mark.parametrize(
    "D", [sp.Interval.open(0, 1), sp.Interval.Lopen(0, 1), sp.Interval.Ropen(-1, 0)]
)
def test_excluded_endpoint_is_not_a_counted_root(D):
    from funcprops.verified_roots import RealRootInterval, verify_real_root_interval

    r = verify_real_root_interval(x, x, D)
    assert r.root_count != 1
    assert not RealRootInterval(x, x, D, 1, True, "monotone-sign-change").verify()


def test_cancelled_pole_is_not_a_counted_root():
    from funcprops.verified_roots import RealRootInterval, verify_real_root_interval

    f = sp.Mul(x**2, sp.Pow(x, -1, evaluate=False), evaluate=False)
    D = sp.Interval(-1, 1)
    r = verify_real_root_interval(f, x, D)
    assert r.root_count is None and not r.certified
    assert not RealRootInterval(f, x, D, 1, True, "monotone-sign-change").verify()


def test_interval_root_replay_and_status():
    from funcprops.verified_roots import verify_real_root_interval

    for f, D, count in [
        (x, sp.Interval(0, 1), 1),
        (x, sp.Interval.open(-1, 1), 1),
        (x**2 + 1, sp.Interval(-1, 1), 0),
    ]:
        r = verify_real_root_interval(f, x, D)
        assert r.root_count == count and verify_certificate(r, expr=f, var=x)
        assert replay_status(r).certified and replay_status(r).complete
        assert not replace(r, unique=not r.unique).verify()


@pytest.mark.parametrize(
    "f,D",
    [(x**2 + sp.Float("0.1") * x, sp.S.Reals), (x**2, sp.Interval(sp.Float("0.1"), 1))],
)
def test_exact_component_route_declines_float_data(f, D):
    r = finite_component_minimum(f, x, D)
    assert not r.complete and not r.certified and r.reason
    assert certify_global_minimum(f, x, D) is None


def test_taylor_step_model_cannot_ignore_jump():
    from funcprops.taylor_models import TaylorModel, taylor_model

    f = sp.Piecewise((0, x < 0), (1, True))
    D = sp.Interval(-1, 1)
    assert taylor_model(f, x, D) is None
    assert not TaylorModel(f, x, D, 0, 2, sp.S.One, sp.S.Zero, sp.S.Zero).verify()


def test_taylor_source_hole_cannot_disappear_in_derivatives():
    from funcprops.taylor_models import taylor_model

    f = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    assert taylor_model(f, x, sp.Interval(-1, 1), center=sp.Rational(1, 2)) is None


def test_taylor_model_replays_with_source_provenance():
    from funcprops.taylor_models import taylor_model

    r = taylor_model(sp.exp(x), x, sp.Interval(-1, 1))
    assert r.domain_record.certified
    assert verify_certificate(r, expr=sp.exp(x), var=x)
    assert replay_status(r).certified and replay_status(r).complete
    assert not verify_certificate(r, expr=sp.sin(x), var=x)
    assert not replace(r, domain_record=track_domain(sp.cos(x), x)).verify()
