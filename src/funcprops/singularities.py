"""Structural singularity, branch, analyticity and continuity analysis."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache

import sympy as sp
from sympy import S
from sympy.calculus.util import continuous_domain
from sympy.core.relational import Relational
from sympy.logic.boolalg import And, Boolean, Or

from .engine import evaluate_property, simplify_condition
from .exactness import certify_identity_equal
from .exceptions import SYMBOLIC_QUERY_ERRORS
from .results import (
    Analyticity,
    ConditionalExpression,
    Continuity,
    Meromorphicity,
    PropertyResult,
    Singularity,
    SingularityKind,
    SingularityResult,
)
from .stratification import evaluate_parameter_strata


def _is_empty(value) -> bool:
    return value in ({}, (), [], S.EmptySet, sp.Tuple())


def _replace_helper_heads(expr):
    """Normalize a few helper heads used only by the catalogue property dump."""
    if not isinstance(expr, sp.Basic):
        return expr
    name = getattr(expr.func, "__name__", "")
    if name == "RemoveQuadratics" and len(expr.args) == 1:
        a = expr.args[0]
        if getattr(a, "func", None) is sp.Abs:
            return _replace_helper_heads(a.args[0])
        if isinstance(a, sp.Pow):
            return _replace_helper_heads(a.args[0])
        return _replace_helper_heads(a)
    if name == "If" and len(expr.args) == 3:
        cond = _replace_helper_heads(expr.args[0])
        if cond in (S.true, True):
            return _replace_helper_heads(expr.args[1])
        if cond in (S.false, False):
            return _replace_helper_heads(expr.args[2])
    args = tuple(_replace_helper_heads(a) for a in expr.args)
    try:
        return expr.func(*args)
    except SYMBOLIC_QUERY_ERRORS:
        return expr


def _combine_guard(a, b, assumptions=S.true):
    return simplify_condition(And(a, b), assumptions=assumptions)


def _split_locus_guard(condition, var, *, assumptions=S.true):
    """Split a condition into analysis-locus and parameter-only parts.

    ``var`` may be one symbol or a collection of independent analysis variables.
    A Boolean atom belongs to the locus whenever it depends on at least one of
    those variables; only genuinely parameter-only atoms are moved to the guard.
    """
    c = sp.sympify(condition)
    variables = _variable_tuple(var) if var is not None else ()

    def depends_on_analysis_variable(node):
        return any(node.has(variable) for variable in variables)

    if c in (S.true, S.false):
        return c, S.true
    if c.func is And:
        locus = []
        guard = []
        for atom in c.args:
            (locus if depends_on_analysis_variable(atom) else guard).append(atom)
        lc = And(*locus) if locus else S.true
        gd = And(*guard) if guard else S.true
        return simplify_condition(lc, assumptions=assumptions), simplify_condition(
            gd, assumptions=assumptions
        )
    if depends_on_analysis_variable(c):
        return c, S.true
    return S.true, simplify_condition(c, assumptions=assumptions)


def _registry_loci(
    expr,
    prop: str,
    kind: SingularityKind,
    *,
    mode="complex",
    var=None,
    assumptions=S.true,
):
    result = evaluate_property(expr, prop, var=var, mode=mode, assumptions=assumptions)
    out = []
    for case in result.cases:
        value = _replace_helper_heads(case.value)
        if _is_empty(value):
            continue
        entries = (
            tuple(value) if isinstance(value, (sp.Tuple, tuple, list)) else (value,)
        )
        for entry in entries:
            entry = _replace_helper_heads(entry)
            if isinstance(entry, (sp.Tuple, tuple, list)) and len(entry) >= 2:
                locus, local_condition = entry[0], entry[1]
                local_locus, local_guard = _split_locus_guard(
                    local_condition, var, assumptions=assumptions
                )
                locus = _combine_guard(locus, local_locus, assumptions=assumptions)
                guard = _combine_guard(
                    case.condition, local_guard, assumptions=assumptions
                )
            else:
                locus, guard = entry, case.condition
            if guard is S.false or locus is S.false:
                continue
            out.append(
                Singularity(
                    kind, sp.sympify(locus), sp.sympify(guard), source="registry"
                )
            )
    return tuple(out)


def _unique(items: Iterable[Singularity]):
    out = []
    seen = set()
    for item in items:
        key = (
            item.kind,
            sp.srepr(item.condition),
            sp.srepr(item.guard),
            str(item.multiplicity),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return tuple(out)


def function_order_at(expr, var, point):
    """Return the local integer/Puiseux order when SymPy can certify it.

    Positive means a zero, negative a pole, and zero a finite nonzero value.
    ``None`` means the order could not be established symbolically.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    point = sp.sympify(point)
    t = sp.Dummy("funcprops_local")
    try:
        shifted = expr.subs(var, point + t)
        lead = shifted.as_leading_term(t)
        pd = lead.as_powers_dict()
        order = sp.simplify(pd.get(t, S.Zero))
        if order.is_number:
            # ``as_leading_term`` can return an unresolved special function
            # such as zeta(1+t); treating the absence of an explicit t power
            # as order zero is not a certificate.
            if order == 0 and lead.has(t):
                pass
            else:
                return order
    except SYMBOLIC_QUERY_ERRORS:
        pass
    # A short series fallback catches cancellation such as sin(x)/x**3.
    try:
        ser = sp.series(expr, var, point, 8).removeO().expand()
        shifted = ser.subs(var, point + t).expand()
        terms = sp.Add.make_args(shifted)
        orders = []
        for term in terms:
            power = term.as_powers_dict().get(t, S.Zero)
            if power.is_number:
                orders.append(power)
        if orders:
            return min(orders, key=lambda q: float(q))
    except SYMBOLIC_QUERY_ERRORS:
        pass
    return None


def _explicit_denominator_poles(expr, var):
    """Extract exact or conditional poles from a denominator without solving generally."""
    expr = sp.sympify(expr)
    try:
        _num, den = sp.fraction(sp.together(expr))
    except SYMBOLIC_QUERY_ERRORS:
        return ()
    if den == 1 or not den.has(var):
        return ()
    out = []
    # Polynomial denominators get exact factor multiplicities and local
    # cancellation checks at explicitly solvable roots.
    try:
        poly = sp.Poly(den, var)
        _, factors = sp.factor_list(poly.as_expr(), var)
        for factor, mult in factors:
            roots = []
            try:
                roots = sp.solve(sp.Eq(factor, 0), var)
            except SYMBOLIC_QUERY_ERRORS:
                roots = []
            if roots and all(not r.has(var) for r in roots):
                for r in roots:
                    order = function_order_at(expr, var, r)
                    if order is not None and order.is_negative:
                        out.append(
                            Singularity(
                                SingularityKind.POLE,
                                sp.Eq(var, r),
                                S.true,
                                int(-order) if (-order).is_Integer else -order,
                                source="local-order",
                            )
                        )
                    elif order is not None and order.is_nonnegative:
                        # Removable or regular: cancellation is certified, so do
                        # not retain the denominator candidate as a pole.
                        continue
                    else:
                        out.append(
                            Singularity(
                                SingularityKind.POLE,
                                sp.Eq(factor, 0),
                                S.true,
                                mult,
                                source="denominator",
                            )
                        )
            else:
                out.append(
                    Singularity(
                        SingularityKind.POLE,
                        sp.Eq(factor, 0),
                        S.true,
                        mult,
                        source="denominator",
                    )
                )
        return _unique(out)
    except SYMBOLIC_QUERY_ERRORS:
        pass
    # Generic denominator: deliberately leave the condition unsolved.
    return (
        Singularity(
            SingularityKind.POLE, sp.Eq(den, 0), S.true, None, source="denominator"
        ),
    )


def _recursive_argument_singularities(expr, var, kind, assumptions=S.true):
    out = []
    for arg in getattr(expr, "args", ()):
        if not getattr(arg, "has", lambda *_: False)(var):
            continue
        if kind is SingularityKind.POLE:
            out.extend(_function_pole_records(arg, var, assumptions=assumptions))
        elif kind is SingularityKind.BRANCH_POINT:
            out.extend(_function_branchpoint_records(arg, var, assumptions=assumptions))
        elif kind is SingularityKind.ESSENTIAL:
            out.extend(
                function_essential_singularities(arg, var, assumptions=assumptions)
            )
    return out


def _validate_pole_candidates(expr, var, candidates):
    out = []
    for p in candidates:
        # Primitive registry/DLMF poles are already exact facts.  Local-order
        # probing is for algebraic denominator candidates and must not erase a
        # special-function pole merely because SymPy cannot expand locally.
        if p.source == "registry":
            out.append(p)
            continue
        cond = p.condition
        point = None
        if isinstance(cond, sp.Equality):
            if cond.lhs == var and not cond.rhs.has(var):
                point = cond.rhs
            elif cond.rhs == var and not cond.lhs.has(var):
                point = cond.lhs
        if point is not None:
            order = function_order_at(expr, var, point)
            if order is not None:
                if order.is_negative:
                    mult = -order
                    out.append(
                        Singularity(
                            SingularityKind.POLE,
                            cond,
                            p.guard,
                            int(mult) if mult.is_Integer else mult,
                            source="local-order",
                        )
                    )
                # nonnegative means cancellation/regularity, drop candidate
                continue
        out.append(p)
    return _unique(out)


def function_removable_singularities(expr, var):
    """Return denominator singularities whose local order is nonnegative.

    This is intentionally internal; ``function_singularities(...,
    return_result=True)`` exposes the classified removable locus and supporting
    records without adding another top-level public function.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    try:
        _, den = sp.fraction(sp.together(expr))
        if den == 1 or not den.has(var):
            return ()
        poly = sp.Poly(den, var)
        roots = sp.solve(sp.Eq(poly.as_expr(), 0), var)
    except SYMBOLIC_QUERY_ERRORS:
        return ()
    out = []
    for point in roots:
        if point.has(var):
            continue
        order = function_order_at(expr, var, point)
        if order is not None and order.is_nonnegative:
            out.append(
                Singularity(
                    SingularityKind.REMOVABLE,
                    sp.Eq(var, point),
                    S.true,
                    source="local-order",
                )
            )
    return _unique(out)


def _function_pole_records(expr, var, *, assumptions=S.true):
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    out = []
    # Exact algebraic/rational structure is preferable to table data because it
    # sees cancellation in the concrete expression.
    out.extend(_explicit_denominator_poles(expr, var))
    if expr.is_Function:
        out.extend(
            _registry_loci(
                expr,
                "Poles",
                SingularityKind.POLE,
                mode="complex",
                var=var,
                assumptions=assumptions,
            )
        )
    # A pole of an argument is not normally a pole of a transcendental outer
    # function, so recurse only through algebraic Add/Mul/Pow containers.
    if expr.is_Add or expr.is_Mul or isinstance(expr, sp.Pow):
        out.extend(
            _recursive_argument_singularities(
                expr, var, SingularityKind.POLE, assumptions
            )
        )
    return _validate_pole_candidates(expr, var, _unique(out))


def _function_branchpoint_records(expr, var, *, assumptions=S.true):
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    out = []
    if expr.is_Function:
        out.extend(
            _registry_loci(
                expr,
                "BranchPoints",
                SingularityKind.BRANCH_POINT,
                mode="complex",
                var=var,
                assumptions=assumptions,
            )
        )
    if isinstance(expr, sp.Pow):
        base, exponent = expr.args
        if exponent.is_integer is not True and base.has(var):
            out.append(
                Singularity(
                    SingularityKind.BRANCH_POINT, sp.Eq(base, 0), S.true, source="power"
                )
            )
    out.extend(
        _recursive_argument_singularities(
            expr, var, SingularityKind.BRANCH_POINT, assumptions
        )
    )
    return _unique(out)


def _pole_location(record, var):
    condition = sp.sympify(record.condition)
    if isinstance(condition, sp.Equality):
        if condition.lhs == var and not condition.rhs.has(var):
            return condition.rhs
        if condition.rhs == var and not condition.lhs.has(var):
            return condition.lhs
    return condition


def function_poles(expr, var, *, assumptions=S.true, return_result=False):
    """Return poles as ``(location, multiplicity)`` pairs.

    Locations that are not isolated remain exact Boolean conditions.  Use
    ``return_result=True`` for the underlying singularity records and provenance.
    """
    var = sp.sympify(var)
    records = _function_pole_records(expr, var, assumptions=assumptions)
    if return_result:
        return records
    return [(_pole_location(record, var), record.multiplicity) for record in records]


def function_branchpoints(expr, var, *, assumptions=S.true, return_result=False):
    """Return the Boolean branch-point locus of ``expr``.

    Use ``return_result=True`` for classified records, guards, and provenance.
    """
    records = _function_branchpoint_records(expr, var, assumptions=assumptions)
    if return_result:
        return records
    return _singularity_records_locus(records, assumptions=assumptions)


def function_definition_cuts(expr, var, *, mode="real", assumptions=S.true):
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    out = []
    if expr.is_Function:
        out.extend(
            _registry_loci(
                expr,
                "DefCuts",
                SingularityKind.DEFINITION_CUT,
                mode=mode,
                var=var,
                assumptions=assumptions,
            )
        )
    # Elementary nonsmooth heads have incomplete DefCuts in parts of the source
    # database, so make their real definition boundaries explicit.
    if mode == "real":
        if expr.func in (sp.Abs, sp.sign) and expr.args and expr.args[0].has(var):
            out.append(
                Singularity(
                    SingularityKind.DEFINITION_CUT,
                    sp.Eq(expr.args[0], 0),
                    S.true,
                    source="structural",
                )
            )
        if expr.func in (sp.floor, sp.ceiling) and expr.args and expr.args[0].has(var):
            a = expr.args[0]
            out.append(
                Singularity(
                    SingularityKind.DEFINITION_CUT,
                    sp.Contains(a, S.Integers),
                    S.true,
                    source="structural",
                )
            )
        if isinstance(expr, sp.Pow):
            base, exponent = expr.args
            if exponent.is_integer is not True and base.has(var):
                out.append(
                    Singularity(
                        SingularityKind.DEFINITION_CUT,
                        sp.Eq(base, 0),
                        S.true,
                        source="power",
                    )
                )
    for arg in getattr(expr, "args", ()):
        if getattr(arg, "has", lambda *_: False)(var):
            out.extend(
                function_definition_cuts(arg, var, mode=mode, assumptions=assumptions)
            )
    return _unique(out)


def function_essential_singularities(expr, var, *, assumptions=S.true):
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    out = []
    if expr.is_Function:
        out.extend(
            _registry_loci(
                expr,
                "Essential",
                SingularityKind.ESSENTIAL,
                mode="complex",
                var=var,
                assumptions=assumptions,
            )
        )
        # A non-polynomial entire transcendental function composed with a pole
        # has an essential singularity at that pole (or, for periodic
        # meromorphic heads, a non-meromorphic accumulation).  These common
        # heads cover the elementary cases that matter for composition.
        transcendental_entire = {
            sp.exp,
            sp.sin,
            sp.cos,
            sp.sinh,
            sp.cosh,
            sp.erf,
            sp.erfc,
        }
        if expr.func in transcendental_entire:
            for arg in expr.args:
                if arg.has(var):
                    for pole in _function_pole_records(
                        arg, var, assumptions=assumptions
                    ):
                        out.append(
                            Singularity(
                                SingularityKind.ESSENTIAL,
                                pole.condition,
                                pole.guard,
                                source="composition",
                            )
                        )
    if expr.is_Add or expr.is_Mul or isinstance(expr, sp.Pow):
        out.extend(
            _recursive_argument_singularities(
                expr, var, SingularityKind.ESSENTIAL, assumptions
            )
        )
    return _unique(out)


def function_branchcuts(expr, var, *, assumptions=S.true, mode="conditions"):
    """Return principal branch-cut loci, unsolved by default."""
    from .branchcuts import (
        IMPLEMENTED_RULE_NAMES,
        branch_cut_conditions,
        branch_cut_jumps,
    )

    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if mode == "jumps":
        return branch_cut_jumps(expr, var, assumptions=assumptions)
    out = []
    for cond in branch_cut_conditions(expr, var, assumptions=assumptions):
        locus, guard = _split_locus_guard(cond, var, assumptions=assumptions)
        if locus is not S.false and guard is not S.false:
            out.append(
                Singularity(
                    SingularityKind.BRANCH_CUT, locus, guard, source="branch-rules"
                )
            )
    # Structural jump rules cover the primitive heads for which funcprops can
    # compute boundary values.  Catalogue loci supplement other function heads
    # without duplicating equivalent structural cuts.
    head = getattr(expr.func, "__name__", "").lower()
    if isinstance(expr, sp.Pow):
        head = "power"
    if expr.is_Function and head not in IMPLEMENTED_RULE_NAMES:
        out.extend(
            _registry_loci(
                expr,
                "BranchCuts",
                SingularityKind.BRANCH_CUT,
                mode="complex",
                var=var,
                assumptions=assumptions,
            )
        )

    # Formula-level DLMF structural cuts broader than the available exact jump
    # formulas.  Record the locus without inventing a jump formula at resonant
    # parameter values.
    if expr.func is sp.hyper and len(expr.args) == 3 and expr.args[2] == var:
        aa = tuple(expr.args[0])
        bb = tuple(expr.args[1])
        if len(aa) == len(bb) + 1:
            terminating = (
                Or(*[And(sp.Contains(a, S.Integers), a <= 0) for a in aa])
                if aa
                else S.false
            )
            bottom_bad = (
                Or(*[And(sp.Contains(b, S.Integers), b <= 0) for b in bb])
                if bb
                else S.false
            )
            guard = simplify_condition(
                And(sp.Not(terminating), sp.Not(bottom_bad)), assumptions=assumptions
            )
            if guard is not S.false:
                out.append(
                    Singularity(
                        SingularityKind.BRANCH_CUT,
                        And(sp.Contains(var, S.Reals), var >= 1),
                        guard,
                        source="DLMF 16.2(iii)",
                    )
                )
    if expr.func is sp.assoc_legendre and len(expr.args) == 3 and expr.args[2] == var:
        nu, mu = expr.args[:2]
        polynomial_exception = And(
            sp.Contains(nu, S.Naturals0),
            sp.Contains(mu, S.Integers),
            sp.Abs(mu) <= nu,
            sp.Eq(sp.Mod(mu, 2), 0),
        )
        zero_exception = And(
            sp.Contains(nu, S.Naturals0), sp.Contains(mu, S.Naturals), mu > nu
        )
        guard = simplify_condition(
            And(sp.Not(polynomial_exception), sp.Not(zero_exception)),
            assumptions=assumptions,
        )
        if guard is not S.false:
            out.append(
                Singularity(
                    SingularityKind.BRANCH_CUT,
                    And(sp.Contains(var, S.Reals), var <= 1),
                    guard,
                    source="DLMF 14.21",
                )
            )
    if (
        expr.func in (sp.elliptic_f, sp.elliptic_e)
        and len(expr.args) == 2
        and expr.args[1] == var
    ):
        phi = expr.args[0]
        q = 1 - var * sp.sin(phi) ** 2
        out.append(
            Singularity(
                SingularityKind.BRANCH_CUT,
                And(sp.Eq(sp.im(q), 0), sp.re(q) <= 0),
                S.true,
                source="DLMF 19.2.4-19.2.5",
            )
        )
    if expr.func is sp.elliptic_pi and len(expr.args) == 3:
        _n, phi, m = expr.args
        if m == var:
            q = 1 - var * sp.sin(phi) ** 2
            out.append(
                Singularity(
                    SingularityKind.BRANCH_CUT,
                    And(sp.Eq(sp.im(q), 0), sp.re(q) <= 0),
                    S.true,
                    source="DLMF 19.2.7",
                )
            )
    out = _unique(out)
    conds = tuple(
        s.condition if s.guard is S.true else And(s.condition, s.guard) for s in out
    )
    if mode == "conditions":
        return conds
    if mode == "records":
        return out
    if mode == "union":
        return Or(*conds) if conds else S.false
    raise ValueError("mode must be 'conditions', 'records', 'union', or 'jumps'")


def _piecewise_boundaries(expr):
    out = []
    if not isinstance(expr, sp.Piecewise):
        return out
    for _, cond in expr.args[:-1]:
        for rel in cond.atoms(Relational) if hasattr(cond, "atoms") else ():
            out.append(sp.Eq(rel.lhs, rel.rhs))
    return out


def _piecewise_branch_for_side(expr, var, point, side):
    t = sp.Dummy("funcprops_side", positive=True)
    probe = point + t if side == "+" else point - t
    for value, cond in expr.args:
        if cond in (S.true, True):
            return value
        try:
            test = sp.simplify(sp.refine(cond.subs(var, probe), sp.Q.positive(t)))
        except SYMBOLIC_QUERY_ERRORS:
            test = cond.subs(var, probe)
        if test is S.true or test is True:
            return value
        if test is S.false or test is False:
            continue
        # reduce simple one-variable inequalities in the positive probe.
        try:
            red = sp.reduce_inequalities(test, t)
            if red is S.true:
                return value
            if red is S.false:
                continue
        except SYMBOLIC_QUERY_ERRORS:
            pass
        return None
    return None


def _piecewise_discontinuous_at(expr, var, condition):
    """Return True/False/None for a simple explicitly solvable boundary."""
    try:
        sols = sp.solve(condition, var)
    except SYMBOLIC_QUERY_ERRORS:
        return None
    if not sols or any(s.has(var) for s in sols):
        return None
    any_unknown = False
    for p in sols:
        left_branch = _piecewise_branch_for_side(expr, var, p, "-")
        right_branch = _piecewise_branch_for_side(expr, var, p, "+")
        if left_branch is None or right_branch is None:
            any_unknown = True
            continue
        try:
            left = (
                sp.limit(left_branch, var, p, dir="-")
                if left_branch.has(var)
                else left_branch
            )
            right = (
                sp.limit(right_branch, var, p, dir="+")
                if right_branch.has(var)
                else right_branch
            )
            value = expr.subs(var, p)
            if (
                certify_identity_equal(left, right) is False
                or certify_identity_equal(value, left) is False
            ):
                return True
        except SYMBOLIC_QUERY_ERRORS:
            any_unknown = True
    return None if any_unknown else False


def _registry_discontinuity_records(
    expr, var, *, assumptions=S.true, registry_var=None
):
    """Return registry discontinuities for scalar or joint analysis variables.

    ``registry_var`` is the distinguished scalar variable used by
    univariate catalogue rules.  Joint multivariate transport leaves it unset while still
    using ``var`` to separate analysis geometry from parameter guards.
    """
    query_var = (
        var if registry_var is None and len(_variable_tuple(var)) == 1 else registry_var
    )
    result = evaluate_property(
        expr, "Discontinuities", var=query_var, assumptions=assumptions
    )
    out = []
    for case in result.cases:
        value = case.value
        if _is_empty(value):
            continue
        entries = (
            tuple(value) if isinstance(value, (sp.Tuple, tuple, list)) else (value,)
        )
        for entry in entries:
            condition = (
                entry[0]
                if isinstance(entry, (sp.Tuple, tuple, list)) and entry
                else entry
            )
            locus, local_guard = _split_locus_guard(
                condition, var, assumptions=assumptions
            )
            guard = _combine_guard(case.condition, local_guard, assumptions=assumptions)
            if locus is S.false or guard is S.false:
                continue
            out.append(
                Singularity(
                    SingularityKind.DISCONTINUITY,
                    sp.sympify(locus),
                    sp.sympify(guard),
                    source="registry",
                )
            )
    return _unique(out)


def _function_discontinuity_records(expr, var, *, assumptions=S.true):
    """Return unsolved real discontinuity conditions."""
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    out = []
    if expr.is_Function:
        out.extend(_registry_discontinuity_records(expr, var, assumptions=assumptions))
    if isinstance(expr, sp.Piecewise):
        from .real_analysis.piecewise import (
            certify_piecewise_boundaries,
            piecewise_decomposition,
        )

        try:
            decomposition = piecewise_decomposition(expr, var, assumptions)
            certificates = certify_piecewise_boundaries(decomposition, max_order=0)
        except SYMBOLIC_QUERY_ERRORS:
            certificates = ()
        if certificates:
            for certificate in certificates:
                if certificate.continuous is not True:
                    out.append(
                        Singularity(
                            SingularityKind.DISCONTINUITY,
                            sp.Eq(var, certificate.boundary.point),
                            S.true,
                            source="piecewise-boundary-certificate",
                        )
                    )
        else:
            for boundary in _piecewise_boundaries(expr):
                verdict = _piecewise_discontinuous_at(expr, var, boundary)
                if verdict is not False:
                    out.append(
                        Singularity(
                            SingularityKind.DISCONTINUITY,
                            boundary,
                            S.true,
                            source="piecewise",
                        )
                    )
    # Discontinuities of inner arguments propagate through ordinary composition
    # unless an outer rule proves a cancellation; conservatively retain them.
    recursive_args = (
        [v for v, _ in expr.args]
        if isinstance(expr, sp.Piecewise)
        else getattr(expr, "args", ())
    )
    for arg in recursive_args:
        if getattr(arg, "has", lambda *_: False)(var):
            out.extend(
                _function_discontinuity_records(arg, var, assumptions=assumptions)
            )
    return _unique(out)


_SINGULARITY_LOCUS_SIMPLIFY_OP_LIMIT = 12


def _bounded_locus_simplify(condition, *, assumptions=S.true):
    """Simplify small singularity loci without exploding warmed Boolean states."""
    condition = sp.sympify(condition)
    assumptions = sp.sympify(assumptions)
    if condition in (S.true, S.false):
        return condition
    if assumptions is not S.true:
        condition = And(condition, assumptions)
    # Rebuild top-level Boolean nodes structurally so an already-expanded warmed
    # expression is not sent through the global simplifier again.
    if condition.func is And:
        condition = And(*condition.args, evaluate=False)
    elif condition.func is Or:
        condition = Or(*condition.args, evaluate=False)
    if sp.count_ops(condition) > _SINGULARITY_LOCUS_SIMPLIFY_OP_LIMIT:
        return condition
    return simplify_condition(condition)


def function_discontinuities(expr, var, *, assumptions=S.true, return_result=False):
    """Return the Boolean real-discontinuity locus of ``expr``.

    Use ``return_result=True`` for classified records and proof provenance.
    """
    records = _function_discontinuity_records(expr, var, assumptions=assumptions)
    if return_result:
        return records
    return _singularity_records_locus(records, assumptions=assumptions)


def _singularity_record_locus(record, *, assumptions=S.true):
    return _bounded_locus_simplify(
        And(record.condition, record.guard), assumptions=assumptions
    )


def _singularity_records_locus(records, *, assumptions=S.true):
    conditions = tuple(
        _singularity_record_locus(record, assumptions=assumptions) for record in records
    )
    conditions = tuple(
        condition for condition in conditions if condition is not S.false
    )
    if not conditions:
        return S.false
    return _bounded_locus_simplify(Or(*conditions), assumptions=assumptions)


def _restrict_boolean_locus(locus, restriction, var, *, assumptions=S.true):
    """Intersect a Boolean locus with a function restriction conservatively."""
    locus = sp.sympify(locus)
    restriction = simplify_condition(restriction, assumptions=assumptions)
    if restriction is S.false or locus is S.false:
        return S.false
    if restriction is S.true:
        if len(_variable_tuple(var)) == 1:
            return simplify_condition(locus, assumptions=assumptions)
        return locus
    locus = simplify_condition(locus, assumptions=assumptions)
    combined = simplify_condition(And(locus, restriction), assumptions=assumptions)
    if combined in (S.true, S.false):
        return combined

    # ``simplify_logic`` does not reason about inequalities across DNF branches.
    # Resolve one-variable real clauses separately so restrictions such as x > 0
    # can certify that the principal logarithm's nonpositive-real cut is absent.
    vv = _variable_tuple(var)
    if len(vv) != 1:
        try:
            from ._semialg import SemialgUnavailable, is_satisfiable

            if not is_satisfiable(combined, vv):
                return S.false
        except (SemialgUnavailable, *SYMBOLIC_QUERY_ERRORS):
            pass
        return combined
    variable = vv[0]
    try:
        dnf = sp.to_dnf(combined, simplify=True, force=True)
    except SYMBOLIC_QUERY_ERRORS:
        return combined
    clauses = dnf.args if dnf.func is Or else (dnf,)
    reduced = []
    for clause in clauses:
        atoms = clause.args if clause.func is And else (clause,)
        contains_reals = any(
            isinstance(atom, sp.Contains) and atom.args == (variable, S.Reals)
            for atom in atoms
        )
        inequalities = tuple(
            atom
            for atom in atoms
            if atom.has(variable) and isinstance(atom, Relational)
        )
        residual = tuple(
            atom
            for atom in atoms
            if atom not in inequalities
            and not (isinstance(atom, sp.Contains) and atom.args == (variable, S.Reals))
        )
        if inequalities:
            try:
                real_part = sp.reduce_inequalities(inequalities, variable)
            except SYMBOLIC_QUERY_ERRORS:
                real_part = And(*inequalities)
            if real_part is S.false:
                continue
            clause_result = And(real_part, *residual)
            if contains_reals and not inequalities:
                clause_result = And(sp.Contains(variable, S.Reals), clause_result)
        else:
            clause_result = clause
        clause_result = simplify_condition(clause_result, assumptions=assumptions)
        if clause_result is not S.false:
            reduced.append(clause_result)
    if not reduced:
        return S.false
    return simplify_condition(Or(*reduced), assumptions=assumptions)


def _merge_zero_boundary_relations(condition):
    """Merge ``g == 0`` with an adjacent strict half-line exactly."""
    condition = sp.sympify(condition)
    if condition.func not in (And, Or):
        return condition
    args = [_merge_zero_boundary_relations(arg) for arg in condition.args]
    if condition.func is not Or:
        return And(*args)

    for index, equality in enumerate(args):
        if not isinstance(equality, sp.Equality):
            continue
        delta = sp.expand(equality.lhs - equality.rhs)
        for other_index, relation in enumerate(args):
            if index == other_index:
                continue
            relation_delta = (
                sp.expand(relation.lhs - relation.rhs)
                if isinstance(relation, Relational)
                else None
            )
            replacement = None
            if relation_delta == delta:
                if isinstance(relation, sp.StrictLessThan):
                    replacement = sp.LessThan(delta, 0)
                elif isinstance(relation, sp.StrictGreaterThan):
                    replacement = sp.GreaterThan(delta, 0)
            elif relation_delta == -delta:
                if isinstance(relation, sp.StrictLessThan):
                    replacement = sp.GreaterThan(delta, 0)
                elif isinstance(relation, sp.StrictGreaterThan):
                    replacement = sp.LessThan(delta, 0)
            if replacement is not None:
                remaining = [
                    arg
                    for pos, arg in enumerate(args)
                    if pos not in (index, other_index)
                ]
                return Or(replacement, *remaining)
    return Or(*args)


def _explicit_complex_locus(locus, var):
    """Write simple complex loci explicitly in ``re(var)``, ``im(var)``.

    Ordering relations on a complex analysis variable describe subsets of the
    real axis.  Preserve that geometry in public complex-domain results rather
    than allowing simplification to collapse it to an apparently real-only
    relation such as ``x <= 0``.
    """
    locus = sp.sympify(locus)
    if locus in (S.true, S.false):
        return locus
    vv = _variable_tuple(var)
    if len(vv) != 1:
        return locus
    variable = vv[0]

    def rewrite(node):
        if isinstance(node, sp.Contains) and node.args == (variable, S.Reals):
            return sp.Eq(sp.im(variable), 0)
        if node.func in (And, Or):
            return node.func(*(rewrite(arg) for arg in node.args))
        if isinstance(node, Relational):
            lhs, rhs = node.lhs, node.rhs
            if lhs == variable and not rhs.has(variable) and rhs.is_real is True:
                real_relation = node.func(sp.re(variable), rhs)
                return And(sp.Eq(sp.im(variable), 0), real_relation)
            if rhs == variable and not lhs.has(variable) and lhs.is_real is True:
                real_relation = node.func(lhs, sp.re(variable))
                return And(sp.Eq(sp.im(variable), 0), real_relation)
        return node

    rewritten = _merge_zero_boundary_relations(rewrite(locus))
    simplified = sp.simplify_logic(rewritten, force=True)
    return _merge_zero_boundary_relations(simplified)


def _depends_on_any(expr, variables):
    return any(getattr(expr, "has", lambda *_: False)(v) for v in variables)


def _pullback_singularity_record(record, dummy, argument, *, source):
    """Pull one univariate singularity record back through ``dummy = argument``."""
    condition = sp.sympify(record.condition).subs(dummy, argument)
    guard = sp.sympify(record.guard).subs(dummy, argument)
    multiplicity = record.multiplicity
    if isinstance(multiplicity, sp.Basic):
        multiplicity = multiplicity.subs(dummy, argument)
    return Singularity(
        record.kind,
        condition,
        guard,
        multiplicity,
        source=source if record.source is None else f"{source}:{record.source}",
    )


def _multivariate_denominator_records(expr, variables):
    """Classify explicit denominator hypersurfaces without assuming isolation.

    When a denominator factor can itself be used as a local coordinate, replacing
    that factor by a dummy variable reduces the transverse behavior to the univariate
    local-order test.  This certifies common removable hypersurfaces such as
    ``sin(x + y)/(x + y)`` while retaining an unsolved pole condition when no
    transverse order can be proved.
    """
    vv = tuple(variables)
    expr = sp.sympify(expr)
    try:
        _num, den = sp.fraction(sp.together(expr))
    except SYMBOLIC_QUERY_ERRORS:
        return ()
    if den == 1 or not _depends_on_any(den, vv):
        return ()

    factors = []
    try:
        _constant, factor_data = sp.factor_list(den)
        factors = [(sp.sympify(factor), mult) for factor, mult in factor_data]
    except SYMBOLIC_QUERY_ERRORS:
        factors = [(den, None)]
    if not factors:
        factors = [(den, None)]

    out = []
    for factor, denominator_mult in factors:
        if not _depends_on_any(factor, vv):
            continue
        dummy = sp.Symbol("_funcprops_transverse")
        try:
            pulled = expr.xreplace({factor: dummy})
            order = function_order_at(pulled, dummy, S.Zero)
        except SYMBOLIC_QUERY_ERRORS:
            order = None
        condition = sp.Eq(factor, 0)
        if order is not None and order.is_nonnegative:
            out.append(
                Singularity(
                    SingularityKind.REMOVABLE,
                    condition,
                    S.true,
                    source="multivariate-transverse-order",
                )
            )
            continue
        if order is not None and order.is_negative:
            multiplicity = -order
            if multiplicity.is_Integer:
                multiplicity = int(multiplicity)
            out.append(
                Singularity(
                    SingularityKind.POLE,
                    condition,
                    S.true,
                    multiplicity,
                    source="multivariate-transverse-order",
                )
            )
            continue
        out.append(
            Singularity(
                SingularityKind.POLE,
                condition,
                S.true,
                denominator_mult,
                source="multivariate-denominator",
            )
        )
    return _unique(out)


@lru_cache(maxsize=128)
def _canonical_multivariate_registry_records(
    expr, canonical_variables, complex_mode, assumptions
):
    """Transport joint registry singularity facts into multivariate loci.

    One-coordinate function heads are handled by the univariate pullback path.
    This routine handles the complementary case: native registry rules for a function
    whose singularity geometry depends on two or more varying arguments.  The
    catalogue rule is instantiated directly on the concrete node, so joint
    conditions such as ``m*sin(phi)**2 == 1`` retain their full geometry and
    parameter guards without introducing an artificial scalar coordinate.
    """
    vv = tuple(canonical_variables)
    analysis_var = sp.Tuple(*vv)
    out = []
    properties = [
        ("Poles", SingularityKind.POLE, "complex"),
        ("Essential", SingularityKind.ESSENTIAL, "complex"),
        ("BranchPoints", SingularityKind.BRANCH_POINT, "complex"),
        (
            "DefCuts",
            SingularityKind.DEFINITION_CUT,
            "complex" if complex_mode else "real",
        ),
    ]
    if complex_mode:
        properties.append(("BranchCuts", SingularityKind.BRANCH_CUT, "complex"))

    for node in sp.preorder_traversal(sp.sympify(expr)):
        if not getattr(node, "is_Function", False):
            continue
        varying = [argument for argument in node.args if _depends_on_any(argument, vv)]
        if len(varying) < 2:
            continue
        for prop, kind, mode in properties:
            out.extend(
                _registry_loci(
                    node,
                    prop,
                    kind,
                    mode=mode,
                    var=analysis_var,
                    assumptions=assumptions,
                )
            )
        if not complex_mode:
            out.extend(
                _registry_discontinuity_records(
                    node,
                    analysis_var,
                    assumptions=assumptions,
                    registry_var=None,
                )
            )
    return _unique(out)


def _multivariate_univariate_pullbacks(
    expr, variables, *, complex_mode, assumptions=S.true
):
    """Reuse the univariate singularity classifiers on one-coordinate pullbacks.

    A multivariate function node with exactly one varying argument is a pullback
    of a univariate function along that argument.  Running the established univariate
    classifiers on a dummy coordinate keeps the two paths classification-
    symmetric, including registry-backed special-function facts.
    """
    vv = tuple(variables)
    out = []
    elementary_structural_heads = {
        sp.log,
        sp.exp,
        sp.sin,
        sp.cos,
        sp.sinh,
        sp.cosh,
        sp.erf,
        sp.erfc,
        sp.Abs,
        sp.sign,
        sp.floor,
        sp.ceiling,
    }
    for node in sp.preorder_traversal(expr):
        if not getattr(node, "is_Function", False):
            continue
        if node.func in elementary_structural_heads:
            # These heads are handled by explicit multivariate rules below.
            # Avoid running the full univariate registry pipeline at every elementary
            # node; that would make simple multivariate expressions needlessly
            # expensive while adding no classification information.
            continue
        varying = [arg for arg in node.args if _depends_on_any(arg, vv)]
        if len(varying) != 1:
            continue
        argument = varying[0]
        dummy = sp.Symbol("_funcprops_pullback")
        try:
            template = node.xreplace({argument: dummy})
        except SYMBOLIC_QUERY_ERRORS:
            continue
        if template == node or template.has(*vv):
            continue

        groups = [
            _function_pole_records(template, dummy, assumptions=assumptions),
            function_removable_singularities(template, dummy),
            function_essential_singularities(template, dummy, assumptions=assumptions),
            _function_branchpoint_records(template, dummy, assumptions=assumptions),
            function_definition_cuts(
                template,
                dummy,
                mode="complex" if complex_mode else "real",
                assumptions=assumptions,
            ),
        ]
        if complex_mode:
            groups.append(
                function_branchcuts(
                    template, dummy, assumptions=assumptions, mode="records"
                )
            )
        else:
            groups.append(
                _function_discontinuity_records(
                    template, dummy, assumptions=assumptions
                )
            )

        for records in groups:
            for record in records:
                out.append(
                    _pullback_singularity_record(
                        record,
                        dummy,
                        argument,
                        source="multivariate-pullback",
                    )
                )
    return _unique(out)


def _multivariate_registry_records(
    expr, variables, *, complex_mode, assumptions=S.true
):
    """Alpha-normalized cached transport of joint multivariate registry facts."""
    vv = tuple(variables)
    canonical = tuple(sp.Symbol(f"_funcprops_alpha_{i}") for i in range(len(vv)))
    to_canonical = dict(zip(vv, canonical, strict=True))
    from_canonical = dict(zip(canonical, vv, strict=True))
    canonical_expr = sp.sympify(expr).xreplace(to_canonical)
    canonical_assumptions = sp.sympify(assumptions).xreplace(to_canonical)
    records = _canonical_multivariate_registry_records(
        canonical_expr, canonical, bool(complex_mode), canonical_assumptions
    )
    out = []
    for record in records:
        multiplicity = record.multiplicity
        if isinstance(multiplicity, sp.Basic):
            multiplicity = multiplicity.xreplace(from_canonical)
        out.append(
            Singularity(
                record.kind,
                sp.sympify(record.condition).xreplace(from_canonical),
                sp.sympify(record.guard).xreplace(from_canonical),
                multiplicity,
                record.source,
            )
        )
    return tuple(out)


def _multivariate_structural_singularity_records(
    expr, variables, *, complex_mode, assumptions=S.true
):
    """Return classified exact singularity loci for multivariate expressions.

    The multivariate path deliberately mirrors all supported singularity classes.  It uses
    exact denominator hypersurfaces, univariate pullbacks for function heads,
    and structural composition rules where singular behavior comes from an
    argument rather than from the outer head itself.
    """
    vv = tuple(variables)
    expr = sp.sympify(expr)
    out = list(_multivariate_denominator_records(expr, vv))
    out.extend(
        _multivariate_registry_records(
            expr, vv, complex_mode=complex_mode, assumptions=assumptions
        )
    )
    out.extend(
        _multivariate_univariate_pullbacks(
            expr, vv, complex_mode=complex_mode, assumptions=assumptions
        )
    )

    transcendental_entire = {
        sp.exp,
        sp.sin,
        sp.cos,
        sp.sinh,
        sp.cosh,
        sp.erf,
        sp.erfc,
    }
    for node in sp.preorder_traversal(expr):
        args = getattr(node, "args", ())
        if not complex_mode and args and _depends_on_any(args[0], vv):
            argument = args[0]
            if node.func in (sp.Abs, sp.sign):
                out.append(
                    Singularity(
                        SingularityKind.DEFINITION_CUT,
                        sp.Eq(argument, 0),
                        S.true,
                        source="multivariate-structural",
                    )
                )
                if node.func is sp.sign:
                    out.append(
                        Singularity(
                            SingularityKind.DISCONTINUITY,
                            sp.Eq(argument, 0),
                            S.true,
                            source="multivariate-structural",
                        )
                    )
            elif node.func in (sp.floor, sp.ceiling):
                integer_locus = sp.Contains(argument, S.Integers)
                out.append(
                    Singularity(
                        SingularityKind.DEFINITION_CUT,
                        integer_locus,
                        S.true,
                        source="multivariate-structural",
                    )
                )
                out.append(
                    Singularity(
                        SingularityKind.DISCONTINUITY,
                        integer_locus,
                        S.true,
                        source="multivariate-structural",
                    )
                )

        if node.func in transcendental_entire:
            for argument in args:
                if not _depends_on_any(argument, vv):
                    continue
                for pole in _multivariate_denominator_records(argument, vv):
                    if pole.kind is SingularityKind.POLE:
                        out.append(
                            Singularity(
                                SingularityKind.ESSENTIAL,
                                pole.condition,
                                pole.guard,
                                source="multivariate-composition",
                            )
                        )

        if node.func is sp.log and args and _depends_on_any(args[0], vv):
            argument = args[0]
            out.append(
                Singularity(
                    SingularityKind.BRANCH_POINT,
                    sp.Eq(argument, 0),
                    S.true,
                    source="multivariate-log",
                )
            )
            if complex_mode:
                out.append(
                    Singularity(
                        SingularityKind.BRANCH_CUT,
                        And(sp.Eq(sp.im(argument), 0), sp.re(argument) < 0),
                        S.true,
                        source="multivariate-log",
                    )
                )
            continue
        if isinstance(node, sp.Pow):
            base, exponent = node.args
            if exponent.is_integer is not True and _depends_on_any(base, vv):
                out.append(
                    Singularity(
                        SingularityKind.BRANCH_POINT,
                        sp.Eq(base, 0),
                        S.true,
                        source="multivariate-power",
                    )
                )
                if complex_mode:
                    out.append(
                        Singularity(
                            SingularityKind.BRANCH_CUT,
                            And(sp.Eq(sp.im(base), 0), sp.re(base) < 0),
                            S.true,
                            source="multivariate-power",
                        )
                    )
                else:
                    out.append(
                        Singularity(
                            SingularityKind.DEFINITION_CUT,
                            sp.Eq(base, 0),
                            S.true,
                            source="multivariate-power",
                        )
                    )

    return _unique(out)


def _relation_closure(atom):
    if isinstance(atom, sp.StrictGreaterThan):
        return sp.GreaterThan(atom.lhs, atom.rhs)
    if isinstance(atom, sp.StrictLessThan):
        return sp.LessThan(atom.lhs, atom.rhs)
    return atom


def _relation_interior(atom):
    if isinstance(atom, sp.GreaterThan):
        return sp.StrictGreaterThan(atom.lhs, atom.rhs)
    if isinstance(atom, sp.LessThan):
        return sp.StrictLessThan(atom.lhs, atom.rhs)
    if isinstance(atom, sp.Equality):
        return S.false
    return atom


def _domain_geometry(condition, variables, *, assumptions=S.true):
    """Return certified ambient interior, boundary and exterior conditions.

    This handles the semialgebraic support forms used throughout funcprops:
    conjunctions of equalities and weak/strict inequalities, plus simple
    disjunctions.  Unsupported Boolean atoms are retained conservatively.
    """
    condition = simplify_condition(condition, assumptions=assumptions)
    if condition is S.true:
        return S.true, S.false, S.false
    if condition is S.false:
        return S.false, S.false, S.true

    def rec(node):
        if node.func is And:
            parts = [rec(a) for a in node.args]
            closure = And(*(p[1] for p in parts))
            interior = And(*(p[0] for p in parts))
            return interior, closure
        if node.func is Or:
            parts = [rec(a) for a in node.args]
            interior = Or(*(p[0] for p in parts))
            closure = Or(*(p[1] for p in parts))
            return interior, closure
        if isinstance(node, Relational):
            return _relation_interior(node), _relation_closure(node)
        return node, node

    interior, closure = rec(condition)
    interior = simplify_condition(interior, assumptions=assumptions)
    closure = simplify_condition(closure, assumptions=assumptions)
    boundary = simplify_condition(
        And(closure, sp.Not(interior)), assumptions=assumptions
    )
    exterior = simplify_condition(sp.Not(closure), assumptions=assumptions)
    return interior, boundary, exterior


def _complexify_equality_locus_impl(locus, variables):
    """Expand complex equalities into explicit real/imaginary equations."""
    vv = tuple(variables)

    def rewrite(node):
        if node.func in (And, Or):
            rewritten = node.func(*(rewrite(a) for a in node.args))
            if rewritten.func is Or and len(rewritten.args) == 2:
                a, b = rewritten.args
                pairs = ((a, b), (b, a))
                for equality, relation in pairs:
                    if not isinstance(equality, sp.Equality):
                        continue
                    delta = sp.expand(equality.lhs - equality.rhs)
                    if delta == 0:
                        continue
                    if isinstance(relation, sp.StrictLessThan):
                        if sp.expand(relation.lhs - relation.rhs) == delta:
                            return sp.LessThan(delta, 0)
                    if isinstance(relation, sp.StrictGreaterThan):
                        if sp.expand(relation.lhs - relation.rhs) == delta:
                            return sp.GreaterThan(delta, 0)
            return rewritten
        if isinstance(node, sp.Equality):
            delta = sp.expand(node.lhs - node.rhs)
            if any(delta.has(v) for v in vv):
                # Registry branch-cut rules are frequently already expressed in
                # explicit real/imaginary coordinates.  Re-complexifying an
                # equality such as ``im(g(x, y)) == 0`` is redundant and can
                # trigger very large expansions for special functions.
                if delta.is_real is True:
                    return sp.Eq(delta, 0)
                if sp.count_ops(delta) > 8 or delta.has(
                    sp.sin,
                    sp.cos,
                    sp.tan,
                    sp.sinh,
                    sp.cosh,
                    sp.tanh,
                ):
                    real_part = sp.re(delta, evaluate=False)
                    imag_part = sp.im(delta, evaluate=False)
                else:
                    real_part = sp.re(delta)
                    imag_part = sp.im(delta)
                return And(sp.Eq(real_part, 0), sp.Eq(imag_part, 0))
        return node

    locus = sp.sympify(locus)
    rewritten = rewrite(locus)
    # Small elementary loci benefit from Boolean normalization (for example,
    # the log branch point plus negative-real cut becomes one nonpositive-real
    # condition).  Large special-function preimages can expand exponentially
    # under simplify_logic; their structurally exact Boolean form is already a
    # canonical public answer, so avoid distributive normalization there.
    if sp.count_ops(rewritten) > 30:
        return rewritten
    rewritten = _merge_zero_boundary_relations(rewritten)
    result = simplify_condition(rewritten)
    return _merge_zero_boundary_relations(simplify_condition(rewrite(result)))


@lru_cache(maxsize=256)
def _cached_complexify_equality_locus(locus, canonical_variables):
    return _complexify_equality_locus_impl(locus, canonical_variables)


def _complexify_equality_locus(locus, variables):
    """Alpha-normalized cached complexification of multivariate equality loci."""
    vv = tuple(variables)
    canonical = tuple(sp.Symbol(f"_funcprops_alpha_{i}") for i in range(len(vv)))
    to_canonical = dict(zip(vv, canonical, strict=True))
    from_canonical = dict(zip(canonical, vv, strict=True))
    canonical_locus = sp.sympify(locus).xreplace(to_canonical)
    result = _cached_complexify_equality_locus(canonical_locus, canonical)
    return sp.sympify(result).xreplace(from_canonical)


def _collect_singularity_records(expr, variables, *, complex_mode, assumptions):
    if len(variables) == 1:
        variable = variables[0]
        return {
            "poles": _function_pole_records(expr, variable, assumptions=assumptions),
            "removable": function_removable_singularities(expr, variable),
            "essential": function_essential_singularities(
                expr, variable, assumptions=assumptions
            ),
            "branch_points": _function_branchpoint_records(
                expr, variable, assumptions=assumptions
            ),
            "branch_cuts": function_branchcuts(
                expr, variable, assumptions=assumptions, mode="records"
            )
            if complex_mode
            else (),
            "definition_cuts": function_definition_cuts(
                expr,
                variable,
                mode="complex" if complex_mode else "real",
                assumptions=assumptions,
            ),
            "discontinuities": ()
            if complex_mode
            else _function_discontinuity_records(
                expr, variable, assumptions=assumptions
            ),
        }

    structural = _multivariate_structural_singularity_records(
        expr, variables, complex_mode=complex_mode, assumptions=assumptions
    )
    return {
        "poles": tuple(r for r in structural if r.kind is SingularityKind.POLE),
        "removable": tuple(
            r for r in structural if r.kind is SingularityKind.REMOVABLE
        ),
        "essential": tuple(
            r for r in structural if r.kind is SingularityKind.ESSENTIAL
        ),
        "branch_points": tuple(
            r for r in structural if r.kind is SingularityKind.BRANCH_POINT
        ),
        "branch_cuts": tuple(
            r for r in structural if r.kind is SingularityKind.BRANCH_CUT
        )
        if complex_mode
        else (),
        "definition_cuts": tuple(
            r for r in structural if r.kind is SingularityKind.DEFINITION_CUT
        ),
        "discontinuities": tuple(
            r for r in structural if r.kind is SingularityKind.DISCONTINUITY
        )
        if not complex_mode
        else (),
    }


def function_singularities(
    expr,
    var,
    domain=S.Complexes,
    *,
    assumptions=S.true,
    return_result=False,
):
    """Return the Boolean locus where ``expr`` is singular.

    For several analysis variables, singularities remain as exact Boolean loci
    such as ``Eq(x + y, 0)`` rather than being forced into isolated points.
    ``ConditionalExpression`` restrictions define the effective function domain.
    Detailed results additionally classify the unrestricted singular locus as
    interior, boundary, or exterior to that domain.
    """
    restriction = S.true
    while isinstance(expr, ConditionalExpression):
        restriction = simplify_condition(
            And(restriction, expr.condition), assumptions=assumptions
        )
        expr = expr.value
    expr = sp.sympify(expr)
    variables = _variable_tuple(var)
    analysis_var = variables[0] if len(variables) == 1 else sp.Tuple(*variables)
    complex_mode = domain in (S.Complexes, "complex", "complexes", "C", "CC")

    classified_records = _collect_singularity_records(
        expr, variables, complex_mode=complex_mode, assumptions=assumptions
    )

    unrestricted_loci = {
        name: _singularity_records_locus(records, assumptions=assumptions)
        for name, records in classified_records.items()
    }
    unrestricted = _bounded_locus_simplify(
        Or(*unrestricted_loci.values()), assumptions=assumptions
    )

    classified_loci = {
        name: _restrict_boolean_locus(
            locus, restriction, analysis_var, assumptions=assumptions
        )
        for name, locus in unrestricted_loci.items()
    }
    singularities = _restrict_boolean_locus(
        unrestricted, restriction, analysis_var, assumptions=assumptions
    )

    domain_interior, domain_boundary, domain_exterior = _domain_geometry(
        restriction, variables, assumptions=assumptions
    )
    interior_singularities = _restrict_boolean_locus(
        unrestricted, domain_interior, analysis_var, assumptions=assumptions
    )
    boundary_singularities = _restrict_boolean_locus(
        unrestricted, domain_boundary, analysis_var, assumptions=assumptions
    )
    exterior_singularities = _restrict_boolean_locus(
        unrestricted, domain_exterior, analysis_var, assumptions=assumptions
    )

    if complex_mode:
        if len(variables) == 1:
            singularities = _explicit_complex_locus(singularities, variables[0])
            unrestricted = _explicit_complex_locus(unrestricted, variables[0])
            classified_loci = {
                name: _explicit_complex_locus(locus, variables[0])
                for name, locus in classified_loci.items()
            }
            interior_singularities = _explicit_complex_locus(
                interior_singularities, variables[0]
            )
            boundary_singularities = _explicit_complex_locus(
                boundary_singularities, variables[0]
            )
            exterior_singularities = _explicit_complex_locus(
                exterior_singularities, variables[0]
            )
        else:
            complex_locus_cache = {}

            def complexify(locus):
                key = sp.srepr(locus)
                if key not in complex_locus_cache:
                    complex_locus_cache[key] = _complexify_equality_locus(
                        locus, variables
                    )
                return complex_locus_cache[key]

            classified_loci = {
                name: complexify(locus) for name, locus in classified_loci.items()
            }
            if restriction is S.true:
                aggregate = Or(*classified_loci.values())
                unrestricted = (
                    _merge_zero_boundary_relations(simplify_condition(aggregate))
                    if sp.count_ops(aggregate) <= 80
                    else aggregate
                )
                singularities = unrestricted
                interior_singularities = unrestricted
                boundary_singularities = S.false
                exterior_singularities = S.false
            else:
                singularities = complexify(singularities)
                unrestricted = complexify(unrestricted)
                interior_singularities = complexify(interior_singularities)
                boundary_singularities = complexify(boundary_singularities)
                exterior_singularities = complexify(exterior_singularities)

    if not return_result:
        return singularities

    restricted_records = []
    if restriction is S.true:
        for records in classified_records.values():
            restricted_records.extend(records)
    else:
        for records in classified_records.values():
            for record in records:
                locus = _restrict_boolean_locus(
                    _singularity_record_locus(record, assumptions=assumptions),
                    restriction,
                    analysis_var,
                    assumptions=assumptions,
                )
                if locus is S.false:
                    continue
                restricted_records.append(
                    Singularity(
                        record.kind,
                        locus,
                        S.true,
                        record.multiplicity,
                        record.source,
                    )
                )
    return SingularityResult(
        singularities=singularities,
        poles=classified_loci["poles"],
        removable=classified_loci["removable"],
        essential=classified_loci["essential"],
        branch_points=classified_loci["branch_points"],
        branch_cuts=classified_loci["branch_cuts"],
        definition_cuts=classified_loci["definition_cuts"],
        discontinuities=classified_loci["discontinuities"],
        records=tuple(restricted_records),
        domain=domain,
        restriction=restriction,
        unrestricted_singularities=unrestricted,
        interior_singularities=interior_singularities,
        boundary_singularities=boundary_singularities,
        exterior_singularities=exterior_singularities,
        domain_interior=domain_interior,
        domain_boundary=domain_boundary,
        domain_exterior=domain_exterior,
    )


def _real_domain_condition(expr, var):
    from .api import function_domain

    try:
        d = function_domain(expr, var, domain=S.Reals)
        if isinstance(d, PropertyResult):
            return None
        return sp.sympify(d)
    except SYMBOLIC_QUERY_ERRORS:
        return None


def _condition_intersects_domain(cond, domain_cond, assumptions=S.true):
    if domain_cond is None:
        return None
    c = simplify_condition(And(cond, domain_cond), assumptions=assumptions)
    if c is S.false:
        return False
    if c is S.true:
        return True
    # For one-dimensional explicit relational conditions SymPy often resolves
    # conjunction consistency via reduce_inequalities.
    syms = tuple(c.free_symbols)
    if len(syms) == 1:
        try:
            red = sp.reduce_inequalities(c, syms[0])
            return red is not S.false
        except SYMBOLIC_QUERY_ERRORS:
            pass
    return None


def _conditional_boolean_status(result):
    """Return True/False when conditional Boolean cases cover all possibilities."""
    if result.primary is S.true:
        return True
    if result.primary is S.false:
        return False
    if not result.cases:
        return None
    if all(c.value is S.true for c in result.cases):
        try:
            if sp.simplify_logic(Or(*[c.condition for c in result.cases])) is S.true:
                return True
        except SYMBOLIC_QUERY_ERRORS:
            pass
    if all(c.value is S.false for c in result.cases):
        try:
            if sp.simplify_logic(Or(*[c.condition for c in result.cases])) is S.true:
                return False
        except SYMBOLIC_QUERY_ERRORS:
            pass
    return None


def _variable_tuple(var):
    if isinstance(var, (tuple, list, sp.Tuple)):
        vv = tuple(sp.sympify(v) for v in var)
    else:
        vv = (sp.sympify(var),)
    if not vv:
        raise ValueError("at least one variable is required")
    return vv


def _multivariate_structural_analytic(expr, variables, *, complex_mode=False):
    """Conservative joint analyticity classifier for several variables."""
    vv = tuple(variables)
    expr = sp.sympify(expr)
    if not any(expr.has(v) for v in vv):
        return Analyticity.ANALYTIC
    if expr.func in (sp.Abs, sp.sign, sp.floor, sp.ceiling) or isinstance(
        expr, sp.Piecewise
    ):
        return Analyticity.NOT_ANALYTIC
    try:
        if expr.is_polynomial(*vv) or expr.is_rational_function(*vv):
            return Analyticity.ANALYTIC
    except SYMBOLIC_QUERY_ERRORS:
        pass
    if expr.is_Add or expr.is_Mul or (isinstance(expr, sp.Pow) and expr.exp.is_integer):
        vals = [
            _multivariate_structural_analytic(a, vv, complex_mode=complex_mode)
            for a in expr.args
        ]
        if any(v is Analyticity.NOT_ANALYTIC for v in vals):
            return Analyticity.NOT_ANALYTIC
        if all(v is Analyticity.ANALYTIC for v in vals):
            return Analyticity.ANALYTIC
        return Analyticity.UNKNOWN
    analytic_heads = (
        sp.exp,
        sp.sin,
        sp.cos,
        sp.sinh,
        sp.cosh,
        sp.tanh,
        sp.erf,
        sp.erfc,
    )
    if expr.func in analytic_heads:
        vals = [
            _multivariate_structural_analytic(a, vv, complex_mode=complex_mode)
            for a in expr.args
            if any(a.has(v) for v in vv)
        ]
        if all(v is Analyticity.ANALYTIC for v in vals):
            return Analyticity.ANALYTIC
        if any(v is Analyticity.NOT_ANALYTIC for v in vals):
            return Analyticity.NOT_ANALYTIC
    return Analyticity.UNKNOWN


def _multivariate_structural_continuity(expr, variables):
    """Conservative joint continuity classifier on the natural real domain."""
    vv = tuple(variables)
    expr = sp.sympify(expr)
    if not any(expr.has(v) for v in vv):
        return Continuity.CONTINUOUS
    if expr.func in (sp.floor, sp.ceiling, sp.sign):
        return Continuity.DISCONTINUOUS
    try:
        if expr.is_polynomial(*vv) or expr.is_rational_function(*vv):
            return Continuity.CONTINUOUS
    except SYMBOLIC_QUERY_ERRORS:
        pass
    if expr.func is sp.Abs:
        vals = [_multivariate_structural_continuity(a, vv) for a in expr.args]
        return (
            Continuity.CONTINUOUS
            if all(v is Continuity.CONTINUOUS for v in vals)
            else Continuity.UNKNOWN
        )
    if expr.is_Add or expr.is_Mul or isinstance(expr, sp.Pow):
        vals = [
            _multivariate_structural_continuity(a, vv)
            for a in expr.args
            if any(a.has(v) for v in vv)
        ]
        if any(v is Continuity.DISCONTINUOUS for v in vals):
            return Continuity.DISCONTINUOUS
        if all(v is Continuity.CONTINUOUS for v in vals):
            return Continuity.CONTINUOUS
        return Continuity.UNKNOWN
    continuous_heads = (
        sp.exp,
        sp.log,
        sp.sin,
        sp.cos,
        sp.tan,
        sp.cot,
        sp.sinh,
        sp.cosh,
        sp.tanh,
        sp.asin,
        sp.acos,
        sp.atan,
        sp.asinh,
        sp.acosh,
        sp.atanh,
        sp.erf,
        sp.erfc,
        sp.gamma,
    )
    if expr.func in continuous_heads:
        vals = [
            _multivariate_structural_continuity(a, vv)
            for a in expr.args
            if any(a.has(v) for v in vv)
        ]
        if all(v is Continuity.CONTINUOUS for v in vals):
            return Continuity.CONTINUOUS
    return Continuity.UNKNOWN


def _complex_analyticity_stage(expr, var, *, assumptions, return_result):
    # "Analytic" means holomorphic on the function's natural complex
    # domain, matching the source LocallyAnalytic property.
    if expr.func in (sp.Abs, sp.sign, sp.floor, sp.ceiling) or isinstance(
        expr, sp.Piecewise
    ):
        result = PropertyResult(Analyticity.NOT_ANALYTIC, source="nonholomorphic-head")
        return result if return_result else result.primary
    # Generalized hypergeometric functions: DLMF 16.2 states that p<=q
    # is entire in z, while p=q+1 has a principal analytic branch off its
    # standard cut.  A terminating top parameter makes the series a
    # polynomial.  We require bottom parameters to be provably outside
    # the excluded nonpositive integers rather than assuming genericity.
    if expr.func is sp.hyper and len(expr.args) == 3 and expr.args[2] == var:
        aa = tuple(expr.args[0])
        bb = tuple(expr.args[1])

        def _bottom_ok(b):
            return b.is_integer is False or b.is_positive is True

        bottoms_ok = all(_bottom_ok(b) for b in bb)
        terminating = any(a.is_integer is True and a.is_nonpositive is True for a in aa)
        if bottoms_ok and (len(aa) <= len(bb) + 1 or terminating):
            src = (
                "DLMF 16.2(ii)"
                if len(aa) <= len(bb)
                else (
                    "DLMF 16.2 terminating polynomial"
                    if terminating
                    else "DLMF 16.2(iii) principal branch"
                )
            )
            result = PropertyResult(Analyticity.ANALYTIC, source=src)
            return result if return_result else result.primary
    local = evaluate_property(
        expr, "LocallyAnalytic", mode="complex", var=var, assumptions=assumptions
    )
    local_status = _conditional_boolean_status(local)
    if local_status is False:
        return (
            PropertyResult(Analyticity.NOT_ANALYTIC, source="registry")
            if return_result
            else Analyticity.NOT_ANALYTIC
        )
    if local_status is True:
        return (
            PropertyResult(Analyticity.ANALYTIC, source="registry")
            if return_result
            else Analyticity.ANALYTIC
        )
    entire = evaluate_property(
        expr, "Entire", mode="complex", var=var, assumptions=assumptions
    )
    if _conditional_boolean_status(entire) is True or expr.is_polynomial(var):
        return (
            PropertyResult(Analyticity.ANALYTIC, source="analytic-primitive")
            if return_result
            else Analyticity.ANALYTIC
        )
    # Arithmetic closure is valid without needing a primitive function
    # theorem.  Do not apply generic composition closure to an unknown head.
    if expr.is_Add or expr.is_Mul or (isinstance(expr, sp.Pow) and expr.exp.is_integer):
        vals = [
            _function_analytic_impl(a, var, domain=S.Complexes, assumptions=assumptions)
            for a in expr.args
            if a.has(var)
        ]
        if vals and all(v == Analyticity.ANALYTIC for v in vals):
            return (
                PropertyResult(Analyticity.ANALYTIC, source="holomorphic-closure")
                if return_result
                else Analyticity.ANALYTIC
            )
        if any(v == Analyticity.NOT_ANALYTIC for v in vals):
            return (
                PropertyResult(Analyticity.NOT_ANALYTIC, source="holomorphic-closure")
                if return_result
                else Analyticity.NOT_ANALYTIC
            )
    return (
        PropertyResult(Analyticity.UNKNOWN, source="insufficient-evidence")
        if return_result
        else Analyticity.UNKNOWN
    )


def _real_analyticity_stage(
    expr, var, *, domain, assumptions, return_result, domain_ready
):
    domain_cond = (
        sp.sympify(domain)
        if domain_ready
        else (
            _real_domain_condition(expr, var)
            if domain in (S.Reals, "real", "reals", "R", "RR")
            else (
                domain.as_relational(var)
                if isinstance(domain, sp.Set)
                else sp.sympify(domain)
            )
        )
    )
    if not domain_ready and domain_cond is not None:
        split = evaluate_parameter_strata(
            domain_cond,
            var,
            lambda branch_domain: _function_analytic_impl(
                expr,
                var,
                domain=branch_domain,
                assumptions=assumptions,
                return_result=return_result,
                domain_ready=True,
            ),
            source="analyticity-parameter-stratification",
        )
        if split is not None:
            return split
    if expr.func in (sp.Abs, sp.sign, sp.floor, sp.ceiling):
        cuts = function_definition_cuts(expr, var, mode="real", assumptions=assumptions)
        bad = []
        unknown_cut = False
        for cut in cuts:
            hit = _condition_intersects_domain(
                And(cut.condition, cut.guard), domain_cond, assumptions
            )
            if hit is True:
                bad.append(cut)
            elif hit is None:
                unknown_cut = True
        if bad:
            result = PropertyResult(
                Analyticity.NOT_ANALYTIC, exceptions=tuple(bad), source="nonsmooth-head"
            )
            return result if return_result else result.primary
        if unknown_cut:
            result = PropertyResult(
                Analyticity.UNKNOWN,
                exceptions=cuts,
                source="conditional-nonsmooth-cuts",
            )
            return result if return_result else result.primary
        # Abs/sign/floor/ceiling are locally analytic on every real component
        # that excludes their kink/jump lattice.  This matters for restricted
        # domains such as Abs(x) on x>0.
        result = PropertyResult(Analyticity.ANALYTIC, source="nonsmooth-head-off-cuts")
        return result if return_result else result.primary
    if isinstance(expr, sp.Piecewise):
        boundaries = _piecewise_boundaries(expr)
        bad = []
        unknown_boundary = False
        for b in boundaries:
            hit = _condition_intersects_domain(b, domain_cond, assumptions)
            if hit is True:
                bad.append(b)
            elif hit is None:
                unknown_boundary = True
        if bad:
            exc = tuple(
                Singularity(
                    SingularityKind.DEFINITION_CUT, b, S.true, source="piecewise"
                )
                for b in bad
            )
            result = PropertyResult(
                Analyticity.NOT_ANALYTIC, exceptions=exc, source="piecewise"
            )
            return result if return_result else result.primary
        if unknown_boundary:
            return (
                PropertyResult(Analyticity.UNKNOWN, source="piecewise-boundary-unknown")
                if return_result
                else Analyticity.UNKNOWN
            )
    cuts = function_definition_cuts(expr, var, mode="real", assumptions=assumptions)
    bad = []
    unknown = False
    for cut in cuts:
        cond = And(cut.condition, cut.guard)
        intersects = _condition_intersects_domain(cond, domain_cond, assumptions)
        if intersects is True:
            bad.append(cut)
        elif intersects is None:
            unknown = True
    if bad:
        result = PropertyResult(
            Analyticity.NOT_ANALYTIC, exceptions=tuple(bad), source="definition-cuts"
        )
        return result if return_result else result.primary
    if unknown:
        return (
            PropertyResult(
                Analyticity.UNKNOWN,
                exceptions=cuts,
                source="conditional-definition-cuts",
            )
            if return_result
            else Analyticity.UNKNOWN
        )

    # Composition theorem: analytic primitives composed with analytic arguments.
    for arg in getattr(expr, "args", ()):
        if arg.has(var) and arg != var:
            a = _function_analytic_impl(
                arg, var, domain=S.Reals, assumptions=assumptions
            )
            if a == Analyticity.NOT_ANALYTIC:
                return (
                    PropertyResult(Analyticity.NOT_ANALYTIC, source="composition")
                    if return_result
                    else Analyticity.NOT_ANALYTIC
                )
            if a == Analyticity.UNKNOWN:
                unknown = True
    entire = evaluate_property(
        expr, "Entire", mode="complex", var=var, assumptions=assumptions
    )
    local = evaluate_property(
        expr, "LocallyAnalytic", mode="real", var=var, assumptions=assumptions
    )
    if expr.is_polynomial(var) or entire.primary is S.true or local.primary is S.true:
        val = Analyticity.UNKNOWN if unknown else Analyticity.ANALYTIC
        return (
            PropertyResult(val, source="registry+composition") if return_result else val
        )
    if expr.is_rational_function(var) and not cuts:
        return (
            PropertyResult(Analyticity.ANALYTIC, source="rational")
            if return_result
            else Analyticity.ANALYTIC
        )
    if expr.is_Add or expr.is_Mul or (isinstance(expr, sp.Pow) and expr.exp.is_integer):
        vals = [
            _function_analytic_impl(a, var, domain=S.Reals, assumptions=assumptions)
            for a in expr.args
            if a.has(var)
        ]
        if vals and all(v == Analyticity.ANALYTIC for v in vals):
            return (
                PropertyResult(Analyticity.ANALYTIC, source="analytic-closure")
                if return_result
                else Analyticity.ANALYTIC
            )
        if any(v == Analyticity.NOT_ANALYTIC for v in vals):
            return (
                PropertyResult(Analyticity.NOT_ANALYTIC, source="analytic-closure")
                if return_result
                else Analyticity.NOT_ANALYTIC
            )
    return (
        PropertyResult(Analyticity.UNKNOWN, source="insufficient-evidence")
        if return_result
        else Analyticity.UNKNOWN
    )


def _function_analytic_impl(
    expr,
    var,
    *,
    domain=S.Reals,
    assumptions=S.true,
    return_result=False,
    _domain_ready=False,
):
    """Classify real analyticity by default, holomorphy for Complexes."""
    expr = sp.sympify(expr)
    vv = _variable_tuple(var)
    is_complex = domain in (S.Complexes, "complex", "complexes", "C", "CC")
    if len(vv) > 1:
        val = _multivariate_structural_analytic(expr, vv, complex_mode=is_complex)
        result = PropertyResult(val, source="multivariate-structural-analyticity")
        return result if return_result else val
    var = vv[0]
    if (
        not is_complex
        and domain not in (S.Reals, "real", "reals", "R", "RR")
        and not isinstance(domain, (sp.Set, Boolean, Relational))
    ):
        raise ValueError(
            "domain must be Reals, Complexes, a set, or a Boolean domain condition"
        )

    # Algebraic expressions are analytic on their natural domain except at
    # branch/definition boundaries, handled below.
    if is_complex:
        return _complex_analyticity_stage(
            expr, var, assumptions=assumptions, return_result=return_result
        )

    return _real_analyticity_stage(
        expr,
        var,
        domain=domain,
        assumptions=assumptions,
        return_result=return_result,
        domain_ready=_domain_ready,
    )


def function_meromorphic(expr, var, *, assumptions=S.true, return_result=False):
    """Classify meromorphicity on the complex plane/natural complex domain."""
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if expr.is_rational_function(var):
        return (
            PropertyResult(Meromorphicity.MEROMORPHIC, source="rational")
            if return_result
            else Meromorphicity.MEROMORPHIC
        )
    branch = _function_branchpoint_records(expr, var, assumptions=assumptions)
    cuts = function_branchcuts(expr, var, assumptions=assumptions, mode="records")
    essential = function_essential_singularities(expr, var, assumptions=assumptions)
    bad = branch + cuts + essential
    definite = []
    conditional = []
    for item in bad:
        g = simplify_condition(item.guard, assumptions=assumptions)
        if g is S.true:
            definite.append(item)
        elif g is not S.false:
            conditional.append(item)
    if definite:
        result = PropertyResult(
            Meromorphicity.NOT_MEROMORPHIC,
            exceptions=tuple(definite + conditional),
            source="singularity-analysis",
        )
        return result if return_result else result.primary
    if conditional:
        bad_guard = simplify_condition(
            Or(*[item.guard for item in conditional]), assumptions=assumptions
        )
        cases = (
            ConditionalExpression(Meromorphicity.NOT_MEROMORPHIC, bad_guard),
            ConditionalExpression(Meromorphicity.MEROMORPHIC, sp.Not(bad_guard)),
        )
        result = PropertyResult(
            Meromorphicity.UNKNOWN,
            cases=cases,
            exceptions=tuple(conditional),
            source="conditional-singularity-analysis",
        )
        return result
    reg = evaluate_property(
        expr, "Meromorphic", mode="complex", assumptions=assumptions
    )
    if reg.primary is S.true:
        return (
            PropertyResult(Meromorphicity.MEROMORPHIC, source="registry")
            if return_result
            else Meromorphicity.MEROMORPHIC
        )
    if reg.primary is S.false:
        return (
            PropertyResult(Meromorphicity.NOT_MEROMORPHIC, source="registry")
            if return_result
            else Meromorphicity.NOT_MEROMORPHIC
        )
    entire = evaluate_property(expr, "Entire", mode="complex", assumptions=assumptions)
    if entire.primary is S.true:
        return (
            PropertyResult(Meromorphicity.MEROMORPHIC, source="entire")
            if return_result
            else Meromorphicity.MEROMORPHIC
        )
    if (
        function_analytic(expr, var, domain=S.Complexes, assumptions=assumptions)
        == Analyticity.ANALYTIC
    ):
        # Holomorphic on its natural domain and with no branch/essential
        # obstruction above: any remaining isolated singularities are poles.
        return (
            PropertyResult(Meromorphicity.MEROMORPHIC, source="analytic-with-poles")
            if return_result
            else Meromorphicity.MEROMORPHIC
        )
    # Closure of meromorphic functions under arithmetic.
    if expr.is_Add or expr.is_Mul or (isinstance(expr, sp.Pow) and expr.exp.is_integer):
        vals = []
        for arg in expr.args:
            if arg.has(var):
                vals.append(function_meromorphic(arg, var, assumptions=assumptions))
        if vals and all(v == Meromorphicity.MEROMORPHIC for v in vals):
            return (
                PropertyResult(Meromorphicity.MEROMORPHIC, source="closure")
                if return_result
                else Meromorphicity.MEROMORPHIC
            )
        if any(v == Meromorphicity.NOT_MEROMORPHIC for v in vals):
            return (
                PropertyResult(Meromorphicity.NOT_MEROMORPHIC, source="closure")
                if return_result
                else Meromorphicity.NOT_MEROMORPHIC
            )
    return (
        PropertyResult(Meromorphicity.UNKNOWN, source="insufficient-evidence")
        if return_result
        else Meromorphicity.UNKNOWN
    )


def _condition_to_set(condition, var):
    """Convert a real condition using the shared structural set converter."""
    if condition is None:
        return None

    # Import lazily to avoid an import cycle through real_analysis.smoothness.
    from .real_analysis.common import condition_to_set

    converted = condition_to_set(condition, var)
    if converted is not None:
        return converted
    try:
        return sp.solveset(condition, var, domain=S.Reals)
    except SYMBOLIC_QUERY_ERRORS:
        return None


def _function_continuous_impl(
    expr,
    var,
    *,
    domain=S.Reals,
    assumptions=S.true,
    return_result=False,
    _domain_ready=False,
):
    """Test continuity on the function's natural real domain by default."""
    expr = sp.sympify(expr)
    vv = _variable_tuple(var)
    if len(vv) > 1:
        val = _multivariate_structural_continuity(expr, vv)
        result = PropertyResult(val, source="multivariate-structural-continuity")
        return result if return_result else val
    var = vv[0]
    domain_cond = (
        sp.sympify(domain)
        if _domain_ready
        else (
            _real_domain_condition(expr, var)
            if domain in (S.Reals, "real", "reals", "R", "RR")
            else (
                domain.as_relational(var)
                if isinstance(domain, sp.Set)
                else sp.sympify(domain)
            )
        )
    )
    if not _domain_ready and domain_cond is not None:
        split = evaluate_parameter_strata(
            domain_cond,
            var,
            lambda branch_domain: _function_continuous_impl(
                expr,
                var,
                domain=branch_domain,
                assumptions=assumptions,
                return_result=return_result,
                _domain_ready=True,
            ),
            source="continuity-parameter-stratification",
        )
        if split is not None:
            return split
    discontinuities = _function_discontinuity_records(
        expr, var, assumptions=assumptions
    )
    actual = []
    uncertain = []
    for d in discontinuities:
        hit = _condition_intersects_domain(
            And(d.condition, d.guard), domain_cond, assumptions
        )
        if hit is True:
            actual.append(d)
        elif hit is None:
            uncertain.append(d)
    if actual:
        result = PropertyResult(
            Continuity.DISCONTINUOUS,
            exceptions=tuple(actual),
            source="discontinuity-analysis",
        )
        return result if return_result else result.primary
    if isinstance(expr, sp.Piecewise) and not uncertain:
        from .real_analysis.piecewise import piecewise_branches

        branches = piecewise_branches(expr, var, domain_cond)
        branch_values = [
            _function_continuous_impl(
                branch.expression,
                var,
                domain=branch.condition,
                assumptions=assumptions,
                _domain_ready=True,
            )
            for branch in branches
            if branch.expression.has(var)
        ]
        if all(v == Continuity.CONTINUOUS for v in branch_values):
            return (
                PropertyResult(Continuity.CONTINUOUS, source="piecewise-analysis")
                if return_result
                else Continuity.CONTINUOUS
            )
    natural_set = _condition_to_set(domain_cond, var)
    if natural_set is not None:
        try:
            cset = continuous_domain(expr, var, S.Reals)
            if cset == natural_set:
                return (
                    PropertyResult(
                        Continuity.CONTINUOUS, source="sympy.continuous_domain"
                    )
                    if return_result
                    else Continuity.CONTINUOUS
                )
            missing = natural_set - cset
            if missing is not S.EmptySet and missing != S.EmptySet:
                result = PropertyResult(
                    Continuity.DISCONTINUOUS,
                    exceptions=(missing,),
                    source="sympy.continuous_domain",
                )
                return result if return_result else result.primary
        except NotImplementedError:
            pass
        except SYMBOLIC_QUERY_ERRORS:
            pass

    # Analytic functions are continuous on their real analytic domain.
    analytic = function_analytic(expr, var, domain=domain, assumptions=assumptions)
    if analytic == Analyticity.ANALYTIC:
        return (
            PropertyResult(Continuity.CONTINUOUS, source="analyticity")
            if return_result
            else Continuity.CONTINUOUS
        )
    if expr.func is sp.Abs:
        return (
            PropertyResult(Continuity.CONTINUOUS, source="Abs")
            if return_result
            else Continuity.CONTINUOUS
        )
    return (
        PropertyResult(Continuity.UNKNOWN, source="insufficient-evidence")
        if return_result
        else Continuity.UNKNOWN
    )


# ---------------------------------------------------------------------------
# Structural singularity traversal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SingularityAnalysis:
    branch_cuts: tuple[Singularity, ...] = ()
    definition_cuts: tuple[Singularity, ...] = ()
    poles: tuple[Singularity, ...] = ()
    essential: tuple[Singularity, ...] = ()
    branch_points: tuple[Singularity, ...] = ()
    removable: tuple[Singularity, ...] = ()
    discontinuities: tuple[Singularity, ...] = ()
    domain_exterior: sp.Basic = S.false
    complete: bool = False
    unknown_heads: tuple[str, ...] = ()
    source: str = "structural-singularity-traversal"

    def all_records(self):
        return _unique(
            self.branch_cuts
            + self.definition_cuts
            + self.poles
            + self.essential
            + self.branch_points
            + self.removable
            + self.discontinuities
        )

    def condition(self):
        conds = []
        if self.domain_exterior is not S.false:
            conds.append(self.domain_exterior)
        for s in self.all_records():
            conds.append(And(s.condition, s.guard))
        return Or(*conds) if conds else S.false


def _conditioned(records, cond):
    if cond is S.true:
        return tuple(records)
    out = []
    for r in records:
        g = simplify_condition(And(r.guard, cond))
        if g is not S.false:
            out.append(Singularity(r.kind, r.condition, g, r.multiplicity, r.source))
    return tuple(out)


def _domain_exterior_condition(expr, var, real=True):
    """Boundary/exterior contribution of the supported natural domain."""
    try:
        from .api import function_domain

        d = function_domain(expr, var, domain=S.Reals if real else S.Complexes)
    except SYMBOLIC_QUERY_ERRORS:
        return None
    if isinstance(d, PropertyResult):
        return None
    d = sp.sympify(d)
    if d is S.true:
        return S.false
    if d is S.false:
        return S.true
    try:
        return sp.simplify_logic(sp.Not(d))
    except SYMBOLIC_QUERY_ERRORS:
        return sp.Not(d)


def _primitive_known(expr, var):
    if expr.is_Atom:
        return True
    if expr.is_Add or expr.is_Mul or isinstance(expr, (sp.Pow, sp.Piecewise)):
        return True
    if expr.func in (
        sp.exp,
        sp.log,
        sp.sin,
        sp.cos,
        sp.tan,
        sp.cot,
        sp.sinh,
        sp.cosh,
        sp.tanh,
        sp.asin,
        sp.acos,
        sp.atan,
        sp.asinh,
        sp.acosh,
        sp.atanh,
        sp.Abs,
        sp.sign,
        sp.erf,
        sp.erfc,
        sp.LambertW,
        sp.besselj,
        sp.bessely,
        sp.gamma,
    ):
        return True
    try:
        fam = evaluate_property(expr, "LocallyAnalytic", var=var, mode="complex")
        if fam.primary is not None or fam.cases:
            return True
    except SYMBOLIC_QUERY_ERRORS:
        pass
    return False


def _function_singularity_analysis_impl(
    expr, var, *, domain=S.Complexes, assumptions=S.true, ignore_unknown=False
):
    """Traverse an expression and return a typed, condition-aware singularity certificate.

    Unlike :func:`function_singularities`, this records whether traversal was
    complete, preserves Piecewise branch guards, includes natural-domain
    exterior conditions, and promotes poles of an inner expression to
    essential singularities when composed through a transcendental entire
    function with an essential singularity at infinity.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    complex_mode = domain in (S.Complexes, "complex", "complexes", "C", "CC")
    bc = []
    dc = []
    po = []
    es = []
    bp = []
    rm = []
    di = []
    unknown = []
    transcendental_entire = {sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh, sp.erf, sp.erfc}

    def visit(e, guard=S.true, inside_essential=False):
        if not getattr(e, "has", lambda *_: False)(var):
            return
        # Piecewise values are traversed only under their active branch guard.
        if isinstance(e, sp.Piecewise):
            covered = S.false
            for value, cond in e.args:
                active = (
                    sp.Not(covered) if cond is S.true else And(cond, sp.Not(covered))
                )
                active = simplify_condition(And(guard, active), assumptions=assumptions)
                if active is not S.false:
                    visit(value, active, inside_essential)
                covered = Or(covered, cond)
            for boundary in _piecewise_boundaries(e):
                dc.append(
                    Singularity(
                        SingularityKind.DEFINITION_CUT,
                        boundary,
                        guard,
                        source="piecewise-boundary",
                    )
                )
                verdict = _piecewise_discontinuous_at(e, var, boundary)
                if verdict is not False:
                    di.append(
                        Singularity(
                            SingularityKind.DISCONTINUITY,
                            boundary,
                            guard,
                            source="piecewise-boundary",
                        )
                    )
            return

        # Collect local information at this node, but condition it by traversal guard.
        if e.is_Function or isinstance(e, sp.Pow):
            if complex_mode:
                bc.extend(
                    _conditioned(
                        function_branchcuts(
                            e, var, assumptions=assumptions, mode="records"
                        ),
                        guard,
                    )
                )
                bp.extend(
                    _conditioned(
                        _function_branchpoint_records(e, var, assumptions=assumptions),
                        guard,
                    )
                )
            dc.extend(
                _conditioned(
                    function_definition_cuts(
                        e,
                        var,
                        mode="complex" if complex_mode else "real",
                        assumptions=assumptions,
                    ),
                    guard,
                )
            )
            localp = _conditioned(
                _function_pole_records(e, var, assumptions=assumptions), guard
            )
            if inside_essential:
                es.extend(
                    Singularity(
                        SingularityKind.ESSENTIAL,
                        p.condition,
                        p.guard,
                        p.multiplicity,
                        "outer-essential-at-infinity",
                    )
                    for p in localp
                )
            else:
                po.extend(localp)
            es.extend(
                _conditioned(
                    function_essential_singularities(e, var, assumptions=assumptions),
                    guard,
                )
            )
            rm.extend(_conditioned(function_removable_singularities(e, var), guard))
            if not complex_mode:
                di.extend(
                    _conditioned(
                        _function_discontinuity_records(
                            e, var, assumptions=assumptions
                        ),
                        guard,
                    )
                )
            if not _primitive_known(e, var):
                unknown.append(getattr(e.func, "__name__", str(e.func)))
                if not ignore_unknown:
                    return

        outer_essential = inside_essential or (
            getattr(e, "func", None) in transcendental_entire
        )
        args = (
            [v for v, _ in e.args]
            if isinstance(e, sp.Piecewise)
            else getattr(e, "args", ())
        )
        for a in args:
            if getattr(a, "has", lambda *_: False)(var):
                visit(a, guard, outer_essential)

    visit(expr)
    dex = _domain_exterior_condition(expr, var, not complex_mode)
    complete = dex is not None and (ignore_unknown or not unknown)
    return SingularityAnalysis(
        branch_cuts=_unique(bc),
        definition_cuts=_unique(dc),
        poles=_unique(po),
        essential=_unique(es),
        branch_points=_unique(bp),
        removable=_unique(rm),
        discontinuities=_unique(di),
        domain_exterior=S.false if dex is None else dex,
        complete=complete,
        unknown_heads=tuple(sorted(set(unknown))),
    )


def function_singularity_analysis(
    expr, var, *, domain=S.Complexes, assumptions=S.true, ignore_unknown=False
):
    """Cached aggregate singularity analysis with assumptions in the cache key."""
    from .proof_cache import property_proof_context

    return property_proof_context(expr, var, assumptions=assumptions).singularities(
        domain=domain, ignore_unknown=ignore_unknown
    )


def function_analytic(
    expr, var, *, domain=S.Reals, assumptions=S.true, return_result=False
):
    """Classify analyticity on the requested domain."""
    return _function_analytic_impl(
        expr,
        var,
        domain=domain,
        assumptions=assumptions,
        return_result=return_result,
        _domain_ready=False,
    )


def function_continuous(
    expr, var, *, domain=S.Reals, assumptions=S.true, return_result=False
):
    """Classify continuity on the requested domain."""
    return _function_continuous_impl(
        expr,
        var,
        domain=domain,
        assumptions=assumptions,
        return_result=return_result,
        _domain_ready=False,
    )
