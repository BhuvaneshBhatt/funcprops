import sympy as sp

from funcprops import verify_zero_geometry
from funcprops.asymptotic_tails import certify_tail_sign
from funcprops.transcendental.unified_real import analyze_transcendental_real


def test_rational_tail_signs():
    x = sp.symbols("x", real=True)
    c = certify_tail_sign((x**3 + 2) / (x**2 + 1), x, direction=1)
    assert c.sign == 1 and c.verify()
    d = certify_tail_sign((x**3 + 2) / (x**2 + 1), x, direction=-1)
    assert d.sign == -1 and d.verify()


def test_exp_polynomial_tail():
    x = sp.symbols("x", real=True)
    c = certify_tail_sign(sp.exp(2 * x) * (x**2 + 1), x, direction=1)
    assert c.sign == 1 and c.verify()


def test_unified_trig_geometry_and_range():
    x = sp.symbols("x", real=True)
    a = analyze_transcendental_real(sp.cos(2 * x + 1), x)
    assert (
        a.complete
        and verify_zero_geometry(a.zero_geometry, expr=sp.cos(2 * x + 1), var=x)
        and a.image == sp.Interval(-1, 1)
    )


def test_unified_unknown_does_not_claim_complete():
    x = sp.symbols("x", real=True)
    a = analyze_transcendental_real(sp.sin(x) + sp.exp(-(x**2)), x)
    assert not (a.complete and a.image is None)
