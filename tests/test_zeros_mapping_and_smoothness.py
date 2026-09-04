import sympy as sp

from funcprops import (
    Boundedness,
    Continuity,
    TruthValue,
    function_bijective,
    function_boundedness,
    function_injective,
    function_smoothness,
    function_surjective,
    function_zeros,
)
from funcprops.transcendental import PeriodicSet, RootIsolationResult

x = sp.symbols("x", real=True)
y = sp.symbols("y", real=True)


def test_zeros_periodic_and_exact():
    z = function_zeros(sp.sin(x), x)
    assert isinstance(z, PeriodicSet)
    assert function_zeros(sp.exp(x) - 2, x) == sp.FiniteSet(sp.log(2))
    assert function_zeros(sp.erf(x), x) == sp.FiniteSet(0)


def test_zeros_implicit_certificate():
    z = function_zeros(x + sp.exp(x) - 3, x, domain=sp.Interval(0, 2))
    assert isinstance(z, RootIsolationResult) and z.complete and z.isolated_intervals


def test_boundedness():
    assert function_boundedness(sp.sin(x), x) is Boundedness.BOUNDED
    assert function_boundedness(sp.exp(x), x) is Boundedness.BOUNDED_BELOW
    assert function_boundedness(x, x) is Boundedness.UNBOUNDED


def test_mapping():
    assert function_injective(sp.exp(x), x) is TruthValue.TRUE
    assert function_injective(x**2, x) is TruthValue.FALSE
    assert function_injective(x**2, x, domain=x >= 0) is TruthValue.TRUE
    assert (
        function_surjective(sp.exp(x), x, codomain=sp.Interval.open(0, sp.oo))
        is TruthValue.TRUE
    )
    assert function_surjective(sp.exp(x), x, codomain=sp.S.Reals) is TruthValue.FALSE
    assert (
        function_bijective(sp.exp(x), x, codomain=sp.Interval.open(0, sp.oo))
        is TruthValue.TRUE
    )


def test_smoothness_abs_exp():
    a = function_smoothness(sp.Abs(x), x)
    assert a.continuity is Continuity.CONTINUOUS
    assert sp.Eq(x, 0) in a.exceptional_loci
    e = function_smoothness(sp.exp(x), x)
    assert e.smooth is True and e.differentiability_order is sp.oo


def test_certified_real_interval_isolation_multiple_transcendental_roots():
    expr = sp.sin(x) - x / 10
    z = function_zeros(expr, x, domain=sp.Interval(-10, 10), return_result=True)
    assert isinstance(z, RootIsolationResult)
    assert z.complete
    assert z.method == "certified_real_interval_isolation"
    assert z.roots == (sp.Integer(0),)
    assert len(z.isolated_intervals) == 6
    assert len(z.roots) + len(z.isolated_intervals) == 7
    for isolated in z.isolated_intervals:
        interval = isolated.interval
        assert interval.start.is_Rational and interval.end.is_Rational
        assert (
            sp.sign(expr.subs(x, interval.start)) * sp.sign(expr.subs(x, interval.end))
            == -1
        )
        assert isolated.certificate.root_count == 1
        assert isolated.certificate.multiplicity == 1


def test_certified_real_interval_isolation_keeps_metadata_optional():
    expr = sp.cos(x) - x
    direct = function_zeros(expr, x, domain=sp.Interval(0, 1))
    detailed = function_zeros(expr, x, domain=sp.Interval(0, 1), return_result=True)
    assert isinstance(direct, RootIsolationResult)
    assert isinstance(detailed, RootIsolationResult)
    assert detailed.complete and len(detailed.isolated_intervals) == 1
    assert direct == detailed


def test_repeated_factor_lifts_isolation_and_multiplicity():
    expr = (sp.cos(x) - x) ** 2
    z = function_zeros(expr, x, domain=sp.Interval(0, 1), return_result=True)
    assert isinstance(z, RootIsolationResult)
    assert z.complete
    assert z.method == "repeated_factor_root_isolation"
    assert len(z.isolated_intervals) == 1
    isolated = z.isolated_intervals[0]
    assert isolated.certificate.multiplicity == 2
    assert isolated.certificate.root_count == 1
    assert (
        sp.sign((sp.cos(x) - x).subs(x, isolated.interval.start))
        * sp.sign((sp.cos(x) - x).subs(x, isolated.interval.end))
        == -1
    )


def test_validated_numeric_even_root_requires_exact_validation():
    expr = x**2 + sp.sin(x) ** 2
    z = function_zeros(
        expr,
        x,
        domain=sp.Interval(-2, 2),
        return_result=True,
        allow_numerical=True,
    )
    assert isinstance(z, RootIsolationResult)
    assert not z.complete
    assert z.method == "validated_even_multiplicity_numeric_fallback"
    assert z.roots == (sp.Integer(0),)
    assert len(z.certificates) == 1
    cert = z.certificates[0]
    assert cert.multiplicity == 2
    assert cert.method == "numerical_candidate+exact_even_multiplicity_validation"
    assert sp.simplify(expr.subs(x, z.roots[0])) == 0
