"""Bounded property proofs, source premises and independent replay."""

import importlib
from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.entire_cancellation import entire_cancellation_proof
from funcprops.real_analysis.hessian_bounds import (
    exponential_hessian_data,
    hessian_counterexample_data,
)
from funcprops.seam_regularity import seam_regularity_proof

x, y = sp.symbols("x y", real=True)
z = sp.Symbol("z")
square = sp.ProductSet(sp.Interval(-1, 1), sp.Interval(-1, 1))
punctured = sp.S.Reals - sp.FiniteSet(0)


def disabled(*args, **kwargs):
    raise AssertionError("replay called a proposer")


def test_jacobian_zero(monkeypatch):
    proof = fp.determinant_nonvanishing(
        sp.sin(x), x, domain=sp.Interval(0, 2), return_result=True
    )
    assert proof.classification is fp.TruthValue.FALSE
    assert proof.source == "scalar-zero-witness" and proof.witness == sp.pi / 2
    assert fp.verify_certificate(proof)
    monkeypatch.setattr("funcprops.transformation._det_nonzero_from_jacobian", disabled)
    monkeypatch.setattr("funcprops.transformation._scalar_zero_witness", disabled)
    monkeypatch.setattr("funcprops.real_analysis.zeros.zeros", disabled)
    fp.clear_caches()
    assert fp.verify_certificate(proof)
    for bad in (
        replace(proof, witness=sp.Integer(0)),
        replace(proof, domain=sp.Interval(0, 1)),
        replace(proof, determinant=sp.sin(x)),
        replace(proof, expressions=(sp.cos(x),)),
        replace(proof, classification=fp.TruthValue.TRUE),
    ):
        assert not fp.verify_certificate(bad)


@pytest.mark.parametrize(
    "domain,expected",
    [
        (sp.Interval.Ropen(0, sp.pi / 2), fp.TruthValue.UNKNOWN),
        (sp.Interval(0, sp.pi / 2), fp.TruthValue.FALSE),
        (sp.Union(sp.Interval(0, 1), sp.Interval(2, 3)), fp.TruthValue.UNKNOWN),
    ],
)
def test_zero_ownership(domain, expected):
    assert fp.determinant_nonvanishing(sp.sin(x), x, domain=domain) is expected


def test_jacobian_source():
    hole = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    expression = sp.Mul(hole, sp.sin(x), evaluate=False)
    result = fp.determinant_nonvanishing(
        expression, x, domain=sp.Interval(0, 2), return_result=True
    )
    assert result.classification is fp.TruthValue.UNKNOWN
    assert result.source == "c1-real-map-unproved"


@pytest.mark.parametrize(
    "expression",
    [
        sp.sin(x) * sp.sign(x),
        x * x * sp.sign(x),
        sp.sin(2 * x - 2) * sp.sign(x - 1),
        sp.Piecewise((-x, x < 0), (x, True)),
    ],
)
def test_continuity_assembly(expression):
    result = fp.continuous(expression, x, return_result=True)
    assert result.primary is fp.Continuity.CONTINUOUS
    proof = seam_regularity_proof(expression, x, sp.S.Reals, "continuous")
    assert proof.verify() and fp.verify_certificate(proof)
    assert proof.conclusion == "continuous" and proof.domain is sp.S.Reals


@pytest.mark.parametrize(
    "expression",
    [
        sp.sign(x),
        sp.Piecewise((1, sp.Eq(x, 0)), (x, True)),
        sp.Piecewise((0, x < 0), (1, True)),
    ],
)
def test_owned_seam_value(expression):
    assert seam_regularity_proof(expression, x, sp.S.Reals, "continuous") is None
    assert fp.continuous(expression, x) is fp.Continuity.DISCONTINUOUS


@pytest.mark.parametrize(
    "domain", [sp.Interval(0, 2), sp.Interval.open(0, 2), punctured]
)
def test_relative_continuity(domain):
    proof = seam_regularity_proof(sp.sin(x) * sp.sign(x), x, domain, "continuous")
    assert proof.verify() and proof.domain == domain


def test_continuity_replay(monkeypatch):
    expression = sp.sin(x) * sp.sign(x)
    proof = seam_regularity_proof(expression, x, sp.S.Reals, "continuous")
    monkeypatch.setattr("funcprops.seam_regularity.seam_regularity_proof", disabled)
    monkeypatch.setattr(
        importlib.import_module("funcprops.singularities.regularity"),
        "_function_continuous_impl",
        disabled,
    )
    fp.clear_caches()
    assert fp.verify_certificate(proof)
    for bad in (
        replace(proof, cells=proof.cells[:-1]),
        replace(proof, cells=proof.cells * 2),
        replace(proof, seams=()),
        replace(proof, expression=sp.sign(x)),
        replace(proof, conclusion="separated-limits"),
        replace(proof, domain=punctured),
    ):
        assert not fp.verify_certificate(bad)
    assert not fp.verify_certificate(proof, expr=sp.cos(x) * sp.sign(x))


@pytest.mark.parametrize(
    "expression", [sp.atan(1 / x), sp.sign(x), sp.Piecewise((0, x < 0), (1, True))]
)
def test_metric_gap(expression):
    lip = fp.lipschitz(expression, x, domain=punctured, return_result=True)
    uniform = fp.uniformly_continuous(
        expression, x, domain=punctured, return_result=True
    )
    assert lip.value is fp.TruthValue.FALSE and lip.constant is None
    assert uniform.primary is fp.TruthValue.FALSE
    assert lip.source == uniform.source == "separated-limits"
    assert (
        lip.verify() and fp.verify_certificate(lip.proof) and fp.verify_certificate(lip)
    )
    assert lip.proof.seams[0][3][0] != lip.proof.seams[0][3][1]


def test_gap_replay(monkeypatch):
    result = fp.lipschitz(sp.atan(1 / x), x, domain=punctured, return_result=True)
    monkeypatch.setattr("funcprops.seam_regularity.seam_regularity_proof", disabled)
    monkeypatch.setattr(
        "funcprops.real_analysis.regularity_extensions.lipschitz", disabled
    )
    fp.clear_caches()
    assert fp.verify_certificate(result)
    for bad in (
        replace(result.proof, seams=()),
        replace(result.proof, cells=()),
        replace(result.proof, domain=sp.Interval(1, 2)),
        replace(result.proof, expression=x),
        replace(result.proof, conclusion="uniformly-continuous"),
    ):
        assert not fp.verify_certificate(bad)
    assert not fp.verify_certificate(replace(result, constant=sp.Integer(1)))
    assert not fp.verify_certificate(replace(result, value=fp.TruthValue.TRUE))


@pytest.mark.parametrize(
    "expression,domain",
    [
        (x, punctured),
        (sp.atan(x), punctured),
        (sp.atan(1 / x), sp.Interval(1, 2)),
        (sp.sign(x), sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2))),
        (sp.sqrt(sp.Abs(x)), punctured),
    ],
)
def test_no_metric_gap(expression, domain):
    assert seam_regularity_proof(expression, x, domain, "separated-limits") is None


def test_source_seam_hole():
    hole = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    expression = sp.Mul(hole, sp.sin(x), sp.sign(x), evaluate=False)
    assert seam_regularity_proof(expression, x, sp.S.Reals, "continuous") is None
    guarded = sp.Piecewise((0, sp.log(x) > 0), (1, True))
    assert seam_regularity_proof(guarded, x, sp.S.Reals, "continuous") is None


@pytest.mark.parametrize("coefficient", [4, 10, 20])
def test_interior_curvature(coefficient):
    expression = x**4 + y**4 + coefficient * x * y
    result = fp.convexity(expression, (x, y), domain=square, return_result=True)
    assert result.primary is fp.Convexity.NEITHER
    proof = result.evidence[0]
    assert proof.method == "interior-hessian-counterexample" and proof.modulus is None
    assert proof.proof[3] == (0, 0)
    assert fp.verify_certificate(proof, expr=expression, var=(x, y))


def test_hessian_replay(monkeypatch):
    expression = x**4 + y**4 + 10 * x * y
    proof = fp.convexity(
        expression, (x, y), domain=square, return_result=True
    ).evidence[0]
    module = importlib.import_module("funcprops.real_analysis.hessian_bounds")
    monkeypatch.setattr(module, "structural_hessian_certificate", disabled)
    monkeypatch.setattr("funcprops.real_analysis.convexity.convexity", disabled)
    fp.clear_caches()
    assert fp.verify_certificate(proof, expr=expression, var=(x, y))
    for bad in (
        replace(proof, proof=()),
        replace(proof, modulus=sp.Integer(1)),
        replace(proof, classification=fp.Convexity.CONVEX),
        replace(proof, domain=sp.ProductSet(sp.Interval(1, 2), sp.Interval(1, 2))),
    ):
        assert not fp.verify_certificate(bad, expr=expression, var=(x, y))


def test_exponential_bound(monkeypatch):
    expression = sp.exp(x * y) + 2 * x * x + 2 * y * y
    proof = fp.convexity(
        expression, (x, y), domain=square, return_result=True
    ).evidence[0]
    assert proof.classification is fp.Convexity.STRONGLY_CONVEX
    assert proof.modulus == 4 - sp.E and proof.modulus > 1
    assert fp.verify_certificate(proof, expr=expression, var=(x, y))
    monkeypatch.setattr(
        "funcprops.real_analysis.hessian_bounds.structural_hessian_certificate",
        disabled,
    )
    fp.clear_caches()
    assert fp.verify_certificate(proof, expr=expression, var=(x, y))
    for bad in (
        replace(proof, modulus=sp.Integer(4)),
        replace(proof, proof=()),
        replace(proof, classification=fp.Convexity.STRONGLY_CONCAVE),
    ):
        assert not fp.verify_certificate(bad, expr=expression, var=(x, y))


@pytest.mark.parametrize(
    "expression",
    [
        sp.exp(x * y),
        -sp.exp(x * y) + 2 * x * x + 2 * y * y,
        sp.exp(x * y) + sp.Symbol("a") * x * x + 2 * y * y,
        sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False) + sp.exp(x * y),
        sp.exp(x * y) + 2.0 * x * x + 2 * y * y,
        sp.exp(x * y) + x**4 + y**4,
    ],
)
def test_exponential_premises(expression):
    assert exponential_hessian_data(expression, (x, y), square) is None


def test_counterexample_premises():
    assert hessian_counterexample_data(x**4 + y**4, (x, y), square) is None
    assert (
        hessian_counterexample_data(
            x**4 + y**4 + 10 * x * y,
            (x, y),
            sp.ProductSet(sp.Interval(1, 2), sp.Interval(1, 2)),
        )
        is None
    )


@pytest.mark.parametrize(
    "expression",
    [
        sp.cos(sp.sqrt(z)),
        sp.cosh(sp.sqrt(z)),
        sp.sin(sp.sqrt(z)) ** 2,
        sp.sinh(sp.sqrt(z)) ** 2,
        sp.cos(sp.sqrt(sp.exp(z))),
        sp.cos(sp.sqrt(z * z + 1)),
    ],
)
def test_entire_cancellation(expression):
    proof = entire_cancellation_proof(expression, z)
    assert proof.verify() and fp.verify_certificate(proof)
    assert fp.meromorphic(expression, z) is fp.Meromorphicity.MEROMORPHIC
    assert fp.analytic(expression, z, domain=sp.S.Complexes) is fp.Analyticity.ANALYTIC


def test_entire_replay(monkeypatch):
    proof = fp.meromorphic(sp.cos(sp.sqrt(z)), z, return_result=True).evidence[0]
    monkeypatch.setattr(
        "funcprops.entire_cancellation.entire_cancellation_proof", disabled
    )
    monkeypatch.setattr(
        importlib.import_module("funcprops.singularities.regularity"),
        "meromorphic",
        disabled,
    )
    fp.clear_caches()
    assert fp.verify_certificate(proof)
    for bad in (
        replace(proof, inner=1 / z),
        replace(proof, template="odd-series"),
        replace(proof, expression=sp.sin(sp.sqrt(z))),
        replace(proof, variable=x),
    ):
        assert not fp.verify_certificate(bad)
    assert not fp.verify_certificate(proof, expr=sp.cosh(sp.sqrt(z)))


@pytest.mark.parametrize(
    "expression",
    [
        sp.sin(sp.sqrt(z)),
        sp.cos(sp.sqrt(sp.log(z))),
        sp.cos(sp.sqrt(1 / z)),
        sp.cos(z ** sp.Rational(1, 3)),
        sp.sin(sp.sqrt(z)) ** 3,
        sp.cos(sp.sqrt(sp.Symbol("a") * z)),
    ],
)
def test_branch_premises(expression):
    assert entire_cancellation_proof(expression, z) is None


def test_entire_source_hole():
    inner = sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False)
    expression = sp.cos(sp.Pow(inner, sp.S.Half, evaluate=False), evaluate=False)
    assert entire_cancellation_proof(expression, z) is None


def test_zero_search_bound(monkeypatch):
    from funcprops.transformation import _scalar_zero_witness

    monkeypatch.setattr("funcprops.real_analysis.zeros.zeros", disabled)
    assert _scalar_zero_witness(sp.cos(x), x, sp.Interval(0, 1000000)) is None
    assert _scalar_zero_witness(sp.cos(x), x, sp.S.Reals) is None
    assert _scalar_zero_witness(sp.cos(sp.pi * x), x, sp.Interval(0, 1)) is None


def test_zero_assumptions():
    proof = fp.determinant_nonvanishing(
        sp.sin(x), x, domain=sp.Interval(0, 2), assumptions=True, return_result=True
    )
    assert proof.classification is fp.TruthValue.FALSE and proof.verify()
    excluded = fp.determinant_nonvanishing(
        sp.sin(x), x, domain=sp.Interval(0, 2), assumptions=x < 1, return_result=True
    )
    assert excluded.classification is fp.TruthValue.TRUE and excluded.verify()


def test_inverse_theorem_witness():
    result = fp.local_invertibility(
        sp.sin(x), x, domain=sp.Interval(0, 2), return_result=True
    )
    assert result.classification is fp.TruthValue.FALSE and result.verify()
    assert result.nonvanishing.witness == sp.pi / 2


@pytest.mark.parametrize(
    "left,right", [(False, False), (False, True), (True, False), (True, True)]
)
def test_box_endpoint_flags(left, right):
    domain = sp.ProductSet(
        sp.Interval(-1, 1, left_open=left, right_open=right), sp.Interval(-1, 1)
    )
    data = exponential_hessian_data(
        sp.exp(x * y) + 2 * x * x + 2 * y * y, (x, y), domain
    )
    assert data[0] is fp.Convexity.STRONGLY_CONVEX and data[1] == 4 - sp.E


def test_seam_intrinsic_domain():
    positive = sp.Symbol("positive", positive=True)
    expression = sp.sin(positive) * sp.sign(positive - 1)
    assert (
        seam_regularity_proof(expression, positive, sp.Interval(-1, 2), "continuous")
        is None
    )


def test_multivariate_exponential():
    w = sp.Symbol("w", real=True)
    expression = sp.exp(x * y) + 2 * (x * x + y * y + w * w)
    domain = sp.ProductSet(*(sp.Interval(-1, 1) for _ in range(3)))
    data = exponential_hessian_data(expression, (x, y, w), domain)
    assert data[0] is fp.Convexity.STRONGLY_CONVEX and data[1] == 4 - sp.E


@pytest.mark.parametrize(
    "expression",
    [
        sp.cos(sp.sqrt(z)),
        sp.cosh(sp.sqrt(z)),
        sp.sin(sp.sqrt(z)) ** 2,
        sp.sinh(sp.sqrt(z)) ** 2,
    ],
)
def test_entire_domain_and_cuts(expression):
    from funcprops.branchcuts import branch_cut_conditions, branch_cut_jumps

    assert fp.branch_points(expression, z) is sp.S.false
    assert fp.branch_cuts(expression, z) == ()
    assert branch_cut_conditions(expression, z) == ()
    assert branch_cut_jumps(expression, z, mode="pairs") == {
        "Plus": [(expression, sp.S.true)],
        "Minus": [(expression, sp.S.true)],
        "Jump": [(sp.S.Zero, sp.S.true)],
    }
    assert fp.domain(expression, z, domain=sp.S.Complexes) is sp.S.true
    assert fp.domain(expression, z) is sp.S.true


def test_remaining_outer_cut():
    expression = sp.log(sp.cos(sp.sqrt(z)))
    assert fp.branch_points(expression, z) != sp.S.false
    assert fp.branch_cuts(expression, z) != ()
    assert fp.branch_points(sp.sin(sp.sqrt(z)), z) == sp.Eq(z, 0)
    assert fp.branch_cuts(sp.sin(sp.sqrt(z)), z) != ()


def test_complex_inner_domain():
    expression = sp.cos(sp.sqrt(sp.I * z))
    assert fp.domain(expression, z, domain=sp.S.Complexes) is sp.S.true
