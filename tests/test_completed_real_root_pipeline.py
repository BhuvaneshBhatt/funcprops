import sympy as sp

from funcprops import (
    exponential_fourier_count,
    function_zeros,
    robust_real_sign,
    solve_monotonic_inverse,
)
from funcprops.transcendental.real_interval import certified_real_interval_evaluate

x = sp.symbols("x", real=True)


def test_domain_cells_split_piecewise_exception_and_keep_zero_interval():
    expr = sp.Piecewise((0, x < 0), (x - 1, True))
    result = function_zeros(expr, x, domain=sp.Interval(-2, 2), return_result=True)
    assert result.complete
    assert result.zero_intervals == (sp.Interval.Ropen(-2, 0),)
    assert result.roots == (sp.Integer(1),)
    assert "domain_cell_isolation" in result.method


def test_domain_cells_do_not_cross_log_or_pole_boundaries():
    expr = sp.log(x - 1) / (x - 2)
    result = function_zeros(expr, x, domain=sp.Interval(-10, 10), return_result=True)
    assert result.complete
    assert result.roots == ()
    assert "domain_cell_isolation" in result.method
    domains = tuple(c.domain for c in result.certificates)
    assert sp.Interval.open(1, 2) in domains
    assert sp.Interval.Lopen(2, 10) in domains


def test_interval_arithmetic_can_prove_root_free_cell():
    expr = sp.exp(x) + x**2 + 10
    enclosure = certified_real_interval_evaluate(expr, x, sp.Interval(-1, 1))
    assert enclosure is not None
    assert enclosure.excludes_zero
    assert enclosure.strict_sign == 1


def test_interval_arithmetic_derivative_can_certify_unique_root():
    expr = x + sp.exp(x) - 3
    result = function_zeros(expr, x, domain=sp.Interval(-1, 1), return_result=True)
    assert result.complete
    assert len(result.isolated_intervals) == 1
    cert = result.isolated_intervals[0].certificate
    assert cert.root_count == 1
    assert any(
        item[0] == "derivative_interval"
        for item in cert.proof
        if isinstance(item, tuple)
    )


def test_certified_monotonic_inverse_returns_isolating_interval():
    cert = solve_monotonic_inverse(x + sp.exp(x), x, 3, domain=sp.Interval(-1, 2))
    assert cert.complete
    assert len(cert.isolated_intervals) == 1
    iv = cert.isolated_intervals[0].interval
    assert robust_real_sign(iv.start + sp.exp(iv.start) - 3) == -1
    assert robust_real_sign(iv.end + sp.exp(iv.end) - 3) == 1


def test_robust_exp_log_sign_avoids_overflow():
    assert robust_real_sign(sp.exp(10000) - sp.exp(9999)) == 1
    assert robust_real_sign(sp.exp(-9999) - sp.exp(-10000)) == 1
    assert robust_real_sign(sp.log(sp.Rational(3, 2))) == 1


def test_exponential_fourier_derivative_sequence_counts_roots():
    expr = sp.exp(2 * x) - 3 * sp.exp(x) + 2
    count = exponential_fourier_count(expr, x, sp.Interval(-10, 10))
    assert count is not None
    assert count.complete
    assert count.root_count == 2
    assert len(count.sequence) == 3


def test_exponential_fourier_respects_open_endpoint_roots():
    expr = sp.exp(2 * x) - 3 * sp.exp(x) + 2
    count = exponential_fourier_count(expr, x, sp.Interval.open(0, sp.log(2)))
    assert count is not None
    assert count.complete
    assert count.root_count == 0
