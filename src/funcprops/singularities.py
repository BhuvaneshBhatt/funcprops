"""Structural singularity, branch, analyticity and continuity analysis."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import sympy as sp
from sympy import S
from sympy.calculus.util import continuous_domain
from sympy.core.relational import Relational
from sympy.logic.boolalg import And, Boolean, Or

from .engine import evaluate_property, simplify_condition
from .exceptions import SYMBOLIC_QUERY_ERRORS
from .results import (
    Analyticity,
    ConditionalValue,
    Continuity,
    Meromorphicity,
    PropertyResult,
    Singularity,
    SingularityKind,
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
    """Split a condition into variable-locus and parameter-only parts."""
    c = sp.sympify(condition)
    if c in (S.true, S.false):
        return c, S.true
    if c.func is And:
        locus = []
        guard = []
        for atom in c.args:
            (locus if atom.has(var) else guard).append(atom)
        lc = And(*locus) if locus else S.true
        gd = And(*guard) if guard else S.true
        return simplify_condition(lc, assumptions=assumptions), simplify_condition(
            gd, assumptions=assumptions
        )
    if c.has(var):
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
            out.extend(function_poles(arg, var, assumptions=assumptions))
        elif kind is SingularityKind.BRANCH_POINT:
            out.extend(function_branchpoints(arg, var, assumptions=assumptions))
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

    This is intentionally internal for now; ``function_singularities`` exposes
    the records under its ``removable`` key without adding another top-level
    public function.
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


def function_poles(expr, var, *, assumptions=S.true):
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


def function_branchpoints(expr, var, *, assumptions=S.true):
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
                    for pole in function_poles(arg, var, assumptions=assumptions):
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
            if sp.simplify(left - right) != 0 or sp.simplify(value - left) != 0:
                return True
        except SYMBOLIC_QUERY_ERRORS:
            any_unknown = True
    return None if any_unknown else False


def function_discontinuities(expr, var, *, assumptions=S.true):
    """Return unsolved real discontinuity conditions."""
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    out = []
    if expr.is_Function:
        r = evaluate_property(expr, "Discontinuities", var=var, assumptions=assumptions)
        for case in r.cases:
            value = case.value
            if _is_empty(value):
                continue
            entries = (
                tuple(value) if isinstance(value, (sp.Tuple, tuple, list)) else (value,)
            )
            for entry in entries:
                cond = (
                    entry[0]
                    if isinstance(entry, (sp.Tuple, tuple, list)) and entry
                    else entry
                )
                out.append(
                    Singularity(
                        SingularityKind.DISCONTINUITY,
                        sp.sympify(cond),
                        case.condition,
                        source="registry",
                    )
                )
    if isinstance(expr, sp.Piecewise):
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
            out.extend(function_discontinuities(arg, var, assumptions=assumptions))
    return _unique(out)


def function_singularities(expr, var, *, domain=S.Complexes, assumptions=S.true):
    """Return all known singularity loci without solving their equations."""
    complex_mode = domain in (S.Complexes, "complex", "complexes", "C", "CC")
    result = {
        "poles": function_poles(expr, var, assumptions=assumptions),
        "removable": function_removable_singularities(expr, var),
        "essential": function_essential_singularities(
            expr, var, assumptions=assumptions
        ),
        "branch_points": function_branchpoints(expr, var, assumptions=assumptions),
        "branch_cuts": function_branchcuts(
            expr, var, assumptions=assumptions, mode="records"
        )
        if complex_mode
        else (),
        "definition_cuts": function_definition_cuts(
            expr,
            var,
            mode="complex" if complex_mode else "real",
            assumptions=assumptions,
        ),
    }
    if not complex_mode:
        result["discontinuities"] = function_discontinuities(
            expr, var, assumptions=assumptions
        )
    return result


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


def function_analytic(
    expr,
    var,
    *,
    domain=S.Reals,
    assumptions=S.true,
    details=False,
    _domain_ready=False,
):
    """Classify real analyticity by default, holomorphy for Complexes."""
    expr = sp.sympify(expr)
    vv = _variable_tuple(var)
    is_complex = domain in (S.Complexes, "complex", "complexes", "C", "CC")
    if len(vv) > 1:
        val = _multivariate_structural_analytic(expr, vv, complex_mode=is_complex)
        result = PropertyResult(val, source="multivariate-structural-analyticity")
        return result if details else val
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
        # "Analytic" means holomorphic on the function's natural complex
        # domain, matching the source LocallyAnalytic property.
        if expr.func in (sp.Abs, sp.sign, sp.floor, sp.ceiling) or isinstance(
            expr, sp.Piecewise
        ):
            result = PropertyResult(
                Analyticity.NOT_ANALYTIC, source="nonholomorphic-head"
            )
            return result if details else result.primary
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
            terminating = any(
                a.is_integer is True and a.is_nonpositive is True for a in aa
            )
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
                return result if details else result.primary
        local = evaluate_property(
            expr, "LocallyAnalytic", mode="complex", var=var, assumptions=assumptions
        )
        local_status = _conditional_boolean_status(local)
        if local_status is False:
            return (
                PropertyResult(Analyticity.NOT_ANALYTIC, source="registry")
                if details
                else Analyticity.NOT_ANALYTIC
            )
        if local_status is True:
            return (
                PropertyResult(Analyticity.ANALYTIC, source="registry")
                if details
                else Analyticity.ANALYTIC
            )
        entire = evaluate_property(
            expr, "Entire", mode="complex", var=var, assumptions=assumptions
        )
        if _conditional_boolean_status(entire) is True or expr.is_polynomial(var):
            return (
                PropertyResult(Analyticity.ANALYTIC, source="analytic-primitive")
                if details
                else Analyticity.ANALYTIC
            )
        # Arithmetic closure is valid without needing a primitive function
        # theorem.  Do not apply generic composition closure to an unknown head.
        if (
            expr.is_Add
            or expr.is_Mul
            or (isinstance(expr, sp.Pow) and expr.exp.is_integer)
        ):
            vals = [
                function_analytic(a, var, domain=S.Complexes, assumptions=assumptions)
                for a in expr.args
                if a.has(var)
            ]
            if vals and all(v == Analyticity.ANALYTIC for v in vals):
                return (
                    PropertyResult(Analyticity.ANALYTIC, source="holomorphic-closure")
                    if details
                    else Analyticity.ANALYTIC
                )
            if any(v == Analyticity.NOT_ANALYTIC for v in vals):
                return (
                    PropertyResult(
                        Analyticity.NOT_ANALYTIC, source="holomorphic-closure"
                    )
                    if details
                    else Analyticity.NOT_ANALYTIC
                )
        return (
            PropertyResult(Analyticity.UNKNOWN, source="insufficient-evidence")
            if details
            else Analyticity.UNKNOWN
        )

    # Real analyticity on the requested/natural real domain.
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
            lambda branch_domain: function_analytic(
                expr,
                var,
                domain=branch_domain,
                assumptions=assumptions,
                details=details,
                _domain_ready=True,
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
            return result if details else result.primary
        if unknown_cut:
            result = PropertyResult(
                Analyticity.UNKNOWN,
                exceptions=cuts,
                source="conditional-nonsmooth-cuts",
            )
            return result if details else result.primary
        # Abs/sign/floor/ceiling are locally analytic on every real component
        # that excludes their kink/jump lattice.  This matters for restricted
        # domains such as Abs(x) on x>0.
        result = PropertyResult(Analyticity.ANALYTIC, source="nonsmooth-head-off-cuts")
        return result if details else result.primary
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
            return result if details else result.primary
        if unknown_boundary:
            return (
                PropertyResult(Analyticity.UNKNOWN, source="piecewise-boundary-unknown")
                if details
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
        return result if details else result.primary
    if unknown:
        return (
            PropertyResult(
                Analyticity.UNKNOWN,
                exceptions=cuts,
                source="conditional-definition-cuts",
            )
            if details
            else Analyticity.UNKNOWN
        )

    # Composition theorem: analytic primitives composed with analytic arguments.
    for arg in getattr(expr, "args", ()):
        if arg.has(var) and arg != var:
            a = function_analytic(arg, var, domain=S.Reals, assumptions=assumptions)
            if a == Analyticity.NOT_ANALYTIC:
                return (
                    PropertyResult(Analyticity.NOT_ANALYTIC, source="composition")
                    if details
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
        return PropertyResult(val, source="registry+composition") if details else val
    if expr.is_rational_function(var) and not cuts:
        return (
            PropertyResult(Analyticity.ANALYTIC, source="rational")
            if details
            else Analyticity.ANALYTIC
        )
    if expr.is_Add or expr.is_Mul or (isinstance(expr, sp.Pow) and expr.exp.is_integer):
        vals = [
            function_analytic(a, var, domain=S.Reals, assumptions=assumptions)
            for a in expr.args
            if a.has(var)
        ]
        if vals and all(v == Analyticity.ANALYTIC for v in vals):
            return (
                PropertyResult(Analyticity.ANALYTIC, source="analytic-closure")
                if details
                else Analyticity.ANALYTIC
            )
        if any(v == Analyticity.NOT_ANALYTIC for v in vals):
            return (
                PropertyResult(Analyticity.NOT_ANALYTIC, source="analytic-closure")
                if details
                else Analyticity.NOT_ANALYTIC
            )
    return (
        PropertyResult(Analyticity.UNKNOWN, source="insufficient-evidence")
        if details
        else Analyticity.UNKNOWN
    )


def function_meromorphic(expr, var, *, assumptions=S.true, details=False):
    """Classify meromorphicity on the complex plane/natural complex domain."""
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if expr.is_rational_function(var):
        return (
            PropertyResult(Meromorphicity.MEROMORPHIC, source="rational")
            if details
            else Meromorphicity.MEROMORPHIC
        )
    branch = function_branchpoints(expr, var, assumptions=assumptions)
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
        return result if details else result.primary
    if conditional:
        bad_guard = simplify_condition(
            Or(*[item.guard for item in conditional]), assumptions=assumptions
        )
        cases = (
            ConditionalValue(Meromorphicity.NOT_MEROMORPHIC, bad_guard),
            ConditionalValue(Meromorphicity.MEROMORPHIC, sp.Not(bad_guard)),
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
            if details
            else Meromorphicity.MEROMORPHIC
        )
    if reg.primary is S.false:
        return (
            PropertyResult(Meromorphicity.NOT_MEROMORPHIC, source="registry")
            if details
            else Meromorphicity.NOT_MEROMORPHIC
        )
    entire = evaluate_property(expr, "Entire", mode="complex", assumptions=assumptions)
    if entire.primary is S.true:
        return (
            PropertyResult(Meromorphicity.MEROMORPHIC, source="entire")
            if details
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
            if details
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
                if details
                else Meromorphicity.MEROMORPHIC
            )
        if any(v == Meromorphicity.NOT_MEROMORPHIC for v in vals):
            return (
                PropertyResult(Meromorphicity.NOT_MEROMORPHIC, source="closure")
                if details
                else Meromorphicity.NOT_MEROMORPHIC
            )
    return (
        PropertyResult(Meromorphicity.UNKNOWN, source="insufficient-evidence")
        if details
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


def function_continuous(
    expr,
    var,
    *,
    domain=S.Reals,
    assumptions=S.true,
    details=False,
    _domain_ready=False,
):
    """Test continuity on the function's natural real domain by default."""
    expr = sp.sympify(expr)
    vv = _variable_tuple(var)
    if len(vv) > 1:
        val = _multivariate_structural_continuity(expr, vv)
        result = PropertyResult(val, source="multivariate-structural-continuity")
        return result if details else val
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
            lambda branch_domain: function_continuous(
                expr,
                var,
                domain=branch_domain,
                assumptions=assumptions,
                details=details,
                _domain_ready=True,
            ),
            source="continuity-parameter-stratification",
        )
        if split is not None:
            return split
    discontinuities = function_discontinuities(expr, var, assumptions=assumptions)
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
        return result if details else result.primary
    if isinstance(expr, sp.Piecewise) and not uncertain:
        from .real_analysis.piecewise import piecewise_branches

        branches = piecewise_branches(expr, var, domain_cond)
        branch_values = [
            function_continuous(
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
                if details
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
                    if details
                    else Continuity.CONTINUOUS
                )
            missing = natural_set - cset
            if missing is not S.EmptySet and missing != S.EmptySet:
                result = PropertyResult(
                    Continuity.DISCONTINUOUS,
                    exceptions=(missing,),
                    source="sympy.continuous_domain",
                )
                return result if details else result.primary
        except NotImplementedError:
            pass
        except SYMBOLIC_QUERY_ERRORS:
            pass

    # Analytic functions are continuous on their real analytic domain.
    analytic = function_analytic(expr, var, domain=domain, assumptions=assumptions)
    if analytic == Analyticity.ANALYTIC:
        return (
            PropertyResult(Continuity.CONTINUOUS, source="analyticity")
            if details
            else Continuity.CONTINUOUS
        )
    if expr.func is sp.Abs:
        return (
            PropertyResult(Continuity.CONTINUOUS, source="Abs")
            if details
            else Continuity.CONTINUOUS
        )
    return (
        PropertyResult(Continuity.UNKNOWN, source="insufficient-evidence")
        if details
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
                        function_branchpoints(e, var, assumptions=assumptions), guard
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
                function_poles(e, var, assumptions=assumptions), guard
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
                        function_discontinuities(e, var, assumptions=assumptions), guard
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
