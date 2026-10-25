"""Source-hole, selected-branch, and complex jet proof-boundary regressions."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.certified_operations import (
    LaurentCertificate,
    ResidueCertificate,
    SingularityClassificationCertificate,
)
from funcprops.complex_interval import complex_box_taylor
from funcprops.local_branches import LocalBranchContext

z = sp.Symbol("z")
g = sp.exp(z) - 2
RECT = (sp.Rational(69, 100) - sp.I / 100, sp.Rational(7, 10) + sp.I / 100)


class LyingTuple(tuple):
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


class LyingBranch(LocalBranchContext):
    def apply(self, expression, variable, point):
        return 1 / variable


@pytest.fixture(scope="module")
def base():
    result = fp.certify_analytic_contour(g, z, *RECT)
    assert result.verify() and result.zero_count == 1
    return result


def assert_rejected(proof):
    assert proof.verify() is False
    assert fp.verify_certificate(proof) is False
    assert fp.replay_status(proof).certified is False


@pytest.mark.parametrize("name", ["minimum_bounds", "maximum_bounds"])
def test_extrema_bounds_cannot_override_comparison_of_reported_values(name):
    x = sp.Symbol("x", real=True)
    c = fp.certify_extrema_bounds(x**2, x, sp.Interval(-1, 1))
    assert c.verify() and c.complete
    assert_rejected(replace(c, **{name: LyingTuple((sp.Integer(-77),) * 2)}))


@pytest.mark.parametrize("name", ["minimum", "maximum", "sign", "monotonicity"])
def test_property_value_container_binding(name):
    x = sp.Symbol("x", real=True)
    c = fp.certify_property_coverage(x**2, x, sp.Interval(-1, 1))
    assert c.verify()
    false = tuple(
        replace(p, value=LyingTuple((sp.Integer(-77), sp.FiniteSet(0))))
        if p.name == name
        else p
        for p in c.conclusions
    )
    assert_rejected(replace(c, conclusions=false))


@pytest.mark.parametrize("outer", [True, False])
def test_real_deflation_cannot_report_another_exact_root_to_extrema(outer):
    x = sp.Symbol("x", real=True)
    D = sp.Interval.open(-sp.Rational(1, 4), sp.Rational(1, 4))
    leaf = fp.deflate_real_root(sp.sin(x) - x, x, D, 0, 3)
    assert leaf.verify() and leaf.roots == ((0, 3),)
    roots = (
        LyingTuple(((sp.Integer(77), 3),))
        if outer
        else (LyingTuple((sp.Integer(77), 3)),)
    )
    bad = replace(leaf, roots=roots)
    assert_rejected(bad)
    cover = fp.CoverageProof(leaf.context, (bad,), sp.S.EmptySet, True, 1, 3)
    assert_rejected(cover)
    with pytest.raises(ValueError, match="invalid supplied critical cover"):
        fp.certify_extrema_bounds(
            -sp.cos(x) - x * x / 2, x, D, critical_covers=(cover,)
        )


@pytest.mark.parametrize("field", ["outer", "row", "box"])
def test_zero_function_cannot_acquire_a_nonzero_jet(base, field):
    zero = (sp.S.Zero,) * 4
    one = (sp.S.One, sp.S.Zero, sp.S.One, sp.S.Zero)
    box = base.rectangle.bounds()
    coefficients = (zero, one)
    if field == "outer":
        coefficients = LyingTuple(coefficients)
    elif field == "row":
        coefficients = (zero, LyingTuple(one))
    else:
        box = LyingTuple(box)
        coefficients = (zero, LyingTuple(one))
    w = fp.ImplicitJetWitness(sp.S.Zero, z, box, 1, coefficients, 30)
    p = fp.ImplicitMultiplicityProof(
        sp.S.Zero, z, base, (fp.certify_root_value(sp.S.Zero, base),), w, 1
    )
    assert_rejected(w)
    assert_rejected(p)


def test_double_root_cannot_use_derivatives_from_another_box(base):
    elsewhere = (sp.Integer(2), sp.S.Zero, sp.Integer(2), sp.S.Zero)
    coefficients = complex_box_taylor(g**2, z, elsewhere, 1)
    w = fp.ImplicitJetWitness(g**2, z, LyingTuple(elsewhere), 1, coefficients, 30)
    p = fp.ImplicitMultiplicityProof(
        g**2, z, base, (fp.certify_root_value(g**2, base),), w, 1
    )
    assert_rejected(w)
    assert_rejected(p)


@pytest.mark.parametrize("field", ["outer", "row", "box"])
def test_point_taylor_witness_uses_plain_exact_containers(field):
    zero = (sp.S.Zero,) * 4
    one = (sp.S.One, sp.S.Zero, sp.S.One, sp.S.Zero)
    coefficients = (
        LyingTuple((zero, one)) if field == "outer" else (zero, LyingTuple(one))
    )
    w = fp.ComplexTaylorWitness(sp.S.Zero, z, sp.S.Zero, 1, coefficients, 30)
    if field == "box":
        # A benign-looking coefficient container subclass is still executable.
        w = replace(w, coefficients=(zero, LyingTuple(zero)))
    assert_rejected(w)


@pytest.mark.parametrize(
    "operation", ["residue", "laurent_series", "classify_singularity"]
)
def test_branch_context_callbacks(operation):
    branch = LyingBranch(sp.S.Zero, ((z, sp.S.Zero),))
    with pytest.raises(TypeError):
        getattr(fp, operation)(
            sp.conjugate(z), z, 0, branch_context=branch, return_certificate=True
        )


@pytest.mark.parametrize("kind", ["residue", "laurent", "singularity"])
def test_forged_selected_branch_certificates_reject(kind):
    branch = LyingBranch(sp.S.Zero, ((z, sp.S.Zero),))
    f = sp.conjugate(z)
    c = (
        ResidueCertificate(f, z, sp.S.Zero, sp.S.One, branch)
        if kind == "residue"
        else LaurentCertificate(f, z, sp.S.Zero, 1 / z, 6, branch)
        if kind == "laurent"
        else SingularityClassificationCertificate(f, z, sp.S.Zero, "pole", -1, branch)
    )
    assert_rejected(c)


@pytest.mark.parametrize("hole", [sp.sin(1 / z), sp.exp(1 / z) - 1])
@pytest.mark.parametrize("extension", [sp.exp(1 / z), sp.log(z), sp.sqrt(z)])
def test_classification_retains_accumulating_canceled_holes(hole, extension):
    raw = sp.Mul(extension, hole, sp.Pow(hole, -1, evaluate=False), evaluate=False)
    assert fp.classify_singularity(raw, z, 0, return_certificate=True) is None
    assert fp.residue(raw, z, 0, return_certificate=True) is None
    assert fp.laurent_series(raw, z, 0, return_certificate=True) is None


@pytest.mark.parametrize("point", [sp.S.Zero, sp.S.One, sp.I])
def test_singularity_source_center(point):
    u = z - point
    hole = sp.sin(1 / u)
    raw = sp.Mul(sp.exp(1 / u), hole, sp.Pow(hole, -1, evaluate=False), evaluate=False)
    assert fp.classify_singularity(raw, z, point, return_certificate=True) is None


@pytest.mark.parametrize(
    "extension,kind", [(sp.exp(1 / z), "essential"), (sp.sqrt(z), "branch_point")]
)
def test_remote_canceled_holes_do_not_block_a_local_classification(extension, kind):
    raw = sp.Mul(extension, z - 1, sp.Pow(z - 1, -1, evaluate=False), evaluate=False)
    c = fp.classify_singularity(raw, z, 0, return_certificate=True)
    assert c.kind == kind and fp.verify_certificate(c)


@pytest.mark.parametrize(
    "expression,point,kind",
    [
        (sp.exp(1 / z), 0, "essential"),
        (sp.log(z), 0, "branch_point"),
        (sp.sqrt(z), 0, "branch_point"),
        (1 / z**2, 0, "pole"),
        (sp.sin(z), 0, "zero"),
        (sp.exp(z), 0, "regular"),
    ],
)
def test_local_branch_classification(expression, point, kind):
    c = fp.classify_singularity(expression, z, point, return_certificate=True)
    assert c.kind == kind and fp.verify_certificate(c)


def test_legitimate_selected_negative_axis_branch_and_replay(base, monkeypatch):
    branch = LocalBranchContext(sp.Integer(-1), ((z, sp.I * sp.pi),))
    c = fp.residue(
        sp.log(z) / (z + 1), z, -1, branch_context=branch, return_certificate=True
    )
    assert c.residue == sp.I * sp.pi and fp.verify_certificate(c)
    order = fp.certify_implicit_multiplicity(g**2, base)
    assert order.verify() and order.order == 2

    def disabled(*args, **kwargs):
        raise AssertionError("proposer called during jet replay")

    monkeypatch.setattr(
        "funcprops.implicit_orders.certify_implicit_multiplicity", disabled
    )
    monkeypatch.setattr("funcprops.implicit_orders.certify_root_value", disabled)
    assert fp.verify_certificate(order)


@pytest.mark.parametrize(
    "operation", ["residue", "laurent_series", "classify_singularity"]
)
@pytest.mark.parametrize("power", [2, -1])
@pytest.mark.parametrize("floating", ["center", "source"])
def test_local_certification_declines_floating_sources_and_centers(
    operation, power, floating
):
    exact, rounded = sp.Rational(1, 10), sp.Float("0.1")
    assert sp.Rational(rounded) > exact
    expression = (z - (rounded if floating == "source" else exact)) ** power
    point = rounded if floating == "center" else exact
    assert getattr(fp, operation)(expression, z, point, return_certificate=True) is None


@pytest.mark.parametrize("kind", ["residue", "laurent", "singularity"])
def test_rounded_local_point_cannot_replay_a_false_pole_or_residue(kind):
    q, p = sp.Rational(1, 10), sp.Float("0.1")
    e = 1 / (z - q)
    c = (
        ResidueCertificate(e, z, p, sp.S.One)
        if kind == "residue"
        else LaurentCertificate(e, z, p, 1 / (z - p), 6)
        if kind == "laurent"
        else SingularityClassificationCertificate(e, z, p, "pole", -1)
    )
    assert_rejected(c)


@pytest.mark.parametrize("stored_float", [False, True])
def test_exact_center_distinction(stored_float):
    q = sp.Rational(1, 10)
    p = sp.Rational(sp.Float("0.1")) if stored_float else q
    c = fp.classify_singularity(1 / (z - q), z, p, return_certificate=True)
    assert c.kind == ("regular" if stored_float else "pole") and fp.verify_certificate(
        c
    )
    c = fp.residue(1 / (z - q), z, p, return_certificate=True)
    assert c.residue == (0 if stored_float else 1) and fp.verify_certificate(c)


def test_branch_values_and_local_order_helpers_do_not_certify_floats():
    from funcprops.singularities.records import order_at

    q, p = sp.Rational(1, 10), sp.Float("0.1")
    assert order_at((z - q) ** 2, z, p) is None
    branch = LocalBranchContext(q, ((z, sp.log(p)),))
    assert branch.apply(sp.log(z) / (z - q), z, q) is None
