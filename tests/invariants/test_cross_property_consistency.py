import sympy as sp

import funcprops as fp
from funcprops.proof_cache import clear_property_proof_cache
from funcprops.results import (
    Analyticity,
    Continuity,
    Convexity,
    Monotonicity,
    Periodicity,
    TruthValue,
)

x, y = sp.symbols("x y", real=True)


def test_analytic_implies_continuous_and_smooth_for_entire_examples():
    for f in (sp.exp(x), sp.sin(x), x**4 + 2 * x):
        assert fp.function_analytic(f, x) is Analyticity.ANALYTIC
        assert fp.function_continuous(f, x) is Continuity.CONTINUOUS
        assert fp.function_smoothness(f, x, return_result=True).smooth is True


def test_strict_monotonicity_implies_injectivity():
    for f in (x, x**3, sp.exp(x)):
        m = fp.function_monotonicity(f, x)
        if m in (Monotonicity.STRICTLY_INCREASING, Monotonicity.STRICTLY_DECREASING):
            assert fp.function_injective(f, x) is TruthValue.TRUE


def test_bijective_implies_both_mapping_properties():
    assert fp.function_bijective(x, x) is TruthValue.TRUE
    assert fp.function_injective(x, x) is TruthValue.TRUE
    assert fp.function_surjective(x, x) is TruthValue.TRUE


def test_strong_convexity_implies_convex_family():
    c = fp.function_convexity(x**2, x, all_properties=True)
    if isinstance(c, tuple):
        assert any(
            v
            in (Convexity.STRONGLY_CONVEX, Convexity.STRICTLY_CONVEX, Convexity.CONVEX)
            for v in c
        )


def test_equivalent_expression_invariance():
    forms = (x**2 + 2 * x + 1, (x + 1) ** 2, sp.expand((x + 1) ** 2))
    signs = [fp.function_sign(f, x) for f in forms]
    cvs = [fp.function_convexity(f, x) for f in forms]
    assert len(set(signs)) == 1
    assert len(set(cvs)) == 1


def test_domain_sensitive_non_equivalence_is_preserved():
    f = (x**2 - 1) / (x - 1)
    g = x + 1
    assert fp.function_domain(f, x) != fp.function_domain(g, x)


def test_cache_order_invariance():
    f = x**3 - 3 * x
    D = sp.Interval(-2, 2)
    clear_property_proof_cache()
    a = (
        fp.function_sign(f, x, domain=D),
        fp.function_monotonicity(f, x, domain=D),
        fp.function_injective(f, x, domain=D),
    )
    clear_property_proof_cache()
    b0 = fp.function_injective(f, x, domain=D)
    b1 = fp.function_monotonicity(f, x, domain=D)
    b2 = fp.function_sign(f, x, domain=D)
    assert a == (b2, b1, b0)


def test_cache_assumption_normalization_is_order_insensitive():
    from funcprops.proof_cache import proof_key

    a, b = sp.symbols("a b", real=True)
    k1 = proof_key(x, x, assumptions=sp.And(a > 0, b > 0))
    k2 = proof_key(x, x, assumptions=sp.And(b > 0, a > 0))
    assert k1 == k2


def test_semialg_delegation_parity_for_semialgebraic_range():
    from funcprops import _semialg

    expected = _semialg.function_range(x**2, x, y)
    assert fp.function_range(x**2, x, y) == expected


def test_semialg_delegation_parity_for_domain():
    from funcprops import _semialg

    clear_property_proof_cache()
    expected = _semialg.function_domain(sp.sqrt(1 - x**2), x)
    got = fp.function_domain(sp.sqrt(1 - x**2), x)
    assert got.as_set() == expected.as_set() == sp.Interval(-1, 1)


def test_semialg_delegation_parity_for_convexity():
    from funcprops import _semialg

    clear_property_proof_cache()
    expected = _semialg.function_convexity(x**2, x)
    got = fp.function_convexity(x**2, x)
    assert got == expected


def test_periodicity_metamorphic_affine_pullback():
    a = fp.function_periodicity(sp.sin(x), x, return_result=True)
    b = fp.function_periodicity(sp.sin(3 * x + 1), x, return_result=True)
    assert (
        a.classification is Periodicity.PERIODIC
        and b.classification is Periodicity.PERIODIC
    )
    assert sp.simplify(a.period / 3 - b.period) == 0


def test_symmetry_equivalent_expression_invariance():
    f = (x + 1) ** 2 + (x - 1) ** 2
    assert fp.function_symmetry(f, x) is fp.Symmetry.EVEN
    assert fp.function_symmetry(sp.expand(f), x) is fp.Symmetry.EVEN


def test_homogeneity_product_degree_adds():
    a = fp.function_homogeneity(x**2, (x,), return_result=True)
    b = fp.function_homogeneity(x**3, (x,), return_result=True)
    c = fp.function_homogeneity(x**5, (x,), return_result=True)
    assert a.degree + b.degree == c.degree
