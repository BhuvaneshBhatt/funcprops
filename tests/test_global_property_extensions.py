import sympy as sp

from funcprops.infinite_root_families import (
    affine_trig_root_family,
    structured_zero_geometry,
)
from funcprops.property_composition import compose_property
from funcprops.results import Convexity, TruthValue


def test_composition_interface_and_completeness():
    f = compose_property(
        "injective",
        TruthValue.TRUE,
        TruthValue.TRUE,
        inner_image=sp.Interval(0, 1),
        outer_domain=sp.Interval(-1, 2),
        inner_complete=False,
    )
    assert f.value is TruthValue.TRUE and not f.complete
    assert (
        compose_property(
            "injective",
            TruthValue.TRUE,
            TruthValue.TRUE,
            inner_image=sp.Interval(-2, 2),
            outer_domain=sp.Interval(0, 1),
        )
        is None
    )


def test_composition_convex_and_lipschitz():
    assert (
        compose_property("convexity", Convexity.CONVEX, Convexity.CONVEX).value
        is Convexity.CONVEX
    )
    q = compose_property(
        "lipschitz", TruthValue.TRUE, TruthValue.TRUE, outer_bound=3, inner_bound=4
    )
    assert q.bound == 12


def test_structured_trig_families_verify_and_integrate():
    x = sp.symbols("x", real=True)
    for f in (sp.sin(2 * x + 1), sp.cos(3 * x - 2), sp.tan(5 * x + 4)):
        fam = affine_trig_root_family(f, x)
        assert fam.verify()
        g = structured_zero_geometry(f, x)
        assert g.complete_on_support and g.real_exhaustive


def test_unresolved_frequency_not_certified():
    x, a = sp.symbols("x a", real=True)
    assert affine_trig_root_family(sp.sin(a * x), x) is None
