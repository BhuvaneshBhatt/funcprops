"""Adversarial tests for domain, replay, local germs and coverage extensions."""

from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops.domain_tracking import track_domain
from funcprops.local_analyticity import complex_meromorphic_germ
from funcprops.verified_roots import interval_newton_count

x = s.Symbol("x", real=True)
z = s.Symbol("z")


@pytest.mark.parametrize(
    "exponent", [s.pi, -s.sqrt(2), s.sqrt(2), s.Symbol("q", real=True)]
)
def test_positive_base_domain_coverage(exponent):
    e = s.Pow(x, exponent, evaluate=False)
    c = track_domain(e, x, s.Interval(1, 2))
    assert c.complete and c.verify() and c.effective == s.Interval(1, 2)
    if exponent.free_symbols:
        assert c.natural is None and c.natural_complete is False
    else:
        natural = s.Interval(0, s.oo) if exponent > 0 else s.Interval.open(0, s.oo)
        assert c.natural == natural and c.natural_complete is True
    assert not replace(c, requested=s.Interval(-1, 2)).verify()


@pytest.mark.parametrize(
    "base,expected", [(x, s.Interval(0, 1)), (x - 1, s.FiniteSet(1)), (s.log(x), None)]
)
def test_power_domain_real_loci(base, expected):
    e = s.Pow(base, s.pi, evaluate=False)
    result = track_domain(e, x, s.Interval(-1, 1))
    if expected is None:
        assert not result.complete and result.effective is None
    else:
        assert result.complete and result.effective == expected and result.verify()


def test_power_domain_retains_source_holes_and_unknown_exponents():
    hole = s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False)
    e = s.Pow(hole, s.pi, evaluate=False)
    result = track_domain(e, x, s.Interval(-1, 1))
    assert result.complete and result.verify()
    assert result.effective == s.Interval(-1, 1) - s.FiniteSet(0)
    assert not replace(result, effective=s.Interval(-1, 1)).verify()
    assert not track_domain(s.Pow(x, s.I, evaluate=False), x, s.Interval(1, 2)).complete
    assert not track_domain(s.Pow(x, x, evaluate=False), x, s.Interval(1, 2)).complete


@pytest.mark.parametrize(
    "k,m,a,expected",
    [(0, 1, 1, 1), (3, 2, 2, 2), (-2, 1, 1, 0), (1, 3, 2, 0), (2, 3, 3, 3)],
)
def test_exact_essential_laurent_family(k, m, a, expected):
    e = (z - 1) ** k * s.exp(a / (z - 1) ** m)
    c = fp.laurent_series(e, z, 1, return_certificate=True)
    assert c.verify() and c.certified and c.series.has(s.Sum)
    assert not replace(c, series=c.series + 1).verify()
    r = fp.residue(e, z, 1, return_certificate=True)
    assert r.verify() and r.residue == expected
    assert not replace(r, residue=r.residue + 1).verify()


def test_essential_linear_combinations_and_unsupported_compositions():
    e = s.exp(1 / z) + 2 * z * s.exp(3 / z)
    c = fp.residue(e, z, 0, return_certificate=True)
    assert c.residue == 10 and c.verify()
    assert fp.laurent_series(s.exp(s.exp(1 / z)), z, return_certificate=True) is None
    assert fp.residue(s.Abs(z) * s.exp(1 / z), z, 0, return_certificate=True) is None
    assert not complex_meromorphic_germ(s.Abs(z), z, 0)
    assert not complex_meromorphic_germ(1 / z, z, z)


@pytest.mark.parametrize(
    "guard,expected", [(s.Ne(z, 0), s.FiniteSet(0)), (s.Eq(z, 0), s.S.EmptySet)]
)
def test_complex_piecewise_first_match_domain_and_roots(guard, expected):
    e = s.Piecewise((1 / z, guard), (z, True))
    c = fp.solve(e, z, return_certificate=True)
    assert c.complete and c.verify() and c.solutions == expected
    assert not replace(c, solutions=s.FiniteSet(7)).verify()


def test_complex_piecewise_finite_roots_and_nested_arithmetic():
    e = s.Piecewise((z - 1, s.Eq(z, 1)), (z - 2, True))
    c = fp.solve(e, z, return_certificate=True)
    assert c.complete and c.verify() and c.solutions == s.FiniteSet(1, 2)
    c = fp.solve(e + 1, z, return_certificate=True)
    assert c.complete and c.verify() and c.solutions == s.S.EmptySet


def test_complex_source_guards():
    e = s.Piecewise((z, s.re(z) > 0), (z - 1, True))
    c = fp.solve(e, z, return_certificate=True)
    assert not c.complete and c.verify()
    bad = s.Mul(z, s.Pow(z, -1, evaluate=False), evaluate=False)
    e = s.Piecewise((z, s.Eq(bad, 1, evaluate=False)), (z - 1, True))
    assert not fp.solve(e, z, return_certificate=True).complete


@pytest.mark.parametrize(
    "function,interval,count",
    [
        (s.exp(x) - 2, s.Interval(0, 1), 1),
        (s.exp(x) - 4, s.Interval(0, 1), 0),
        (s.exp(x) - 2, s.Interval.open(0, 1), 1),
        (x * x, s.Interval(-1, 1), None),
    ],
)
def test_interval_newton_proof_boundaries(function, interval, count):
    assert interval_newton_count(function, x, interval) == count


def test_root_coverage_taylor_exclusion_and_incomplete_budget():
    e = s.exp(x) - 1 - x + s.Rational(1, 100)
    c = fp.root_coverage(e, x, s.Interval(-1, 1), max_depth=0)
    assert c.complete and c.root_count == 0 and c.verify()
    assert c.regions[0].method == "taylor-exclusion"
    assert not replace(c.regions[0], root_count=1).verify()
    unresolved = fp.root_coverage(s.sin(x) ** 2, x, s.Interval(-1, 1), max_cells=0)
    assert not unresolved.complete and unresolved.verify()


@pytest.mark.parametrize(
    "make",
    [
        lambda: fp.residue(s.exp(z) / z, z, 0, return_certificate=True),
        lambda: fp.laurent_series(1 / z, z, return_certificate=True),
        lambda: fp.inverse(x + 1, x, return_certificate=True),
        lambda: fp.solve(x - 1, x, domain=s.S.Reals, return_certificate=True),
    ],
)
def test_operation_replay_binds_caller_expression_and_coordinate(make):
    c = make()
    assert fp.verify_certificate(c, expr=c.expression, var=c.variable)
    assert not fp.verify_certificate(c, expr=c.expression + 1, var=c.variable)
    assert not fp.verify_certificate(c, expr=c.expression, var=s.Symbol("wrong"))


def test_isolated_replay_budget_has_distinct_unresolved_status():
    c = fp.residue(1 / z, z, 0, return_certificate=True)
    assert fp.verify_certificate(c, work_budget=1e-6) is None
    status = fp.replay_status(c, work_budget=1e-6)
    assert status.certified is None and status.complete is None
    assert status.reason == "work-budget-exhausted"
    assert fp.verify_certificate(c, work_budget=10) is True
    assert fp.replay_status(c, work_budget=10).certified is True
    assert fp.verify_certificate(c, expr=2 / z, work_budget=10) is False
    with pytest.raises(ValueError):
        fp.verify_certificate(c, work_budget=True)


def test_interval_newton_completes_a_rounding_limited_cell():
    cutoff = s.Rational(str(s.E.evalf(60))) - s.Rational(1, 10) ** 59
    e = (s.E - cutoff) * (x - s.Rational(1, 3))
    c = fp.root_coverage(e, x, s.Interval(0, 1), max_depth=0)
    assert c.complete and c.root_count == 1 and c.verify()
    assert c.regions[0].method == "interval-newton"
    assert not replace(c.regions[0], region=s.Interval(1, 2)).verify()


def test_shared_germ_cache_is_bounded_and_lifecycle_managed():
    fp.clear_caches()
    assert complex_meromorphic_germ(1 / z, z, 0)
    assert complex_meromorphic_germ(1 / z, z, 0)
    info = fp.cache_info()["complex_meromorphic_germ"]
    assert info.hits >= 1 and info.maxsize == 256
    fp.clear_caches()
    assert fp.cache_info()["complex_meromorphic_germ"].currsize == 0


@pytest.mark.parametrize("base", [s.im(z), s.sin(1 / z), s.exp(1 / z) - 1])
def test_raw_local_source_holes_survive_rebasing_and_cancellation(base):
    held = s.Mul(base, s.Pow(base, -1, evaluate=False), evaluate=False)
    assert fp.laurent_series(held, z, 0, return_certificate=True) is None
    assert fp.residue(held, z, 0, return_certificate=True) is None
    essential = s.Mul(held, s.exp(1 / z), evaluate=False)
    assert fp.laurent_series(essential, z, 0, return_certificate=True) is None
    assert fp.residue(essential, z, 0, return_certificate=True) is None


@pytest.mark.parametrize(
    "form",
    [
        lambda a: a * x,
        lambda a: a * x + 1,
        lambda a: a * (x * x - 1),
        lambda a: 1 / (a * x),
    ],
)
def test_equation_parameter_degeneracy_remains_unresolved(form):
    a = s.Symbol("a", real=True)
    c = fp.solve(form(a), x, domain=s.S.Reals, return_certificate=True)
    assert not c.complete and c.verify()


def test_safe_parameter_affine_and_nonzero_factors_remain_supported():
    a = s.Symbol("a", real=True)
    c = fp.solve(x - a, x, domain=s.S.Reals, return_certificate=True)
    assert c.complete and c.verify() and c.solutions == s.FiniteSet(a)
    nonzero = s.Symbol("nonzero", real=True, nonzero=True)
    c = fp.solve(nonzero * (x * x - 1), x, domain=s.S.Reals, return_certificate=True)
    assert c.complete and c.verify() and c.solutions == s.FiniteSet(-1, 1)


def test_parameter_domain_exclusions_do_not_ignore_zero_slope():
    a = s.Symbol("a", real=True)
    assert not track_domain(1 / (a * x), x, s.Interval(1, 2)).complete
    assert not track_domain(
        s.Pow(a * x, s.pi, evaluate=False), x, s.Interval(1, 2)
    ).complete
    nonzero = s.Symbol("nonzero", real=True, nonzero=True)
    c = track_domain(1 / (nonzero * x), x, s.Interval(1, 2))
    assert c.complete and c.verify()
