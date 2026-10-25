from dataclasses import replace
from unittest.mock import patch

import pytest
import sympy as s

import funcprops as fp
from funcprops.coverage_checker import regular_on_cell
from funcprops.coverage_search import coverage_context, propose_leaf

x = s.Symbol("x", real=True)
D = s.Interval(0, 1)


@pytest.mark.parametrize(
    "f,region,method,count",
    [
        (s.exp(x) + 1, D, "interval-exclusion", 0),
        (s.exp(x) - 2, D, "monotone-crossing", 1),
        (s.exp(x) - 1, s.Interval.open(0, 1), "monotone-crossing", 0),
        (s.exp(x) - 2, s.Interval(s.Rational(1, 2), 1), "interval-newton", 1),
        (s.exp(x) - 2, s.Interval(0, s.Rational(1, 10)), "interval-newton", 0),
        (s.exp(x) - 2 * x + s.Rational(1, 2), D, "taylor-exclusion", 0),
        ((x - 1) ** 3 * (x + 1) ** 2, s.Interval(-2, 2), "rational-sturm", 2),
        (s.exp(x) - 1, s.FiniteSet(0), "point-zero", 1),
        (s.exp(x), s.FiniteSet(0), "point-exclusion", 0),
    ],
)
def test_theorem_witnesses_replay_without_any_producer(f, region, method, count):
    leaf = propose_leaf(coverage_context(f, x, region), region, method=method)
    assert leaf.root_count == count and leaf.verify()

    def forbidden(*a, **kw):
        raise AssertionError("checker called a producer")

    with (
        patch("funcprops.coverage_search.propose_leaf", forbidden),
        patch("funcprops.root_coverage._local_data", forbidden),
        patch("funcprops.verified_roots.verify_real_root_interval", forbidden),
        patch("funcprops.verified_roots.interval_newton_count", forbidden),
        patch("funcprops.taylor_models.taylor_model", forbidden),
        patch("funcprops.enclosures.enclosure_witness", forbidden),
        patch.object(s.Poly, "real_roots", forbidden),
    ):
        assert leaf.verify()
    assert not replace(leaf, root_count=count + 1).verify()
    assert not replace(leaf, root_count=True).verify()


@pytest.mark.parametrize(
    "field,value",
    [
        ("expression", s.exp(x) - 3),
        ("variable", s.Symbol("y", real=True)),
        ("requested", s.Interval(-1, 1)),
        ("effective", s.Interval(0, 2)),
        ("source_syntax", "normalized expression"),
        ("coordinate_assumptions", ()),
        ("parameter_guard", s.Symbol("a") > 0),
    ],
)
def test_context_mutations_cannot_rebind_evidence(field, value):
    p = fp.prove_root_coverage(s.exp(x) - 2, x, D)
    c = replace(p.context, **{field: value})
    assert not replace(p, context=c).verify()
    assert not replace(p.leaves[0], context=c).verify()


@pytest.mark.parametrize(
    "method", ["monotone-crossing", "interval-newton", "taylor-exclusion"]
)
def test_derivative_witness_mutations(method):
    f = (
        s.exp(x) - 2
        if method != "taylor-exclusion"
        else s.exp(x) - 2 * x + s.Rational(1, 2)
    )
    region = s.Interval(s.Rational(1, 2), 1) if method == "interval-newton" else D
    p = propose_leaf(coverage_context(f, x, region), region, method=method)
    derivative = replace(
        p.witness.derivative, lower=s.Integer(100), upper=s.Integer(101)
    )
    assert not replace(p, witness=replace(p.witness, derivative=derivative)).verify()
    derivative = replace(p.witness.derivative, expression=s.Integer(1))
    assert not replace(p, witness=replace(p.witness, derivative=derivative)).verify()


def test_newton_midpoint_image_and_endpoint_bindings():
    region = s.Interval(s.Rational(1, 2), 1)
    p = propose_leaf(
        coverage_context(s.exp(x) - 2, x, region), region, method="interval-newton"
    )
    for name, value in [
        ("midpoint", s.S.Zero),
        ("image_lower", s.S.Zero),
        ("image_upper", s.S.One),
    ]:
        assert not replace(p, witness=replace(p.witness, **{name: value})).verify()
    assert not replace(p, region=D).verify()


def test_taylor_coefficient_order_center_and_remainder_mutations():
    f = s.exp(x) - 2 * x + s.Rational(1, 2)
    p = propose_leaf(coverage_context(f, x, D), D, method="taylor-exclusion")
    w = p.witness
    for field, value in [
        ("center", s.S.Zero),
        ("order", True),
        ("coefficients", (s.Integer(100),)),
        ("polynomial", s.Integer(100)),
        ("remainder_lower", s.S.Zero),
        ("remainder_upper", s.S.Zero),
    ]:
        assert not replace(p, witness=replace(w, **{field: value})).verify()


@pytest.mark.parametrize("order", [1, 2])
def test_higher_taylor_witnesses_replay_independently(order):
    f = s.exp(x) + 2
    leaf = propose_leaf(
        coverage_context(f, x, D), D, method="taylor-exclusion", taylor_order=order
    )
    assert leaf.witness.order == order and leaf.verify()
    with patch(
        "funcprops.taylor_models.taylor_model",
        side_effect=AssertionError("producer called"),
    ):
        assert leaf.verify()


def test_sturm_counts_multiplicities_and_algebraic_roots():
    p = fp.prove_root_coverage((x * x - 2) ** 3, x, s.Interval(-2, 2))
    assert p.verify() and p.root_count == 2 and p.multiplicity_count == 6
    leaf = p.leaves[0]
    assert not replace(leaf, multiplicity_count=2).verify()
    roots = leaf.roots
    assert not replace(leaf, roots=(roots[0], roots[0])).verify()
    assert not replace(leaf, roots=((roots[0][0], 2), roots[1])).verify()
    assert not replace(
        leaf, witness=replace(leaf.witness, numerator=(s.S.One,))
    ).verify()


@pytest.mark.parametrize(
    "left,right,count",
    [(False, False, 2), (True, False, 1), (False, True, 1), (True, True, 0)],
)
def test_sturm_endpoint_ownership(left, right, count):
    p = fp.prove_root_coverage(x * (x - 1), x, s.Interval(0, 1, left, right))
    assert p.verify() and p.root_count == count


def test_cover_gap_overlap_and_false_totals_are_rejected():
    region = s.Union(s.Interval(-2, -1), s.Interval(1, 2))
    p = fp.prove_root_coverage(x * x - 1, x, region)
    assert p.verify() and len(p.leaves) == 2
    assert not replace(p, leaves=p.leaves[:1]).verify()
    assert not replace(p, leaves=(*p.leaves, p.leaves[0])).verify()
    assert not replace(
        p,
        unresolved=s.FiniteSet(1),
        complete=False,
        root_count=None,
        multiplicity_count=None,
    ).verify()
    assert not replace(p, root_count=3).verify()
    assert not replace(p, complete=False).verify()


def test_partial_and_exhausted_status():
    p = fp.prove_root_coverage(
        s.exp(x) - 2, x, D, policy=fp.EnclosurePolicy(max_cells=0)
    )
    assert p.verify() and not p.complete and p.unresolved == D and p.root_count is None
    assert p.check().outcome is fp.CheckOutcome.EXHAUSTED
    assert fp.replay_status(p).outcome == "resource-exhaustion"
    assert not replace(p, complete=True, root_count=0, multiplicity_count=0).verify()
    assert fp.replay_status(replace(p, schema_version=2)).certified is None
    assert fp.replay_status(object()).certified is None


def test_parameter_guard_and_specialization_bind_original_held_source():
    a = s.Symbol("a", real=True)
    p = fp.prove_root_coverage(s.exp(x) - a, x, D, substitutions={a: 2})
    assert p.verify() and p.root_count == 1 and p.context.parameter_guard == s.Eq(a, 2)
    assert not replace(p, context=replace(p.context, parameter_guard=s.S.true)).verify()
    assert not replace(
        p, context=replace(p.context, substitutions=((a, s.Integer(3)),))
    ).verify()
    held = s.Mul(a, x, s.Pow(x, -1, evaluate=False), evaluate=False)
    p = fp.prove_root_coverage(held, x, s.Interval(-1, 1), substitutions={a: 2})
    assert p.verify() and p.root_count == 0
    assert p.context.effective == s.Interval(-1, 1) - s.FiniteSet(0)


def test_real_checker_does_not_inherit_selected_complex_sheets():
    p = fp.prove_root_coverage(s.log(x), x, s.Interval(1, 2))
    for point in (s.S.One, s.Integer(2)):
        branch = fp.LocalBranchContext(point, ((x, 2 * s.pi * s.I),))
        checked = replace(p, context=replace(p.context, branch_context=branch)).check()
        assert (
            checked.outcome is fp.CheckOutcome.UNSUPPORTED and checked.certified is None
        )


def test_inadmissible_real_input():
    p = fp.prove_root_coverage(s.I, x, D)
    assert (
        p.check().outcome is fp.CheckOutcome.INADMISSIBLE
        and p.verify()
        and not p.complete
    )
    assert not replace(p, expression=s.S.One).verify()


def test_coverage_export_replay():
    old = fp.root_coverage(s.exp(x) - 2, x, D)
    p = fp.export_coverage_proof(old)
    assert p.verify() and p.complete and p.root_count == old.root_count
    assert (
        fp.replay_status(old).factory_replay and not fp.replay_status(p).factory_replay
    )
    assert fp.verify_certificate(p, expr=s.exp(x) - 2, var=x)
    assert not fp.verify_certificate(p, expr=s.exp(x) - 3, var=x)


def test_continuity_does_not_upgrade_abs_corner_to_c1():
    assert regular_on_cell(s.Abs(x), x, s.Interval(-1, 1), 0)
    assert not regular_on_cell(s.Abs(x), x, s.Interval(-1, 1), 1)
    assert not regular_on_cell(s.sqrt(x), x, D, 1)
    f = s.Piecewise((x - 1, x < 0), (x + 1, True))
    assert not regular_on_cell(f, x, s.Interval(-1, 1), 1)
    p = fp.prove_root_coverage(f, x, s.Interval(-1, 1))
    assert p.verify() and p.complete and p.root_count == 0


def test_replay_inventory_contracts():
    from funcprops.verification import _certificate_verifiers

    manifest = fp.proof_api_manifest()
    records = {r["type"]: r for r in manifest["records"]}
    for cls, _ in _certificate_verifiers():
        assert records[cls.__module__ + "." + cls.__name__]["replay_supported"]
    assert (
        records["funcprops.root_coverage.RootRegionProof"]["contract"]
        == "factory-certificate"
    )
    assert (
        records["funcprops.coverage_contract.CoverageProof"]["contract"]
        == "witness-kernel"
    )
    assert {
        "root_coverage",
        "prove_root_coverage",
        "certify_inequality",
        "enclose_expression",
    } <= {r["api"] for r in manifest["public_entrypoints"]}


def test_factory_tail_threshold_mutation_does_not_escape_source_scope():
    tail = fp.certify_tail_sign(x - 2, x, threshold=3)
    assert tail.verify()
    assert not replace(tail, threshold=s.S.One).verify()


def test_held_zero_inequality(
    monkeypatch,
):
    # The baseline state probe recorded InconsistentAssumptions at the
    # simplify(original) replay step for this exact held source, before the
    # identity oracle was entered. Fault injection makes that failure stable.
    from sympy.core.facts import InconsistentAssumptions

    import funcprops.certified_inequalities as module

    cert = fp.certify_inequality(1, 0, x, D)
    original = s.simplify

    def reject_held_source(expr, *args, **kwargs):
        if expr == cert.source_expression:
            raise InconsistentAssumptions({}, "even", True)
        return original(expr, *args, **kwargs)

    monkeypatch.setattr(module.sp, "simplify", reject_held_source)
    assert cert.verify()
    chain = fp.derivative_chain_positive(x, x, D)
    assert chain.verify()


def test_float_endpoint_cannot_certify_wrong_rational_root_ownership():
    lo = s.Float("0.1")
    exact = s.Rational(lo)
    root = s.Rational(1, 10)
    assert exact > root
    # This is the backend comparison that made the baseline count incorrect.
    assert s.Interval(lo, 1).contains(root) is s.S.true
    for operation in (fp.root_coverage, fp.prove_root_coverage):
        p = operation(x - root, x, s.Interval(lo, 1))
        assert not p.complete and p.root_count is None and not p.verify()
        correct = operation(x - root, x, s.Interval(exact, 1))
        assert correct.verify() and correct.complete and correct.root_count == 0


def test_float_source_pole_cannot_certify_a_false_exact_exclusion():
    record = fp.track_domain(
        1 / (x - s.Float("0.1")), x, s.FiniteSet(s.Rational(1, 10))
    )
    assert not record.complete and not record.verify()
    assert record.reason == "inexact-source-expression"
