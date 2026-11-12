import pytest
import sympy as sp

import funcprops as fp
from funcprops.work_budget import BudgetedResult


@pytest.mark.parametrize("operation", ["atlas", "value", "multiplicity", "common"])
def test_operations_honor_process_wall_budgets(operation):
    z = sp.Symbol("z")
    g = sp.exp(z) - 2
    rectangle = fp.CoverageRectangle(
        sp.Rational(69, 100) - sp.I / 100, sp.Rational(7, 10) + sp.I / 100
    )
    base = fp.certify_analytic_contour(
        g, z, rectangle.lower_left, rectangle.upper_right
    )
    policy = fp.EnclosurePolicy(seconds=0.001)
    if operation == "atlas":
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


def test_completed_worker_queries_proof_records():
    z = sp.Symbol("z")
    g = sp.exp(z) - 2
    rectangle = fp.CoverageRectangle(
        sp.Rational(69, 100) - sp.I / 100, sp.Rational(7, 10) + sp.I / 100
    )
    base = fp.certify_analytic_contour(
        g, z, rectangle.lower_left, rectangle.upper_right
    )
    policy = fp.EnclosurePolicy(seconds=30)
    results = (
        fp.certify_log_atlas(z, z, (rectangle,), policy=policy),
        fp.certify_root_value(g, base, work_budget=30),
        fp.certify_implicit_multiplicity(g, base, policy=policy),
        fp.certify_common_zero((g, sp.sin(g)), base, policy=policy),
    )
    assert all(fp.verify_certificate(p) is True for p in results)
    assert all(not isinstance(p, BudgetedResult) for p in results)
