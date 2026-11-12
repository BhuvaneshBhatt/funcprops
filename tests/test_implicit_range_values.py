import pickle
import sys
from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x, y = sp.symbols("x y", real=True)
f = x * x + sp.sin(x)
D = sp.Interval(-1, 1)


def test_root_and_value():
    root = fp.implicit_real_root(
        2 * x + sp.cos(x), x, sp.Interval.open(-sp.Rational(1, 2), 0)
    )
    assert not root.free_symbols and root.is_real is True and root.verify()
    assert abs(float(root) + 0.45018361129487355) < 1e-14
    value = fp.critical_value(f, x, root)
    bounds = value.enclosure(16)
    assert bounds.verify() and bounds.upper - bounds.lower < sp.Rational(1, 10**15)
    assert (
        bounds.lower
        < sp.Rational(-232465575158, 10**12)
        < bounds.upper + sp.Rational(1, 10**10)
    )
    assert pickle.loads(pickle.dumps(root)) == root
    with pytest.raises(ValueError):
        fp.implicit_real_root(x * x + 1, x, D)


def test_implicit_image():
    result = fp.analyze_range(f, x, D, certified=True)
    assert result.complete and result.certified and result.verify()
    assert isinstance(result.image.start, fp.CriticalValue)
    assert result.image.end == 1 + sp.sin(1)
    assert result.image.left_open is sp.false and result.image.right_open is sp.false
    assert not fp.analyze_range(f, x, D).certified
    assert (
        fp.condition_to_real_set(fp.range(f, x, y, domain=D), y).end == result.image.end
    )
    for bad in [
        replace(result, image=sp.Interval(-1, 2)),
        replace(result, inner=sp.Interval(-1, 2)),
        replace(result, outer=sp.S.EmptySet),
        replace(result, variable=y),
    ]:
        assert not bad.verify()


def test_partial_refinement():
    coarse = fp.analyze_range(f, x, D, policy=fp.EnclosurePolicy(max_cells=0))
    assert coarse.verify() and not coarse.complete
    assert (
        coarse.inner is sp.S.EmptySet
        and coarse.outer is sp.S.Reals
        and coarse.unresolved == D
    )
    refined = fp.refine_range(
        coarse, policy=fp.EnclosurePolicy(max_cells=200, max_depth=8), certified=True
    )
    assert refined.complete and refined.verify() and refined.certified
    assert refined.critical_coverage_complete and refined.value_coverage_complete


def test_replay_does_not_search():
    result = fp.analyze_range(f, x, D)
    watched = {
        fp.adaptive_root_coverage.__code__,
        fp.analyze_range.__code__,
        sp.solveset.__code__,
    }
    called = []

    def observe(frame, event, arg):
        if event == "call" and frame.f_code in watched:
            called.append(frame.f_code.co_name)

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        assert result.verify()
    finally:
        sys.setprofile(previous)
    assert called == []


def test_root_endpoint_signs():
    # A closed zero endpoint does not determine whether the unique root is zero.
    root = fp.implicit_real_root(x - sp.Rational(1, 2), x, sp.Interval(0, 1))
    assert root.is_positive is not False
    assert root.evalf(15) == sp.Rational(1, 2).evalf(15)
    assert sp.diff(root, x) == 0
    negative = fp.implicit_real_root(x + sp.Rational(1, 2), x, sp.Interval(-1, 0))
    assert negative.is_negative is not False
    assert negative.evalf(15) == -sp.Rational(1, 2).evalf(15)


def test_bound_certificate_binding():
    r = fp.analyze_range(f, x, D)
    bound = r.image.start.enclosure(12)
    assert fp.verify_certificate(bound, expr=f, var=x)
    assert not fp.verify_certificate(bound, expr=f + 1, var=x)
    assert not replace(
        bound, enclosure=replace(bound.enclosure, lower=bound.upper + 1)
    ).verify()
    cell = r.cells[0]
    assert fp.verify_certificate(cell, expr=f, var=x)
    for bad in (
        replace(cell, sites=cell.sites[:-1]),
        replace(cell, expression=f + 1),
        replace(cell, domain=sp.Interval.open(-1, 1)),
        replace(cell, critical_cover=None),
    ):
        assert not bad.verify()


def test_isolated_budget():
    r = fp.analyze_range(f, x, D, policy=fp.EnclosurePolicy(seconds=0.001))
    assert isinstance(r, fp.BudgetedResult) and not r.complete and not r.certified
    assert r.operation == "analyze_range" and r.primary is None


def test_range_example():
    import runpy
    from pathlib import Path

    runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "examples/range_analysis.py"),
        run_name="__main__",
    )
