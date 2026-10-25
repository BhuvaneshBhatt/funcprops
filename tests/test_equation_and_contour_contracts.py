"""Certified operation extensions: branches, strata, native replay and tails."""

from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops.asymptotic_tails import certify_tail_sign
from funcprops.certified_balls import certified_real_ball
from funcprops.meromorphic_contours import meromorphic_rectangle_count

z = s.Symbol("z")
x = s.Symbol("x", real=True)
a, b = s.symbols("a b", real=True)


@pytest.mark.parametrize("sheet", [-3, -1, 0, 1, 3])
def test_explicit_logarithmic_germ_residue_and_scope(sheet):
    value = (2 * sheet + 1) * s.I * s.pi
    ctx = fp.LocalBranchContext(-1, ((z, value),))
    e = s.log(z) / (z + 1)
    c = fp.residue(e, z, -1, branch_context=ctx, return_certificate=True)
    assert c.verify() and c.residue == value and c.branch_context == ctx
    assert fp.verify_certificate(c, expr=e, var=z)
    assert not replace(c, branch_context=None).verify()
    assert not replace(
        c, branch_context=fp.LocalBranchContext(-1, ((z, value + 2 * s.pi * s.I),))
    ).verify()
    kind = fp.classify_singularity(
        e, z, -1, branch_context=ctx, return_certificate=True
    )
    assert kind.kind == "pole" and kind.verify()
    assert fp.residue(e, z, -1, return_certificate=True) is None


@pytest.mark.parametrize(
    "value,expected", [(s.I * s.pi, s.I), (-s.I * s.pi, -s.I), (3 * s.I * s.pi, -s.I)]
)
def test_selected_power_germ_uses_logarithm_value(value, expected):
    ctx = fp.LocalBranchContext(-1, ((z, value),))
    c = fp.laurent_series(
        s.sqrt(z), z, -1, order=3, branch_context=ctx, return_certificate=True
    )
    assert c.verify()
    assert s.simplify(c.series.removeO().subs(z, -1) - expected) == 0
    assert not replace(c, branch_context=None).verify()


@pytest.mark.parametrize(
    "context",
    [
        fp.LocalBranchContext(1, ((z, s.I * s.pi),)),
        fp.LocalBranchContext(-1, ((z, s.S.Zero),)),
        fp.LocalBranchContext(-1, ((z, s.I * s.pi), (z, -s.I * s.pi))),
        fp.LocalBranchContext(-1, ((z + 1, s.I * s.pi),)),
        fp.LocalBranchContext(-1, ((z, z),)),
    ],
)
def test_invalid_branch_context_cannot_be_a_proof(context):
    assert (
        fp.residue(
            s.log(z) / (z + 1), z, -1, branch_context=context, return_certificate=True
        )
        is None
    )


def test_branch_context_cannot_fill_branch_points_or_raw_source_holes():
    ctx = fp.LocalBranchContext(0, ((z, s.S.Zero),))
    assert (
        fp.laurent_series(s.log(z), z, 0, branch_context=ctx, return_certificate=True)
        is None
    )
    hole = s.Mul(s.im(z), s.Pow(s.im(z), -1, evaluate=False), evaluate=False)
    ctx = fp.LocalBranchContext(-1, ((z, s.I * s.pi),))
    assert (
        fp.residue(
            s.Mul(hole, s.log(z), evaluate=False),
            z,
            -1,
            branch_context=ctx,
            return_certificate=True,
        )
        is None
    )


def test_guarded_affine_cases_are_exhaustive_and_source_bound():
    c = fp.solve(a * x + b, x, domain=s.S.Reals, guarded=True, return_certificate=True)
    assert c.verify() and c.complete and len(c.cases) == 3 and c.root_count is None
    assert [case.value.root_count for case in c.cases] == [1, s.oo, 0]
    assert not replace(c, cases=c.cases[:-1]).verify()
    assert not replace(c, expression=a * x + b + 1).verify()
    assert not fp.verify_certificate(c, expr=a * x + b + 1, var=x)
    assert not fp.solve(
        a * x + b, x, domain=s.S.Reals, return_certificate=True
    ).complete


@pytest.mark.parametrize(
    "context,count,solutions",
    [
        (s.Ne(a, 0), 1, s.FiniteSet(-b / a)),
        (s.And(s.Eq(a, 0), s.Eq(b, 0)), s.oo, s.S.Reals),
        (s.And(s.Eq(a, 0), s.Ne(b, 0)), 0, s.S.EmptySet),
    ],
)
def test_affine_strata_specialize_under_assumptions(context, count, solutions):
    c = fp.solve(a * x + b, x, domain=s.S.Reals, guarded=True, return_certificate=True)
    d = c.specialize(context)
    assert (
        d.verify() and d.complete and d.root_count == count and d.solutions == solutions
    )
    assert len(d.cases) == 1 and d.cases[0].condition is s.S.true
    assert not replace(d, assumptions=s.S.true).verify()


@pytest.mark.parametrize(
    "expression,count,solutions",
    [
        (s.S.Zero, s.oo, s.S.Complexes),
        (s.S.One, 0, s.S.EmptySet),
        (2 * z - 1, 1, s.FiniteSet(s.Rational(1, 2))),
    ],
)
def test_guarded_constant_and_unconditional_affine_cases(expression, count, solutions):
    c = fp.solve(expression, z, guarded=True, return_certificate=True)
    assert c.verify() and c.root_count == count and c.solutions == solutions


def test_affine_source_premises():
    for e in (a * x * x + b, s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False)):
        c = fp.solve(e, x, guarded=True, domain=s.S.Reals, return_certificate=True)
        assert not c.complete and not c.certified
    c = fp.solve(a * x + b, x, guarded=True, assumptions=False, return_certificate=True)
    assert not c.complete
    with pytest.raises(ValueError):
        fp.solve(a * x, x, guarded=True, assumptions=x > 0, return_certificate=True)
    with pytest.raises(ValueError):
        fp.solve(a * x, x, assumptions=s.Ne(a, 0))


def test_real_coefficient_guards_and_real_coordinate_premises():
    q = s.Symbol("q", complex=True)
    c = fp.solve(q * x + 1, x, guarded=True, domain=s.S.Reals, return_certificate=True)
    assert not c.complete
    c = fp.solve(
        q * x + 1,
        x,
        guarded=True,
        domain=s.S.Reals,
        assumptions=s.Q.real(q),
        return_certificate=True,
    )
    assert c.verify() and c.complete
    positive = s.Symbol("positive", positive=True)
    assert not fp.solve(
        a * positive + b,
        positive,
        domain=s.S.Reals,
        guarded=True,
        return_certificate=True,
    ).complete


@pytest.mark.parametrize("family", [s.erf, s.erfc, s.erfi])
def test_common_entire_families_local_and_continuation(family):
    e = family(z)
    c = fp.laurent_series(e, z, 0, return_certificate=True)
    assert c.verify()
    c = fp.residue(e / z, z, 0, return_certificate=True)
    assert c.verify() and c.residue == family(0)
    t = s.Symbol("t", real=True)
    circle = fp.ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    c = fp.analytic_continue(e, z, circle, return_certificate=True)
    assert c.verify() and c.continued == e
    assert fp.laurent_series(family(1 / z), z, 0, return_certificate=True) is None


@pytest.mark.parametrize(
    "function,direction,sign",
    [
        (s.exp(x) - x * x, 1, 1),
        (-s.exp(x) + x * x, 1, -1),
        (s.exp(-x) - x * x, -1, 1),
        (s.exp(2 * x) - x * s.exp(x) - 10 * x * x, 1, 1),
        (s.exp(-x) - 2 * s.exp(-2 * x), 1, 1),
    ],
)
def test_exponential_polynomial_sum_tails(function, direction, sign):
    c = certify_tail_sign(function, x, direction=direction)
    assert c.sign == sign and c.verify()
    assert c.source == "exponential-polynomial-sum"
    assert not replace(c, sign=-sign).verify()
    assert not replace(c, dominance=replace(c.dominance, remainder_upper=-1)).verify()
    assert fp.verify_certificate(c, expr=function, var=x)
    assert fp.replay_status(c).certified is True


def test_tail_source_premises():
    e = s.exp(x) - x * x
    assert certify_tail_sign(e, x, threshold=0) is None
    hole = s.Mul(x - 5, s.Pow(x - 5, -1, evaluate=False), evaluate=False)
    raw = s.Mul(hole, e, evaluate=False)
    assert certify_tail_sign(raw, x, threshold=4) is None
    c = certify_tail_sign(raw, x, threshold=8)
    assert c.verify()
    assert certify_tail_sign(s.exp(x + s.I) - x * x, x) is None


def native_records():
    return [
        (certify_tail_sign(x * x + 1, x, threshold=1), x * x + 1, x),
        (
            meromorphic_rectangle_count(
                (z - 1) / (z + 2), z, -3 - 3 * s.I, 3 + 3 * s.I
            ),
            (z - 1) / (z + 2),
            z,
        ),
        (certified_real_ball(s.exp(x), x, s.Interval(0, 1)), s.exp(x), x),
        (
            fp.rouche_polynomial_circle(z**3 + s.Rational(1, 10), z),
            z**3 + s.Rational(1, 10),
            z,
        ),
        (
            fp.rouche_polynomial_rectangle(
                z**3 + s.Rational(1, 100), z, -1 - s.I, 1 + s.I
            ),
            z**3 + s.Rational(1, 100),
            z,
        ),
        (
            fp.argument_principle_rectangle(z * z + 1, z, -2 - 2 * s.I, 2 + 2 * s.I),
            z * z + 1,
            z,
        ),
    ]


@pytest.mark.parametrize("index", range(6))
def test_remaining_native_records_use_source_bound_unified_replay(index):
    c, e, v = native_records()[index]
    assert fp.verify_certificate(c, expr=e, var=v) is True
    assert fp.replay_status(c).certified is True
    assert not fp.verify_certificate(c, expr=e + 1, var=v)
    assert not fp.verify_certificate(c, expr=e, var=s.Symbol("wrong"))
    assert fp.replay_status(c, work_budget=1e-6).certified is None


def test_polynomial_source_binding():
    hole = s.Mul(z, s.Pow(z, -1, evaluate=False), evaluate=False)
    assert fp.rouche_polynomial_circle(hole, z) is None
    assert fp.rouche_polynomial_rectangle(hole, z, -1 - s.I, 1 + s.I) is None
    assert fp.argument_principle_rectangle(hole, z, -1 - s.I, 1 + s.I) is None
    assert fp.argument_principle_rectangle(z, z, 0, 0) is None
    assert fp.argument_principle_rectangle(a * z, z, -1 - s.I, 1 + s.I) is None
    c = fp.rouche_polynomial_rectangle(z**3 + s.Rational(1, 100), z, -1 - s.I, 1 + s.I)
    assert not replace(c, center=s.S.One).verify()


def test_records_and_contexts_survive_isolated_execution():
    ctx = fp.LocalBranchContext(-1, ((z, s.I * s.pi),))
    c = fp.residue(
        s.log(z) / (z + 1),
        z,
        -1,
        branch_context=ctx,
        return_certificate=True,
        work_budget=10,
    )
    assert c.verify() and c.residue == s.I * s.pi
    c = fp.solve(
        a * x + b,
        x,
        guarded=True,
        domain=s.S.Reals,
        assumptions=s.Ne(a, 0),
        return_certificate=True,
        work_budget=10,
    )
    assert c.verify() and c.root_count == 1


@pytest.mark.parametrize(
    "offset,count,admissible",
    [(s.S.Zero, 1, True), (s.Integer(2), 0, True), (s.S.One, None, False)],
)
def test_guarded_affine_circle_counts_keep_boundary_strata(offset, count, admissible):
    t = s.Symbol("t", real=True)
    circle = fp.ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    c = fp.argument_principle(
        z + offset, z, circle, guarded=True, return_certificate=True
    )
    assert c.verify() and c.complete and c.admissible is admissible
    assert c.zeros_minus_poles == count
    assert fp.verify_certificate(c, expr=z + offset, var=z)
    assert not fp.verify_certificate(c, expr=z + offset + 3, var=z)
    wrong = replace(c.cases[0], value=fp.AffineContourCount(7, True))
    assert not replace(c, cases=(wrong, *c.cases[1:])).verify()


def test_guarded_circle_parameter_strata_and_orientation():
    t = s.Symbol("t", real=True)
    circle = fp.ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    c = fp.argument_principle(a * z, z, circle, guarded=True, return_certificate=True)
    assert c.verify() and c.cases
    positive = c.specialize(a > 0)
    assert (
        positive.verify()
        and positive.admissible is True
        and positive.zeros_minus_poles == 1
    )
    zero = c.specialize(s.Eq(a, 0))
    assert zero.verify() and zero.admissible is False and zero.zeros_minus_poles is None
    reversed_count = fp.argument_principle(
        a * z,
        z,
        circle.reversed(),
        guarded=True,
        assumptions=a > 0,
        return_certificate=True,
    )
    assert reversed_count.verify() and reversed_count.zeros_minus_poles == -1


def test_unsupported_contour_paths():
    t = s.Symbol("t", real=True)
    path = fp.ParametricContour(s.exp(s.I * s.sin(t)), (t, 0, 2 * s.pi))
    c = fp.argument_principle(a * z, z, path, guarded=True, return_certificate=True)
    assert not c.certified and not c.complete
    path = fp.ParametricContour(t, (t, 0, 1))
    assert not fp.argument_principle(
        z, z, path, guarded=True, return_certificate=True
    ).certified
