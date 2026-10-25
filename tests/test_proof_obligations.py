"""Theorem-premise sentinels for checker mutation and cross-family replay."""

from dataclasses import replace

import sympy as sp

import funcprops as fp
from funcprops.analytic_contours import ComplexBoxWitness

x, a, b = sp.symbols("x a b", real=True)
z, w = sp.symbols("z w")


def test_unique_coefficient_root():
    proof = fp.encode_algebraic_coefficients((sp.sqrt(2) * x,), (x,))
    assert proof.verify()
    altered = replace(proof, interval=(-sp.S(2), sp.S(2)))
    assert not altered.verify()


def test_owned_value_with_consistent_total():
    source = sp.Piecewise((10, sp.Eq(x, 0)), (0, True))
    proof = fp.certify_jump_variation(source, x, sp.Interval(-1, 1))
    assert proof.total_variation == 20 and proof.verify()
    points = tuple((p, sp.Integer(9) if p == 0 else v) for p, v in proof.points)
    assert not replace(proof, points=points, total_variation=sp.Integer(18)).verify()


def test_parameter_premise():
    positive = sp.Symbol("p", positive=True)
    proof = fp.certify_parameter_geometry(
        x * x - positive, x, (positive,), max_cells=100
    )
    assert proof.verify() and proof.specialize({positive: 1}) == 2
    assert proof.specialize({positive: -1}) is None


def test_geometry_source_events():
    proof = fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=100)
    assert proof.verify()
    assert not replace(proof, expression=x * x + a * x + b + 1).verify()


def test_anchor_is_not_identity():
    rectangle = fp.CoverageRectangle(-1 - sp.I, 1 + sp.I)
    left = fp.certify_branch_chart(w * w - z * z, z, w, rectangle, z)
    right = fp.certify_branch_chart(w * w - z * z, z, w, rectangle, -z)
    proof = fp.glue_branch_charts((left, right))
    assert proof.verify() and proof.coverage_complete and not proof.complete
    assert proof.unresolved_overlaps[0].anchor == 0


def test_denominator_witness():
    rectangle = fp.CoverageRectangle(1 - sp.I, 2 + sp.I)
    witness = ComplexBoxWitness(z, z, rectangle.bounds(), rectangle.bounds(), 50)
    chart = fp.certify_branch_chart(z * w - 1, z, w, rectangle, 1 / z, units=(witness,))
    assert chart.verify() and fp.verify_certificate(chart)
    assert not replace(chart, units=()).verify()
    wide = replace(witness, bounds=(sp.S.Zero, -sp.S.One, sp.S(2), sp.S.One))
    assert wide.verify()
    assert not replace(chart, units=(wide,)).verify()


def test_chart_chain_and_corner():
    boxes = (
        fp.CoverageRectangle(0, 1 + sp.I),
        fp.CoverageRectangle(1, 2 + sp.I),
        fp.CoverageRectangle(1 + sp.I, 2 + 2 * sp.I),
    )
    charts = tuple(fp.certify_branch_chart(w - z, z, w, box, z) for box in boxes)
    proof = fp.glue_branch_charts(charts)
    assert proof.verify() and proof.complete and len(proof.overlaps) == 3
    assert not replace(proof, overlaps=proof.overlaps[:-1]).verify()


def test_disconnected_charts():
    boxes = (fp.CoverageRectangle(0, 1 + sp.I), fp.CoverageRectangle(2, 3 + sp.I))
    charts = tuple(fp.certify_branch_chart(w - z, z, w, box, z) for box in boxes)
    proof = fp.glue_branch_charts(charts)
    assert proof.verify() and proof.complete and proof.overlaps == ()
