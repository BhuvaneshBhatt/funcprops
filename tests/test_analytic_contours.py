from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.complex_coverage import CoverageRectangle
from funcprops.complex_interval import complex_box_evaluate

z = sp.Symbol("z")
P = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=200, max_depth=5
)
LO, HI = -sp.Rational(1, 2) - sp.I / 2, sp.Rational(1, 2) + sp.I / 2


@pytest.mark.parametrize(
    "f,count",
    [
        (sp.exp(z) - 1, 1),
        ((sp.exp(z) - 1) ** 2, 2),
        (sp.erf(z), 1),
        (sp.erf(z) - sp.Rational(1, 5), 1),
        (sp.erf(z) + 2, 0),
        (sp.sin(z), 1),
        (sp.cosh(z), 0),
        (sp.erfc(z) - 1, 1),
    ],
)
def test_entire_counts_with_independent_replay(f, count, monkeypatch):
    c = fp.certify_analytic_contour(f, z, LO, HI, policy=P)
    assert c.complete and c.zero_count == count and c.verify()
    assert c.multiplicity_count == count
    assert c.root_count == (0 if count == 0 else None)
    assert c.real_root_count == (0 if count == 0 else None)

    def disabled(*a, **k):
        raise AssertionError("producer used during replay")

    monkeypatch.setattr(
        "funcprops.analytic_contours.certify_analytic_contour", disabled
    )
    monkeypatch.setattr(
        "funcprops.analytic_contours.analytic_complex_coverage", disabled
    )
    assert c.verify() and fp.verify_certificate(c, expr=f, var=z)
    assert fp.replay_status(c).outcome == "complete-coverage"
    assert fp.replay_status(c).factory_replay is False
    entries = {r["type"]: r for r in fp.proof_api_manifest()["records"]}
    for name in (
        "AnalyticComplexCoverage",
        "AnalyticContourCertificate",
        "ComplexBoxWitness",
    ):
        assert (
            entries["funcprops.analytic_contours." + name]["contract"]
            == "witness-kernel"
        )


@pytest.mark.parametrize(
    "f",
    [
        sp.log(z),
        sp.sqrt(z),
        1 / z,
        sp.conjugate(z),
        sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False),
        sp.exp(z) + sp.Symbol("a"),
    ],
)
def test_source_holes_branches_parameters_decline(f):
    c = fp.certify_analytic_contour(f, z, LO, HI, policy=P)
    assert not c.complete and c.zero_count is None and c.check().certified is not True


@pytest.mark.parametrize(
    "f,lo,hi",
    [
        (sp.exp(z) - 1, 0, 1 + sp.I),
        (sp.erf(z), -1, 1 + sp.I),
        (sp.exp(z) - 1, -1 - sp.I, 0),
    ],
)
def test_boundary_zeros_never_complete(f, lo, hi):
    c = fp.certify_analytic_contour(
        f, z, lo, hi, policy=replace(P, max_cells=30, max_depth=2)
    )
    assert not c.complete and c.zero_count is None and c.verify()
    cover = fp.analytic_complex_coverage(
        f, z, lo, hi, policy=replace(P, max_cells=30, max_depth=2)
    )
    assert (
        not cover.complete
        and cover.multiplicity_count is None
        and cover.unresolved
        and cover.verify()
    )


def test_mutations_source_geometry_images_winding_schema():
    c = fp.certify_analytic_contour(sp.exp(z) - 1, z, LO, HI, policy=P)
    for bad in (
        replace(c, zero_count=2),
        replace(c, zero_count=True),
        replace(c, expression=sp.exp(z) - 2),
        replace(c, rectangle=CoverageRectangle(-1 - sp.I, 1 + sp.I)),
        replace(c, knots=c.knots[1:]),
        replace(c, images=c.images[:-1]),
        replace(c, vertices=(0,) * len(c.vertices)),
        replace(c, coordinate_assumptions=()),
        replace(c, images=list(c.images)),
    ):
        assert bad.check().certified is False
    w = c.images[0]
    bad = replace(w, bounds=(sp.S.One, sp.S.One, sp.Integer(2), sp.Integer(2)))
    assert not bad.verify()
    assert not replace(c, images=(bad, *c.images[1:])).verify()
    assert fp.replay_status(replace(c, schema_version=2)).certified is None


def test_exact_tiling_shared_edges_and_omissions():
    f = sp.exp(z) - 1
    left = fp.certify_analytic_contour(
        f, z, -1 - sp.I, -sp.Rational(1, 4) + sp.I, policy=P
    )
    right = fp.certify_analytic_contour(
        f, z, -sp.Rational(1, 4) - sp.I, 1 + sp.I, policy=P
    )
    c = fp.AnalyticComplexCoverage(
        f, z, CoverageRectangle(-1 - sp.I, 1 + sp.I), (left, right), (), True, 1
    )
    assert left.complete and right.complete and c.verify()
    assert not replace(c, regions=(right,)).verify()
    assert not replace(c, regions=(left, right, right)).verify()
    assert not replace(c, multiplicity_count=True).verify()
    boundary = fp.certify_analytic_contour(
        f, z, -1 - sp.I, sp.I, policy=replace(P, max_cells=20, max_depth=2)
    )
    assert not replace(c, regions=(boundary, right)).verify()


def test_budget_primitive_and_complex_coordinate_guards():
    c = fp.certify_analytic_contour(
        sp.exp(z) - 1, z, LO, HI, policy=replace(P, max_cells=0)
    )
    assert not c.complete and c.tested == 0 and c.verify()
    assert fp.replay_status(c).outcome == "resource-exhaustion"
    assert (
        complex_box_evaluate(sp.erf(z), z, (sp.S.Zero,) * 4, max_series_terms=0) is None
    )
    assert (
        complex_box_evaluate(
            sp.exp(z), z, (sp.S.Zero, sp.S.Zero, sp.S.One, sp.S.One), precision=True
        )
        is None
    )
    c = fp.certify_analytic_contour(
        sp.exp(sp.Symbol("x", real=True)) - 1,
        sp.Symbol("x", real=True),
        LO,
        HI,
        policy=P,
    )
    assert not c.complete and not c.verify()


@pytest.mark.parametrize(
    "f",
    [
        sp.exp(z),
        sp.erf(z),
        sp.sin(z),
        sp.cos(z),
        sp.sinh(z),
        sp.cosh(z),
        sp.erfc(z),
        sp.exp(sp.sin(z)),
    ],
)
def test_outward_complex_primitive_contains_high_precision_samples(f):
    box = (sp.Rational(-1, 4), sp.Rational(-1, 5), sp.Rational(1, 3), sp.Rational(1, 4))
    bounds = complex_box_evaluate(f, z, box, precision=25)
    for re in (box[0], 0, box[2]):
        for im in (box[1], 0, box[3]):
            v = f.subs(z, re + sp.I * im).evalf(70)
            assert bool(bounds[0].evalf(70) <= sp.re(v) <= bounds[2].evalf(70))
            assert bool(bounds[1].evalf(70) <= sp.im(v) <= bounds[3].evalf(70))


def test_erf_disk_shared_cluster_evidence_and_multiple_winding():
    c = fp.certify_complex_cluster(
        sp.erf(z), z, 0, sp.Rational(1, 4), policy=replace(P, max_taylor_order=12)
    )
    assert c.complete and c.zero_count == 1 and c.verify()
    assert c.real_root_count is None and c.individual_multiplicities is None
    c = fp.certify_analytic_contour(
        sp.exp(z) - 1,
        z,
        -1 - 7 * sp.I,
        1 + 7 * sp.I,
        policy=replace(P, max_cells=400, max_depth=7),
    )
    assert c.complete and c.zero_count == 3 and c.verify()


@pytest.mark.parametrize(
    "operation", [fp.certify_analytic_contour, fp.analytic_complex_coverage]
)
def test_hard_wall_returns_native_source_bound_pending(operation):
    c = operation(sp.exp(z) - 1, z, LO, HI, policy=replace(P, seconds=0.000001))
    assert not c.complete and c.verify()
    status = fp.replay_status(c)
    assert status.outcome == "resource-exhaustion" and status.complete is False
