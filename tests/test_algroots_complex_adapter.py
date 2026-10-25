from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import algebraic_complex as ac
from funcprops.transcendental import complex_roots as cr

z = sp.Symbol("z")
RECT = (-2 - 2 * sp.I, 2 + 2 * sp.I)


@pytest.mark.parametrize(
    "f,distinct,total",
    [
        (z * z + 1, 2, 2),
        ((z - 1) ** 3, 1, 3),
        ((z - 1) ** 3 * (z + 1) ** 2, 2, 5),
        (z - sp.sqrt(2), 1, 1),
        (z - sp.I, 1, 1),
        (z**5 - z + 1, 5, 5),
    ],
)
def test_routes_exact_algebraic_sources_to_algroots(f, distinct, total, monkeypatch):
    def factory_replay(*args, **kwargs):
        raise AssertionError("factory_replay symbolic root solving must not run")

    monkeypatch.setattr(cr, "_exact_roots", factory_replay)
    r = fp.isolate_complex_roots(f, z, RECT)
    assert r.complete and r.isolation_complete and r.coverage_complete
    assert r.method == "algroots_algebraic_complex_roots"
    assert r.root_count == r.distinct_root_count == distinct
    assert r.total_count == r.multiplicity_count == total
    p = r.algebraic_certificate
    assert p.backend == "algroots-exact-rur"
    assert r.verify() and fp.verify_certificate(p, expr=f, var=z)
    assert all(
        d.certificate.verify() for d in p.decisions if d.disposition == "accepted"
    )


def test_public_detailed_result_exposes_the_adapted_certificate():
    r = fp.complex_zeros(z * z + 1, variable=z, rectangle=RECT, return_result=True)
    assert isinstance(r, fp.ComplexRootIsolationResult) and r.verify()
    assert fp.complex_zeros(z * z + 1, z, rectangle=RECT) == sp.FiniteSet(-sp.I, sp.I)
    assert fp.complex_zeros(1, z, rectangle=RECT) is sp.S.EmptySet


@pytest.mark.parametrize("power", [2, 3, 4])
def test_held_source_poles_are_not_added_back_by_algebraization(power):
    raw = sp.Mul(z**power, sp.Pow(z, -1, evaluate=False), evaluate=False)
    r = fp.isolate_complex_roots(raw, z, RECT)
    assert r.complete and r.roots == () and r.total_count == 0
    assert r.algebraic_certificate.source_syntax == sp.srepr(raw)
    assert fp.verify_certificate(r, expr=raw, var=z)


def test_rational_saturation_preserves_other_defined_roots_and_orders():
    raw = sp.Mul(z, (z - 1) ** 3, sp.Pow(z, -1, evaluate=False), evaluate=False)
    r = fp.isolate_complex_roots(raw, z, RECT)
    assert r.complete and r.roots == (1,) and r.total_count == 3
    assert r.algebraic_certificate.system.nonzero_constraints


@pytest.mark.parametrize(
    "f,roots",
    [
        (sp.sqrt(z) - 1, (1,)),
        (sp.sqrt(z) + 1, ()),
        (sp.sqrt(z), (0,)),
        (sp.sqrt(z) + sp.I, ()),
        (sp.sqrt(z) - sp.I, (-1,)),
    ],
)
def test_principal_radical_branches_are_filtered_before_completion(f, roots):
    p = fp.certify_algebraic_complex_roots(f, z, RECT)
    assert p.complete and p.roots == roots and p.verify()
    assert p.root_count == len(roots)
    assert p.total_count == (0 if not roots else None)


def test_augmented_branch_multiplicity_is_not_a_source_order():
    p = fp.certify_algebraic_complex_roots(sp.sqrt(z), z, RECT)
    c = next(d.certificate for d in p.decisions if d.disposition == "accepted")
    assert c.multiplicity == 1
    assert p.complete and p.multiplicity_count is None


@pytest.mark.parametrize(
    "domain,expected",
    [
        (sp.S.Complexes - sp.FiniteSet(sp.I), (-sp.I,)),
        (sp.FiniteSet(sp.I), (sp.I,)),
        (sp.S.Reals, ()),
        (sp.S.EmptySet, ()),
    ],
)
def test_requested_set_domain_is_retained_and_checked(domain, expected):
    r = fp.isolate_complex_roots(z * z + 1, z, RECT, domain=domain)
    assert r.complete and r.roots == expected and r.verify()
    assert r.algebraic_certificate.domain == domain


def test_exact_closed_rectangle_owns_its_boundary_roots():
    p = fp.certify_algebraic_complex_roots(z * (z - 1), z, (0, 1 + sp.I))
    assert p.complete and p.roots == (0, 1) and p.root_count == p.total_count == 2
    assert p.verify()


def test_conditional_and_public_assumption_guards_are_both_retained():
    f = fp.ConditionalExpression(z * z - 1, sp.Ne(z, 1))
    r = fp.complex_zeros(
        f, z, rectangle=RECT, assumptions=sp.Ne(z, -1), return_result=True
    )
    assert r.complete and r.root_count == 0 and r.verify()
    c = r.algebraic_certificate.condition
    assert c.has(sp.Ne(z, 1)) and c.has(sp.Ne(z, -1))


@pytest.mark.parametrize("negated", [False, True])
def test_raw_guard_holes_survive_normalization_and_negation(negated):
    raw = sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False)
    guard = sp.Eq(raw, 1, evaluate=False)
    if negated:
        guard = sp.Not(
            sp.Eq(sp.Pow(z, -1, evaluate=False), 0, evaluate=False), evaluate=False
        )
    r = fp.complex_zeros(
        fp.ConditionalExpression(z, guard), z, rectangle=RECT, return_result=True
    )
    assert r.complete and r.root_count == 0 and r.verify()
    assert sp.srepr(r.algebraic_certificate.condition) == sp.srepr(guard)


def test_unresolved_root_counts(
    monkeypatch,
):
    original = ac._condition_at
    with monkeypatch.context() as m:
        m.setattr(
            ac, "_condition_at", lambda c, x, r: None if r == 1 else original(c, x, r)
        )
        p = fp.certify_algebraic_complex_roots(z * z - 1, z, RECT)
    assert p.roots == (-1,) and not p.complete and not p.isolation_complete
    assert p.root_count is p.multiplicity_count is None
    assert p.verify()
    status = fp.replay_status(p)
    assert status.certified is True and status.complete is False
    assert status.outcome == "valid-local-proof" and status.factory_replay is True
    assert not replace(p, complete=True).verify()


@pytest.mark.parametrize(
    "f",
    [
        sp.exp(z) - 1,
        z + sp.Symbol("a"),
        sp.Float("0.1") * z,
        sp.oo,
        sp.Piecewise((z, sp.Eq(z, 0)), (1, True)),
    ],
)
def test_unsupported_algebraic_inputs_do_not_get_backend_claims(f):
    p = fp.certify_algebraic_complex_roots(f, z, RECT)
    assert not p.complete and p.root_count is p.multiplicity_count is None
    assert fp.replay_status(p).outcome == "unsupported-replay"


def test_non_algebraic_problem_keeps_the_existing_contour_route():
    r = fp.isolate_complex_roots(sp.exp(z) - 1, z, (-1 - sp.I, 1 + sp.I))
    assert r.complete and r.total_count == 1 and r.algebraic_certificate is None
    assert fp.replay_status(r).supported is True
    assert r.isolation_certificate.verify()


@pytest.mark.parametrize(
    "f", [0, sp.Mul(0, sp.Pow(z, -1, evaluate=False), evaluate=False)]
)
def test_positive_dimensional_zero_sets(f):
    p = fp.certify_algebraic_complex_roots(f, z, RECT)
    assert not p.complete and not p.verify() and p.root_count is None


def test_algebraic_scope_and_effort_caps():
    for f, x, rect, opts in [
        (z**1000, z, RECT, {}),
        (z**4 + 1, z, RECT, {"max_quotient_dimension": 2}),
        (z, z, (sp.Float(-1) - sp.I, 1 + sp.I), {}),
        (sp.Symbol("x", real=True), sp.Symbol("x", real=True), RECT, {}),
    ]:
        p = fp.certify_algebraic_complex_roots(f, x, rect, **opts)
        assert not p.complete and not p.verify()
    with pytest.raises(ValueError):
        fp.certify_algebraic_complex_roots(z, z, RECT, max_quotient_dimension=True)


def test_producer_disabled_replay_and_consistent_status(monkeypatch):
    r = fp.isolate_complex_roots((z - 1) ** 2, z, RECT)
    monkeypatch.setattr(
        ac,
        "certify_algebraic_complex_roots",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("producer called")),
    )
    assert fp.verify_certificate(r, expr=(z - 1) ** 2, var=z)
    assert fp.verify_certificate(r.algebraic_certificate)
    status = fp.replay_status(r)
    assert status.certified and status.complete and status.factory_replay
    assert status.schema_version == 1 and status.outcome == "complete-coverage"
    mismatch = fp.replay_status(r, expr=z + 1, var=z)
    assert not mismatch.certified and mismatch.reason == "source-mismatch"


def test_mutated_adapter_payloads_are_rejected():
    p = fp.certify_algebraic_complex_roots(z * z - 1, z, RECT)
    for bad in (
        replace(p, expression=z + 1),
        replace(p, roots=p.roots[:1]),
        replace(p, decisions=p.decisions[:1]),
        replace(p, decisions=p.decisions * 2),
        replace(p, multiplicities=(True, 1)),
        replace(p, complete=False),
        replace(p, domain=sp.FiniteSet(1)),
        replace(p, condition=sp.Ne(z, 1)),
        replace(p, backend="fake-backend"),
    ):
        assert not bad.verify()
    assert (
        fp.replay_status(replace(p, schema_version=2)).outcome == "unsupported-replay"
    )
    d = p.decisions[0]
    bad_c = replace(d.certificate, multiplicity=99)
    assert not replace(
        p, decisions=(replace(d, certificate=bad_c), *p.decisions[1:])
    ).verify()
    assert not replace(
        p, decisions=(replace(d, multiplicity=True), *p.decisions[1:])
    ).verify()


def test_mutated_wrapper_counts_and_scope_are_rejected():
    r = fp.isolate_complex_roots((z - 1) ** 3, z, RECT)
    for bad in (
        replace(r, total_count=1),
        replace(r, distinct_root_count=3),
        replace(r, roots=()),
        replace(r, complete=False),
        replace(r, isolation_complete=False),
        replace(r, method="exact_complex_roots"),
    ):
        assert not fp.verify_certificate(bad)


def test_backend_failure_does_not_fabricate_completeness(monkeypatch):
    import algroots.rational_univariate as rur

    def failed(*args, **kwargs):
        raise ValueError("backend inconclusive")

    monkeypatch.setattr(rur, "compute_rational_univariate_representation", failed)
    r = fp.isolate_complex_roots(z * z + 1, z, RECT)
    assert not r.complete and not r.isolation_complete
    assert r.root_count is r.total_count is None and not r.certified


def test_condition_set_source_holes():
    raw = sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False)
    domain = sp.ConditionSet(z, sp.Eq(raw, 1, evaluate=False), sp.S.Complexes)
    p = fp.certify_algebraic_complex_roots(z, z, RECT, domain=domain)
    assert not p.complete and fp.replay_status(p).outcome == "unsupported-replay"


def test_fake_self_attesting_backend_certificate_is_rejected():
    p = fp.certify_algebraic_complex_roots(z - 1, z, RECT)

    class Fake:
        def verify(self, **kwargs):
            return True

    d = replace(p.decisions[0], certificate=Fake())
    assert not replace(p, decisions=(d,)).verify()


def test_mutated_rectangle_and_backend_enumeration_are_rejected():
    p = fp.certify_algebraic_complex_roots(z * z - 1, z, RECT)
    from funcprops.complex_coverage import CoverageRectangle

    assert not replace(p, rectangle=CoverageRectangle(-sp.I, 2 + sp.I)).verify()
    assert not replace(
        p, representation=replace(p.representation, geometric_solution_count=99)
    ).verify()
