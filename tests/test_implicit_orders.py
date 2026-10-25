from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.shared_zeros import SharedZeroOrderProof, SharedZeroRegion

z = sp.Symbol("z")
g = sp.exp(z) - 2
RECT = (sp.Rational(69, 100) - sp.I / 100, sp.Rational(7, 10) + sp.I / 100)
P = fp.EnclosurePolicy(
    precision=20, max_precision=40, max_refinements=1, max_cells=192, max_depth=5
)


@pytest.fixture(scope="module")
def base():
    b = fp.certify_analytic_contour(g, z, *RECT, policy=P)
    assert b.verify() and b.zero_count == 1
    return b


def model(m):
    return sp.sin(g) ** m + z * (sp.exp(g) - 1) ** m


@pytest.fixture(scope="module")
def double(base):
    return fp.certify_implicit_multiplicity(model(2), base, max_order=3, policy=P)


@pytest.mark.parametrize("m", [1, 2, 3, 4])
def test_general_congruences_and_local_multiplicity(base, m):
    f = model(m)
    v = fp.certify_root_value(f, base)
    assert v.value == 0 and v.verify() and fp.verify_certificate(v)
    assert not v.complete and not v.coverage_complete
    p = fp.certify_implicit_multiplicity(f, base, max_order=m + 1, policy=P)
    assert p.verify() and p.order_complete and p.order == m and p.minimum_order == m
    assert not p.coverage_complete and not p.complete
    assert fp.verify_certificate(p.taylor)
    assert fp.replay_status(p).outcome == "valid-local-proof"
    count = fp.certify_analytic_contour(f, z, *RECT, policy=P)
    full = SharedZeroOrderProof(count, p)
    assert full.verify() and full.root_count == 1 and full.multiplicity_count == m
    transfer = SharedZeroRegion(full, base)
    assert transfer.verify() and fp.verify_certificate(transfer)


def test_known_nonzero_values_and_nearby_distinct_zeros(base):
    p = fp.certify_root_value(sp.exp(z), base)
    assert p.value == 2 and p.verify()
    epsilon = sp.Rational(1, 10**50)
    f = model(1) + epsilon
    p = fp.certify_root_value(f, base)
    assert p.value == epsilon and p.verify()
    common = fp.certify_common_zero((model(1), f), base, policy=P)
    assert (
        common.verify()
        and not common.common_zero_certified
        and common.orders_complete
        and common.common_zero_excluded
    )
    assert not common.complete
    assert common.common_zero_status is fp.TruthValue.FALSE


def test_exact_leading_values_prove_positive_orders(base):
    p = fp.certify_implicit_multiplicity(g**2, base, max_order=3, policy=P)
    assert p.verify() and p.order == 2 and p.taylor is None
    assert p.leading_value.value == 8
    assert fp.verify_certificate(p)
    false_value = replace(p.leading_value, value=sp.S.Zero)
    assert not fp.verify_certificate(replace(p, leading_value=false_value))
    assert not fp.verify_certificate(replace(p, zero_jets=p.zero_jets[:-1]))


def test_common_root_order_tuple_and_non_discrete_case(base):
    c = fp.certify_common_zero((model(1), model(2)), base, max_order=3, policy=P)
    assert c.verify() and c.common_zero_certified and c.orders_complete
    assert c.multiplicities == (1, 2) and not c.complete
    assert fp.verify_certificate(c)
    assert not fp.verify_certificate(replace(c, expressions=(model(2), model(1))))
    zero = fp.certify_implicit_multiplicity(sp.S.Zero, base, max_order=2, policy=P)
    assert zero.verify() and zero.minimum_order >= 1 and not zero.order_complete
    assert not zero.complete


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: replace(p, value=sp.Integer(77)),
        lambda p: replace(p, quotient=1 / g),
        lambda p: replace(p, expression=p.expression + 1),
        lambda p: replace(p, children=p.children * 2),
        lambda p: replace(p, schema_version=True),
    ],
)
def test_false_root_values_rejected(base, mutate):
    p = fp.certify_root_value(model(1), base)
    assert not mutate(p).verify() and fp.verify_certificate(mutate(p)) is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: replace(p, order=3),
        lambda p: replace(p, zero_jets=p.zero_jets[:-1]),
        lambda p: replace(
            p, taylor=replace(p.taylor, coefficients=p.taylor.coefficients[:-1])
        ),
        lambda p: replace(
            p, taylor=replace(p.taylor, box=(sp.S.Zero, sp.S.Zero, sp.S.One, sp.S.One))
        ),
        lambda p: replace(p, expression=model(2) + 1),
        lambda p: replace(p, schema_version=2),
    ],
)
def test_false_orders_and_jet_domains_rejected(double, mutate):
    assert double.verify() and double.order == 2
    assert (
        not mutate(double).verify() and fp.verify_certificate(mutate(double)) is False
    )
    assert not fp.verify_certificate(replace(double.taylor, coefficients=()))


def test_replay_independent_of_all_proposers_and_symbolic_division(
    base, double, monkeypatch
):
    c = fp.certify_common_zero((model(1), model(2)), base, policy=P)
    v = fp.certify_root_value(model(1), base)

    def disabled(*args, **kwargs):
        raise AssertionError("proposer called")

    for name in (
        "certify_root_value",
        "certify_implicit_multiplicity",
        "certify_common_zero",
    ):
        monkeypatch.setattr("funcprops.implicit_orders." + name, disabled)
    monkeypatch.setattr(sp, "reduced", disabled)
    monkeypatch.setattr(sp, "solveset", disabled)
    for p in (v, double, c, double.taylor):
        assert fp.verify_certificate(p)


def test_source_holes_parameters_and_nonunique_bases_are_declined(base):
    hole = sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False)
    assert fp.certify_root_value(hole, base) is None
    with pytest.raises(ValueError):
        fp.certify_implicit_multiplicity(hole, base)
    wide = fp.certify_analytic_contour(sp.sin(z), z, -4 - sp.I, 4 + sp.I, policy=P)
    assert wide.zero_count == 3
    with pytest.raises(ValueError):
        fp.certify_root_value(z, wide)
    p = fp.certify_implicit_multiplicity(model(1), base, policy=replace(P, max_cells=0))
    assert p.verify() and not p.order_complete and not p.complete


@pytest.mark.parametrize("m,n", [(1, 1), (2, 3)])
def test_orders_are_consumed_by_quotient_ledger(base, m, n):
    q = fp.certify_quotient_isolation(
        model(m) / g**n, z, *RECT, policy=replace(P, max_cells=1024)
    )
    assert q.verify() and q.coverage_complete
    assert q.multiplicity_count == 0
    assert q.pole_multiplicity_count == max(n - m, 0)


def test_radical_ideal_value_proof_at_a_multiple_implicit_base():
    state = fp.certify_complex_isolation(g**2, z, *RECT, policy=P)
    assert state.complete
    base = state.proof.root_regions[0]
    assert base.zero_count == 2 and base.known_distinct == 1
    p = fp.certify_root_value(g, base)
    assert p.power == 2 and p.value == 0 and p.verify()
    assert not fp.verify_certificate(replace(p, power=0))
    assert not fp.verify_certificate(replace(p, power=True))
    order = fp.certify_implicit_multiplicity(g**2, base, max_order=3, policy=P)
    assert order.verify() and order.order == 2


def test_generic_guard_proof_preserves_canceled_source_holes(base):
    guard = model(1)
    held = sp.Mul(g, guard, sp.Pow(guard, -1, evaluate=False), evaluate=False)
    q = fp.certify_quotient_isolation(held, z, *RECT, policy=replace(P, max_cells=1024))
    assert q.verify() and q.coverage_complete and q.multiplicity_count == 0
    assert q.proof.excluded_zero_multiplicity == 1
    index = next(i for i, c in enumerate(q.proof.cells) if c.numerator.zero_count)
    refined = fp.certify_quotient_refinement(
        q, cell_index=index, policy=replace(P, max_cells=512)
    )
    assert refined.verify()
    assert any(c.guard_zero.verify() for c in refined.cells if c.guard_zero)


def test_erf_derivatives_and_complex_roots(base):
    f = sp.erf(g) ** 2 + z * (sp.erfc(g) - 1) ** 2
    p = fp.certify_implicit_multiplicity(f, base, max_order=3, policy=P)
    assert p.verify() and p.order == 2
    nonreal = fp.certify_analytic_contour(
        sp.exp(z) + 1,
        z,
        -sp.Rational(1, 10) + 3 * sp.I,
        sp.Rational(1, 10) + sp.Rational(33, 10) * sp.I,
        policy=P,
    )
    assert nonreal.zero_count == 1
    h = sp.exp(z) + 1
    f = sp.sin(h) + z * (sp.exp(h) - 1)
    p = fp.certify_implicit_multiplicity(f, nonreal, max_order=2, policy=P)
    assert p.verify() and p.order == 1
