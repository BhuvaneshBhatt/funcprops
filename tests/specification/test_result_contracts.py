"""Executable obligations behind the public result-contract tables."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
x = sp.Symbol("x", real=True)
RECTANGLE = (-1 - sp.I, 1 + sp.I)


@pytest.mark.parametrize("case", ["complete", "cluster", "accuracy", "unresolved"])
def test_native_three_way_completion_contract(case):
    f = sp.sin(z) ** 2 if case == "cluster" else sp.exp(z) - 1
    options = {}
    if case in ("cluster", "accuracy"):
        options.update(policy=fp.EnclosurePolicy(max_depth=0), use_multiple=False)
    if case == "accuracy":
        options["max_box_width"] = sp.Rational(1, 100)
    if case == "unresolved":
        options["policy"] = fp.EnclosurePolicy(max_cells=0)
    result = fp.certify_complex_isolation(f, z, *RECTANGLE, **options)
    assert result.verify() and fp.verify_certificate(result)
    assert result.complete is (
        result.coverage_complete
        and result.isolation_complete
        and result.accuracy_complete
    )
    if case == "complete":
        assert result.complete and result.root_count == result.multiplicity_count == 1
    elif case == "cluster":
        assert result.coverage_complete and not result.isolation_complete
        assert result.multiplicity_count == 2 and result.root_count is None
    elif case == "accuracy":
        assert result.coverage_complete and result.isolation_complete
        assert not result.accuracy_complete and result.root_count == 1
    else:
        assert not result.coverage_complete and result.total_count is None
    status = fp.replay_status(result)
    assert status.certified is True and status.complete is result.complete


def test_algebraic_locations_do_not_imply_source_multiplicity():
    proof = fp.certify_algebraic_complex_roots(
        sp.sqrt(z), z, (-2 - 2 * sp.I, 2 + 2 * sp.I)
    )
    assert proof.verify() and proof.complete and proof.root_count == 1
    assert proof.multiplicity_count is None
    assert fp.replay_status(proof).factory_replay is True


def test_partial_property_replay_status():
    proof = fp.adaptive_root_coverage(
        sp.exp(x) - 2, x, sp.Interval(0, 1), policy=fp.EnclosurePolicy(max_cells=0)
    )
    status = fp.replay_status(proof)
    assert status.supported and status.certified is True and status.complete is False
    assert proof.root_count is None
    good = fp.prove_root_coverage(x, x, sp.Interval(-1, 1))
    bad = replace(good, root_count=77)
    assert fp.replay_status(bad).certified is False
    assert fp.replay_status(object()).certified is None


def test_conditional_contract_does_not_claim_finite_completion():
    run = fp.adaptive_quotient_isolation(1 / (sp.exp(z) - 2), z, *RECTANGLE, stages=0)
    theorem = run.termination_contract
    assert run.verify() and not run.complete
    assert theorem.verify() and theorem.conditional and theorem.complete is False
    assert theorem.applicable is None


def test_s0_s3_records_keep_native_replay_status_and_schema_checks():
    from dataclasses import fields, is_dataclass

    from funcprops.quotient_cofinal import (
        QuotientIsolationGuarantee,
        QuotientIsolationRun,
    )
    from funcprops.quotient_refinement import QuotientNewtonRefinement
    from funcprops.shared_zeros import (
        ComplexZeroSubsetProof,
        SharedZeroImplication,
        SharedZeroOrderProof,
        SharedZeroRegion,
    )

    expected = {
        QuotientIsolationRun,
        QuotientIsolationGuarantee,
        QuotientNewtonRefinement,
        SharedZeroImplication,
        SharedZeroOrderProof,
        SharedZeroRegion,
        ComplexZeroSubsetProof,
    }
    g = sp.exp(z) - 2
    parent = fp.certify_quotient_isolation(
        g / sp.sin(g) ** 2,
        z,
        sp.Rational(1, 2) - sp.I / 4,
        1 + sp.I / 4,
        policy=fp.EnclosurePolicy(max_cells=8192, max_depth=24, max_taylor_order=5),
    )
    refinement = fp.certify_quotient_refinement(parent)
    run = fp.adaptive_quotient_isolation(1 / g, z, *RECTANGLE, stages=0)
    found = {}
    visited = set()

    def visit(value):
        if id(value) in visited:
            return
        visited.add(id(value))
        if type(value) in expected:
            found.setdefault(type(value), value)
        if is_dataclass(value):
            for field in fields(value):
                visit(getattr(value, field.name))
        elif isinstance(value, (tuple, list)):
            for item in value:
                visit(item)

    for value in (parent, refinement, run, run.termination_contract):
        visit(value)
    zero_free = fp.certify_analytic_contour(sp.exp(z), z, *RECTANGLE)
    visit(ComplexZeroSubsetProof(zero_free, zero_free.rectangle))
    assert set(found) == expected
    for cls, record in found.items():
        status = fp.replay_status(record)
        checked = record.check()
        assert status.certified is True and status.factory_replay is False
        assert (
            status.complete is checked.complete
            and status.outcome == checked.outcome.value
        )
        assert status.schema_version == 1
        mismatch = fp.replay_status(record, expr=sp.Integer(77), var=z)
        assert mismatch.certified is False and mismatch.outcome == "rejected-evidence"
        unsupported = fp.replay_status(replace(record, schema_version=2))
        assert unsupported.certified is None and unsupported.supported is False
        assert (
            unsupported.factory_replay is False
            and unsupported.outcome == "unsupported-replay"
        )
        child = type(
            "Unregistered" + cls.__name__,
            (cls,),
            {"check": lambda self, checked=checked: checked},
        )
        forged = object.__new__(child)
        rejected = fp.replay_status(forged)
        assert rejected.certified is False and rejected.factory_replay is False


def test_shared_zero_implication_is_local_even_when_other_zeros_exist():
    from funcprops.shared_zeros import SharedZeroImplication

    g = sp.exp(z) - 2
    base = fp.certify_analytic_contour(g, z, *RECTANGLE)
    f = g * (z - sp.I / 2)
    implication = SharedZeroImplication(f, z, base, 1, cofactor=z - sp.I / 2)
    count = fp.certify_analytic_contour(f, z, *RECTANGLE)
    assert count.verify() and count.zero_count == 2
    assert implication.verify() and fp.verify_certificate(implication)
    assert implication.complete is False and implication.check().complete is False
    assert implication.check().outcome.value == "valid-local-proof"
    status = fp.replay_status(implication)
    assert (
        status.certified is True
        and status.complete is False
        and status.factory_replay is False
    )


def test_unregistered_status_callbacks():
    from funcprops.coverage_contract import CheckOutcome, CheckResult, CoverageProof

    good = fp.prove_root_coverage(x, x, sp.Interval(-1, 1))

    class Unregistered(CoverageProof):
        def check(self):
            return CheckResult(CheckOutcome.COMPLETE, True, True)

    forged = Unregistered(**replace(good, root_count=77).__dict__)
    assert forged.check().certified is True
    assert fp.verify_certificate(forged) is False
    status = fp.replay_status(forged)
    assert status.certified is False and status.complete is False
    assert status.factory_replay is False and status.outcome == "rejected-evidence"


@pytest.mark.parametrize(
    "result,expected",
    [
        (True, True),
        (False, False),
        (sp.S.true, True),
        (sp.S.false, False),
        (sp.Eq(x, 0), False),
        (sp.Integer(1), False),
        (None, False),
    ],
)
def test_public_replay_accepts_only_literal_exact_truth(monkeypatch, result, expected):
    import funcprops.verification as verification

    class Record:
        pass

    monkeypatch.setattr(
        verification,
        "_certificate_verifiers",
        lambda: ((Record, lambda cert, expr, var: result),),
    )
    assert fp.verify_certificate(Record()) is expected
