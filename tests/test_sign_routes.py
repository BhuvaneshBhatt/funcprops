"""Exact sign dispatch, source restrictions and box-curvature replay."""

import importlib
import random
from dataclasses import replace

import pytest
import semialg
import sympy as sp

import funcprops as fp
from funcprops.real_analysis.common import set_to_condition
from funcprops.real_analysis.hessian_bounds import hessian_dominance_data
from funcprops.real_analysis.sign_rules import (
    rational_polynomials,
    rational_sign,
    threshold_sign,
    trig_sign,
)
from tools.benchmark_sign_routes import cases

x, y = sp.symbols("x y", real=True)


@pytest.mark.parametrize(
    ("group", "name", "operation", "expression", "variables", "domain", "expected"),
    cases(),
)
def test_fixed_answers(group, name, operation, expression, variables, domain, expected):
    result = getattr(fp, operation)(expression, variables, domain=domain)
    assert result.name == expected


def test_sturm_backend():
    rng = random.Random(9172)
    for _ in range(35):
        numerator = sp.Integer(rng.choice((-1, 1)))
        for _ in range(rng.randrange(1, 4)):
            numerator *= (x - rng.randrange(-2, 3)) ** rng.randrange(1, 4)
        expression = numerator / (x * x + 1)
        left = sp.Rational(rng.randrange(-6, 3), 2)
        right = left + sp.Rational(rng.randrange(1, 9), 2)
        domain = sp.Interval(
            left,
            right,
            left_open=bool(rng.randrange(2)),
            right_open=bool(rng.randrange(2)),
        )
        guard = set_to_condition(domain, x)
        observed = []
        for relation in (numerator > 0, numerator < 0, sp.Eq(numerator, 0)):
            decision = semialg.quantifier_eliminate(
                sp.And(guard, relation), [("exists", x)]
            )
            assert decision in (sp.S.true, sp.S.false)
            observed.append(decision is sp.S.true)
        positive, negative, zero = observed
        expected = (
            fp.Sign.SIGN_CHANGING
            if positive and negative
            else fp.Sign.NONNEGATIVE
            if positive and zero
            else fp.Sign.NONPOSITIVE
            if negative and zero
            else fp.Sign.POSITIVE
            if positive
            else fp.Sign.NEGATIVE
            if negative
            else fp.Sign.ZERO
        )
        assert rational_sign(expression, x, domain) == expected


@pytest.mark.parametrize(
    ("expression", "domain", "expected"),
    [
        (x * x, sp.Interval.open(0, 1), fp.Sign.POSITIVE),
        (x * x, sp.Interval(0, 1), fp.Sign.NONNEGATIVE),
        (x**3, sp.Interval(-1, 1), fp.Sign.SIGN_CHANGING),
        (-((x - 1) ** 2), sp.Interval(0, 2), fp.Sign.NONPOSITIVE),
        (x, sp.FiniteSet(0), fp.Sign.ZERO),
        (x, sp.FiniteSet(-1, 1), fp.Sign.SIGN_CHANGING),
        (
            1 / x,
            sp.Union(sp.Interval.Ropen(-1, 0), sp.Interval.Lopen(0, 1)),
            fp.Sign.SIGN_CHANGING,
        ),
        (1 / x, sp.Interval(-1, 1), fp.Sign.UNKNOWN),
        (x - 1, sp.Interval.open(1, 3), fp.Sign.POSITIVE),
        (x - 1, sp.Interval(1, 3), fp.Sign.NONNEGATIVE),
    ],
)
def test_owned_zeros(expression, domain, expected):
    assert rational_sign(expression, x, domain) == expected


def test_held_source():
    held = sp.Mul(x, x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    assert fp.sign(held, x, domain=sp.Interval(0, 2)) is fp.Sign.POSITIVE
    missing = sp.Mul(x - 1, sp.Pow(x - 1, -1, evaluate=False), evaluate=False)
    assert fp.sign(missing, x, domain=sp.FiniteSet(1)) is fp.Sign.UNKNOWN
    assert fp.sign(missing, x, domain=sp.Interval(0, 2)) is fp.Sign.POSITIVE


@pytest.mark.parametrize(
    ("expression", "domain", "expected"),
    [
        (sp.exp(x * x) - 2, sp.Interval(1, 2), fp.Sign.POSITIVE),
        (2 - sp.exp(x * x), sp.Interval(1, 2), fp.Sign.NEGATIVE),
        (sp.exp(x * x) - 1, sp.Interval.open(0, 1), fp.Sign.POSITIVE),
        (sp.exp(x * x) - 1, sp.Interval(-1, 1), fp.Sign.NONNEGATIVE),
        (sp.log(x * x + 1) - sp.log(2), sp.Interval.open(-1, 1), fp.Sign.NEGATIVE),
        (sp.log(x * x + 1) - sp.log(2), sp.Interval(-1, 1), fp.Sign.NONPOSITIVE),
        (sp.log(x * x) - 1, sp.Interval(-1, 1), fp.Sign.UNKNOWN),
        (sp.exp(x * x) + 1, sp.Interval(-2, 2), fp.Sign.POSITIVE),
    ],
)
def test_threshold_ownership(expression, domain, expected):
    assert threshold_sign(expression, x, domain) == expected


@pytest.mark.parametrize(
    "expression",
    (
        sp.log(x * x + 1) - 1000,
        sp.exp(x * x) - sp.exp(1000),
        (sp.Integer(1) << 513) * sp.exp(x * x) - 2,
        sp.exp(sp.I * x) - 2,
        sp.exp(x * x) - sp.Symbol("a", positive=True),
    ),
)
def test_threshold_scope(expression):
    assert threshold_sign(expression, x, sp.Interval(-1, 1)) is fp.Sign.UNKNOWN


@pytest.mark.parametrize(
    ("expression", "domain", "expected"),
    [
        (sp.sin(x), sp.Interval(0, 3), fp.Sign.NONNEGATIVE),
        (sp.sin(x), sp.Interval.Lopen(0, 3), fp.Sign.POSITIVE),
        (sp.sin(1 - x, evaluate=False), sp.Interval.Ropen(0, 1), fp.Sign.POSITIVE),
        (sp.sin(x), sp.Interval(-3, 3), fp.Sign.SIGN_CHANGING),
        (
            sp.cos(x),
            sp.Interval(-sp.Rational(3, 2), sp.Rational(3, 2)),
            fp.Sign.POSITIVE,
        ),
        (sp.cos(x), sp.Interval(2, 3), fp.Sign.NEGATIVE),
        (sp.cos(x), sp.Interval(-3, -2), fp.Sign.NEGATIVE),
        (sp.cos(x), sp.Interval(0, 2), fp.Sign.UNKNOWN),
    ],
)
def test_trig_charts(expression, domain, expected):
    assert trig_sign(expression, x, domain) == expected


@pytest.mark.parametrize(
    "expression",
    (
        sp.sqrt(2) * x,
        x**13 + 1,
        sp.sin(x),
        sp.Symbol("a") * x,
        sp.Mul(sp.Pow(2, 100000, evaluate=False), x, evaluate=False),
        sp.Mul(x, sp.Pow(x - x, -1, evaluate=False), evaluate=False),
        sp.Float(1) * x,
    ),
)
def test_rational_declines(expression):
    assert rational_polynomials(expression, x) is None


def test_scope_guards():
    positive = sp.Symbol("p", positive=True)
    assert rational_sign(positive**2, positive, sp.S.Reals) is fp.Sign.UNKNOWN
    assert rational_sign(x, x, sp.Interval(0, sp.sqrt(2))) is fp.Sign.UNKNOWN
    assert rational_sign(x, x, sp.S.Integers) is fp.Sign.UNKNOWN
    assert rational_sign(x, x, sp.S.EmptySet) is fp.Sign.UNKNOWN
    assert rational_sign(x, x, sp.Interval(0, sp.Integer(1) << 513)) is fp.Sign.UNKNOWN


def test_general_sign_routes_unused(monkeypatch):
    module = importlib.import_module("funcprops.real_analysis.sign")

    def fail(*args, **kwargs):
        pytest.fail("bounded sign rule reached a general proposer")

    for name in (
        "_registry_sign",
        "_semialg_sign",
        "algebraize",
        "transcendental_roots",
        "_interval_sign",
    ):
        monkeypatch.setattr(module, name, fail)
    fp.clear_caches()
    assert (
        fp.sign(sp.expand((x * x - x + 1) ** 3), x, domain=sp.Interval(0, 1))
        is fp.Sign.POSITIVE
    )
    assert (
        fp.sign((x - 1) ** 3 / (x + 2), x, domain=sp.Interval(0, 2))
        is fp.Sign.SIGN_CHANGING
    )
    assert (
        fp.sign(sp.exp(x * x) - 2, x, domain=sp.Interval(0, 1)) is fp.Sign.SIGN_CHANGING
    )
    assert fp.sign(sp.sin(x), x, domain=sp.Interval(-1, 1)) is fp.Sign.SIGN_CHANGING


def test_jacobian_replay(monkeypatch):
    proof = fp.determinant_nonvanishing(
        sp.sin(x), x, domain=sp.Interval(-1, 1), return_result=True
    )
    assert proof.classification is fp.TruthValue.TRUE
    assert proof.source == "scalar-sign-exclusion"
    fp.clear_caches()
    assert proof.verify()
    assert not replace(proof, witness=fp.Sign.NEGATIVE).verify()
    assert not replace(proof, domain=sp.Interval(0, 2)).verify()
    assert not replace(proof, expressions=(sp.cos(x),)).verify()


def test_jacobian_assumptions(monkeypatch):
    module = importlib.import_module("funcprops.transformation")
    monkeypatch.setattr(module, "_scalar_sign_exclusion", lambda *args: fp.Sign.UNKNOWN)
    expression = x**3 / 3 - x * x / 2
    proof = fp.determinant_nonvanishing(
        expression, x, assumptions=x > 2, return_result=True
    )
    assert proof.classification is fp.TruthValue.TRUE
    assert proof.source == "semialgebraic-no-zero"
    assert proof.verify()
    contradiction = fp.determinant_nonvanishing(
        expression, x, assumptions=(x > 2) & (x < 1), return_result=True
    )
    assert contradiction.classification is fp.TruthValue.UNKNOWN
    assert contradiction.source == "c1-real-map-unproved"


def test_disconnected_sign_is_not_zero(monkeypatch):
    import funcprops._semialg as backend

    domain = sp.Union(sp.Interval(-2, -1), sp.Interval(1, 2))
    assert rational_sign(2 * x, x, domain) is fp.Sign.SIGN_CHANGING
    monkeypatch.setattr(backend, "is_satisfiable", lambda *args: None)
    proof = fp.determinant_nonvanishing(x * x, x, domain=domain, return_result=True)
    assert proof.classification is fp.TruthValue.UNKNOWN
    assert proof.source == "unresolved"


def test_boolean_assumptions():
    proof = fp.determinant_nonvanishing(
        x * x + x, x, domain=sp.Interval(1, 2), assumptions=True, return_result=True
    )
    assert proof.classification is fp.TruthValue.TRUE
    assert proof.verify()


def test_hessian_replay(monkeypatch):
    expression = x**4 + y**4 + 2 * x * x + 2 * y * y + x * y
    domain = sp.ProductSet(sp.Interval(-1, 1), sp.Interval(-1, 1))
    result = fp.convexity(expression, (x, y), domain=domain, return_result=True)
    proof = result.evidence[0]
    assert proof.method == "box-hessian-dominance"
    assert proof.modulus == 3
    assert fp.verify_certificate(proof, expr=expression, var=(x, y))
    module = importlib.import_module("funcprops.real_analysis.hessian_bounds")

    def fail(*args, **kwargs):
        pytest.fail("replay called the certificate proposer")

    monkeypatch.setattr(module, "hessian_dominance_certificate", fail)
    assert fp.verify_certificate(proof, expr=expression, var=(x, y))
    for bad in (
        replace(proof, modulus=4),
        replace(proof, classification=fp.Convexity.STRONGLY_CONCAVE),
        replace(proof, proof=()),
        replace(proof, domain=sp.ProductSet(sp.Interval(-2, 2), sp.Interval(-2, 2))),
    ):
        assert not fp.verify_certificate(bad, expr=expression, var=(x, y))
    assert not fp.verify_certificate(proof, expr=expression + 1, var=(x, y))


@pytest.mark.parametrize(
    "expression",
    (
        sp.Abs(x) + y * y + x * y,
        sp.Piecewise((x + y, x < 0), (x + y + 1, True)) + x * y,
        sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False) + y * y,
        sp.log(x) + y * y + x * y,
        sp.I * x * x + y * y,
        sp.Symbol("a", real=True) * x * x + y * y + x * y,
        sp.exp(1000 * x) + y * y + x * y,
    ),
)
def test_hessian_premises(expression):
    domain = sp.ProductSet(sp.Interval(-1, 1), sp.Interval(-1, 1))
    assert hessian_dominance_data(expression, (x, y), domain) is None
