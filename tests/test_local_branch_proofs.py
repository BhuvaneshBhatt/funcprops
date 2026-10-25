"""Adversarial replay and mathematical regressions for practical proof paths."""

from dataclasses import replace

import sympy as s

from funcprops.certified_balls import certified_real_ball
from funcprops.certified_inequalities import certify_inequality
from funcprops.domain_tracking import smooth_domain_record, track_domain
from funcprops.global_multivariate import affine_global_mapping, compose_global_maps
from funcprops.results import TruthValue as T
from funcprops.verified_roots import verify_real_root_interval

x = s.Symbol("x", real=True)


def test_precision_is_effective_and_exact():
    a = certified_real_ball(s.exp(x), x, s.Interval(0, 1), precision=20)
    b = certified_real_ball(s.exp(x), x, s.Interval(0, 1), precision=80)
    assert a.verify() and b.verify()
    assert a.lower == b.lower == 1
    assert b.upper < a.upper
    assert b.upper.is_Rational
    assert not replace(b, upper=b.upper - s.Rational(1, 10) ** 90).verify()


def test_zero_contact_and_unattained_infimum():
    for f, D, relation in [
        (x * x, s.Interval(-1, 1), ">="),
        (x * x, s.Interval.open(0, 1), ">"),
        (-(x * x), s.Interval(-1, 1), "<="),
    ]:
        c = certify_inequality(f, 0, x, D, relation=relation, max_depth=0)
        assert c.classification is T.TRUE and c.verify()
        assert c.source == "exact-minimum"
        assert not replace(c, expression=f + 1).verify()


def test_false_has_bound_counterexample():
    c = certify_inequality(x, 0, x, s.Interval(-1, 1), max_depth=0)
    assert c.classification is T.FALSE and c.verify()
    assert not replace(c, evidence=(s.Integer(2), s.Integer(2))).verify()
    assert not replace(c, classification=T.TRUE).verify()


def test_logs_and_principal_roots_domains():
    for f, D in [(s.log(x), s.Interval(1, 2)), (s.sqrt(x), s.Interval(0, 1))]:
        c = track_domain(f, x, D)
        assert c.complete and c.effective == D and c.verify()
    c = track_domain(s.Pow(x, s.Rational(1, 3), evaluate=False), x, s.Interval(-1, 1))
    assert c.complete and c.effective == s.Interval(0, 1)
    held = s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False)
    assert track_domain(held, x, s.Interval(-1, 1)).effective != s.Interval(-1, 1)


def test_piecewise_local_domain_is_not_continuity():
    f = s.Piecewise((-1, x < 0), (1, True))
    D = s.Interval(-1, 1)
    r = track_domain(f, x, D)
    assert r.complete and r.verify() and r.natural is None and not r.natural_complete
    assert smooth_domain_record(f, x, D, 1) is None
    assert verify_real_root_interval(f, x, D).root_count is None
    g = s.Piecewise((s.log(x), x > 0), (0, True))
    assert track_domain(g, x, D).verify()


def test_guarded_mapping_composition():
    a = s.Symbol("a", real=True)
    c = affine_global_mapping((a * x,), (x,))
    assert c.classification is T.UNKNOWN and c.cases and c.verify()
    assert not replace(c, cases=()).verify()
    d = compose_global_maps((c, c))
    assert d.cases and d.verify()
    assert all(case.value is not T.FALSE for case in d.cases)


def test_zero_exclusion_reuses_complete_coverage():
    c = certify_inequality(s.sin(x), 0, x, s.Interval.open(0, 1), max_depth=3)
    assert c.source == "nonnegative-with-zero-exclusion" and c.verify()
    ball, coverage = c.evidence
    assert coverage.complete and coverage.root_count == 0
    assert not replace(c, evidence=(ball, replace(coverage, complete=False))).verify()
    assert not replace(c, domain=s.Interval(0, 1)).verify()


def test_false_children_cannot_prove_true_subdivision():
    a = certify_inequality(x, 0, x, s.Interval(-1, 0), max_depth=0)
    b = certify_inequality(x, 0, x, s.Interval(0, 1), max_depth=0)
    assert a.classification is b.classification is T.FALSE
    c = certify_inequality(x, 0, x, s.Interval(-1, 1), max_depth=0)
    assert not replace(
        c, classification=T.TRUE, source="interval-subdivision", evidence=(a, b)
    ).verify()


def test_tiny_bounds_do_not_underflow_to_zero():
    c = certified_real_ball(s.exp(x), x, s.Interval(-1000, -999), precision=60)
    assert c.lower > 0 and c.verify()
    assert not replace(c, precision=0).verify()


def test_piecewise_missing_values_and_guard_holes():
    D = s.Interval(-1, 1)
    missing = track_domain(s.Piecewise((1, x > 0)), x, D)
    assert missing.complete and missing.verify()
    assert missing.effective == s.Interval.Lopen(0, 1)
    condition = s.Gt(s.Pow(x, -1, evaluate=False), 0, evaluate=False)
    guarded = track_domain(s.Piecewise((1, condition), (0, True)), x, D)
    assert guarded.complete and guarded.verify()
    assert guarded.effective == D - s.FiniteSet(0)
    assert not replace(guarded, effective=D).verify()


def test_open_endpoint_is_not_a_counterexample():
    c = certify_inequality(x, 0, x, s.Interval.open(0, 1), max_depth=0)
    assert c.classification is T.TRUE and c.verify()
    assert not replace(
        c,
        classification=T.FALSE,
        source="point-counterexample",
        evidence=(s.S.Zero, s.S.Zero),
    ).verify()


def test_guarded_composition_reports_unresolved_cases():
    a = s.Symbol("a", real=True)
    c = compose_global_maps((affine_global_mapping((a * x,), (x,)),) * 2)
    assert c.certified and not c.complete
    assert not replace(c, cases=()).verify()


def test_unknown_affine_reality_cases_remain_incomplete():
    offset = s.Symbol("offset")
    c = affine_global_mapping((x + offset,), (x,))
    assert c.cases and c.certified and not c.complete
    assert any(case.value is T.UNKNOWN for case in c.cases)


def test_non_symbol_coordinate_cannot_fabricate_constant_bounds():
    for variable in (s.S.One, x + 1, s.Tuple(x)):
        assert certified_real_ball(s.S.One, variable, s.Interval(-2, -1)) is None


def test_held_source_cannot_escape_coordinate_assumptions():
    positive = s.Symbol("positive", positive=True)
    held = s.Abs(positive, evaluate=False)
    D = s.Interval(-2, -1)
    c = certify_inequality(held, 0, positive, D, relation="<")
    assert c.classification is T.UNKNOWN and not c.verify()
    assert not track_domain(held, positive, D).complete
    assert certify_inequality(held, 0, positive, s.Interval(1, 2)).verify()


def test_coordinate_assumption_conflicts():
    import pytest

    import funcprops as fp

    positive = s.Symbol("positive", positive=True)
    held = s.Abs(positive, evaluate=False)
    for operation in (fp.sign, fp.monotonicity, fp.convexity):
        with pytest.raises(ValueError, match="Symbol assumptions"):
            operation(held, positive, domain=s.Interval(-2, -1))


def test_affine_coordinate_scope():
    positive = s.Symbol("positive", positive=True)
    held = s.Abs(positive, evaluate=False)
    c = affine_global_mapping((held,), (positive,))
    assert c.classification is T.UNKNOWN and not c.verify()


def test_negative_assumption_facts_are_also_domain_premises():
    for assumptions, D in [
        ({"zero": False}, s.Interval(-1, 1)),
        ({"positive": False}, s.Interval(1, 2)),
        ({"negative": False}, s.Interval(-2, -1)),
        ({"integer": False}, s.Interval(0, 1)),
    ]:
        coordinate = s.Symbol("coordinate", **assumptions)
        assert not track_domain(coordinate, coordinate, D).complete
    coordinate = s.Symbol("coordinate", zero=False)
    held = s.Mul(coordinate, s.Pow(coordinate, -1, evaluate=False), evaluate=False)
    c = certify_inequality(held, 0, coordinate, s.Interval(-1, 1))
    assert c.classification is T.UNKNOWN and not c.verify()


def test_composition_case_budget_decline_is_not_unconditional_true():
    components = tuple(
        affine_global_mapping((s.Symbol(f"a_{k}", real=True) * x,), (x,))
        for k in range(9)
    )
    c = compose_global_maps(components)
    assert c.classification is T.UNKNOWN and not c.verify() and not c.complete
