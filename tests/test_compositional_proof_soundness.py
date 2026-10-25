from dataclasses import replace

import pytest
import sympy as sp

from funcprops import replay_status, verify_certificate
from funcprops.asymptotic_tails import certify_tail_sign
from funcprops.certified_inequalities import certify_inequality
from funcprops.derivative_inequalities import derivative_chain_positive
from funcprops.global_analysis import (
    GlobalInequalityCertificate,
    certify_global_positive,
)
from funcprops.global_multivariate import affine_global_mapping, compose_global_maps
from funcprops.results import TruthValue

x, y, z = sp.symbols("x y z", real=True)
D = sp.Interval(0, 1)


def test_unknown_is_not_a_false_inequality_proof():
    c = certify_inequality(
        sp.Symbol("a", real=True) + x, 0, x, sp.Interval(-1, 1), max_depth=0
    )
    assert c.classification is TruthValue.UNKNOWN and not c.verify()
    assert not replace(c, classification=TruthValue.FALSE).verify()
    assert not replay_status(c).certified


def test_subdivision_proof_replays_without_global_enclosure():
    f = sp.exp(x) - 2 * x + sp.Rational(1, 2)
    c = certify_inequality(f, 0, x, D)
    assert c.classification is TruthValue.TRUE and c.source == "interval-subdivision"
    assert c.verify() and replay_status(c).certified
    a, b = c.evidence
    assert not replace(c, evidence=(a, a)).verify()
    assert not replace(c, evidence=(a, replace(b, domain=sp.Interval(2, 3)))).verify()


@pytest.mark.parametrize(
    "field,value",
    [
        ("expression", -sp.exp(x)),
        ("variable", y),
        ("domain", sp.Interval(-2, -1)),
        ("relation", "<"),
        ("classification", TruthValue.FALSE),
    ],
)
def test_inequality_nested_source_and_context_bindings(field, value):
    c = certify_inequality(sp.exp(x), 0, x, D)
    assert c.verify()
    assert not replace(c, **{field: value}).verify()


def test_original_cancellation_hole_cannot_receive_inequality_proof():
    f = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    c = certify_inequality(f, 0, x, sp.Interval(-1, 1))
    assert c.classification is TruthValue.UNKNOWN and not c.verify()
    assert c.domain_record.effective == sp.Interval(-1, 1) - sp.FiniteSet(0)
    valid = certify_inequality(f, 0, x, D - sp.FiniteSet(0))
    assert valid.classification is TruthValue.TRUE and valid.verify()


def test_source_rhs_hole_is_not_canceled():
    rhs = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    c = certify_inequality(2, rhs, x, sp.Interval(-1, 1))
    assert c.classification is TruthValue.UNKNOWN and not c.verify()


def test_source_subdivision_preserves_open_endpoints():
    c = certify_inequality(
        sp.exp(x) - 2 * x + sp.Rational(1, 2), 0, x, sp.Interval.open(0, 1)
    )
    assert c.verify()
    assert sp.Union(*(child.domain for child in c.evidence)) == c.domain


def test_global_proof_cannot_change_source_or_relation():
    c = certify_global_positive(x * x + 1, x)
    assert c.complete and c.verify()
    assert not replace(c, expression=-x * x - 1).verify()
    assert not replace(c, relation="<").verify()
    assert not replace(c, variable=y).verify()
    assert verify_certificate(c, expr=x * x + 1, var=x)
    assert not verify_certificate(c, expr=x * x - 1, var=x)


def test_valid_tails_do_not_cover_a_gap_around_negative_values():
    f = (x - 2) ** 2 - 1
    core = sp.Interval(-sp.Rational(1, 2), sp.Rational(1, 2))
    cc = certify_inequality(f, 0, x, core)
    lt = certify_tail_sign(f, x, direction=-1, threshold=8)
    rt = certify_tail_sign(f, x, direction=1, threshold=8)
    assert cc.verify() and lt.verify() and rt.verify() and f.subs(x, 2) < 0
    false = GlobalInequalityCertificate(f, x, ">", core, cc, lt, rt, True)
    assert not false.verify()


def test_global_core_unknown_is_not_a_positive_proof():
    c = certify_global_positive(x * x - 1, x, core_radius=2)
    assert not c.complete and not c.verify()


def test_global_source_hole_cannot_disappear_between_core_and_tails():
    f = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    c = certify_global_positive(f, x)
    assert not c.complete and not c.verify()


def test_derivative_chain_binds_actual_derivative():
    c = derivative_chain_positive(x, x, D)
    assert c.verify()
    assert not replace(c, expression=-x).verify()
    assert not replace(c, variable=y).verify()
    assert not replace(c, depth=2).verify()


def test_derivative_chain_endpoint_cannot_move_outside_domain():
    c = derivative_chain_positive(x, x, D)
    bad = replace(c, expression=x - 1, endpoint=sp.Integer(2))
    assert not bad.verify()


def test_chain_retains_weak_boundary_and_reports_strict_scope():
    c = derivative_chain_positive(sp.exp(x) - 1 - x, x, D)
    assert c.verify() and c.relation == ">="
    assert c.strict_domain == sp.Interval.Lopen(0, 1)
    d = derivative_chain_positive(x, x, sp.Interval.Lopen(0, 1))
    assert (
        d is not None
        and d.verify()
        and d.relation == ">"
        and d.strict_domain == d.domain
    )


def test_derivative_chain_rejects_jump_and_canceled_source_pole():
    for f in [
        sp.Piecewise((0, x < 0), (1, True)),
        sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False),
    ]:
        assert derivative_chain_positive(f, x, sp.Interval(-1, 1), max_depth=2) is None


def test_chain_base_domain_cannot_be_replaced():
    c = derivative_chain_positive(x, x, D)
    base = certify_inequality(1, 0, x, sp.Interval(2, 3))
    assert base.verify() and not replace(c, base_certificate=base).verify()


def test_piecewise_constant_jacobian_does_not_prove_affine_bijection():
    f = sp.Piecewise((x, x < 0), (x + 1, True))
    assert sp.diff(f, x) == 1
    c = affine_global_mapping((f,), (x,))
    assert c.classification is TruthValue.UNKNOWN and not c.verify()


def test_real_affine_helper_requires_real_offsets_and_coefficients():
    for f in [x + sp.I, sp.I * x]:
        c = affine_global_mapping((f,), (x,))
        assert c.classification is TruthValue.UNKNOWN and not c.verify()


def test_parameter_rank_is_not_assumed_generic():
    a = sp.Symbol("a", real=True)
    c = affine_global_mapping((a * x,), (x,))
    assert c.classification is TruthValue.UNKNOWN and c.cases and c.verify()
    b = sp.Symbol("b", positive=True)
    known = affine_global_mapping((b * x,), (x,))
    assert known.classification is TruthValue.TRUE and known.verify()


def test_helper_does_not_restore_source_definition_after_cancellation():
    f = sp.Mul(x, x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    c = affine_global_mapping((f,), (x,))
    assert c.classification is TruthValue.UNKNOWN and not c.verify()


def test_bound_affine_map_replays_true_and_false_rank_claims():
    a = affine_global_mapping((x + y, x - y), (x, y))
    assert a.verify() and verify_certificate(a, expr=(x + y, x - y), var=(x, y))
    assert not replace(a, expressions=(-x + y, x - y)).verify()
    assert not verify_certificate(a, expr=(x, y), var=(x, y))
    b = affine_global_mapping((x + y, 2 * x + 2 * y), (x, y))
    assert b.classification is TruthValue.FALSE and b.verify()
    assert not replace(b, classification=TruthValue.TRUE).verify()


def test_incompatible_composition_is_unknown_not_bijective():
    a = affine_global_mapping((x, y), (x, y))
    b = affine_global_mapping((x, y, z), (x, y, z))
    c = compose_global_maps((a, b))
    assert c.classification is TruthValue.UNKNOWN and not c.verify()
    assert not replace(c, classification=TruthValue.TRUE).verify()
    assert not replace(c, classification=TruthValue.FALSE).verify()


def test_rectangular_injection_composition():
    a = affine_global_mapping((x, 2 * x), (x,), kind="injective")
    b = affine_global_mapping((x, y, x + y), (x, y), kind="injective")
    c = compose_global_maps((a, b), kind="injective")
    assert c.classification is TruthValue.TRUE and c.verify()
    assert verify_certificate(c) and replay_status(c).certified
    assert not compose_global_maps((b, a), kind="injective").verify()


def test_failed_component_does_not_disprove_composite_injectivity():
    outer = affine_global_mapping((x,), (x, y), kind="injective")
    inner = affine_global_mapping((x, sp.S.Zero), (x,), kind="injective")
    c = compose_global_maps((inner, outer), kind="injective")
    assert c.classification is TruthValue.UNKNOWN and not c.verify()
    assert not replace(c, classification=TruthValue.FALSE).verify()


def test_invalid_radius_and_depth_fail_early():
    for R in [0, -1, sp.oo, sp.I]:
        with pytest.raises(ValueError):
            certify_global_positive(x * x + 1, x, core_radius=R)
    with pytest.raises(ValueError):
        certify_inequality(x, 0, x, D, relation="!=")
    with pytest.raises(ValueError):
        derivative_chain_positive(x, x, D, max_depth=True)


def test_rounded_float_determinant_is_not_an_exact_rank_proof():
    from funcprops import bijective, injective, surjective

    a = sp.Float("0.1")
    numeric = sp.Matrix([[sp.Float(1), a], [sp.Float(10), sp.Float(1)]])
    assert numeric.det() == 0
    assert numeric.applyfunc(sp.Rational).det() != 0
    expressions = (x + a * y, 10 * x + y)
    for query in (injective, surjective, bijective):
        assert query(expressions, (x, y)) is TruthValue.UNKNOWN
    helper = affine_global_mapping(expressions, (x, y))
    assert helper.classification is TruthValue.UNKNOWN and not helper.verify()
    assert bijective((x + sp.Rational(a) * y, 10 * x + y), (x, y)) is TruthValue.TRUE
    assert (
        bijective((x + sp.Rational(1, 10) * y, 10 * x + y), (x, y)) is TruthValue.FALSE
    )


def test_krawczyk_cannot_invent_root_across_piecewise_jump():
    from funcprops.multivariate_intervals import krawczyk_box

    f = sp.Piecewise((x - 1, x < 0), (x + 1, True))
    assert sp.diff(f, x) == 1
    assert krawczyk_box((f,), (x,), (sp.Interval(-2, 2),)) is None


def test_krawczyk_symbolic_inverse_requires_nonzero_center_jacobian():
    from funcprops.multivariate_intervals import krawczyk_box

    a = sp.Symbol("a", real=True)
    assert krawczyk_box((a * x,), (x,), (sp.Interval(-1, 1),)) is None
    b = sp.Symbol("b", positive=True)
    c = krawczyk_box((b * x,), (x,), (sp.Interval(-1, 1),))
    assert c.verify()


def test_factory_affine_krawczyk_requires_actual_zero_and_unique_rank():
    from funcprops.multivariate_intervals import KrawczykBoxCertificate

    for f, point in [(x + 5, sp.S.Zero), (sp.S.Zero, sp.S.Zero)]:
        bad = KrawczykBoxCertificate(
            (f,), (x,), (sp.Interval(-1, 1),), (point,), True, "affine-krawczyk"
        )
        assert not bad.verify()
    good = KrawczykBoxCertificate(
        (x,), (x,), (sp.Interval(-1, 1),), (sp.S.Zero,), True, "affine-krawczyk"
    )
    assert good.verify()


def test_krawczyk_source_and_center():
    from funcprops.multivariate_intervals import krawczyk_box

    c = krawczyk_box((x,), (x,), (sp.Interval(-1, 1),))
    assert not replace(c, center=(sp.Rational(1, 2),)).verify()
    for f in [
        sp.I * x,
        sp.Float(".1") * x,
        sp.Mul(x * x, sp.Pow(x, -1, evaluate=False), evaluate=False),
    ]:
        assert krawczyk_box((f,), (x,), (sp.Interval(-1, 1),)) is None


def test_float_determinant_does_not_disprove_inverse_theorem():
    from funcprops import determinant_nonvanishing, local_invertibility

    a = sp.Float(".1")
    f = (x + a * y, 10 * x + y)
    assert determinant_nonvanishing(f, (x, y)) is TruthValue.UNKNOWN
    c = local_invertibility(f, (x, y), return_result=True)
    assert c.classification is TruthValue.UNKNOWN
    assert not replace(c, classification=TruthValue.FALSE).verify()


def test_nested_unresolved_solution_set_does_not_claim_completeness():
    from funcprops.certified_operations import solve

    c = solve(x * (sp.cos(x) - x), x, domain=sp.S.Reals, return_certificate=True)
    assert isinstance(c.solutions, sp.Union) and c.solutions.has(sp.ConditionSet)
    assert c.complete is False and c.verify()
    assert not replace(c, complete=True).verify()
    assert not replace(c, complete=0).verify()


def test_explicit_solution_sets_complete():
    from funcprops.certified_operations import solve

    c = solve(x * x - 1, x, domain=sp.S.Reals, return_certificate=True)
    assert c.complete and c.verify() and c.solutions == sp.FiniteSet(-1, 1)
