import sympy as sp

from funcprops.proof_cache import (
    cached_derivative,
    clear_property_proof_cache,
    property_proof_cache_info,
)


def test_raw_derivative_does_not_factor_eagerly():
    x = sp.symbols("x")
    f = (x + 1) * (x + 2) * (x + 3)
    clear_property_proof_cache()
    d = cached_derivative(f, x)
    assert sp.expand(d - sp.diff(f, x)) == 0
    info = property_proof_cache_info()
    assert info["derivative"].misses == 1
    assert info["factored_derivative"].misses == 0


def test_factored_derivative_has_separate_lazy_slot_and_reuses_raw():
    x = sp.symbols("x")
    f = x**4 - x**2
    clear_property_proof_cache()
    raw = cached_derivative(f, x)
    before = property_proof_cache_info()
    fac = cached_derivative(f, x, factored=True)
    after = property_proof_cache_info()
    assert sp.expand(fac - raw) == 0
    assert (
        after["factored_derivative"].misses == before["factored_derivative"].misses + 1
    )
    assert after["derivative"].hits >= before["derivative"].hits + 1
    cached_derivative(f, x, factored=True)
    final = property_proof_cache_info()
    assert final["factored_derivative"].hits >= after["factored_derivative"].hits + 1


def test_orders_are_independent_cache_entries():
    x = sp.symbols("x")
    f = sp.exp(x**2)
    clear_property_proof_cache()
    d1 = cached_derivative(f, x, order=1)
    d2 = cached_derivative(f, x, order=2)
    assert d1 == sp.diff(f, x)
    assert d2 == sp.diff(f, x, 2)
    info = property_proof_cache_info()["derivative"]
    assert info.misses == 2


def test_cache_clear_clears_both_derivative_slots():
    x = sp.symbols("x")
    cached_derivative(x**4, x)
    cached_derivative(x**4, x, factored=True)
    clear_property_proof_cache()
    info = property_proof_cache_info()
    assert info["derivative"].currsize == 0
    assert info["factored_derivative"].currsize == 0


def test_invalid_derivative_order_rejected():
    x = sp.symbols("x")
    try:
        cached_derivative(x**2, x, order=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("negative derivative order should be rejected")


def test_differentiability_uses_raw_derivative_without_factorization():
    from funcprops import function_differentiability

    x = sp.symbols("x")
    f = sp.Abs(x)
    clear_property_proof_cache()
    function_differentiability(f, x)
    info = property_proof_cache_info()
    assert info["derivative"].misses >= 1
    assert info["factored_derivative"].misses == 0


def test_monotonic_partition_can_reuse_factored_derivative():
    from funcprops import monotonic_partition

    x = sp.symbols("x")
    f = x**4 - 2 * x**2
    clear_property_proof_cache()
    monotonic_partition(f, x, domain=sp.Interval(-2, 2))
    first = property_proof_cache_info()
    assert first["factored_derivative"].misses >= 1
    monotonic_partition(f, x, domain=sp.Interval(-2, 2))
    second = property_proof_cache_info()
    # The partition itself may hit before the derivative layer, but no extra
    # factorization miss may occur on the repeated proof.
    assert second["factored_derivative"].misses == first["factored_derivative"].misses


def test_fractional_derivative_order_is_not_truncated():
    x = sp.symbols("x")
    for bad_order in (1.5, sp.Rational(3, 2), True):
        try:
            cached_derivative(x**3, x, order=bad_order)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid derivative order accepted: {bad_order!r}")
