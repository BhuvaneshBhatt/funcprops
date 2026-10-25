"""Source, hypothesis and numerical-value obligations for differential proofs."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x, y, a = sp.symbols("x y a", real=True)


@pytest.fixture(scope="module")
def differential_records():
    return {
        "gradient": fp.registry_gradient(sp.erf(x)),
        "hessian": fp.registry_hessian(sp.erf(x)),
        "scalar": fp.registry_derivative(sp.erf(x * x), x),
        "vector": fp.registry_chain_rule(sp.erf(x + 2 * y), (x, y), second_order=True),
    }


@pytest.mark.parametrize("kind", ["gradient", "hessian", "scalar", "vector"])
def test_derivation_source(differential_records, kind):
    proof = differential_records[kind]
    assert proof.verify() is True
    assert replace(proof, expression=sp.exp(x)).verify() is False
    assert replace(proof, conditions=sp.S.false).verify() is False
    assert replace(proof, complete=1).verify() is False


def test_gradient_consistent_forgery(differential_records):
    proof = differential_records["gradient"]
    bad = replace(
        proof,
        components=(replace(proof.components[0], partial_derivative=sp.Integer(99)),),
        gradient=(sp.Integer(99),),
    )
    assert bad.verify() is False
    assert replace(proof, positions=()).verify() is False


def test_symmetric_hessian_forgery(differential_records):
    proof = differential_records["hessian"]
    assert replace(proof, hessian=sp.ImmutableMatrix([[99]])).verify() is False


def test_chain_sum_forgery(differential_records):
    proof = differential_records["scalar"]
    bad = replace(
        proof,
        terms=tuple(replace(t, product=sp.S.Zero) for t in proof.terms),
        derivative=sp.S.Zero,
    )
    assert bad.verify() is False
    assert replace(proof, variable=y).verify() is False
    assert replace(proof, gradient_certificate=None).verify() is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("gradient", sp.ImmutableMatrix([99, 99])),
        ("hessian", sp.ImmutableMatrix([[99, 0], [0, 99]])),
        ("jacobian", sp.ImmutableMatrix([[99, 99]])),
        ("variables", (y, x)),
        ("second_order", False),
        ("gradient_certificate", None),
        ("hessian_certificate", None),
    ],
)
def test_transport_field_binding(differential_records, field, value):
    assert replace(differential_records["vector"], **{field: value}).verify() is False


def test_custom_registry_is_a_replay_premise():
    F = sp.Function("F")
    slot = fp.FunctionSlot(0, "u")
    registry = fp.FunctionRegistry(
        [], derivative_rules=[fp.DerivativeRule(F, slot, 2 * slot, conditions=slot > 0)]
    )
    other = fp.FunctionRegistry(
        [], derivative_rules=[fp.DerivativeRule(F, slot, 3 * slot, conditions=slot > 0)]
    )
    proof = fp.registry_derivative(F(x * x), x, registry=registry)
    assert proof.derivative == 4 * x**3 and proof.conditions == (x * x > 0)
    assert proof.verify(registry=registry) is True
    assert proof.verify() is False and proof.verify(registry=other) is False
    assert replace(proof, conditions=sp.S.true).verify(registry=registry) is False


@pytest.mark.parametrize(
    "source,gradient", [(x, (1, 0)), (y, (0, 1)), (sp.Integer(3), (0, 0))]
)
@pytest.mark.parametrize("second_order", [False, True])
def test_atomic_transport(source, gradient, second_order):
    proof = fp.registry_chain_rule(source, (x, y), second_order=second_order)
    assert proof.complete and proof.verify()
    assert proof.gradient == sp.ImmutableMatrix(gradient)
    assert proof.jacobian.shape == (0, 2)
    assert proof.hessian == (sp.zeros(2) if second_order else None)
    assert proof.second_order is second_order


@pytest.mark.parametrize(
    "source",
    [
        sp.nan,
        sp.oo,
        -sp.oo,
        sp.zoo,
        sp.Mul(0, sp.log(0, evaluate=False), evaluate=False),
    ],
)
def test_undefined_constant_derivative(source):
    scalar = fp.registry_derivative(source, x)
    vector = fp.registry_chain_rule(source, (x, y), second_order=True)
    assert scalar.complete is False and scalar.verify() is False
    assert vector.complete is False and vector.verify() is False
    assert scalar.conditions is sp.S.false and vector.conditions is sp.S.false


def test_constant_source_hole_is_a_condition():
    source = sp.Mul(a, sp.Pow(a, -1, evaluate=False), evaluate=False)
    proof = fp.registry_derivative(source, x)
    assert proof.complete and proof.verify() and proof.derivative == 0
    assert proof.conditions.subs(a, 0) is sp.S.false
    assert proof.conditions.subs(a, 1) is sp.S.true


@pytest.mark.parametrize("base", [sp.Integer(2), sp.Rational(1, 2), y])
def test_held_logarithm_hessian(base):
    source = sp.erf(sp.log(x, base, evaluate=False), evaluate=False)
    proof = fp.registry_chain_rule(source, (x, y), second_order=True)
    expanded = sp.erf(sp.log(x) / sp.log(base))
    expected = sp.hessian(expanded, (x, y))
    assert proof.complete and proof.verify()
    assert all(
        sp.simplify(u - v) == 0 for u, v in zip(proof.hessian, expected, strict=True)
    )
    if base == 2:
        assert proof.hessian[0, 0].subs(x, 1) == -2 / (sp.sqrt(sp.pi) * sp.log(2))


@pytest.mark.parametrize(
    "source",
    [
        sp.Mul(x, x, sp.Pow(x, -1, evaluate=False), evaluate=False),
        1 / x,
        sp.oo * x,
        sp.nan,
        sp.Piecewise((x, x < 0), (x + 1, True)),
    ],
)
def test_map_source_premises(source):
    proof = fp.determinant_nonvanishing(source, x, return_result=True)
    assert proof.classification is fp.TruthValue.UNKNOWN and proof.verify()
    local = fp.local_invertibility(source, x, return_result=True)
    assert local.classification is fp.TruthValue.UNKNOWN
    assert not replace(
        proof, classification=fp.TruthValue.TRUE, source="constant-nonzero"
    ).verify()


def test_narrowed_coordinate_domain():
    positive = sp.Symbol("positive", positive=True)
    proof = fp.local_invertibility(positive**2, positive, return_result=True)
    assert proof.classification is fp.TruthValue.UNKNOWN
    restricted = fp.determinant_nonvanishing(
        positive**2, positive, domain=sp.Interval(1, 2), return_result=True
    )
    assert restricted.classification is fp.TruthValue.TRUE and restricted.verify()


@pytest.mark.parametrize("source", [sp.S.Zero, x])
def test_empty_map_query(source):
    proof = fp.determinant_nonvanishing(
        source, x, domain=sp.S.EmptySet, return_result=True
    )
    assert proof.classification is fp.TruthValue.UNKNOWN and proof.verify()


@pytest.mark.parametrize(
    "source,domain", [(1 / x, sp.Interval(1, 2)), (sp.log(x), sp.Interval(1, 2))]
)
def test_restricted_map_proof(source, domain):
    proof = fp.determinant_nonvanishing(source, x, domain=domain, return_result=True)
    assert proof.classification is fp.TruthValue.TRUE
    assert proof.expressions == (source,) and proof.verify()
    assert replace(proof, domain=sp.S.Reals).verify() is False
    assert replace(proof, determinant=sp.Integer(99)).verify() is False
    assert fp.verify_certificate(proof, expr=[source], var=[x]) is True


def test_map_hole_cannot_borrow_a_determinant():
    proof = fp.local_invertibility(x, x, return_result=True)
    hole = sp.Mul(x, x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    bad = replace(
        proof, expressions=(hole,), jacobian=fp.registry_jacobian((hole,), (x,))
    )
    assert proof.verify() and bad.verify() is False
    forged = replace(proof.nonvanishing, expressions=(hole,))
    assert forged.verify() is False


def test_inconclusive_backend_is_not_exclusion(monkeypatch):
    import funcprops._semialg as backend
    import funcprops.transformation as transformation

    monkeypatch.setattr(
        transformation, "_scalar_sign_exclusion", lambda *args: fp.Sign.UNKNOWN
    )

    proof = fp.determinant_nonvanishing(
        x * x, x, domain=(x > 1) & (x < 2), return_result=True
    )
    assert proof.classification is fp.TruthValue.TRUE and proof.verify()
    assert proof.source == "semialgebraic-no-zero"
    monkeypatch.setattr(backend, "is_satisfiable", lambda *args, **kwargs: None)
    assert proof.verify() is False
