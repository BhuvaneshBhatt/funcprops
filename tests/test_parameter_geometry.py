"""Multi-parameter trace-form geometry and exact partition replay."""

from dataclasses import replace
from itertools import product

import pytest
import sympy as sp

import funcprops as fp

x, a, b, c = sp.symbols("x a b c", real=True)


@pytest.fixture(scope="module")
def quadratic():
    return fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=100)


def test_quadratic_strata(quadratic):
    assert (
        quadratic.complete and quadratic.verify() and fp.verify_certificate(quadratic)
    )
    assert quadratic.unresolved_condition is sp.S.false
    assert quadratic.specialize({a: 0, b: -1}) == 2
    assert quadratic.specialize({a: 0, b: 0}) == 1
    assert quadratic.specialize({a: 0, b: 1}) == 0
    assert quadratic.specialize({a: 2, b: 1}) == 1


@pytest.mark.parametrize("av,bv", list(product((-2, 0, 2), (-1, 0, 1))))
def test_quadratic_counts(quadratic, av, bv):
    expected = len(set(sp.real_roots(x * x + av * x + bv)))
    assert quadratic.specialize({a: av, b: bv}) == expected


def test_degree_loss():
    p = fp.certify_parameter_geometry(
        a * x * x + b * x + c, x, (a, b, c), max_cells=100
    )
    assert p.complete and p.verify()
    for values, count in [
        ({a: 0, b: 0, c: 0}, sp.oo),
        ({a: 0, b: 0, c: 1}, 0),
        ({a: 0, b: 2, c: 1}, 1),
        ({a: 1, b: 0, c: -1}, 2),
        ({a: 1, b: 0, c: 1}, 0),
    ]:
        assert p.specialize(values) == count


@pytest.mark.parametrize(
    "support",
    [
        sp.Interval(0, 1),
        sp.Interval.open(0, 1),
        sp.Interval.Lopen(0, 1),
        sp.Interval.Ropen(0, 1),
        sp.Interval.open(0, sp.oo),
        sp.Interval(-sp.oo, 0),
    ],
)
def test_endpoint_counts(support):
    proof = fp.certify_parameter_geometry(x - a, x, (a,), domain=support, max_cells=100)
    assert proof.complete and proof.verify()
    for value in (-1, 0, sp.Rational(1, 2), 1, 2):
        assert proof.specialize({a: value}) == int(bool(support.contains(value)))


def test_multiple_root_count():
    proof = fp.certify_parameter_geometry(
        (x - a) ** 2, x, (a,), domain=sp.Interval(0, 1), max_cells=150
    )
    assert proof.complete and proof.verify()
    assert proof.specialize({a: sp.Rational(1, 2)}) == 1
    assert proof.specialize({a: 0}) == 1
    assert proof.specialize({a: 2}) == 0


def test_partial_and_resume(quadratic):
    partial = fp.certify_parameter_geometry(x * x + a * x + b, x, (a, b), max_cells=1)
    assert partial.verify() and not partial.complete and partial.unresolved
    assert partial.specialize({a: 0, b: -1}) is None
    restored = fp.resume_parameter_geometry(partial, max_cells=100)
    assert restored.verify() and restored.complete
    assert (
        restored.specialize({a: 0, b: -1}) == quadratic.specialize({a: 0, b: -1}) == 2
    )
    assert fp.resume_parameter_geometry(restored, max_cells=0) is restored


def test_guarded_geometry():
    proof = fp.certify_parameter_geometry(
        x * x + a * x + b,
        x,
        (a, b),
        parameter_domain=(a >= 0) & (b <= 0),
        max_cells=100,
    )
    assert proof.verify() and proof.complete
    assert proof.specialize({a: 1, b: -1}) == 2
    assert proof.specialize({a: -1, b: -1}) is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: replace(p, cells=p.cells[:-1]),
        lambda p: replace(p, cells=p.cells * 2),
        lambda p: replace(
            p, cells=(replace(p.cells[0], root_count=sp.Integer(99)), *p.cells[1:])
        ),
        lambda p: replace(p, unresolved=(fp.ParameterGeometryRegion(2),)),
        lambda p: replace(p, expression=x * x + a * x + b + 1),
        lambda p: replace(p, parameters=(b, a)),
        lambda p: replace(p, domain=sp.Interval(0, 1)),
    ],
)
def test_geometry_mutations(quadratic, mutate):
    altered = mutate(quadratic)
    # Reordering declared parameter coordinates alone preserves the theorem.
    if altered.parameters == (b, a):
        assert altered.verify() and altered.specialize({a: 0, b: -1}) == 2
    else:
        assert not altered.verify() and not fp.verify_certificate(altered)


def test_geometry_replay(quadratic, monkeypatch):
    def disabled(*args, **kwargs):
        raise AssertionError("proposer called")

    monkeypatch.setattr(
        "funcprops.parameter_geometry.certify_parameter_geometry", disabled
    )
    monkeypatch.setattr(
        "funcprops.parameter_geometry.resume_parameter_geometry", disabled
    )
    assert quadratic.verify() and fp.verify_certificate(quadratic)


def test_unsupported_source():
    held = sp.Add(
        x * x,
        sp.Mul(0, sp.Pow(x - a, -1, evaluate=False), evaluate=False),
        evaluate=False,
    )
    for expression in (held, sp.exp(x) + a):
        with pytest.raises(ValueError):
            fp.certify_parameter_geometry(expression, x, (a,))
    with pytest.raises(NotImplementedError):
        fp.certify_parameter_geometry(x**5 + a, x, (a,))


def test_geometry_budget():
    proof = fp.certify_parameter_geometry(
        x * x + a * x + b, x, (a, b), work_budget=sp.Rational(1, 1000000)
    )
    assert proof.complete is False and proof.certified is False
    assert proof.operation == "certify_parameter_geometry"


@pytest.mark.parametrize("degree,counts", [(3, (1, 1, 1)), (4, (0, 1, 2))])
def test_higher_degree_geometry(degree, counts):
    proof = fp.certify_parameter_geometry(x**degree - a, x, (a,), max_cells=500)
    assert proof.complete and proof.verify()
    for value, count in zip((-1, 0, 1), counts, strict=True):
        assert proof.specialize({a: value}) == count


@pytest.mark.parametrize("guard", [a < sp.pi, a < sp.sqrt(2), 1 / a > 0])
def test_guard_coefficient_scope(guard):
    with pytest.raises(ValueError):
        fp.certify_parameter_geometry(x - a, x, (a,), parameter_domain=guard)


def test_parameter_assumption_specialization():
    positive = sp.Symbol("positive", positive=True)
    proof = fp.certify_parameter_geometry(
        x * x - positive, x, (positive,), max_cells=100
    )
    assert proof.verify() and proof.complete
    assert proof.specialize({positive: 1}) == 2
    assert proof.specialize({positive: -1}) is None
    assert proof.specialize({positive: 0}) is None


def test_geometry_worker_transport():
    proof = fp.certify_parameter_geometry(
        x**4 - a, x, (a,), max_cells=500, work_budget=30
    )
    assert proof.complete and proof.verify() and fp.verify_certificate(proof)
    assert proof.specialize({a: -1}) == 0
    assert proof.specialize({a: 0}) == 1
    assert proof.specialize({a: 1}) == 2
