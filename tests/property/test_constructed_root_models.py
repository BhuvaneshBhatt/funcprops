"""Generated exact oracles: prescribed roots, orders, holes and interval images."""

import sympy as sp
from hypothesis import given, settings
from hypothesis import strategies as st

import funcprops as fp

x, y = sp.symbols("x y", real=True)
z = sp.Symbol("z")


@settings(max_examples=20)
@given(
    st.dictionaries(st.integers(-3, 3), st.integers(1, 3), min_size=1, max_size=4),
    st.integers(-3, 3),
)
def test_held_source_holes_remove_prescribed_roots_not_just_orders(orders, hole):
    polynomial = sp.prod((x - r) ** m for r, m in orders.items())
    g = x - hole
    held = sp.Mul(polynomial, g, sp.Pow(g, -1, evaluate=False), evaluate=False)
    proof = fp.prove_root_coverage(held, x, sp.Interval(-4, 4))
    assert proof.verify() and proof.complete
    assert proof.root_count == sum(r != hole for r in orders)
    assert proof.multiplicity_count == sum(m for r, m in orders.items() if r != hole)
    assert proof.context.effective.contains(hole) is sp.false


@settings(max_examples=12)
@given(st.dictionaries(st.integers(-2, 2), st.integers(1, 2), min_size=1, max_size=3))
def test_exact_real_and_algebraic_routes_agree_with_prescribed_orders(orders):
    real = fp.prove_root_coverage(
        sp.prod((x - r) ** m for r, m in orders.items()), x, sp.Interval(-3, 3)
    )
    algebraic = fp.certify_algebraic_complex_roots(
        sp.prod((z - r) ** m for r, m in orders.items()), z, (-3 - sp.I, 3 + sp.I)
    )
    assert real.verify() and algebraic.verify() and real.complete and algebraic.complete
    assert real.root_count == algebraic.root_count == len(orders)
    assert (
        real.multiplicity_count == algebraic.multiplicity_count == sum(orders.values())
    )


@settings(max_examples=16)
@given(st.integers(-3, 1), st.integers(1, 3), st.booleans(), st.booleans())
def test_strict_exponential_images_preserve_endpoint_ownership(
    a, width, left_open, right_open
):
    b = a + width
    constraints = (x > a if left_open else x >= a) & (x < b if right_open else x <= b)
    image = fp.range(sp.exp(x), x, y, constraints=constraints)
    expected = (y > sp.exp(a) if left_open else y >= sp.exp(a)) & (
        y < sp.exp(b) if right_open else y <= sp.exp(b)
    )
    assert sp.simplify(image ^ expected) is sp.false
