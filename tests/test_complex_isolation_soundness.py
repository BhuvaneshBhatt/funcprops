from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.transcendental import complex_roots as cr

z = sp.Symbol("z")
RECT = (-2 - 2 * sp.I, 2 + 2 * sp.I)


@pytest.mark.parametrize("power", [2, 3, 4])
def test_exact_solver_retains_raw_source_hole(power):
    raw = sp.Mul(z**power, sp.Pow(z, -1, evaluate=False), evaluate=False)
    assert raw.subs(z, 0) is sp.nan
    result = fp.isolate_complex_roots(raw, z, RECT)
    assert result.complete and result.roots == ()
    assert result.total_count == result.multiplicity_count == 0
    assert result.distinct_root_count == 0 and result.isolation_complete


def test_source_hole_does_not_remove_a_different_defined_root():
    raw = sp.Mul(z, z - 1, sp.Pow(z, -1, evaluate=False), evaluate=False)
    result = fp.isolate_complex_roots(raw, z, RECT)
    assert result.complete and result.roots == (1,)
    assert result.total_count == result.distinct_root_count == 1


@pytest.mark.parametrize(
    "expression,distinct,total",
    [(z**4, 1, 4), ((z - 1) ** 3 * (z + 1) ** 2, 2, 5), (z**2 + 1, 2, 2)],
)
def test_exact_and_contour_counts_use_multiplicity_consistently(
    expression, distinct, total
):
    exact = fp.isolate_complex_roots(expression, z, RECT)
    contour = fp.argument_principle_count(expression, z, RECT, precision=30)
    assert exact.complete and exact.isolation_complete
    assert exact.distinct_root_count == distinct
    assert contour.certified
    assert exact.total_count == exact.multiplicity_count == contour.zero_count == total


def test_unknown_exact_multiplicity_does_not_fabricate_a_simple_root():
    result = fp.isolate_complex_roots(sp.log(z) ** 2, z, RECT)
    assert result.complete and result.roots == (1,)
    assert result.distinct_root_count == 1 and result.isolation_complete
    assert result.multiplicity_count is None and result.total_count is None


def test_unresolved_parameter_degeneracy():
    a = sp.Symbol("a")
    result = fp.isolate_complex_roots(a * z, z, RECT, max_boundary_depth=1)
    assert not result.complete and not result.isolation_complete
    assert result.distinct_root_count is None and result.total_count is None


@pytest.mark.parametrize("value", [sp.oo, -sp.oo, sp.zoo, sp.nan])
def test_nonfinite_constant_has_no_holomorphic_neighborhood(value):
    assert fp.holomorphic_on_rectangle(value, z, RECT).holomorphic is None
    raw = sp.Mul(0, value, z, evaluate=False)
    assert fp.holomorphic_on_rectangle(raw, z, RECT).holomorphic is None


def test_unresolved_constant_parameter_does_not_imply_finiteness():
    a = sp.Symbol("a")
    assert fp.holomorphic_on_rectangle(sp.exp(z + a), z, RECT).holomorphic is None
    finite = sp.Symbol("finite", complex=True)
    assert fp.holomorphic_on_rectangle(sp.exp(z + finite), z, RECT).holomorphic is True


def test_composite_branch_cancellation():
    raw = sp.exp(sp.log(z, evaluate=False), evaluate=False)
    rectangle = (-2 - sp.I, -1 + sp.I)
    assert fp.holomorphic_on_rectangle(sp.log(z), z, rectangle).holomorphic is False
    # The held source equals z throughout this rectangle, but this helper does
    # not yet prove branch descent. It must not inherit the child's negative.
    assert fp.holomorphic_on_rectangle(raw, z, rectangle).holomorphic is None


@pytest.mark.parametrize("root", [0, 1, sp.I, 1 + sp.I, sp.Rational(1, 2)])
def test_polynomial_argument_principle_requires_zero_free_boundary(root):
    assert fp.argument_principle_rectangle(z - root, z, 0, 1 + sp.I) is None
    invalid = fp.ArgumentPrincipleCertificate(z - root, z, 0, 1 + sp.I, 1)
    assert not invalid.verify()


def test_polynomial_contour_multiplicity():
    c = fp.argument_principle_rectangle(
        (z - sp.Rational(1, 2)) ** 3, z, -sp.I, 1 + sp.I
    )
    assert c and c.count == 3 and c.verify()
    assert not replace(c, count=2).verify()


def test_contour_count_source_witness(monkeypatch):
    monkeypatch.setattr(cr, "_polygon_winding", lambda _: 12345)
    c = fp.argument_principle_count(sp.exp(z) - 1, z, (-1 - sp.I, 1 + sp.I))
    assert c.certified and c.zero_count == 1
    native = dict(c.evidence)["native_contour"]
    assert native.expression == sp.exp(z) - 1 and native.variable == z
    assert native.verify() and native.zero_count == c.zero_count
    assert not replace(native, zero_count=2).verify()


@pytest.mark.parametrize("precision", [20, 80])
def test_exact_phase_offsets(precision):
    raw = sp.Add(
        z, -sp.sin(sp.Integer(10) ** 40 * sp.pi, evaluate=False), evaluate=False
    )
    assert sp.simplify(raw) == z
    c = fp.argument_principle_count(
        raw,
        z,
        (-2 - sp.I, -sp.Rational(1, 5) + sp.I),
        precision=precision,
        max_boundary_depth=2,
    )
    # The baseline claimed one root at precision 20, after using an approximate
    # pi before the interval sine. The only actual root is zero, outside here.
    assert not c.certified or c.zero_count == 0
    if precision == 80:
        assert c.certified and c.zero_count == 0


def test_canceled_contour_source_pole():
    raw = sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False)
    c = fp.argument_principle_count(raw, z, RECT, max_boundary_depth=2)
    assert not c.certified and c.zero_count is None


def test_cluster_coverage_is_not_individual_isolation():
    f = (sp.exp(z) - 1) ** 2
    c = fp.isolate_complex_roots(
        f, z, (-1 - sp.I, 1 + sp.I), max_isolation_depth=0, use_multiple=False
    )
    assert c.coverage_complete and not c.complete
    assert c.total_count == c.multiplicity_count == 2
    assert not c.isolation_complete and c.distinct_root_count is None
    assert len(c.rectangles) == 1 and c.rectangles[0].root_count == 2


def test_uncertain_boundary_never_reports_isolation_complete():
    c = fp.isolate_complex_roots(
        sp.exp(z) - 1, z, (-sp.I, 1 + sp.I), max_boundary_depth=2
    )
    assert not c.complete and not c.isolation_complete
    assert c.total_count is None and c.distinct_root_count is None


def test_exact_empty_set_has_complete_zero_counts():
    c = fp.isolate_complex_roots(sp.exp(z), z, RECT)
    assert c.complete and c.isolation_complete
    assert c.total_count == c.distinct_root_count == 0
