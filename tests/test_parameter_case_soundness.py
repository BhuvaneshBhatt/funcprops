"""Parameter case transformations preserve premises and specialize conclusions."""

import sympy as sp

import funcprops as fp


def test_cyclic_equalities_keep_a_spanning_guard():
    a, b, c = sp.symbols("a b c")
    guard = sp.And(sp.Eq(a, b), sp.Eq(b, c), sp.Eq(a, c))
    result = fp.PropertyResult(
        None, (fp.ConditionalExpression(fp.TruthValue.TRUE, guard),)
    )
    simplified = fp.minimize_strata(result)
    assert simplified.primary is None
    assert len(simplified.cases) == 1
    condition = simplified.cases[0].condition
    assert len(sp.And.make_args(condition)) == 2
    for values, expected in [
        ({a: 1, b: 1, c: 1}, sp.S.true),
        ({a: 1, b: 2, c: 1}, sp.S.false),
        ({a: 1, b: 1, c: 2}, sp.S.false),
    ]:
        assert condition.subs(values) is expected


def test_dependent_equations_remain_equivalent():
    a, b, c = sp.symbols("a b c")
    original = sp.And(sp.Eq(a, b), sp.Eq(b, c), sp.Eq(a, c), sp.Ne(a, 0))
    result = fp.minimize_strata(
        fp.PropertyResult(None, (fp.ConditionalExpression(7, original),))
    )
    condition = result.cases[0].condition
    for av in (-1, 0, 1):
        for bv in (-1, 0, 1):
            for cv in (-1, 0, 1):
                replacements = {a: av, b: bv, c: cv}
                assert condition.subs(replacements) == original.subs(replacements)


def test_specialization_rewrites_result_values():
    a = sp.Symbol("a", real=True)
    original = fp.PropertyResult(
        None,
        (fp.ConditionalExpression(a**2, a >= 0), fp.ConditionalExpression(-a, a < 0)),
    )
    assert fp.specialize_cells(original, {a: 2}).resolved == 4
    assert fp.specialize_cells(original, {a: -3}).resolved == 3


def test_specialization_is_simultaneous():
    a, b = sp.symbols("a b")
    original = fp.PropertyResult(
        sp.Tuple(a, b), all_properties=(sp.FiniteSet(a),), exceptions=(sp.Eq(a, b),)
    )
    result = fp.specialize_cells(original, {a: b, b: a})
    assert result.primary == sp.Tuple(b, a)
    assert result.all_properties == (sp.FiniteSet(b),)
    assert result.exceptions == (sp.Eq(b, a),)


def test_specialization_does_not_relabel_parent_proof():
    a = sp.Symbol("a", real=True)
    original = fp.PropertyResult(
        None,
        (fp.ConditionalExpression(a + 1, a > 0),),
        complete=True,
        certified=True,
        evidence=(sp.Eq(a, 1),),
        domain_record=object(),
    )
    result = fp.specialize_cells(original, {a: 2})
    assert result.resolved == 3
    assert (
        result.complete,
        result.certified,
        result.domain_record,
        result.evidence,
    ) == (None, None, None, ())
