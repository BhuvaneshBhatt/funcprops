import sympy as sp

import funcprops as fp
from funcprops.proof_cache import (
    clear_property_proof_cache,
    property_proof_cache_info,
    property_proof_context,
)
from funcprops.results import Monotonicity, TruthValue

x = sp.symbols("x", real=True)


def test_property_proof_context_is_lazy_and_canonical():
    clear_property_proof_cache()
    ctx = property_proof_context(x**2, x, domain=sp.Interval(-1, 1))
    info = property_proof_cache_info()
    assert (
        info["domain"].misses == 0
        and info["sign"].misses == 0
        and info["zero_geometry"].misses == 0
    )
    assert ctx.derivative() == 2 * x
    assert property_proof_cache_info()["derivative"].misses == 1


def test_monotonic_partition_helpers_directly():
    p = fp.monotonic_partition(
        x**3 - 3 * x, x, domain=sp.Interval(-2, 2), return_result=True
    )
    assert p.complete and len(p.cells) == 3
    r = fp.range_from_monotonic_partition(x**3 - 3 * x, x, p)
    assert r.complete and r.image == sp.Interval(-2, 2)
    assert fp.injectivity_from_partition(p) is TruthValue.FALSE
    inv = fp.certified_monotonic_inverse(
        x**3 - 3 * x, x, 0, domain=sp.Interval(-2, 2), partition=p
    )
    assert inv.complete and inv.solutions == sp.FiniteSet(-sp.sqrt(3), 0, sp.sqrt(3))


def test_property_interval_decomposition_directly():
    d = fp.property_interval_decomposition(
        x**3 - 3 * x,
        x,
        derivative_order=1,
        domain=sp.Interval(-2, 2),
        positive_value=1,
        negative_value=-1,
    )
    assert d.cells and d.boundary_geometry


def test_simplify_extremum_range_directly():
    r = fp.symbolic_extremum_range(x**2, x, sp.Interval(-1, 2))
    s = fp.simplify_extremum_range(x**2, x, r)
    assert s.complete and s.lower == 0 and s.upper == 4


def test_cache_clear_helper_directly():
    fp.monotonic_partition(x**2, x, domain=sp.Interval(-1, 1), return_result=True)
    fp.clear_monotonic_partition_cache()
    info = property_proof_cache_info()
    assert info["derivative"].currsize == 0 and info["zero_geometry"].currsize == 0


def test_certificate_replay_monotonicity_and_zero_geometry():
    p = fp.monotonic_partition(
        x**3 - 3 * x, x, domain=sp.Interval(-2, 2), return_result=True
    )
    assert fp.verify_monotonic_partition(x**3 - 3 * x, x, p)
    assert fp.verify_certificate(p, expr=x**3 - 3 * x, var=x)
    g = fp.zero_geometry(sp.besselj(0, x), x)
    assert g and all(fp.verify_zero_geometry(c) for c in g)


def test_certificate_replay_decomposition_and_convexity():
    d = fp.monotonic_decomposition(sp.acos(sp.exp(x)), x, return_result=True)
    assert fp.verify_monotonic_decomposition(d)
    from funcprops.real_analysis.advanced_convexity import strong_convexity

    got = strong_convexity(x**2, x, sp.Interval(-2, 2))
    _cls, cert = got
    assert fp.verify_convexity_certificate(x**2, x, cert)


def test_certificate_replay_tail_and_extremum_theorem():
    k = sp.Symbol("k", integer=True, positive=True)
    z = fp.IndexedZero("BesselJ", k, 0, 0, "positive")
    cert = fp.indexed_tail_inversion(z, fp.IndexedZero("BesselJ", 3, 0, 0, "positive"))
    assert fp.verify_indexed_tail_inversion(cert)
    th = fp.extremum_ordering_theorems(sp.airyai(x), x)
    assert th and all(fp.verify_extremum_ordering(t) for t in th)


def test_remaining_exported_helpers_direct_contracts():
    assert fp.registry().require("erf").id == "erf"
    assert isinstance(fp.dlmf_facts("BesselJ"), tuple)
    fp.dlmf_audit_report(
        "BesselJ"
    )  # direct API contract: may be None when family has no audit rows
    k = sp.Symbol("k", integer=True, positive=True)
    z = fp.IndexedZero("BesselJ", k, 0, 0, "positive")
    assert fp.zero_ordering_bounds(z)
    b = fp.indexed_tail_integer_bracket(z, 10)
    assert b.lower <= b.upper
    assert fp.extremum_geometry(sp.airyai(x), x)
    roots = fp.transcendental_roots(
        sp.sin(x), x, sp.Interval(0, 2 * sp.pi), allow_numerical=False
    )
    assert roots.complete and roots.roots == (0, sp.pi, 2 * sp.pi)
    red = fp.reduce_univariate_condition(sp.sin(x) > 0, x, sp.Interval(0, 2 * sp.pi))
    assert red.complete
    alg = fp.algebraize(sp.exp(2 * x) - 3 * sp.exp(x) + 2, x)
    assert alg.exact
    assert fp.holomorphic_on_rectangle(sp.exp(x), x, (-1, 1, -1, 1)).holomorphic is True
    assert (
        fp.analytic_neighborhood(sp.exp(x), x, sp.Interval(-1, 1)).holomorphic is True
    )


def test_exported_function_api_contract_manifest_is_complete():
    tested = {
        "domain",
        "range",
        "branch_cuts",
        "branch_points",
        "poles",
        "singularities",
        "singularity_analysis",
        "discontinuities",
        "analytic",
        "meromorphic",
        "continuous",
        "differentiability",
        "monotonicity",
        "convexity",
        "sign",
        "zeros",
        "boundedness",
        "injective",
        "surjective",
        "bijective",
        "smoothness",
        "lipschitz",
        "uniformly_continuous",
        "holder_regularity",
        "variation",
        "integrability",
        "oscillation",
        "periodicity",
        "symmetry",
        "homogeneity",
        "complex_zeros",
        "complete_monotonicity",
        "boundary_behavior",
        "level_boundedness",
        "mode_existence",
        "geometry",
        "jacobian",
        "determinant_nonvanishing",
        "local_invertibility",
        "change_of_variables",
        "transformation_geometry",
    }
    exported = {name for name, _category, _summary in fp.properties()}
    assert exported == tested


def test_certificate_replay_root_extremum_range_and_bracket():
    roots = fp.transcendental_roots(
        sp.sin(x), x, sp.Interval(0, 2 * sp.pi), allow_numerical=False
    )
    assert roots.certificates and all(
        fp.verify_root_certificate(c) for c in roots.certificates
    )
    ex = fp.extremum_geometry(sp.airyai(x), x)
    assert ex and all(fp.verify_extremum_family(c) for c in ex)
    er = fp.symbolic_extremum_range(x**2, x, sp.Interval(-1, 2))
    assert fp.verify_extremum_range(er)
    k = sp.Symbol("k", integer=True, positive=True)
    z = fp.IndexedZero("BesselJ", k, 0, 0, "positive")
    b = fp.indexed_tail_integer_bracket(z, 10)
    assert fp.verify_integer_bracket(b)


def test_monotonic_partition_default_is_compact_mathematical_result():
    x = sp.symbols("x", real=True)
    out = fp.monotonic_partition(x**3 - 3 * x, x, domain=sp.Interval(-3, 3))
    assert out == (
        (sp.Interval.open(-3, -1), Monotonicity.STRICTLY_INCREASING),
        (sp.Interval.open(-1, 1), Monotonicity.STRICTLY_DECREASING),
        (sp.Interval.open(1, 3), Monotonicity.STRICTLY_INCREASING),
    )
    rich = fp.monotonic_partition(
        x**3 - 3 * x,
        x,
        domain=sp.Interval(-3, 3),
        return_result=True,
    )
    assert isinstance(rich, fp.MonotonicPartition)
    assert rich.complete is True


def test_compact_monotonic_decomposition():
    x = sp.symbols("x", real=True)
    out = fp.monotonic_decomposition(sp.acos(sp.exp(x)), x)
    inner, outer, direction, condition = out
    assert inner == sp.exp(x)
    assert sp.simplify(outer(inner) - sp.acos(sp.exp(x))) == 0
    assert direction == -1
    assert condition == (sp.exp(x) <= 1)
    rich = fp.monotonic_decomposition(sp.acos(sp.exp(x)), x, return_result=True)
    assert isinstance(rich, fp.MonotonicDecomposition)


def test_compact_monotonic_partition_composes_with_public_helpers():
    x = sp.symbols("x", real=True)
    compact = fp.monotonic_partition(x**3, x, domain=sp.Interval(-2, 2))
    assert fp.injectivity_from_partition(compact) is TruthValue.TRUE
    pr = fp.range_from_monotonic_partition(x**3, x, compact, domain=sp.Interval(-2, 2))
    assert pr.complete is True
    assert pr.image == sp.Interval(-8, 8)
