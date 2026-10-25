from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)


def test_ball_backend_metadata_is_not_relabelable():
    r = fp.certified_real_ball(sp.exp(x), x, sp.Interval(0, 1))
    assert r.verify()
    assert not replace(r, backend="unverified-point-sampling").verify()


@pytest.mark.parametrize("sign,strict,weak", [(1, ">", ">="), (-1, "<", "<=")])
def test_ball_refinement_at_zero(sign, strict, weak):
    bounds = (0, 1) if sign == 1 else (-1, 0)
    for relation, precision in ((strict, 80), (weak, 20)):
        ball = fp.certified_real_ball(
            sign * x,
            x,
            sp.Interval(0, 1),
            relation=relation,
            precision=20,
            max_precision=80,
        )
        assert ball.precision == precision
        assert (ball.lower, ball.upper) == bounds
        assert ball.verify()


def test_sqrt_derivative_regularity():
    r = fp.enclose_derivative(sp.sqrt(x), x, sp.Interval(0, 1), order=0)
    assert r.verify()
    assert r.enclosure.lower == 0 and r.enclosure.upper >= 1
    assert not fp.enclose_derivative(sp.sqrt(x), x, sp.Interval(0, 1)).verify()


def test_enclosures_honor_zero_cell_budget_and_status():
    for query in (fp.enclose_expression, fp.enclose_derivative):
        r = query(
            sp.exp(x), x, sp.Interval(0, 1), policy=fp.EnclosurePolicy(max_cells=0)
        )
        assert not r.verify() and not r.complete
        status = fp.replay_status(r)
        assert status.complete is False and status.outcome == "resource-exhaustion"


def test_fixed_sign_abs_uses_checked_cell_derivative():
    from funcprops.coverage_search import coverage_context, propose_leaf

    f = sp.Abs(sp.sin(x)) - sp.Rational(1, 2)
    D = sp.Interval(sp.Rational(1, 10), 1)
    leaf = propose_leaf(coverage_context(f, x, D), D, method="monotone-crossing")
    assert leaf.verify() and leaf.root_count == 1


def test_piecewise_branch_multiplicity_mutation_is_rejected():
    f = sp.Piecewise((-x, x < 0), (2 * x, True))
    proof = fp.prove_root_coverage(f, x, sp.Interval(-1, 1))
    leaf = next(a for a in proof.leaves if a.root_count)
    assert leaf.multiplicity_count is None and leaf.verify()
    assert not replace(leaf, multiplicity_count=1).verify()
