import sympy as sp
from sympy import S

from funcprops import (
    Analyticity,
    Continuity,
    Convexity,
    TruthValue,
    function_boundary_behavior,
    function_geometry,
    function_level_boundedness,
    function_mode_existence,
    verify_certificate,
)


def test_boundary_behavior_records_both_real_escape_limits():
    x = sp.symbols("x", real=True)
    result = function_boundary_behavior(x**2, x)
    assert result.complete
    assert tuple(item.endpoint for item in result.limits) == (
        S.NegativeInfinity,
        S.Infinity,
    )
    assert all(item.value is S.Infinity for item in result.limits)


def test_univariate_level_boundedness_from_infinity_limits():
    x = sp.symbols("x", real=True)
    assert function_level_boundedness(x**4 - x, x) is TruthValue.TRUE
    positive = function_level_boundedness(x**4 - x, x, return_result=True)
    assert positive.classification is TruthValue.TRUE
    assert positive.source == "boundary-plus-infinity"
    assert positive.verify()
    assert verify_certificate(positive)
    assert function_level_boundedness(sp.exp(x), x) is TruthValue.FALSE
    negative = function_level_boundedness(sp.exp(x), x, return_result=True)
    assert negative.classification is TruthValue.FALSE
    assert negative.source == "escaping-nonpositive-infinity"


def test_bounded_domain_is_level_bounded_but_open_domain_does_not_prove_mode():
    x = sp.symbols("x", real=True)
    domain = sp.Interval.open(0, 1)
    cert = function_level_boundedness(x, x, domain=domain, return_result=True)
    assert cert.classification is TruthValue.TRUE
    mode = function_mode_existence(x, x, domain=domain, sense="max", return_result=True)
    assert mode.exists is None
    assert mode.domain_closed is TruthValue.FALSE


def test_mode_existence_for_coercive_minimum_and_log_density_maximum():
    x = sp.symbols("x", real=True)
    assert function_mode_existence(x**2 + 1, x, sense="min") is TruthValue.TRUE
    minimum = function_mode_existence(x**2 + 1, x, sense="min", return_result=True)
    assert minimum.exists is True
    assert minimum.verify()
    assert verify_certificate(minimum)
    maximum = function_mode_existence(-(x**2) / 2, x, sense="max", return_result=True)
    assert maximum.exists is True
    assert maximum.verify()


def test_multivariate_strong_convexity_certifies_level_boundedness():
    x, y = sp.symbols("x y", real=True)
    cert = function_level_boundedness(x**2 + y**2, (x, y), return_result=True)
    assert cert.classification is TruthValue.TRUE
    assert cert.source in {"strong-convexity", "separable-coercivity"}
    assert function_mode_existence(x**2 + y**2, (x, y), sense="min") is TruthValue.TRUE


def test_multivariate_separable_high_even_powers_are_coercive():
    x, y = sp.symbols("x y", real=True)
    cert = function_level_boundedness(x**4 + y**6 + 3, (x, y), return_result=True)
    assert cert.classification is TruthValue.TRUE
    assert cert.source == "separable-coercivity"


def test_function_geometry_combines_regularity_and_attainment_contracts():
    x = sp.symbols("x", real=True)
    result = function_geometry(x**2, x)
    assert result.continuity is Continuity.CONTINUOUS
    assert result.c2 is TruthValue.TRUE
    assert result.analytic is Analyticity.ANALYTIC
    assert result.convexity in {
        Convexity.STRONGLY_CONVEX,
        Convexity.STRICTLY_CONVEX,
        Convexity.CONVEX,
    }
    assert result.singularities.singularities is S.false
    assert result.level_boundedness.classification is TruthValue.TRUE
    assert result.minimum_exists.exists is True
    assert result.maximum_exists.exists is None


def test_boundary_behavior_on_bounded_domain_has_no_escape_limits():
    x = sp.symbols("x", real=True)
    result = function_boundary_behavior(x**2, x, domain=sp.Interval(-1, 2))
    assert result.complete
    assert result.limits == ()


def test_function_geometry_retains_singularity_information():
    x = sp.symbols("x", real=True)
    result = function_geometry(1 / x, x)
    assert result.singularities.singularities is not S.false
    assert result.level_boundedness.classification is not TruthValue.TRUE


def test_geometry_rejects_invalid_coordinates():
    x = sp.symbols("x")
    for variables in ((), (x, x)):
        try:
            function_geometry(x**2, variables)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected invalid variables to fail: {variables!r}")
    try:
        function_geometry(x**2, 1)
    except TypeError:
        pass
    else:
        raise AssertionError("numeric coordinate should fail")
