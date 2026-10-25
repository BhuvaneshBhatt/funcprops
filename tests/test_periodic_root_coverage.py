from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)


@pytest.mark.parametrize(
    "f,count,mult",
    [
        (sp.sin(x), sp.oo, sp.oo),
        (sp.sin(x) + sp.Rational(1, 3), sp.oo, sp.oo),
        (sp.cos(2 * x + sp.pi / 3), sp.oo, sp.oo),
        (sp.sin(-3 * x - sp.pi / 7), sp.oo, sp.oo),
        (sp.tan(x), sp.oo, sp.oo),
        (1 / sp.sin(x), 0, 0),
        (sp.sin(x) + 2, 0, 0),
        (sp.cos(x) ** 2 - 1, sp.oo, sp.oo),
        (sp.Integer(0), sp.oo, None),
        (sp.Integer(2), 0, 0),
    ],
)
def test_exhaustive_indexed_or_degenerate_families(f, count, mult):
    r = fp.infinite_root_coverage(f, x)
    assert (
        r.complete
        and r.root_count == count
        and r.multiplicity_count == mult
        and r.verify()
    )


@pytest.mark.parametrize(
    "D,count",
    [
        (sp.Interval(0, 2 * sp.pi), 3),
        (sp.Interval.open(0, 2 * sp.pi), 1),
        (sp.Interval.Lopen(0, 2 * sp.pi), 2),
        (sp.Interval.Ropen(0, 2 * sp.pi), 2),
        (sp.Interval(100 * sp.pi, 102 * sp.pi), 3),
        (sp.FiniteSet(0, sp.pi, 2 * sp.pi, sp.Rational(1, 3)), 3),
        (sp.Union(sp.Interval(0, sp.pi), sp.Interval(3 * sp.pi, 4 * sp.pi)), 4),
    ],
)
def test_finite_integer_ranges_and_endpoint_ownership(D, count):
    r = fp.infinite_root_coverage(sp.sin(x), x, D)
    assert r.complete and r.root_count == count and r.verify()


@pytest.mark.parametrize(
    "f,D,count,mult",
    [
        (sp.sin(x) ** 2, sp.Interval(0, 2 * sp.pi), 3, 6),
        (sp.cos(x) - 1, sp.Interval(0, 2 * sp.pi), 2, 4),
        (sp.sin(x) - 1, sp.Interval(0, 2 * sp.pi), 1, 2),
        (sp.sin(x) + 1, sp.Interval(0, 2 * sp.pi), 1, 2),
        (sp.sin(x) + sp.Rational(1, 3), sp.Interval(0, 10), 3, 3),
        (sp.cos(x) - sp.Rational(1, 3), sp.Interval(-10, 10), 6, 6),
        (sp.tan(x), sp.Interval(-sp.pi / 2, sp.pi / 2), 1, 1),
    ],
)
def test_fold_multiplicities_and_inverse_phase_boundaries(f, D, count, mult):
    r = fp.infinite_root_coverage(f, x, D)
    assert (
        r.complete
        and r.root_count == count
        and r.multiplicity_count == mult
        and r.verify()
    )


def test_cancelled_denominator_and_tangent_chart_poles_are_not_roots():
    atom = sp.sin(x)
    held = sp.Mul(atom, sp.Pow(atom, -1, evaluate=False), evaluate=False)
    r = fp.infinite_root_coverage(held, x, sp.Interval(0, 2 * sp.pi))
    assert r.complete and r.root_count == 0 and r.verify()
    record = r.proof.context.domain_record
    assert isinstance(record, fp.PeriodicDomainWitness)
    assert not replace(
        record, poles=(), excluded=sp.S.EmptySet, effective=record.requested
    ).verify()
    q = fp.infinite_root_coverage(sp.tan(x), x, sp.FiniteSet(-sp.pi / 2, sp.pi / 2))
    assert q.complete and q.root_count == 0 and q.verify()


def test_held_zero_expression_has_infinite_defined_roots():
    atom = sp.sin(x)
    held = sp.Add(atom, sp.Mul(-1, atom, evaluate=False), evaluate=False)
    r = fp.infinite_root_coverage(held, x)
    assert (
        r.complete
        and r.root_count is sp.oo
        and r.multiplicity_count is None
        and r.verify()
    )


def test_source_formula_transfer_keeps_a_nonperiodic_hole():
    held = sp.Mul(sp.sin(x), x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    r = fp.infinite_root_coverage(held, x)
    assert r.complete and r.root_count is sp.oo and r.verify()
    assert r.proof.context.effective.contains(0) is sp.S.false


def test_family_mutations_and_replay_without_enumeration(monkeypatch):
    r = fp.infinite_root_coverage(sp.sin(x) + sp.Rational(1, 3), x, sp.Interval(0, 10))
    leaf = r.proof.leaves[0]
    w, family = leaf.witness, leaf.witness.families[0]
    for bad in (
        replace(w, levels=w.levels + w.levels[:1]),
        replace(w, families=w.families[:-1]),
        replace(w, families=(replace(family, period=sp.pi), *w.families[1:])),
        replace(w, families=(replace(family, offset=0), *w.families[1:])),
        replace(
            w,
            families=(
                replace(family, ranges=(replace(family.ranges[0], lower=99),)),
                *w.families[1:],
            ),
        ),
    ):
        assert not replace(leaf, witness=bad).verify()

    def disabled(*args, **kwargs):
        raise AssertionError("periodic search called during replay")

    monkeypatch.setattr("funcprops.infinite_roots.periodic_domain", disabled)
    monkeypatch.setattr("funcprops.infinite_roots.propose_periodic", disabled)
    monkeypatch.setattr(sp.Poly, "real_roots", disabled)
    assert r.verify()


@pytest.mark.parametrize(
    "f", [sp.sin(x) + sp.cos(x), sp.sin(x * x), sp.sin(x) + sp.sin(sp.sqrt(2) * x)]
)
def test_unsupported_global_family_never_infers_exhaustiveness(f):
    r = fp.infinite_root_coverage(f, x, policy=fp.EnclosurePolicy(max_cells=4))
    assert not r.complete and r.root_count is None
