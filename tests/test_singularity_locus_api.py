import sympy as sp

import funcprops as fp
from funcprops.results import SingularityKind, SingularityResult


def test_complex_log_returns_single_boolean_singularity_locus():
    x = sp.Symbol("x")
    locus = fp.function_singularities(sp.log(x), x, sp.S.Complexes)
    expected = (sp.re(x) <= 0) & sp.Eq(sp.im(x), 0)
    assert sp.simplify_logic(sp.Xor(locus, expected), force=True) is sp.S.false


def test_conditional_expression_can_restrict_away_singularities():
    x = sp.Symbol("x")
    expr = fp.ConditionalExpression(sp.log(x), x > 0)
    assert fp.function_singularities(expr, x) is sp.S.false


def test_detailed_result_classifies_loci_and_preserves_records():
    x = sp.Symbol("x")
    result = fp.function_singularities(sp.log(x), x, return_result=True)
    assert isinstance(result, SingularityResult)
    assert result.singularities == ((sp.re(x) <= 0) & sp.Eq(sp.im(x), 0))
    assert result.branch_points == (sp.Eq(sp.re(x), 0) & sp.Eq(sp.im(x), 0))
    assert result.branch_cuts == ((sp.re(x) < 0) & sp.Eq(sp.im(x), 0))
    assert result.poles is sp.S.false
    assert result.removable is sp.S.false
    assert result.essential is sp.S.false
    assert result.definition_cuts is sp.S.false
    assert result.discontinuities is sp.S.false
    assert {record.kind for record in result.records} == {
        SingularityKind.BRANCH_POINT,
        SingularityKind.BRANCH_CUT,
    }


def test_detailed_singularities_are_disjunction_of_classified_loci():
    x = sp.Symbol("x", real=True)
    expr = sp.sign(x) / (x - 1)
    result = fp.function_singularities(expr, x, sp.S.Reals, return_result=True)
    union = sp.Or(
        result.poles,
        result.removable,
        result.essential,
        result.branch_points,
        result.branch_cuts,
        result.definition_cuts,
        result.discontinuities,
    )
    assert sp.simplify_logic(sp.Xor(result.singularities, union)) is sp.S.false


def test_restricted_detailed_result_has_no_excluded_records():
    x = sp.Symbol("x")
    expr = fp.ConditionalExpression(sp.log(x), x > 0)
    result = fp.function_singularities(expr, x, return_result=True)
    assert result.singularities is sp.S.false
    assert result.records == ()
    assert result.restriction == (x > 0)


def test_third_positional_argument_is_ambient_domain():
    x = sp.Symbol("x", real=True)
    result = fp.function_singularities(sp.sign(x), x, sp.S.Reals, return_result=True)
    assert result.definition_cuts == sp.Eq(x, 0)
    assert result.discontinuities == sp.Eq(x, 0)
    assert result.singularities == sp.Eq(x, 0)
