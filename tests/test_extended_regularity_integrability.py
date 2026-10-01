import sympy as sp

import funcprops as fp
from funcprops import TruthValue

x = sp.symbols("x", real=True)


def test_lipschitz_affine_and_sine():
    assert fp.lipschitz(3 * x + 2, x) == 3
    assert fp.lipschitz(sp.sin(x), x) == 1


def test_uniform_continuity_compact_and_polynomial():
    assert fp.uniformly_continuous(x**2, x, domain=sp.Interval(0, 1)) is TruthValue.TRUE
    assert fp.uniformly_continuous(x**2, x) is TruthValue.FALSE


def test_holder_power_cusp():
    assert fp.holder_regularity(sp.sqrt(x), x, domain=sp.Interval(0, 1)) == sp.Rational(
        1, 2
    )


def test_variation_monotone_interval():
    assert fp.variation(x**2, x, domain=sp.Interval(0, 2)) == 4


def test_integrability_is_structured():
    result = fp.integrability(x, x, domain=sp.Interval(0, 1))
    assert result.riemann is TruthValue.TRUE
    assert result.locally_integrable is TruthValue.TRUE
    assert result.absolutely_integrable is TruthValue.TRUE
    assert result.integral == sp.Rational(1, 2)


def test_improper_absolute_distinction():
    result = fp.integrability(1 / x**2, x, domain=sp.Interval(1, sp.oo))
    assert result.improper_integrable is TruthValue.TRUE
    assert result.absolutely_integrable is TruthValue.TRUE
