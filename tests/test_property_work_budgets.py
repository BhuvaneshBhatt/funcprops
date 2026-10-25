"""Property and mapping wall budgets retain explicit incomplete outcomes."""

import inspect

import pytest
import sympy as sp

import funcprops as fp
from funcprops.work_budget import PROPERTY_BUDGET_OPERATIONS, BudgetedResult

x = sp.Symbol("x", real=True)


@pytest.mark.parametrize(
    "name",
    sorted(PROPERTY_BUDGET_OPERATIONS - {"range", "sign", "monotonicity", "convexity"}),
)
def test_property_exhaustion(name):
    function = getattr(fp, name)
    assert "work_budget" in inspect.signature(function).parameters
    result = function(x, x, work_budget=1e-6)
    assert isinstance(result, BudgetedResult)
    assert result.operation == name and result.outcome == "resource-exhaustion"
    assert (
        result.complete is False
        and result.certified is False
        and result.verify() is False
    )
    assert fp.as_detailed_result(result).complete is False


@pytest.mark.parametrize(
    "name",
    [
        "jacobian",
        "determinant_nonvanishing",
        "local_invertibility",
        "change_of_variables",
        "transformation_geometry",
    ],
)
def test_mapping_exhaustion(name):
    result = getattr(fp, name)(2 * x, x, work_budget=1e-6)
    assert isinstance(result, BudgetedResult)
    assert (
        result.operation == name
        and result.complete is False
        and result.verify() is False
    )


def test_domain_record_exhaustion():
    requested = sp.Interval(0, 1)
    result = fp.track_domain(x ** sp.sqrt(2), x, requested, work_budget=1e-6)
    assert isinstance(result, fp.DomainRecord)
    assert result.expression == x ** sp.sqrt(2) and result.requested == requested
    assert result.natural is None and result.effective is None
    assert result.complete is False and result.natural_complete is False
    assert result.reason == "work-budget-exhausted" and result.verify() is False


@pytest.mark.parametrize("budget", [True, 0, -1, float("nan"), float("inf")])
def test_invalid_budgets(budget):
    with pytest.raises(ValueError, match="finite positive"):
        fp.domain(x, x, work_budget=budget)


def test_completed_property_workers():
    assert fp.domain(x ** sp.sqrt(2), x, work_budget=10) == (x >= 0)
    logarithm = sp.log(x, sp.Rational(1, 2), evaluate=False)
    assert fp.lipschitz(logarithm, x, domain=sp.Interval(2, 4), work_budget=10) == 1 / (
        2 * sp.log(2)
    )
    assert fp.injective(2 * x, x, work_budget=10) is fp.TruthValue.TRUE
    record = fp.track_domain(x ** sp.sqrt(2), x, sp.Interval(0, 1), work_budget=10)
    assert record.complete and record.effective == sp.Interval(0, 1) and record.verify()
    assert fp.jacobian(2 * x, x, work_budget=10) == sp.Matrix([[2]])


def test_worker_errors_propagate():
    with pytest.raises(ValueError):
        fp.domain(x, x, domain="invalid", work_budget=10)
