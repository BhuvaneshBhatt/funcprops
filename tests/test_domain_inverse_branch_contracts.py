import pytest
import sympy as sp

from funcprops.exactness import certify_identity_equal, certify_identity_equal_on_domain
from funcprops.real_analysis.common import combine_domain, condition_to_set
from funcprops.real_analysis.piecewise import combine_piecewise_conditions


def test_set_domain_combination_binds_analysis_variable():
    x = sp.symbols("x", real=True)
    dom = sp.Complement(sp.S.Reals, sp.FiniteSet(0))
    c = combine_domain(dom, x > -2, x)
    assert c.has(x)
    assert sp.simplify(c.subs(x, 0)) is sp.S.false
    assert sp.simplify(c.subs(x, 1)) is sp.S.true


def test_set_domain_combination_rejects_missing_variable():
    with pytest.raises(ValueError):
        combine_domain(sp.Interval(0, 1), sp.S.true)


def test_complement_condition_keeps_relative_universe():
    x = sp.symbols("x", real=True)
    dom = sp.Complement(sp.Interval(-1, 1), sp.FiniteSet(0))
    assert condition_to_set(sp.Contains(x, dom), x) == dom


def test_branch_sensitive_identities_are_not_global_identities():
    z = sp.symbols("z")
    assert certify_identity_equal(sp.sqrt(z**2), z) is not True
    assert certify_identity_equal(sp.log(z**2), 2 * sp.log(z)) is not True


def test_domain_aware_identity_rejects_cancelled_hole():
    x = sp.symbols("x", real=True)
    raw = sp.Mul(x**2 - 1, sp.Pow(x - 1, -1, evaluate=False), evaluate=False)
    assert certify_identity_equal(raw, x + 1) is True
    assert certify_identity_equal_on_domain(raw, x + 1, x) is not True


def test_piecewise_overlapping_images_union_semantics():
    y = sp.symbols("y", real=True)
    merged = combine_piecewise_conditions((y <= 1, y >= 0))
    # Overlap must not be interpreted as a disjoint partition; the union is all reals.
    assert sp.simplify_logic(merged) is sp.S.true


def test_equality_zero_preimage_is_composed_through_subject_map():
    from funcprops.registry import FunctionSlot
    from funcprops.registry_transport import SubjectMap, _preimage_of_zero_result

    x = sp.symbols("x", real=True)
    u = FunctionSlot(0, "u")
    sm = SubjectMap((u,), (x**2,), (x,), sp.ImmutableMatrix([[2 * x]]))
    pulled = _preimage_of_zero_result(sp.Eq(u, 1), sm, x, sp.S.Reals)
    assert pulled == sp.FiniteSet(-1, 1)
