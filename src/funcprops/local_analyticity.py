"""Shared sufficient complex-germ rules and exact essential-series families."""

from functools import lru_cache

import sympy as sp

from .source_syntax import finite_constant_source, logarithm_quotient

ENTIRE_FUNCTIONS = frozenset(
    (sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh, sp.erf, sp.erfc, sp.erfi)
)


def _declared_meromorphic(expression, variable, point):
    """Compose declared entire families only with finite analytic arguments."""
    if expression.is_meromorphic(variable, point) is True:
        return True
    if expression.is_Add or expression.is_Mul:
        return all(
            _declared_meromorphic(arg, variable, point) for arg in expression.args
        )
    if expression.func in ENTIRE_FUNCTIONS:
        for argument in expression.args:
            if not _declared_meromorphic(argument, variable, point):
                return False
            value = sp.simplify(argument.subs(variable, point))
            if value.is_finite is not True:
                value = sp.limit(argument, variable, point)
            if value.is_finite is not True:
                return False
        return True
    if expression.is_Pow:
        if not _declared_meromorphic(expression.base, variable, point):
            return False
        if expression.exp.is_Integer is True:
            if expression.exp.is_nonnegative is True:
                return True
            u = sp.Dummy("declared_leading_coordinate", complex=True)
            leading = expression.base.subs(variable, u + point).as_leading_term(u)
            coefficient, exponent = leading.as_coeff_exponent(u)
            return (
                coefficient.is_zero is False
                and coefficient.is_finite is True
                and not coefficient.has(u)
                and exponent.is_Integer is True
            )
        return (
            expression.exp.is_finite is True
            and not expression.exp.has(variable)
            and _principal_branches_local(expression, variable, point)
        )
    if expression.func is sp.log:
        return _declared_meromorphic(
            expression.args[0], variable, point
        ) and _principal_branches_local(expression, variable, point)
    return False


def _punctured_source_defined(
    expression, variable, point, *, allow_branch_points=False
):
    """Sufficient raw-source definition on some punctured disk at point."""
    axis = sp.Dummy("punctured_coordinate", complex=True)

    def nonzero_germ(value):
        normalized = sp.simplify(value.xreplace({variable: axis + point}))
        if not _declared_meromorphic(normalized, axis, sp.S.Zero):
            return False
        leading = normalized.as_leading_term(axis)
        coefficient, exponent = leading.as_coeff_exponent(axis)
        return (
            not coefficient.has(axis)
            and coefficient.is_finite is True
            and coefficient.is_zero is False
            and exponent.is_Integer is True
        )

    def defined(node):
        if node == variable:
            return True
        if node.func is sp.log and len(node.args) == 2:
            return defined(logarithm_quotient(node))
        if not node.has(variable):
            return finite_constant_source(node)
        if node.is_Add or node.is_Mul:
            return all(defined(arg) for arg in node.args)
        if node.is_Pow:
            if (
                not defined(node.base)
                or node.exp.has(variable)
                or not finite_constant_source(node.exp)
            ):
                return False
            if node.exp.is_Integer is True:
                return node.exp.is_nonnegative is True or nonzero_germ(node.base)
            # Classification can admit a branch point at the center, while
            # local meromorphic-germ consumers still require a regular branch.
            # Both need the original base to have no accumulating source holes.
            return (
                allow_branch_points
                or _declared_meromorphic(node.xreplace({variable: axis}), axis, point)
            ) and nonzero_germ(node.base)
        if node.func in ENTIRE_FUNCTIONS:
            return all(defined(arg) for arg in node.args)
        if node.func is sp.log:
            return defined(node.args[0]) and nonzero_germ(node.args[0])
        return False

    return defined(expression)


def _principal_branches_local(expression, variable, point):
    """Require a neighborhood avoiding principal Log/power cuts.

    Meromorphic continuation of a chosen branch is a different theorem from
    local analyticity of the principal expression supplied by the caller.
    """
    for node in sp.preorder_traversal(expression):
        base = (
            node.args[0]
            if node.func is sp.log
            else node.base
            if isinstance(node, sp.Pow) and node.exp.is_integer is not True
            else None
        )
        if base is None or not node.has(variable):
            continue
        value = sp.simplify(base.subs(variable, point))
        if value.is_finite is not True or not (
            sp.im(value).is_zero is False or sp.re(value).is_positive is True
        ):
            return False
    return True


@lru_cache(maxsize=256)
def complex_meromorphic_germ(expression, variable, point):
    """Construct supported exact local Laurent data while preserving source definition."""

    expression, variable, point = map(sp.sympify, (expression, variable, point))
    if (
        not isinstance(variable, sp.Symbol)
        or point.has(variable)
        or point.is_finite is not True
        or point.has(sp.Float)
        or expression.has(sp.Float)
        or expression.has(sp.oo, -sp.oo, sp.zoo, sp.nan)
    ):
        return False
    axis = sp.Dummy("germ_coordinate", complex=True)
    try:
        normalized = sp.simplify(expression.xreplace({variable: axis}))
        return (
            _punctured_source_defined(expression, variable, point)
            and _principal_branches_local(normalized, axis, point)
            and _declared_meromorphic(normalized, axis, point)
        )
    except (AttributeError, TypeError, ValueError, NotImplementedError):
        return False


def essential_laurent_data(expression, variable, point):
    """Exact Laurent sums/residues for finite sums c*u**k*exp(a/u**m).

    The exponential series converges normally on every compact annulus about
    u=0. This proves a punctured-neighborhood Laurent expansion independently
    of directional series output. Coefficients must be finite constants.
    """
    if (
        not isinstance(variable, sp.Symbol)
        or point.has(variable)
        or point.is_finite is not True
        or point.has(sp.Float)
        or expression.has(sp.Float)
        or expression.has(sp.oo, -sp.oo, sp.zoo, sp.nan)
    ):
        return None
    u = sp.Dummy("essential_coordinate", complex=True)
    # Check raw syntax before substitution/rebuilding can erase a dense or
    # accumulating set of source holes. Only monomial poles at this center are
    # admitted by the punctured-neighborhood family theorem.
    for node in sp.preorder_traversal(expression):
        if not node.has(variable) and not finite_constant_source(node):
            return None
        if (
            isinstance(node, sp.Function)
            and node.has(variable)
            and node.func is not sp.exp
        ):
            return None
        if isinstance(node, sp.Pow) and node.base.has(variable):
            if node.exp.is_Integer is not True:
                return None
            if node.exp.is_negative is True:
                base = sp.expand(node.base.xreplace({variable: u + point}))
                coefficient, power = base.as_coeff_exponent(u)
                if (
                    coefficient.has(u)
                    or coefficient.is_finite is not True
                    or coefficient.is_zero is not False
                    or power.is_Integer is not True
                ):
                    return None
    f = sp.expand(expression.xreplace({variable: u + point}))
    series, residue = [], sp.S.Zero
    for term in sp.Add.make_args(f):
        atoms = tuple(a for a in term.atoms(sp.exp) if a.has(u))
        if len(atoms) != 1:
            return None
        atom = atoms[0]
        coefficient, k = sp.cancel(term / atom).as_coeff_exponent(u)
        a, power = atom.args[0].as_coeff_exponent(u)
        if (
            coefficient.has(u)
            or coefficient.is_finite is not True
            or k.is_Integer is not True
            or a.has(u)
            or a.is_finite is not True
            or power.is_Integer is not True
            or power.is_negative is not True
        ):
            return None
        m = -power
        n = sp.Dummy("laurent_index", integer=True, nonnegative=True)
        series.append(
            coefficient
            * sp.Sum(
                a**n / sp.factorial(n) * (variable - point) ** (k - m * n),
                (n, 0, sp.oo),
            )
        )
        index = (k + 1) / m
        if index.is_Integer is True and index.is_nonnegative is True:
            residue += coefficient * a**index / sp.factorial(index)
    return sp.Add(*series), sp.simplify(residue)


def _set_difference(region, removed):
    if isinstance(removed, sp.Complement) and removed.args[0] == region:
        return sp.Intersection(region, removed.args[1])
    return sp.Complement(region, removed)


def _set_union(parts):
    # SymPy does not always reduce (Complexes \ F) union F, even for finite F.
    # Apply the identity only after both inclusions have been proved exactly.
    for part in parts:
        if isinstance(part, sp.Complement):
            universe, excluded = part.args
            rest = sp.Union(*(p for p in parts if p != part))
            if excluded.is_subset(rest) is True and rest.is_subset(universe) is True:
                return universe
    return sp.Union(*parts)


def complex_definition_domain(expression, variable, domain, *, _branch_cells=None):
    """Exact definition set for finite elementary syntax and Eq/Ne partitions.

    Ordering guards on the complex plane and unresolved zero sets decline.
    Conditions must themselves be defined where evaluated, before first-match
    branch ownership is assigned.
    """
    axis = sp.Dummy("complex_definition_coordinate")

    def zero_set(value, region):
        roots = sp.solveset(value.xreplace({variable: axis}), axis, domain=region)
        return None if roots.has(sp.ConditionSet) else roots

    def guard_set(condition, region):
        if condition is sp.S.true:
            return region
        if condition is sp.S.false:
            return sp.S.EmptySet
        if isinstance(condition, (sp.Equality, sp.Unequality)):
            if any(
                defined(arg, region) != region for arg in (condition.lhs, condition.rhs)
            ):
                return None
            roots = zero_set(condition.lhs - condition.rhs, region)
            if roots is None:
                return None
            return (
                roots
                if isinstance(condition, sp.Equality)
                else sp.Complement(region, roots)
            )
        if isinstance(condition, (sp.And, sp.Or)):
            parts = [guard_set(arg, region) for arg in condition.args]
            if any(part is None for part in parts):
                return None
            return (sp.Intersection if isinstance(condition, sp.And) else sp.Union)(
                *parts
            )
        return None

    def defined(node, region):
        if region is sp.S.EmptySet:
            return region
        if node == variable:
            return region
        if node.func is sp.log and len(node.args) == 2:
            return defined(logarithm_quotient(node), region)
        if not node.has(variable):
            return region if finite_constant_source(node) else None
        if isinstance(node, sp.Piecewise):
            remaining, pieces = region, []
            for branch, guard in node.args:
                if remaining is sp.S.EmptySet:
                    break
                active = guard_set(guard, remaining)
                if active is None:
                    return None
                branch_domain = defined(branch, active)
                if branch_domain is None:
                    return None
                pieces.append(branch_domain)
                if node is expression and _branch_cells is not None:
                    _branch_cells.append((branch, branch_domain))
                remaining = _set_difference(remaining, active)
            return _set_union(pieces)
        if node.is_Add or node.is_Mul:
            parts = [defined(arg, region) for arg in node.args]
            return (
                None if any(part is None for part in parts) else sp.Intersection(*parts)
            )
        if node.is_Pow:
            if node.exp.has(variable) or not finite_constant_source(node.exp):
                return None
            base_domain = defined(node.base, region)
            if base_domain is None:
                return None
            if node.exp.is_nonnegative is True:
                return base_domain
            zeros = zero_set(node.base, base_domain)
            return None if zeros is None else sp.Complement(base_domain, zeros)
        if node.func in ENTIRE_FUNCTIONS | {sp.Abs, sp.conjugate, sp.re, sp.im}:
            return defined(node.args[0], region)
        if node.func is sp.log:
            base_domain = defined(node.args[0], region)
            if base_domain is None:
                return None
            zeros = zero_set(node.args[0], base_domain)
            return None if zeros is None else sp.Complement(base_domain, zeros)
        return None

    try:
        return defined(expression, domain)
    except (
        AttributeError,
        TypeError,
        ValueError,
        NotImplementedError,
        ArithmeticError,
    ):
        return None
