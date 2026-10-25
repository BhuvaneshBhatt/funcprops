import sympy as sp

from funcprops import zeros
from funcprops.transcendental.roots import RootIsolationResult


def test_domain_cells_exclude_undefined_candidate_root():
    x = sp.symbols("x", real=True)
    expr = sp.log(x - 1) / (x - 2)

    result = zeros(expr, x, domain=sp.Interval(-10, 10), return_result=True)

    assert isinstance(result, RootIsolationResult)
    assert result.complete
    assert result.roots == ()
    assert result.zero_intervals == ()
    assert zeros(expr, x, domain=sp.Interval(-10, 10)) is sp.S.EmptySet
    assert "domain_cell_isolation" in result.method


def test_domain_cells_preserve_roots_on_valid_components():
    x = sp.symbols("x", real=True)
    expr = (x - 3) / (x - 2)

    result = zeros(expr, x, domain=sp.Interval(-10, 10), return_result=True)

    assert result.complete
    assert result.roots == (sp.Integer(3),)
    assert zeros(expr, x, domain=sp.Interval(-10, 10)) == sp.FiniteSet(3)


def test_disconnected_radical_domain_keeps_attained_boundary_roots():
    x = sp.symbols("x", real=True)
    expr = sp.sqrt((x - 1) * (x - 3))

    result = zeros(expr, x, domain=sp.Interval(-10, 10), return_result=True)

    assert result.complete
    assert result.roots == (sp.Integer(1), sp.Integer(3))


def test_piecewise_zero_interval_set():
    x = sp.symbols("x", real=True)
    expr = sp.Piecewise((0, x < 0), (x - 1, True))
    domain = sp.Interval(-2, 2)

    result = zeros(expr, x, domain=domain, return_result=True)

    assert result.complete
    assert result.roots == (sp.Integer(1),)
    assert result.zero_intervals == (sp.Interval.Ropen(-2, 0),)
    assert zeros(expr, x, domain=domain) == sp.Union(
        sp.FiniteSet(1), sp.Interval.Ropen(-2, 0)
    )
    assert any(
        c.method == "solveset_identically_zero_interval" for c in result.certificates
    )


def test_range_root_exclusion():
    x = sp.symbols("x", real=True)
    expr = x + sp.sin(x) + 4
    domain = sp.Interval(-1, 1)

    result = zeros(expr, x, domain=domain, return_result=True)

    assert result.complete
    assert result.roots == ()
    assert result.method == "certified_interval_resolution"
    assert result.certificates[0].method == "certified_interval_range_exclusion"


def test_derivative_range_resolves_unique_transcendental_root():
    x = sp.symbols("x", real=True)
    expr = x + sp.exp(x) - 3
    domain = sp.Interval(-1, 1)

    result = zeros(expr, x, domain=domain, return_result=True)

    assert result.complete
    assert result.isolated_intervals
    isolated = result.isolated_intervals[0]
    assert isolated.certificate.root_count == 1
    assert isolated.certificate.multiplicity == 1
    a, b = isolated.interval.start, isolated.interval.end
    assert sp.sign(expr.subs(x, a)) * sp.sign(expr.subs(x, b)) == -1
    assert isolated.certificate.method == "interval_resolution_rational_isolation"
