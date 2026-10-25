import sympy as sp
from sympy import S

from funcprops import (
    domain,
    monotonic_partition,
    sign,
    singularity_analysis,
    symbolic_extremum_range,
)
from funcprops.proof_cache import (
    cached_endpoint_limit,
    clear_property_proof_cache,
    property_proof_cache_info,
)
from funcprops.transcendental.zero_geometry import zero_geometry


def test_domain_cache_reused_across_property_calls():
    x = sp.symbols("x", real=True)
    clear_property_proof_cache()
    assert domain(sp.exp(x), x) is S.true
    before = property_proof_cache_info()["domain"]
    sign(sp.exp(x), x)
    after = property_proof_cache_info()["domain"]
    assert after.hits > before.hits


def test_zero_geometry_shared_between_partition_and_direct_query():
    x = sp.symbols("x", positive=True)
    clear_property_proof_cache()
    p = monotonic_partition(
        sp.besselj(0, x), x, domain=sp.Interval.open(0, sp.oo), return_result=True
    )
    assert p.indexed.complete and p.has_indexed_oscillation
    before = property_proof_cache_info()["zero_geometry"]
    g = zero_geometry(
        sp.besselj(0, x), x, derivative_order=1, domain=sp.Interval.open(0, sp.oo)
    )
    after = property_proof_cache_info()["zero_geometry"]
    assert g
    assert after.hits > before.hits


def test_endpoint_limit_shared_with_extrema():
    x = sp.symbols("x", real=True)
    d = sp.Interval.open(-1, 1)
    clear_property_proof_cache()
    assert cached_endpoint_limit(x**2, x, 1, direction="-", attained=False) == 1
    before = property_proof_cache_info()["endpoint_limit"]
    r = symbolic_extremum_range(x**2, x, d)
    after = property_proof_cache_info()["endpoint_limit"]
    assert (r.lower, r.upper, r.lower_attained, r.upper_attained) == (0, 1, True, False)
    assert after.hits > before.hits


def test_singularity_cache_key_includes_assumptions():
    x, a = sp.symbols("x a", real=True)
    clear_property_proof_cache()
    e = sp.log(a * x)
    r1 = singularity_analysis(e, x, domain=S.Complexes, assumptions=a > 0)
    info1 = property_proof_cache_info()["singularity"]
    r2 = singularity_analysis(e, x, domain=S.Complexes, assumptions=a > 0)
    info2 = property_proof_cache_info()["singularity"]
    assert r1 == r2
    assert info2.hits == info1.hits + 1
    singularity_analysis(e, x, domain=S.Complexes, assumptions=a < 0)
    info3 = property_proof_cache_info()["singularity"]
    assert info3.misses == info2.misses + 1


def test_cache_is_lazy():
    x = sp.symbols("x", real=True)
    clear_property_proof_cache()
    domain(sp.sin(x), x)
    info = property_proof_cache_info()
    assert info["domain"].misses >= 1
    assert info["sign"].misses == 0
    assert info["endpoint_limit"].misses == 0
    assert info["zero_geometry"].misses == 0
    assert info["singularity"].misses == 0


def test_cached_domain_preserves_invalid_domain_error():
    x = sp.symbols("x")
    import pytest

    with pytest.raises(ValueError):
        domain(sp.exp(x), x, domain=sp.Integers)
