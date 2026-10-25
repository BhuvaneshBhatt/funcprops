"""Exact coefficient fields choose supported portfolios before backend loading."""

import pytest
import sympy as sp

import funcprops as fp
from funcprops import _semialg

x = sp.Symbol("x", real=True)


@pytest.mark.parametrize(
    "coefficient,kind",
    [
        (sp.S.One, "rational"),
        (sp.sqrt(2), "algebraic"),
        (sp.pi, "transcendental"),
        (sp.E, "transcendental"),
        (sp.I, "nonreal"),
        (sp.Float("1.25"), "inexact"),
    ],
)
def test_coefficient_fields(coefficient, kind):
    assert _semialg.coefficient_profile(coefficient * x, x).kind == kind


def test_parameters_are_not_numeric_coefficients():
    a = sp.Symbol("a", real=True)
    profile = _semialg.coefficient_profile(a * x + 1, x, conditions=(x > a,))
    assert profile.kind == "rational" and profile.parameters == (a,)
    assert _semialg.eligible_problem(a * x + 1, x, domain=x > a)
    assert _semialg.coefficient_profile(sp.sqrt(2) * a * x, x).kind == "algebraic"


def test_conditions_participate_in_routing():
    assert not _semialg.eligible_problem(x * x, x, domain=x > sp.pi)
    assert (
        _semialg.coefficient_profile(
            x, x, conditions=(sp.Interval(-sp.oo, sp.sqrt(2)),)
        ).kind
        == "algebraic"
    )


@pytest.mark.parametrize(
    "call",
    [
        lambda c: _semialg.domain(c * x, x),
        lambda c: _semialg.sign(c * x, x),
        lambda c: _semialg.sign_partition(c * x, x),
        lambda c: _semialg.range(c * x, x, sp.Symbol("y", real=True)),
        lambda c: _semialg.monotonicity(c * x, x),
        lambda c: _semialg.convexity(c * x * x, x),
        lambda c: _semialg.smoothness(c * x, x),
        lambda c: _semialg.function_mapping_properties(c * x, x),
        lambda c: _semialg.prove_sign(c * x, x, "positive"),
    ],
)
def test_unsupported_fields_skip_backend(monkeypatch, call):
    def unavailable(_name):
        pytest.fail("rational backend loaded for unsupported coefficients")

    monkeypatch.setattr(_semialg, "_public_function", unavailable)
    for coefficient in (sp.sqrt(2) + sp.sqrt(3) + sp.sqrt(5), sp.pi, sp.I):
        with pytest.raises(NotImplementedError, match="coefficients"):
            call(coefficient)


@pytest.mark.parametrize("coefficient", [sp.sqrt(2), sp.pi, sp.E])
def test_native_routes_retain_results(coefficient):
    assert fp.sign(coefficient * x, x, domain=x > 0) is fp.Sign.POSITIVE
    assert fp.monotonicity(coefficient * x, x) is fp.Monotonicity.STRICTLY_INCREASING
    assert fp.convexity(coefficient * x * x, x) in (
        fp.Convexity.STRICTLY_CONVEX,
        fp.Convexity.STRONGLY_CONVEX,
    )
    y = sp.Symbol("y", real=True)
    actual = fp.range(coefficient * x, x, y, constraints=sp.FiniteSet(0, 1))
    from funcprops.real_analysis.common import condition_to_set

    assert condition_to_set(actual, y) == sp.FiniteSet(0, coefficient)


def test_coefficient_cache_lifecycle():
    fp.clear_caches()
    _semialg.coefficient_profile(sp.sqrt(2) * x, x)
    _semialg.coefficient_profile(sp.sqrt(2) * x, x)
    assert fp.cache_info()["coefficient_profiles"].hits == 1
    fp.clear_caches()
    assert fp.cache_info()["coefficient_profiles"].currsize == 0
