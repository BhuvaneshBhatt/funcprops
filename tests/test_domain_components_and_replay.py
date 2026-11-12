from dataclasses import replace

import pytest
import sympy as sp

from funcprops import (
    convexity,
    monotonicity,
    range,
    replay_status,
    sign,
    track_domain,
    verify_certificate,
)
from funcprops.proof_cache import property_proof_context

x, y = sp.symbols("x y", real=True)


def test_requested_natural_effective_domain():
    D = sp.Interval(-2, 3)
    r = track_domain(1 / x, x, D)
    assert r.requested == D
    assert r.natural == sp.S.Reals - sp.FiniteSet(0)
    assert r.effective == D - sp.FiniteSet(0)
    assert r.complete and r.certified and verify_certificate(r, expr=1 / x, var=x)


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


def test_proof_context_domain_assumptions():
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


def test_restricted_rewrite_source_expression():
    f = sp.Abs(x)
    r = sign(f, x, domain=x > 0, return_result=True)
    assert r.domain_record.expression == f
    assert r.domain_record.effective == sp.Interval.open(0, sp.oo)


def test_certificate_presence_status():
    status = replay_status(object())
    assert not status.supported and status.certified is None and status.complete is None


def test_domain_mutations_fail_replay():
    r = track_domain(1 / x, x)
    for bad in [
        replace(r, effective=sp.S.Reals),
        replace(r, exclusions=()),
        replace(r, complete=1),
    ]:
        assert not bad.verify() and not replay_status(bad).certified


def test_root_records_share_provenance_replay_status():
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


def test_partial_root_coverage():
    from funcprops.transcendental.roots import transcendental_roots

    r = replace(transcendental_roots(sp.sin(x), x), complete=False)
    status = replay_status(r)
    assert status.certified is True and status.complete is False


def test_detailed_property_domain_includes_assumptions():
    r = sign(x, x, domain=sp.Interval(-2, 2), assumptions=x > 0, return_result=True)
    assert r.domain_record.effective == sp.Interval.Lopen(0, 2)


def test_periodic_pole_domain_fresh_bound_indices():
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


def test_taylor_step_model_cannot_ignore_jump():
    from funcprops.taylor_models import TaylorModel, taylor_model

    f = sp.Piecewise((0, x < 0), (1, True))
    D = sp.Interval(-1, 1)
    assert taylor_model(f, x, D) is None
    assert not TaylorModel(f, x, D, 0, 2, sp.S.One, sp.S.Zero, sp.S.Zero).verify()


def test_taylor_source_hole():
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
