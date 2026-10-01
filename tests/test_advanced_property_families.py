import sympy as sp

from funcprops.asymptotic_tails import certify_tail_sign
from funcprops.certified_optimization import certify_global_minimum
from funcprops.derivative_inequalities import derivative_chain_positive
from funcprops.infinite_root_families import affine_sine_root_family
from funcprops.meromorphic_contours import meromorphic_rectangle_count
from funcprops.multivariate_intervals import krawczyk_box
from funcprops.parameter_discriminants import (
    exp_linear_discriminant,
    exp_linear_root_strata,
)
from funcprops.property_composition import compose_property
from funcprops.results import Monotonicity


def test_property_composition_monotonicity():
    f = compose_property(
        "monotonicity",
        Monotonicity.STRICTLY_DECREASING,
        Monotonicity.STRICTLY_DECREASING,
    )
    assert f.value is Monotonicity.STRICTLY_INCREASING


def test_derivative_chain_positive():
    x = sp.symbols("x", real=True)
    c = derivative_chain_positive(sp.exp(x) - 1 - x, x, sp.Interval(0, 1))
    assert c is not None and c.verify()


def test_polynomial_tail_replay():
    x = sp.symbols("x", real=True)
    c = certify_tail_sign(x**4 - 3 * x + 1, x, direction=1, threshold=8)
    assert c is not None and c.sign == 1 and c.verify()


def test_certified_global_minimum():
    x = sp.symbols("x", real=True)
    c = certify_global_minimum((x - 3) ** 2 + 5, x)
    assert c is not None and c.point == 3 and c.value == 5 and c.verify()


def test_infinite_affine_sine_family():
    x = sp.symbols("x", real=True)
    c = affine_sine_root_family(sp.sin(2 * x + 1), x)
    assert c is not None and c.complete and c.simple and c.verify()


def test_affine_krawczyk_box():
    x, y = sp.symbols("x y", real=True)
    c = krawczyk_box(
        (2 * x + y - 1, x - y), (x, y), (sp.Interval(-1, 1), sp.Interval(-1, 1))
    )
    assert c is not None and c.verify()


def test_meromorphic_zero_minus_pole_count():
    z = sp.symbols("z")
    c = meromorphic_rectangle_count(
        (z - 1) * (z + 1) / (z - 2), z, -3 - 3 * sp.I, 3 + 3 * sp.I
    )
    assert c is not None and (c.zeros, c.poles, c.winding) == (2, 1, 1) and c.verify()


def test_exp_linear_discriminant_and_strata():
    x, a, b = sp.symbols("x a b", real=True)
    d = exp_linear_discriminant(sp.exp(x) + a * x + b, x, a, b)
    assert d is not None and sp.simplify(d.transition - (b + a * (sp.log(-a) - 1))) == 0
    s = exp_linear_root_strata(sp.exp(x) + a * x + b, x, a, b)
    assert len(s) == 6


def test_meromorphic_boundary_zero_is_rejected():
    z = sp.symbols("z")
    assert (
        meromorphic_rectangle_count((z - 1) / (z + 2), z, -1 - sp.I, 1 + sp.I) is None
    )


def test_special_function_expansion_has_guarded_catalogue_entries():
    from funcprops.real_analysis.special_functions import dlmf_facts

    assert dlmf_facts("LambertW")
    assert dlmf_facts("zeta")
    assert dlmf_facts("polylog")
