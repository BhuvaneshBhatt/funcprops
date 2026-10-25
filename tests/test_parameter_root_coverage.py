from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x, a = sp.symbols("x a", real=True)


def test_quadratic_three_strata_include_double_root():
    r = fp.parameter_root_coverage(x * x - a, x, a)
    assert r.complete and r.certified and r.verify()
    assert [(c.region, c.root_count, c.multiplicity_count) for c in r.cells] == [
        (sp.Interval.open(-sp.oo, 0), 0, 0),
        (sp.FiniteSet(0), 1, 2),
        (sp.Interval.open(0, sp.oo), 2, 2),
    ]
    assert fp.replay_status(r).outcome == "complete-coverage"


@pytest.mark.parametrize(
    "value,count,mult", [(0, 1, 1), (sp.Rational(1, 4), 1, 2), (-1, 2, 2), (1, 0, 0)]
)
def test_leading_coefficient_zero_and_discriminant_cases(value, count, mult):
    r = fp.parameter_root_coverage(a * x * x + x + 1, x, a)
    q = fp.specialize_parameter_coverage(r, value)
    assert r.complete and r.verify()
    assert (
        q.complete
        and q.root_count == count
        and q.multiplicity_count == mult
        and q.verify()
    )
    assert fp.verify_certificate(q, expr=q.expression, var=x)
    assert not fp.verify_certificate(q, expr=sp.exp(x), var=x)


@pytest.mark.parametrize(
    "value,count,mult",
    [
        (-2, 0, 0),
        (-1, 0, 0),
        (-sp.Rational(1, 2), 2, 2),
        (0, 1, 2),
        (sp.Rational(1, 2), 0, 0),
        (1, 0, 0),
        (2, 2, 2),
    ],
)
def test_polynomial_parameter_events(value, count, mult):
    r = fp.parameter_root_coverage((a * a - 1) * x * x - a, x, a)
    assert r.complete and r.verify()
    q = fp.specialize_parameter_coverage(r, value)
    assert q.verify() and (q.root_count, q.multiplicity_count) == (count, mult)


def test_affine_zero_and_constant_degeneracy():
    r = fp.parameter_root_coverage(a * x, x, a)
    q = fp.specialize_parameter_coverage(r, 0)
    assert (
        r.complete
        and q.verify()
        and q.root_count is sp.oo
        and q.multiplicity_count is None
    )
    r = fp.parameter_root_coverage(a, x, a)
    assert r.complete and r.verify()
    assert fp.specialize_parameter_coverage(r, 1).root_count == 0
    assert fp.specialize_parameter_coverage(r, 0).root_count is sp.oo


@pytest.mark.parametrize(
    "left,right", [(False, False), (True, False), (False, True), (True, True)]
)
def test_exponential_parameter_endpoints_have_exact_ownership(left, right):
    D = sp.Interval(0, 1, left, right)
    r = fp.parameter_root_coverage(sp.exp(x) - a, x, a, D)
    assert r.complete and r.verify() and len(r.cells) == 5
    for value, count in (
        (0, 0),
        (1, int(not left)),
        (2, 1),
        (sp.E, int(not right)),
        (3, 0),
    ):
        q = fp.specialize_parameter_coverage(r, value)
        assert q.verify() and q.root_count == count


def test_decreasing_translation_and_restricted_parameter_components():
    P = sp.Union(sp.Interval(0, sp.Rational(1, 2)), sp.FiniteSet(1))
    r = fp.parameter_root_coverage(
        sp.exp(-x) - a, x, a, sp.Interval.open(0, 1), parameter_domain=P
    )
    assert r.complete and r.verify()
    assert fp.specialize_parameter_coverage(r, 1).root_count == 0
    assert fp.specialize_parameter_coverage(r, sp.Rational(1, 2)).root_count == 1
    assert not fp.specialize_parameter_coverage(r, 2).complete


def test_parameter_partition_tampering():
    r = fp.parameter_root_coverage(a * x * x + x + 1, x, a)
    assert not replace(
        r, cells=tuple(c for c in r.cells if c.region != sp.FiniteSet(0))
    ).verify()
    assert not replace(r, cells=r.cells + r.cells[:1]).verify()
    c = r.cells[0]
    assert not replace(r, cells=(replace(c, root_count=99), *r.cells[1:])).verify()
    signs = c.witness.signs
    bad = replace(
        c,
        witness=replace(
            c.witness, signs=(replace(signs[0], sign=-signs[0].sign), *signs[1:])
        ),
    )
    assert not replace(r, cells=(bad, *r.cells[1:])).verify()
    assert not replace(r, source_syntax="changed").verify()


def test_budget_does_not_omit_unprocessed_parameter_strata():
    for n in (0, 1, 2):
        r = fp.parameter_root_coverage(
            x * x - a, x, a, policy=fp.EnclosurePolicy(max_cells=n)
        )
        assert not r.complete and r.unresolved is not sp.S.EmptySet and r.verify()
        assert sp.Union(r.unresolved, *(c.region for c in r.cells)) == sp.S.Reals
        assert fp.replay_status(r).outcome == "resource-exhaustion"


def test_parameter_proof_replay_does_not_call_search(monkeypatch):
    r = fp.parameter_root_coverage(x * x - a, x, a)
    t = fp.parameter_root_coverage(sp.exp(x) - a, x, a, sp.Interval(0, 1))

    def disabled(*args, **kwargs):
        raise AssertionError("parameter search called during replay")

    monkeypatch.setattr(
        "funcprops.parameter_coverage.parameter_root_coverage", disabled
    )
    monkeypatch.setattr("funcprops.parameter_coverage._polynomial_cells", disabled)
    monkeypatch.setattr("funcprops.parameter_coverage._monotone_cells", disabled)
    monkeypatch.setattr(sp.Poly, "real_roots", disabled)
    assert r.verify() and t.verify()


def test_source_holes_and_float_specialization_never_disappear():
    held = sp.Mul(a, sp.Pow(a, -1, evaluate=False), evaluate=False)
    f = sp.Add(sp.exp(x), -a, sp.Mul(0, held, evaluate=False), evaluate=False)
    r = fp.parameter_root_coverage(
        f, x, a, sp.Interval(0, 1), policy=fp.EnclosurePolicy(max_cells=1)
    )
    assert not r.complete
    p = fp.parameter_root_coverage(x * x - a, x, a)
    assert not fp.specialize_parameter_coverage(p, sp.Float("0.1")).verify()
    with pytest.raises(ValueError):
        fp.parameter_root_coverage(x * x, x, x)


def test_hard_timeout_preserves_all_parameter_obligations():
    r = fp.parameter_root_coverage(
        x * x - a, x, a, policy=fp.EnclosurePolicy(seconds=0.001)
    )
    assert (
        not r.complete and r.unresolved == sp.S.Reals and r.exhaustion == "wall-budget"
    )
    assert r.verify() and fp.replay_status(r).outcome == "resource-exhaustion"


@pytest.mark.parametrize(
    "g,threshold,side",
    [
        (sp.exp(x) - a, 0, 1),
        (2 * sp.exp(-3 * x + 1) + 4 - a, 4, 1),
        (-2 * sp.exp(2 * x) - 3 - a, -3, -1),
    ],
)
def test_full_real_exponential_parameter_strata(g, threshold, side):
    r = fp.parameter_root_coverage(g, x, a)
    assert r.complete and r.verify() and len(r.cells) == 3
    for value, count in ((threshold - side, 0), (threshold, 0), (threshold + side, 1)):
        q = fp.specialize_parameter_coverage(r, value)
        assert q.verify() and q.root_count == count and q.multiplicity_count == count


def test_nonrational_translation():
    p = fp.parameter_root_coverage(x - sp.E - a, x, a, sp.Interval(0, 1))
    assert p.complete and p.verify()
    for value, count in ((-sp.E, 1), (1 - sp.E, 1), (-2, 1), (0, 0)):
        q = fp.specialize_parameter_coverage(p, value)
        assert q.verify() and q.root_count == count
