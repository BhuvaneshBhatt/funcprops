"""Finite metric and jump-variation replay with proposing functions disabled."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)


@pytest.fixture
def finite():
    return fp.lipschitz(x * x, x, domain=sp.FiniteSet(0, 1, 2), return_result=True)


def test_finite_replay(finite, monkeypatch):
    assert finite.constant == 3 and finite.optimal is fp.TruthValue.TRUE
    assert finite.verify() and fp.verify_certificate(finite, expr=x * x, var=x)
    assert finite.proof.values == ((0, 0), (1, 1), (2, 4))

    def disabled(*args, **kwargs):
        raise AssertionError("proposer called")

    monkeypatch.setattr("funcprops.metric_proofs.certify_finite_lipschitz", disabled)
    monkeypatch.setattr(
        "funcprops.real_analysis.regularity_extensions.lipschitz", disabled
    )
    assert fp.verify_certificate(finite.proof) and finite.verify()


@pytest.mark.parametrize(
    "field,value",
    [
        ("effective", sp.FiniteSet(0, 1)),
        ("values", ((0, 0), (1, 1))),
        ("ratios", ()),
        ("constant", sp.Integer(2)),
        ("expression", x),
    ],
)
def test_finite_mutations(finite, field, value):
    bad = replace(finite.proof, **{field: value})
    assert not bad.verify() and not fp.verify_certificate(bad)
    assert not replace(finite, proof=bad).verify()


def test_finite_summary_mutation(finite):
    assert not replace(finite, constant=sp.Integer(99)).verify()
    assert not replace(finite, domain=sp.FiniteSet(0, 1)).verify()
    assert not fp.verify_certificate(finite, expr=x, var=x)


@pytest.mark.parametrize(
    "support,constant",
    [
        (sp.S.EmptySet, 0),
        (sp.FiniteSet(2), 0),
        (sp.FiniteSet(0, 1, 2), sp.Rational(1, 2)),
    ],
)
def test_pole_and_vacuous_domains(support, constant):
    proof = fp.certify_finite_lipschitz(1 / x, x, support)
    assert proof.verify() and proof.constant == constant
    assert proof.effective == support - sp.FiniteSet(0)


def test_original_finite_source():
    expression = sp.Piecewise((x * x, x < 1), (x + 2, True))
    result = fp.lipschitz(expression, x, domain=sp.FiniteSet(2, 3), return_result=True)
    assert (
        result.proof.expression == expression
        and result.proof.requested == sp.FiniteSet(2, 3)
    )
    assert result.constant == 1 and result.verify()


@pytest.fixture
def jump():
    expression = sp.Piecewise((10, sp.Eq(x, 0)), (x * x, True))
    return fp.variation(expression, x, domain=sp.Interval(-1, 1), return_result=True)


def test_jump_replay(jump, monkeypatch):
    assert jump.total_variation == 22 and jump.verify()
    assert len(jump.proof.cells) == 2

    def disabled(*args, **kwargs):
        raise AssertionError("proposer called")

    monkeypatch.setattr("funcprops.metric_proofs.certify_jump_variation", disabled)
    monkeypatch.setattr("funcprops.real_analysis.variation.variation", disabled)
    monkeypatch.setattr(
        "funcprops.real_analysis.monotonic_certificates.monotonic_partition", disabled
    )
    assert jump.proof.verify() and fp.verify_certificate(jump)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: replace(p, cells=p.cells[:-1]),
        lambda p: replace(p, cells=p.cells * 2),
        lambda p: replace(p, points=p.points[:-1]),
        lambda p: replace(p, total_variation=sp.Integer(2)),
        lambda p: replace(
            p, cells=(replace(p.cells[0], right=sp.Integer(10)), *p.cells[1:])
        ),
        lambda p: replace(p, cells=(replace(p.cells[0], direction=1), *p.cells[1:])),
        lambda p: replace(p, expression=x * x),
        lambda p: replace(p, domain=sp.Interval.open(-1, 1)),
    ],
)
def test_jump_mutations(jump, mutate):
    proof = mutate(jump.proof)
    assert not proof.verify() and not fp.verify_certificate(proof)
    assert not replace(jump, proof=proof).verify()


@pytest.mark.parametrize(
    "left_open,right_open,expected",
    [(False, False, 22), (True, False, 22), (False, True, 22), (True, True, 22)],
)
def test_jump_endpoints(left_open, right_open, expected):
    expression = sp.Piecewise((10, sp.Eq(x, 0)), (x * x, True))
    proof = fp.certify_jump_variation(
        expression, x, sp.Interval(-1, 1, left_open, right_open)
    )
    assert proof.verify() and proof.total_variation == expected


def test_jump_guard_hole():
    expression = sp.Piecewise((x, sp.log(x) > 0), (0, True))
    assert fp.certify_jump_variation(expression, x, sp.Interval(-1, 2)) is None


def test_jump_summary_rejection(jump):
    altered = replace(jump, total_variation=sp.Integer(2))
    assert not fp.verify_certificate(altered)


def test_jump_coordinate_premises():
    positive = sp.Symbol("p", positive=True)
    source = sp.Piecewise((positive, positive < 2), (3 * positive, True))
    assert fp.certify_jump_variation(source, positive, sp.Interval(-1, 3)) is None


@pytest.mark.parametrize(
    "operation", ["certify_finite_lipschitz", "certify_jump_variation"]
)
def test_metric_budgets(operation):
    support = (
        sp.FiniteSet(0, 1)
        if operation == "certify_finite_lipschitz"
        else sp.Interval(0, 1)
    )
    result = getattr(fp, operation)(x, x, support, work_budget=sp.Rational(1, 1000000))
    assert result.complete is False and result.certified is False
    assert result.operation == operation
