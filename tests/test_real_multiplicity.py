from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.coverage_search import coverage_context
from funcprops.multiple_roots import propose_multiple_leaf

x = sp.Symbol("x", real=True)
P = fp.EnclosurePolicy(
    precision=20, max_precision=80, max_refinements=2, max_cells=600, max_depth=10
)


@pytest.mark.parametrize("m", [2, 3, 4])
def test_powers_of_certified_simple_roots(m):
    r = fp.adaptive_root_coverage((sp.exp(x) - 2) ** m, x, sp.Interval(0, 1), policy=P)
    assert r.complete and r.root_count == 1 and r.multiplicity_count == m and r.verify()


def test_nearby_simple_root_is_not_absorbed_into_multiple_root():
    f = (sp.exp(x) - 2) ** 2 * (sp.exp(x) - sp.Rational(17, 8))
    D = sp.Interval(0, 1)
    # A putative unit vanishes elsewhere in the full initial cell.
    assert propose_multiple_leaf(coverage_context(f, x, D), D, P) is None
    r = fp.adaptive_root_coverage(f, x, D, policy=P)
    assert r.complete and r.root_count == 2 and r.multiplicity_count == 3 and r.verify()
    assert len([a for a in r.proof.leaves if a.root_count]) == 2


@pytest.mark.parametrize("f,m", [(sp.exp(x) - 1 - x, 2), (sp.sin(x) - x, 3)])
def test_selected_analytic_taylor_deflation(f, m):
    leaf = fp.deflate_real_root(
        f, x, sp.Interval(-sp.Rational(1, 4), sp.Rational(1, 4)), 0, m, policy=P
    )
    assert leaf.verify() and leaf.root_count == 1 and leaf.multiplicity_count == m
    assert leaf.theorem == "taylor-deflation"
    assert not replace(leaf, multiplicity_count=m + 1).verify()
    assert not replace(
        leaf, witness=replace(leaf.witness, jets=(sp.S.One,) * m)
    ).verify()
    assert not replace(
        leaf, witness=replace(leaf.witness, center=sp.Rational(1, 100))
    ).verify()
    assert not replace(leaf, witness=replace(leaf.witness, unit_lower=0)).verify()


def test_excluded_endpoint_root_is_not_counted():
    leaf = fp.deflate_real_root(
        sp.exp(x) - 1 - x, x, sp.Interval.Lopen(0, sp.Rational(1, 4)), 0, 2, policy=P
    )
    assert leaf.verify() and leaf.root_count == 0 and leaf.multiplicity_count == 0


@pytest.mark.parametrize(
    "f,center",
    [
        (sp.exp(x) - 1 - x + sp.Rational(1, 10) ** 60, 0),
        (sp.exp(x) - 1 - x, sp.Rational(1, 10) ** 60),
        (sp.Abs(x), 0),
    ],
)
def test_failed_jets_or_regularity_are_not_multiplicity_proofs(f, center):
    assert fp.deflate_real_root(f, x, sp.Interval(-1, 1), center, 2, policy=P) is None


def test_power_unit_and_base_witnesses_are_bound(monkeypatch):
    D = sp.Interval(0, 1)
    f = (sp.exp(x) - 2) ** 2
    leaf = propose_multiple_leaf(coverage_context(f, x, D), D, P)
    assert leaf.verify()
    for witness in (
        replace(leaf.witness, exponent=3),
        replace(leaf.witness, unit=-1),
        replace(leaf.witness, base=sp.exp(x) - 3),
        replace(
            leaf.witness, unit_bound=replace(leaf.witness.unit_bound, lower=0, upper=0)
        ),
    ):
        assert not replace(leaf, witness=witness).verify()

    def disabled(*args, **kwargs):
        raise AssertionError("multiplicity proposer called during replay")

    monkeypatch.setattr("funcprops.multiple_roots.propose_multiple_leaf", disabled)
    monkeypatch.setattr("funcprops.multiple_roots.propose_leaf", disabled)
    assert leaf.verify()


def test_parameter_collision_requires_specialization():
    a = sp.Symbol("a", real=True)
    f = (sp.exp(x) - 2) ** 2 * (sp.exp(x) - 2 - a)
    r = fp.adaptive_root_coverage(f, x, sp.Interval(0, 1), policy=P)
    assert not r.complete and r.root_count is None
    r = fp.adaptive_root_coverage(
        f, x, sp.Interval(0, 1), substitutions={a: 0}, policy=P
    )
    assert r.complete and r.root_count == 1 and r.multiplicity_count == 3 and r.verify()


def test_low_effort_retains_multiple_root_obligations():
    r = fp.adaptive_root_coverage(
        (sp.exp(x) - 2) ** 2, x, sp.Interval(0, 1), policy=replace(P, max_cells=0)
    )
    assert not r.complete and r.multiplicity_count is None and r.verify()


def test_float_jet_center_cannot_create_a_spurious_multiple_root():
    f = (x - sp.Rational(1, 10)) ** 2
    leaf = fp.deflate_real_root(
        f, x, sp.Interval(0, 1), sp.Rational(1, 10), 2, policy=P
    )
    assert leaf.verify()
    rounded = sp.Float("0.1")
    D = sp.Interval(sp.Rational(rounded), 1)
    # The exact stored Float lies above 1/10, yet substitution rounds both jets
    # to zero. A replay must reject it before invoking exact jet identities.
    assert sp.Rational(rounded) > sp.Rational(1, 10)
    derivative = replace(leaf.witness.derivative, domain=D)
    forged = replace(
        leaf,
        context=coverage_context(f, x, D),
        region=D,
        roots=((rounded, 2),),
        witness=replace(leaf.witness, center=rounded, derivative=derivative),
    )
    assert not forged.verify()
    assert fp.deflate_real_root(f, x, D, rounded, 2, policy=P) is None
