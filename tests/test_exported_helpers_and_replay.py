import sympy as sp

import funcprops as fp
from funcprops.proof_cache import (
    clear_property_proof_cache,
    property_proof_cache_info,
    property_proof_context,
)
from funcprops.results import TruthValue

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
    p = fp.monotonic_partition(x**3 - 3 * x, x, domain=sp.Interval(-2, 2))
    assert p.complete and len(p.cells) == 3
    r = fp.range_from_monotonic_partition(x**3 - 3 * x, x, p)
    assert r.complete and r.image is not None
    assert fp.injectivity_from_monotonic_partition(p) is TruthValue.FALSE
    inv = fp.solve_monotonic_inverse(
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
    fp.monotonic_partition(x**2, x, domain=sp.Interval(-1, 1))
    fp.clear_monotonic_partition_cache()
    info = property_proof_cache_info()
    assert info["derivative"].currsize == 0 and info["zero_geometry"].currsize == 0


def test_certificate_replay_monotonicity_and_zero_geometry():
    p = fp.monotonic_partition(x**3 - 3 * x, x, domain=sp.Interval(-2, 2))
    assert fp.verify_monotonic_partition(x**3 - 3 * x, x, p)
    assert fp.verify_certificate(p, expr=x**3 - 3 * x, var=x)
    g = fp.zero_geometry(sp.besselj(0, x), x)
    assert g and all(fp.verify_zero_geometry(c) for c in g)


def test_certificate_replay_decomposition_and_convexity():
    d = fp.monotonic_decomposition(sp.acos(sp.exp(x)), x)
    assert d is not None and fp.verify_monotonic_decomposition(d)
    from funcprops.real_analysis.advanced_convexity import strong_convexity

    got = strong_convexity(x**2, x, sp.Interval(-2, 2))
    assert got is not None
    _cls, cert = got
    assert fp.verify_convexity_certificate(x**2, x, cert)


def test_certificate_replay_tail_and_extremum_theorem():
    k = sp.Symbol("k", integer=True, positive=True)
    z = fp.IndexedZero("BesselJ", k, 0, 0, "positive")
    cert = fp.indexed_tail_inversion(z, fp.IndexedZero("BesselJ", 3, 0, 0, "positive"))
    assert fp.verify_indexed_tail_inversion(cert)
    th = fp.extremum_ordering_theorems(sp.airyai(x), x)
    assert th and all(fp.verify_extremum_ordering_theorem(t) for t in th)


def test_remaining_exported_helpers_direct_contracts():
    assert fp.registry() is not None
    assert isinstance(fp.dlmf_facts("BesselJ"), tuple)
    fp.dlmf_audit_report(
        "BesselJ"
    )  # direct API contract: may be None when family has no audit rows
    k = sp.Symbol("k", integer=True, positive=True)
    z = fp.IndexedZero("BesselJ", k, 0, 0, "positive")
    assert fp.zero_ordering_bounds(z)
    b = fp.indexed_tail_integer_bracket(z, 10)
    assert b is not None and b.lower <= b.upper
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
        "function_domain",
        "function_range",
        "function_branchcuts",
        "function_branchpoints",
        "function_poles",
        "function_singularities",
        "function_singularity_analysis",
        "function_discontinuities",
        "function_analytic",
        "function_meromorphic",
        "function_continuous",
        "function_differentiability",
        "function_monotonicity",
        "function_convexity",
        "function_sign",
        "function_zeros",
        "function_boundedness",
        "function_injective",
        "function_surjective",
        "function_bijective",
        "function_smoothness",
        "function_oscillation",
        "function_periodicity",
        "function_symmetry",
        "function_homogeneity",
        "function_complex_zeros",
    }
    exported = {n for n in fp.__all__ if n.startswith("function_")}
    assert exported == tested


def test_certificate_replay_root_extremum_range_and_bracket():
    roots = fp.transcendental_roots(
        sp.sin(x), x, sp.Interval(0, 2 * sp.pi), allow_numerical=False
    )
    assert roots.certificates and all(
        fp.verify_root_certificate(c) for c in roots.certificates
    )
    ex = fp.extremum_geometry(sp.airyai(x), x)
    assert ex and all(fp.verify_extremum_family_certificate(c) for c in ex)
    er = fp.symbolic_extremum_range(x**2, x, sp.Interval(-1, 2))
    assert fp.verify_extremum_range(er)
    k = sp.Symbol("k", integer=True, positive=True)
    z = fp.IndexedZero("BesselJ", k, 0, 0, "positive")
    b = fp.indexed_tail_integer_bracket(z, 10)
    assert fp.verify_integer_bracket(b)


def test_exported_helper_contract_manifest_is_complete():
    import inspect

    exported = {
        n
        for n in fp.__all__
        if callable(getattr(fp, n))
        and not inspect.isclass(getattr(fp, n))
        and not n.startswith("function_")
    }
    tested = {
        "registry",
        "as_detailed_result",
        "monotonic_decomposition",
        "monotonic_partition",
        "solve_monotonic_inverse",
        "range_from_monotonic_partition",
        "injectivity_from_monotonic_partition",
        "clear_monotonic_partition_cache",
        "dlmf_facts",
        "dlmf_audit_report",
        "verify_certificate",
        "verify_monotonic_decomposition",
        "verify_monotonic_partition",
        "verify_zero_geometry",
        "verify_convexity_certificate",
        "verify_extremum_ordering_theorem",
        "verify_indexed_tail_inversion",
        "verify_root_certificate",
        "verify_extremum_family_certificate",
        "verify_extremum_range",
        "verify_integer_bracket",
        "zero_geometry",
        "property_interval_decomposition",
        "zero_ordering_bounds",
        "indexed_tail_inversion",
        "indexed_tail_integer_bracket",
        "extremum_geometry",
        "extremum_ordering_theorems",
        "simplify_extremum_range",
        "symbolic_extremum_range",
        "transcendental_roots",
        "reduce_univariate_condition",
        "algebraize",
        "holomorphic_on_rectangle",
        "analytic_neighborhood",
        "certified_monotonic_inverse",
        "robust_real_sign",
        "exponential_fourier_count",
        "exponential_polynomial_terms",
        "argument_principle_count",
        "isolate_complex_roots",
    }
    assert exported == tested
