"""Input, replay and metadata contracts shared by symbolic helpers."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.assumptions import _ask_refine
from funcprops.certified_operations import solve
from funcprops.global_multivariate import affine_global_mapping, compose_global_maps
from funcprops.multivariate_intervals import krawczyk_box
from funcprops.parameter_cells import minimize_strata, refine_parameter_cells
from funcprops.results import ConditionalExpression, PropertyResult

x, y, a, b, c = sp.symbols("x y a b c", real=True)
z = sp.Symbol("z")
D = sp.Interval(0, 1)
RECT = (-1 - sp.I, 1 + sp.I)


@pytest.mark.parametrize("helper", [minimize_strata, refine_parameter_cells])
def test_guard_metadata(helper):
    original = PropertyResult(
        None,
        cases=(ConditionalExpression(sp.S.One, a > 0),),
        source="bound-query",
        exceptions=("unresolved-branch",),
        evidence=("retained-evidence",),
        complete=False,
        certified=False,
        domain_record="bound-domain",
    )
    result = helper(original)
    for field in ("exceptions", "evidence", "complete", "certified", "domain_record"):
        assert getattr(result, field) == getattr(original, field)
    assert result.cases == original.cases


def test_redundant_equalities():
    guard = sp.Eq(a, b) & sp.Eq(b, c) & sp.Eq(a, c)
    result = minimize_strata(
        PropertyResult(None, cases=(ConditionalExpression(sp.S.One, guard),))
    )
    reduced = result.cases[0].condition
    assert reduced.subs({a: 1, b: 1, c: 1}) is sp.S.true
    for values in ((1, 2, 1), (1, 1, 2), (2, 1, 1)):
        assert reduced.subs(dict(zip((a, b, c), values, strict=True))) is sp.S.false


@pytest.mark.parametrize("backend", ["refine", "ask"])
def test_dependency_index_error(monkeypatch, backend):
    def failed(*args, **kwargs):
        raise IndexError("incomplete dependency assumption table")

    monkeypatch.setattr(sp, backend, failed)
    assert _ask_refine(a > 0, sp.S.true) is None


def test_continuity_domain_error():
    with pytest.raises(ValueError, match="real domain"):
        fp.continuous(z, z, domain=sp.S.Complexes)


@pytest.mark.parametrize("field", ["critical_covers", "zero_covers"])
@pytest.mark.parametrize("value", [(1,), (object(),), [None]])
def test_supplied_cover_types(field, value):
    with pytest.raises(TypeError, match="cover"):
        fp.certify_property_coverage(x * x, x, D, **{field: value})


@pytest.mark.parametrize("field", ["root_count", "multiplicity_count"])
@pytest.mark.parametrize("value", [1.0, sp.Float(1), sp.Integer(1), True])
def test_complex_count_schema(field, value):
    proof = fp.complex_root_coverage(z, z, *RECT)
    assert proof.complete and proof.root_count == 1 and proof.verify()
    assert replace(proof, **{field: value}).verify() is False


@pytest.mark.parametrize(
    "assumptions", [{"real": True}, {"positive": True}, {"complex": True}]
)
def test_complex_coordinate_policy(assumptions):
    coordinate = sp.Symbol("q", **assumptions)
    coverage = fp.complex_root_coverage(coordinate + 1, coordinate, *RECT)
    assert coverage.complete is False and coverage.root_count is None
    assert coverage.unresolved == (coverage.rectangle,)
    assert not coverage.verify()
    assert (
        fp.rouche_polynomial_circle(coordinate, coordinate, center=0, radius=1) is None
    )


def test_native_replay_failure_status():
    proof = fp.adaptive_root_coverage(x, x, sp.Interval(-1, 1)).proof
    status = fp.replay_status(replace(proof, context=None), expr=x, var=x)
    assert status.supported is True
    assert status.certified is False and status.complete is False
    assert status.factory_replay is False
    assert status.schema_version == 1 and status.outcome == "rejected-evidence"
    assert fp.verify_certificate(replace(proof, context=None), expr=x, var=x) is False


def test_native_metric_status():
    proof = fp.certify_finite_lipschitz(x * x, x, sp.FiniteSet(0, 1, 2))
    status = fp.replay_status(proof)
    assert status.certified is True and status.factory_replay is False
    bad = fp.replay_status(replace(proof, values=None))
    assert bad.certified is False and bad.factory_replay is False


@pytest.mark.parametrize("shape", ["scalar", "tuple", "list"])
def test_replay_context_forms(shape):
    proof = fp.local_invertibility(2 * x, x, return_result=True)
    expression, variable = {
        "scalar": (2 * x, x),
        "tuple": ((2 * x,), (x,)),
        "list": ([2 * x], [x]),
    }[shape]
    assert fp.verify_certificate(proof, expr=expression, var=variable)
    assert fp.replay_status(proof, expr=expression, var=variable).certified is True
    assert not fp.verify_certificate(proof, expr=x, var=variable)


def test_nonsquare_replay():
    proof = fp.local_invertibility((x + y,), (x, y), return_result=True)
    assert proof.classification is fp.TruthValue.UNKNOWN
    assert proof.verify() and fp.verify_certificate(proof, expr=[x + y], var=[x, y])
    assert not replace(proof, classification=fp.TruthValue.TRUE).verify()
    assert not replace(proof, jacobian=None).verify()
    substitution = fp.change_of_variables((x + y,), (x, y))
    assert substitution.verify() and fp.verify_certificate(substitution)
    assert substitution.classification is fp.TruthValue.UNKNOWN
    assert not replace(substitution, classification=fp.TruthValue.TRUE).verify()
    assert not replace(substitution, absolute_determinant=sp.S.One).verify()
    assert not replace(substitution, orientation=fp.Sign.POSITIVE).verify()


def test_inverse_theorem_scope():
    proof = fp.local_invertibility(x**3, x, return_result=True)
    assert proof.classification is fp.TruthValue.FALSE and proof.verify()
    assert proof.scope == "real-C1-inverse-function-theorem-applicability"


def test_equation_certification_scope():
    proof = solve(x * (sp.cos(x) - x), x, domain=sp.S.Reals, return_certificate=True)
    assert proof.certified is True and proof.complete is False
    assert proof.solutions.has(sp.ConditionSet)
    assert proof.scope == "source-domain-and-equation-solution-set"
    assert replace(proof, solutions=None).verify() is False


def test_iteration_center():
    proof = krawczyk_box(
        (x * x - 2,), (x,), (sp.Interval(sp.Rational(7, 5), sp.Rational(3, 2)),)
    )
    assert proof.verify() and proof.source == "interval-krawczyk"
    assert proof.center == (sp.Rational(29, 20),)
    assert proof.expressions[0].subs(x, proof.center[0]) != 0
    lower, upper = proof.enclosure[0]
    assert lower < sp.sqrt(2) < upper
    assert not replace(proof, center=(sp.S.Zero,)).verify()


def test_zero_germ():
    proof = fp.classify_singularity(0, z, 0, return_certificate=True)
    assert proof.kind == "identically_zero" and proof.order is sp.oo
    assert proof.verify() and fp.verify_certificate(proof)
    assert not replace(proof, kind="zero").verify()
    hole = sp.Mul(0, sp.Pow(sp.sin(1 / z), -1, evaluate=False), evaluate=False)
    assert fp.classify_singularity(hole, z, 0) is None


def test_boundary_depth_status():
    state = fp.certify_quotient_isolation(
        1 / (sp.exp(z) - 1),
        z,
        0,
        1 + sp.I,
        policy=fp.EnclosurePolicy(max_cells=256),
        max_boundary_depth=0,
    )
    assert state.verify() and not state.complete
    assert state.exhaustion == "depth-budget" and state.tested < 256


def test_mixed_composition_error():
    proof = affine_global_mapping((x,), (x,))
    with pytest.raises(TypeError, match="mapping certificates"):
        compose_global_maps((proof, 1))


@pytest.mark.parametrize("head", [sp.sign, sp.Heaviside])
def test_catalogue_range_decline(head):
    result = fp.range(head(sp.exp(x) - 2), x, y)
    assert result.func.__name__ == "UnknownRange"


@pytest.mark.parametrize("head", [sp.Min, sp.Max])
def test_nested_limit_decline(head):
    result = fp.range(head(sp.exp(x**3), 2), x, y, domain=sp.Interval.open(0, sp.oo))
    assert result.func.__name__ == "UnknownRange"


def test_zeroth_derivative_endpoint():
    result = fp.enclose_derivative(sp.sqrt(x), x, D, order=0)
    assert result.certified is True and result.obligations == ()


def test_monotone_payload_rejection():
    proof = fp.monotonic_decomposition(sp.acos(sp.exp(x)), x, return_result=True)
    assert fp.verify_certificate(proof)
    assert fp.verify_certificate(proof, expr=[sp.acos(sp.exp(x))], var=[x])
    assert not fp.verify_certificate(proof, expr=x, var=x)
    assert not fp.verify_certificate(proof, expr=sp.acos(sp.exp(x)), var=y)
    assert fp.verify_certificate(replace(proof, outer=None)) is False


def test_homogeneity_coordinate_binding():
    proof = fp.homogeneity(sp.Abs(x), x, return_result=True)
    assert fp.verify_certificate(proof, expr=sp.Abs(x), var=[x])
    assert not fp.verify_certificate(proof, expr=sp.Abs(x), var=y)


def test_root_context_binding():
    result = fp.transcendental_roots(sp.sin(x), x, allow_numerical=False)
    proof = result.certificates[0]
    assert fp.verify_certificate(proof, expr=[sp.sin(x)], var=[x])
    assert not fp.verify_certificate(proof, expr=sp.cos(x), var=x)
    assert not fp.verify_certificate(proof, expr=sp.sin(x), var=y)


def test_endpoint_limit_failure(monkeypatch):
    from funcprops.real_analysis.range import _monotone_image_interval

    def unsupported(*args, **kwargs):
        raise TypeError("unsupported limit-series expansion")

    monkeypatch.setattr(sp, "limit", unsupported)
    assert _monotone_image_interval(sp.exp(x), x, sp.Interval.open(0, sp.oo)) is None
