import sympy as sp
from sympy import S

from funcprops import (
    function_domain,
    function_sign,
    function_singularity_analysis,
    monotonic_partition,
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
    assert function_domain(sp.exp(x), x) is S.true
    before = property_proof_cache_info()["domain"]
    function_sign(sp.exp(x), x)
    after = property_proof_cache_info()["domain"]
    assert after.hits > before.hits


def test_zero_geometry_shared_between_partition_and_direct_query():
    x = sp.symbols("x", positive=True)
    clear_property_proof_cache()
    p = monotonic_partition(sp.besselj(0, x), x, domain=sp.Interval.open(0, sp.oo))
    assert p.indexed is not None
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
    assert r is not None
    assert after.hits > before.hits


def test_singularity_cache_key_includes_assumptions():
    x, a = sp.symbols("x a", real=True)
    clear_property_proof_cache()
    e = sp.log(a * x)
    r1 = function_singularity_analysis(e, x, domain=S.Complexes, assumptions=a > 0)
    info1 = property_proof_cache_info()["singularity"]
    r2 = function_singularity_analysis(e, x, domain=S.Complexes, assumptions=a > 0)
    info2 = property_proof_cache_info()["singularity"]
    assert r1 == r2
    assert info2.hits == info1.hits + 1
    function_singularity_analysis(e, x, domain=S.Complexes, assumptions=a < 0)
    info3 = property_proof_cache_info()["singularity"]
    assert info3.misses == info2.misses + 1


def test_cache_is_lazy():
    x = sp.symbols("x", real=True)
    clear_property_proof_cache()
    function_domain(sp.sin(x), x)
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
        function_domain(sp.exp(x), x, domain=sp.Integers)
