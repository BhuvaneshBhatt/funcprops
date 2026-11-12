from dataclasses import replace

import pytest
import sympy as sp
from sympy.logic.boolalg import BooleanFunction

import funcprops as fp

x = sp.Symbol("x", real=True)


def test_condition_domain():
    class IntegerCondition(BooleanFunction):
        nargs = 1

    assert fp.condition_to_real_set(sp.Not(IntegerCondition(x)), x) is None
    assert fp.condition_to_real_set(None, x) is None
    assert fp.condition_to_real_set(sp.And(x > 0, x <= 1), x) == sp.Interval.Lopen(0, 1)
    assert fp.condition_to_real_set(sp.false, x) == sp.S.EmptySet


def test_formula_cells():
    f = sp.Piecewise((x * x, x < 0), (100, sp.Eq(x, 0)), (x + 10, True))
    cells = fp.function_cells(f, x, sp.Interval(-1, 1))
    assert sp.Union(*(region for _, region in cells)) == sp.Interval(-1, 1)
    assert (sp.Integer(100), sp.FiniteSet(0)) in cells
    raw = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    record = fp.track_domain(raw, x, sp.Interval(-1, 1))
    assert record.effective.contains(0) is sp.false
    assert fp.normalize_real_expression(raw) == 1


def test_derivative_and_enclosure():
    assert fp.derivative_on_domain(x * x, x, sp.Interval(-1, 1)) == 2 * x
    assert fp.derivative_on_domain(abs(x), x, sp.Interval(-1, 1)) is None
    witness = fp.value_enclosure(x * x + 1, x, sp.Interval(-1, 1))
    assert witness.lower <= 1 and witness.upper >= 2
    assert fp.verify_value_enclosure(witness, x * x + 1, x, sp.Interval(-1, 1))
    assert not fp.verify_value_enclosure(witness, x * x + 2, x, sp.Interval(-1, 1))
    assert not fp.verify_value_enclosure(
        replace(witness, lower=10), x * x + 1, x, sp.Interval(-1, 1)
    )


def test_cover_refinement():
    p = fp.EnclosurePolicy(max_cells=64, max_depth=5)
    cover = fp.adaptive_root_coverage(
        sp.exp(x) + 2 * x, x, sp.Interval.open(-1, 1), policy=p
    ).proof
    refined = fp.refine_root_cover(cover, policy=p)
    assert refined.context == cover.context
    assert refined.context.effective == cover.context.effective
    assert fp.check_coverage(refined).certified is True
    assert refined.root_count == cover.root_count == 1
    with pytest.raises(ValueError):
        fp.refine_root_cover(None)


def test_transport_and_identity():
    import pickle

    raw = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
    restored = pickle.loads(fp.pack_analysis_data(raw))
    assert fp.analysis_data_equal(raw, restored)
    assert fp.track_domain(restored, x).effective == sp.S.Reals - sp.FiniteSet(0)
    assert fp.verify_real_identity(sp.sin(x) ** 2 + sp.cos(x) ** 2, 1)
    assert not fp.verify_real_identity(x, x + 1)


def test_analysis_owns_no_optimization():
    assert not hasattr(fp, "finite_component_minimum")
    assert not hasattr(fp, "certify_global_minimum")
    assert not hasattr(fp, "certify_extrema_bounds")
