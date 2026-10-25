from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.work_budget import BudgetedResult


@pytest.mark.parametrize(
    "operation", ["extrema", "atlas", "value", "multiplicity", "common"]
)
def test_operations_honor_process_wall_budgets(operation):
    x = sp.Symbol("x", real=True)
    z = sp.Symbol("z")
    g = sp.exp(z) - 2
    rectangle = fp.CoverageRectangle(
        sp.Rational(69, 100) - sp.I / 100, sp.Rational(7, 10) + sp.I / 100
    )
    base = fp.certify_analytic_contour(
        g, z, rectangle.lower_left, rectangle.upper_right
    )
    policy = fp.EnclosurePolicy(seconds=0.001)
    if operation == "extrema":
        result = fp.certify_extrema_bounds(
            sp.exp(x) + x * x, x, sp.Interval(-1, 1), policy=policy
        )
    elif operation == "atlas":
        result = fp.certify_log_atlas(z, z, (rectangle,), policy=policy)
    elif operation == "value":
        result = fp.certify_root_value(sp.sin(g), base, work_budget=0.001)
    elif operation == "multiplicity":
        result = fp.certify_implicit_multiplicity(sp.sin(g), base, policy=policy)
    else:
        result = fp.certify_common_zero((g, sp.sin(g)), base, policy=policy)
    assert isinstance(result, BudgetedResult)
    assert not result.complete and result.verify() is False
    assert fp.replay_status(result).outcome == "resource-exhaustion"


def test_failed_value_accuracy_does_not_erase_valid_extrema_bounds():
    x = sp.Symbol("x", real=True)
    policy = fp.EnclosurePolicy(
        precision=5, max_precision=5, max_refinements=0, max_depth=1, max_cells=32
    )
    proof = fp.certify_extrema_bounds(
        sp.exp(x) + x * x,
        x,
        sp.Interval(-1, 1),
        tolerance=sp.Rational(1, 10**80),
        policy=policy,
    )
    assert (
        proof.verify() and proof.coverage_complete and proof.minimum_bounds is not None
    )
    assert not proof.accuracy_complete and not proof.complete
    assert (
        fp.verify_certificate(replace(proof, minimum_bounds=(sp.S.Zero, sp.S.Zero)))
        is False
    )


def test_completed_worker_queries_preserve_proof_records():
    x, z = sp.Symbol("x", real=True), sp.Symbol("z")
    g = sp.exp(z) - 2
    rectangle = fp.CoverageRectangle(
        sp.Rational(69, 100) - sp.I / 100, sp.Rational(7, 10) + sp.I / 100
    )
    base = fp.certify_analytic_contour(
        g, z, rectangle.lower_left, rectangle.upper_right
    )
    policy = fp.EnclosurePolicy(seconds=30)
    results = (
        fp.certify_extrema_bounds(x, x, sp.Interval(0, 1), policy=policy),
        fp.certify_log_atlas(z, z, (rectangle,), policy=policy),
        fp.certify_root_value(g, base, work_budget=30),
        fp.certify_implicit_multiplicity(g, base, policy=policy),
        fp.certify_common_zero((g, sp.sin(g)), base, policy=policy),
    )
    assert all(fp.verify_certificate(p) is True for p in results)
    assert all(not isinstance(p, BudgetedResult) for p in results)
