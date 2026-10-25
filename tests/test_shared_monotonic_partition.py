import sympy as sp

from funcprops import (
    Monotonicity,
    Oscillation,
    TruthValue,
    certified_monotonic_inverse,
    injective,
    monotonic_partition,
    monotonicity,
    oscillation,
    range,
    range_from_monotonic_partition,
    symbolic_extremum_range,
)

x, y = sp.symbols("x y", real=True)


def test_partition_cache_is_shared_identity():
    p1 = monotonic_partition(
        x**3 - 3 * x, x, domain=sp.Interval(-2, 2), return_result=True
    )
    p2 = monotonic_partition(
        x**3 - 3 * x, x, domain=sp.Interval(-2, 2), return_result=True
    )
    assert p1 is p2


def test_range_reuses_finite_partition_with_open_attainment():
    p = monotonic_partition(x**2, x, domain=sp.Interval.open(-1, 1), return_result=True)
    pr = range_from_monotonic_partition(x**2, x, p)
    assert pr.complete
    assert pr.image == sp.Interval.Ropen(0, 1)
    assert range(x**2, x, y, constraints=(x > -1) & (x < 1)) == ((y >= 0) & (y < 1))


def test_endpoint_derivative_zero_does_not_make_empty_cell():
    p = monotonic_partition(x**2, x, domain=sp.Interval(0, 1), return_result=True)
    assert p.complete
    assert len(p.cells) == 1
    assert p.critical_points == ()
    assert p.cells[0].direction is Monotonicity.STRICTLY_INCREASING


def test_stationary_inflection_shared_partition_proves_injective():
    p = monotonic_partition(x**3, x, domain=sp.Interval(-2, 2), return_result=True)
    assert p.complete and len(p.cells) == 2
    assert all(c.direction is Monotonicity.STRICTLY_INCREASING for c in p.cells)
    assert (
        monotonicity(x**3, x, domain=(x >= -2) & (x <= 2))
        is Monotonicity.STRICTLY_INCREASING
    )
    assert injective(x**3, x, domain=(x >= -2) & (x <= 2)) is TruthValue.TRUE


def test_inverse_solver_uses_partition_cells():
    p = monotonic_partition(
        x**3 - 3 * x, x, domain=sp.Interval(-2, 2), return_result=True
    )
    r = certified_monotonic_inverse(x**3 - 3 * x, x, 0, partition=p)
    assert r.complete
    assert r.partition is p
    assert r.solutions == sp.FiniteSet(-sp.sqrt(3), 0, sp.sqrt(3))


def test_finite_and_indexed_oscillation_from_partition():
    assert (
        oscillation(x**3 - 3 * x, x, domain=(x >= -2) & (x <= 2))
        is Oscillation.FINITELY_OSCILLATORY
    )
    nu = sp.symbols("nu", real=True, nonnegative=True)
    assert oscillation(sp.besselj(nu, x), x, domain=x > 0) is Oscillation.OSCILLATORY


def test_indexed_phase_not_guessed_without_theorem():
    nu = sp.symbols("nu", real=True, nonnegative=True)
    p = monotonic_partition(
        sp.besselj(nu, x), x, domain=sp.Interval.open(0, sp.oo), return_result=True
    )
    assert p.indexed.complete
    assert p.indexed.first_direction is None
    assert p.indexed.direction_pattern == ()


def test_support_completeness_is_not_domain_completeness():
    nu = sp.symbols("nu", real=True, nonnegative=True)
    p = monotonic_partition(sp.besselj(nu, x), x, domain=sp.S.Reals, return_result=True)
    assert not p.complete
    # The contained positive indexed family is still enough to prove oscillation.
    assert (
        oscillation(sp.besselj(nu, x), x, domain=sp.S.Reals) is Oscillation.OSCILLATORY
    )


def test_unknown_natural_domain_is_not_sympified_as_boolean():
    e = sp.Max(x, 0)
    # This used to be able to raise SympifyError when domain returned
    # a PropertyResult.  The explicit/global domain now remains usable.
    assert monotonicity(e, x) is Monotonicity.NONDECREASING


def test_extrema_uses_partition_critical_points():
    p = monotonic_partition(
        x**3 - 3 * x, x, domain=sp.Interval(-2, 2), return_result=True
    )
    assert p.critical_points_complete and p.critical_points == (-1, 1)
    r = symbolic_extremum_range(x**3 - 3 * x, x, sp.Interval(-2, 2), partition=p)
    assert r.complete and r.lower == -2 and r.upper == 2
