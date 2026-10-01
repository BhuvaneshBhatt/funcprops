import sympy as sp

from funcprops import (
    IndexedTailIndex,
    IndexedTailInversionCertificate,
    IndexedZero,
    indexed_tail_inversion,
)
from funcprops.transcendental.extrema import ExtremumRange, symbolic_extremum_range

x = sp.symbols("x", real=True)


def test_same_family_bessel_tail_inversion_is_integer_exact():
    k = sp.symbols("k", integer=True, positive=True)
    tmpl = IndexedZero("BesselJ", k, 1, 1, "positive")
    cut = IndexedZero("BesselJ", 4, 1, 1, "positive")
    cert = indexed_tail_inversion(tmpl, cut, direction="right", inclusive=True)
    assert cert.complete
    assert cert.first_index == 4
    strict = indexed_tail_inversion(tmpl, cut, direction="right", inclusive=False)
    assert strict.first_index == 5


def test_bessel_function_zero_to_derivative_zero_uses_interlacing():
    k = sp.symbols("k", integer=True, positive=True)
    tmpl = IndexedZero("BesselJ", k, 2, 1, "positive")
    cut = IndexedZero("BesselJ", 3, 2, 0, "positive")
    cert = indexed_tail_inversion(tmpl, cut, direction="right")
    assert cert.first_index == 4
    assert "10.21.E3" in cert.source


def test_airy_function_zero_to_left_derivative_zero_uses_interlacing():
    k = sp.symbols("k", integer=True, positive=True)
    tmpl = IndexedZero("AiryAi", k, sp.S.NaN, 1, "negative")
    cut = IndexedZero("AiryAi", 3, sp.S.NaN, 0, "negative")
    cert = indexed_tail_inversion(tmpl, cut, direction="left")
    assert cert.first_index == 4


def test_general_cutoff_returns_exact_symbolic_inverse_index():
    A = sp.symbols("A", positive=True)
    k = sp.symbols("k", integer=True, positive=True)
    tmpl = IndexedZero("BesselJ", k, 1, 1, "positive")
    cert = indexed_tail_inversion(tmpl, A, direction="right")
    assert isinstance(cert.first_index, IndexedTailIndex)
    assert cert.complete
    assert cert.first_index.is_integer is True
    assert cert.first_index.is_positive is True


def test_bessel_tail_range_eliminates_infinite_envelope():
    A = sp.symbols("A", positive=True)
    r = symbolic_extremum_range(sp.besselj(1, x), x, sp.Interval(A, sp.oo))
    assert isinstance(r, ExtremumRange)
    assert r.complete
    assert not r.lower.has(sp.Function("ExtremumEnvelope"))
    assert any(isinstance(e, IndexedTailInversionCertificate) for e in r.evidence)
    # The exact cutoff value remains a candidate; it cannot be discarded merely
    # because later critical amplitudes decrease.
    assert r.lower.has(sp.besselj(1, A)) or r.upper.has(sp.besselj(1, A))


def test_bessel_tail_at_indexed_critical_point_resolves_selector():
    A = IndexedZero("BesselJ", 5, 1, 1, "positive")
    r = symbolic_extremum_range(sp.besselj(1, x), x, sp.Interval(A, sp.oo))
    cert = next(e for e in r.evidence if isinstance(e, IndexedTailInversionCertificate))
    assert cert.first_index == 5
    # first odd is 5 (max), first even is 6 (min)
    assert r.upper.has(IndexedZero("BesselJ", 5, 1, 1, "positive"))
    assert r.lower.has(IndexedZero("BesselJ", 6, 1, 1, "positive"))


def test_airy_left_tail_inversion_reduces_infinite_envelope():
    B = sp.symbols("B", negative=True)
    r = symbolic_extremum_range(sp.airyai(x), x, sp.Interval(-sp.oo, B))
    assert isinstance(r, ExtremumRange)
    cert = next(e for e in r.evidence if isinstance(e, IndexedTailInversionCertificate))
    assert cert.direction == "left"
    assert isinstance(cert.first_index, IndexedTailIndex)
    # -infinity contributes only the interior limit 0 and cannot dominate the
    # certified positive/negative Airy extrema, so it is removed from bounds.
    assert r.lower != 0 and r.upper != 0


def test_bessel_tail_endpoint_attainment():
    A = sp.symbols("A", positive=True)
    r = symbolic_extremum_range(sp.besselj(1, x), x, sp.Interval.open(A, sp.oo))
    assert r.lower_attained is None
    assert r.upper_attained is None


def test_public_range_uses_parameterized_tail_interval():
    from funcprops import range

    y = sp.symbols("y", real=True)
    A = sp.symbols("A", positive=True)
    r = range(sp.besselj(1, x), x, y, constraints=x >= A)
    assert isinstance(r, sp.logic.boolalg.Boolean)
    assert r.has(IndexedTailIndex)
    assert r.has(sp.besselj(1, A))
