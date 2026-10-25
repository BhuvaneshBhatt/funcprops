"""Constructed property families with exact mathematical answers."""

import pytest
import sympy as sp
from hypothesis import given
from hypothesis import strategies as st

import funcprops as fp

x, y, a, b = sp.symbols("x y a b", real=True)


@given(st.integers(1, 4), st.integers(0, 4), st.booleans(), st.booleans())
def test_piecewise_order_and_image(slope, jump, left_open, right_open):
    source = sp.Piecewise((slope * x, x < 0), (slope * x + jump, True))
    support = sp.Interval(-1, 1, left_open, right_open)
    partition = fp.monotonic_partition(source, x, domain=support, return_result=True)
    expected = sp.Union(
        sp.Interval(-slope, 0, left_open, True),
        sp.Interval(jump, slope + jump, False, right_open),
    )
    assert (
        partition.complete
        and partition.same_strict_direction() is fp.Monotonicity.STRICTLY_INCREASING
    )
    assert fp.range_from_monotonic_partition(source, x, partition).image == expected
    assert fp.injectivity_from_partition(partition) is fp.TruthValue.TRUE
    variation = fp.variation(source, x, domain=support, return_result=True)
    assert variation.total_variation == 2 * slope + jump
    assert fp.certify_jump_variation(source, x, support).verify()


@given(st.integers(0, 5), st.sampled_from([-1, 0, 1]))
def test_owned_spike_variation(height, point):
    source = sp.Piecewise((height, sp.Eq(x, point)), (0, True))
    proof = fp.certify_jump_variation(source, x, sp.Interval(-1, 1))
    expected = height * (2 if point == 0 else 1)
    assert proof.verify() and proof.total_variation == expected


@given(st.integers(-4, 4), st.integers(-3, 3), st.integers(1, 4))
def test_finite_affine_secants(slope, offset, width):
    result = fp.lipschitz(
        slope * x + offset, x, domain=sp.FiniteSet(-width, 0, width), return_result=True
    )
    assert result.constant == abs(slope) and result.optimal is fp.TruthValue.TRUE
    assert result.verify()


@pytest.mark.parametrize("constant", [sp.sqrt(2), -sp.sqrt(2), sp.sqrt(2) + sp.sqrt(3)])
@pytest.mark.parametrize(
    "support",
    [
        sp.Interval(0, 1),
        sp.Interval.open(0, 1),
        sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2)),
    ],
)
def test_public_algebraic_images(constant, support):
    answer = fp.range(constant * x, x, y, constraints=support.as_relational(x))
    expected = sp.Union(
        *(
            sp.Interval(
                min(constant * part.start, constant * part.end),
                max(constant * part.start, constant * part.end),
                part.left_open if constant > 0 else part.right_open,
                part.right_open if constant > 0 else part.left_open,
            )
            for part in (support.args if isinstance(support, sp.Union) else (support,))
        )
    )
    from funcprops.real_analysis.common import condition_to_set

    assert condition_to_set(answer, y) == expected


@given(st.integers(-2, 2), st.integers(-2, 2))
def test_quadratic_specializations(av, bv):
    proof = fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=100)
    discriminant = av * av - 4 * bv
    expected = 2 if discriminant > 0 else 1 if discriminant == 0 else 0
    assert proof.verify() and proof.complete
    assert proof.specialize({a: av, b: bv}) == expected


@pytest.mark.parametrize("degree", [3, 4])
@pytest.mark.parametrize("value,expected", [(-1, 0), (0, 1), (1, 1), (2, 0)])
def test_multiple_endpoint_roots(degree, value, expected):
    proof = fp.certify_parameter_geometry(
        (x - a) ** degree, x, (a,), domain=sp.Interval(0, 1), max_cells=5000
    )
    assert proof.verify() and proof.complete
    assert proof.specialize({a: value}) == expected


def test_parameter_budget_preserves_cells():
    partial = fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=5)
    resumed = fp.resume_parameter_geometry(partial, max_cells=100)
    assert partial.verify() and resumed.verify() and resumed.complete
    assert all(cell in resumed.cells for cell in partial.cells)
    assert resumed.specialize({a: 0, b: -1}) == 2


def test_coefficient_boundaries():
    assert fp.encode_algebraic_coefficients((sp.sqrt(2) + sp.sqrt(3),), (x,)).verify()
    assert (
        fp.encode_algebraic_coefficients((sp.sqrt(2) + sp.sqrt(3) + sp.sqrt(5),), (x,))
        is None
    )
    assert fp.encode_algebraic_coefficients((sp.sqrt(2) * x + a,), (x,)) is None
    raw = sp.Mul(
        x - sp.sqrt(2), sp.Pow(x - sp.sqrt(2), -1, evaluate=False), evaluate=False
    )
    assert fp.range(raw, x, y, constraints=sp.Eq(x, sp.sqrt(2))) is sp.S.false


def test_symbolic_point_collision():
    assert fp.certify_finite_lipschitz(x * x, x, sp.FiniteSet(a, b)) is None
