"""Source-bound domain provenance for supported real expressions.

Unknown domains are retained as unknown, never replaced with the real line.
"""

from dataclasses import dataclass

import sympy as sp

from .exactness import certify_zero
from .source_syntax import (
    differentiate,
    finite_constant_source,
    logarithm_quotient,
    normalize_arithmetic,
)
from .work_budget import budgeted_operation


@dataclass(frozen=True)
class DomainRecord:
    """Preserve requested, natural and effective domains with raw source restrictions."""

    expression: sp.Expr
    variable: sp.Symbol
    requested: object
    natural: sp.Set | None
    effective: sp.Set | None
    complete: bool
    exclusions: tuple = ()
    reason: str | None = None
    natural_complete: bool = True

    @property
    def certified(self):
        return self.complete is True and self.verify()

    @property
    def scope(self):
        return "real-definition-domain"

    def matches(self, other):
        """Compare provenance allowing alpha-renaming of bound set indices."""
        if not isinstance(other, DomainRecord) or type(self.complete) is not bool:
            return False

        def same_set(a, b):
            return a == b or (
                isinstance(a, sp.Set) and isinstance(b, sp.Set) and a.dummy_eq(b)
            )

        return (
            self.expression == other.expression
            and self.variable == other.variable
            and self.requested == other.requested
            and self.complete is other.complete
            and self.exclusions == other.exclusions
            and self.reason == other.reason
            and self.natural_complete is other.natural_complete
            and same_set(self.natural, other.natural)
            and same_set(self.effective, other.effective)
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                any(guard is sp.S.false for guard in self.exclusions)
                and self.effective is not sp.S.EmptySet
            ):
                return False
            return self.complete is True and self.matches(
                track_domain(self.expression, self.variable, self.requested)
            )
        except (AttributeError, TypeError, ValueError, NotImplementedError):
            return False


def _parameter_guard_safe(base, variable):
    """Do not ask an unguarded set solver to divide by unknown parameters."""
    parameters = base.free_symbols - {variable}
    if not parameters:
        return True
    coefficient, dependent = base.as_independent(variable, as_Add=False)
    if (
        coefficient.is_finite is True
        and coefficient.is_zero is False
        and not (dependent.free_symbols - {variable})
    ):
        return True
    try:
        polynomial = sp.Poly(base, variable)
        if polynomial.degree() == 1:
            slope, offset = polynomial.all_coeffs()
            return slope.is_zero is False and all(
                c.is_finite is True and c.is_real is True for c in (slope, offset)
            )
    except (sp.PolynomialError, TypeError, ValueError):
        pass
    return False


def _domain_from_condition(expression, variable, requested, support, *, local=False):
    """Reuse structural source guards only when their real set is resolved exactly."""
    from .proof_cache import cached_domain
    from .real_analysis.common import condition_to_set
    from .results import PropertyResult

    for piecewise in expression.atoms(sp.Piecewise):
        for _branch, guard in piecewise.args:
            if any(
                isinstance(node, sp.logic.boolalg.BooleanFunction)
                and node.func not in (sp.And, sp.Or, sp.Not)
                for node in sp.preorder_traversal(guard)
            ):
                return None
    condition = cached_domain(expression, variable)
    if isinstance(condition, PropertyResult):
        return None
    natural = condition_to_set(condition, variable)
    if not isinstance(natural, sp.Set) or natural.has(sp.ConditionSet):
        return None
    return DomainRecord(
        expression,
        variable,
        requested,
        None if local else natural,
        sp.Intersection(support, natural),
        True,
        () if condition is sp.S.true else (condition,),
        natural_complete=not local,
    )


def _global_domain(expr, var, domain=sp.S.Reals):
    """Track requested, natural and effective sets before source cancellation.

    Exact natural-domain coverage supports continuous elementary expressions,
    logarithms and finite real constant powers. Discrete and unresolved domains decline.
    """
    from .real_analysis.common import condition_to_set

    f, x = sp.sympify(expr), sp.sympify(var)
    if not isinstance(x, sp.Symbol):
        raise ValueError("domain tracking requires a scalar Symbol")
    requested = domain

    def unknown(reason):
        return DomainRecord(f, x, requested, None, None, False, reason=reason)

    try:
        D = condition_to_set(sp.S.true if domain is None else domain, x)
        if not isinstance(D, sp.Set):
            return unknown("unresolved-requested-domain")
        # SymPy can compare Rational(1,10) equal to Float('0.1'), although
        # the latter's stored binary value is strictly larger. Such comparisons
        # cannot certify endpoint ownership or exact source exclusions.
        if D.has(sp.Float):
            return unknown("inexact-requested-domain")
        if f.has(sp.Float):
            return unknown("inexact-source-expression")
        if not coordinate_domain_compatible(x, D):
            return unknown("requested-domain-conflicts-with-coordinate-assumptions")
        from .real_analysis.domain import (
            _complex_intermediates,
            _function_domain_impl,
            _real_value_on_domain,
        )

        if any(
            isinstance(node, sp.Expr) and _complex_intermediates(node, x)
            for node in sp.preorder_traversal(f)
        ):
            # Real-only guards on every radical/log operand are too strong for
            # a source whose complex intermediates combine to a real value.
            # Keep the raw complex definition guards and final reality locus.
            condition = _function_domain_impl(f, x)
            if hasattr(condition, "primary"):
                if not _real_value_on_domain(f, x, D):
                    return unknown("unresolved-real-output-locus")
                condition = _function_domain_impl(f, x, domain=sp.S.Complexes)
                if hasattr(condition, "primary"):
                    return unknown("unresolved-complex-definition-domain")
                defined = condition_to_set(condition, x)
                if not isinstance(defined, sp.Set):
                    return unknown("unresolved-complex-definition-domain")
                return DomainRecord(
                    f,
                    x,
                    requested,
                    None,
                    sp.Intersection(D, defined),
                    True,
                    natural_complete=False,
                )
            natural = condition_to_set(condition, x)
            if not isinstance(natural, sp.Set) or natural.has(sp.ConditionSet):
                return unknown("unresolved-real-output-locus")
            exclusions = tuple(
                sp.Ne(node.base if isinstance(node, sp.Pow) else node.args[0], 0)
                for node in sp.preorder_traversal(f)
                if (isinstance(node, sp.Pow) and node.exp.is_negative is True)
                or node.func is sp.log
            )
            return DomainRecord(
                f, x, requested, natural, sp.Intersection(D, natural), True, exclusions
            )
        if f.has(sp.erf, sp.erfc):
            natural = _entire_composition_domain(f, x)
            if natural is None:
                return unknown("unsupported-definition-domain")
            return DomainRecord(
                f, x, requested, natural, sp.Intersection(D, natural), True
            )
        allowed = {
            sp.log,
            sp.exp,
            sp.sin,
            sp.cos,
            sp.tan,
            sp.cot,
            sp.sinh,
            sp.cosh,
            sp.tanh,
            sp.Abs,
        }
        if f.has(sp.Piecewise) or any(
            isinstance(n, sp.Function) and n.func not in allowed
            for n in sp.preorder_traversal(f)
        ):
            return unknown("unsupported-definition-domain")
        for node in sp.preorder_traversal(f):
            base = (
                node.base
                if isinstance(node, sp.Pow)
                and (node.exp.is_negative is True or node.exp.is_integer is not True)
                else node.args[0]
                if node.func is sp.log
                else None
            )
            if base is not None and not _parameter_guard_safe(base, x):
                return unknown("unresolved-parameter-domain-guard")
        nonrational_powers = tuple(
            node
            for node in sp.preorder_traversal(f)
            if isinstance(node, sp.Pow) and node.exp.is_Rational is not True
        )
        if nonrational_powers:
            if any(
                node.exp.free_symbols
                or node.exp.is_real is not True
                or node.exp.is_finite is not True
                or node.exp.is_integer is None
                for node in nonrational_powers
            ):
                return unknown("unsupported-definition-domain")
            shared = _domain_from_condition(f, x, requested, D)
            return (
                shared
                if shared is not None
                else unknown("unresolved-principal-power-domain")
            )
        axis = sp.Dummy("domain_coordinate", real=True)
        real_f = normalize_arithmetic(f).xreplace({x: axis})
        natural = sp.calculus.util.continuous_domain(real_f, axis, sp.S.Reals)
        exclusions = []
        # continuous_domain can simplify an unevaluated cancellation first.
        # Retain every negative-power base from the original syntax.
        for node in sp.preorder_traversal(f):
            if isinstance(node, sp.Function):
                node_domain = sp.calculus.util.continuous_domain(
                    normalize_arithmetic(node).xreplace({x: axis}), axis, sp.S.Reals
                )
                natural = sp.Intersection(natural, node_domain)
            if (
                isinstance(node, sp.Pow)
                and node.exp.is_Rational
                and not node.exp.is_Integer
            ):
                base = normalize_arithmetic(node.base)
                guard = base > 0 if node.exp.is_negative else base >= 0
                guard_set = condition_to_set(guard, x)
                if not isinstance(guard_set, sp.Set):
                    return unknown("unresolved-principal-power-domain")
                natural = sp.Intersection(natural, guard_set)
                exclusions.append(guard)
            if isinstance(node, sp.Pow) and node.exp.is_negative:
                guard = sp.Ne(normalize_arithmetic(node.base), 0)
                guard_set = condition_to_set(guard, x)
                if not isinstance(guard_set, sp.Set):
                    return unknown("unresolved-source-exclusion")
                natural = sp.Intersection(natural, guard_set)
                exclusions.append(guard)
            if not node.has(x):
                constant = normalize_arithmetic(node)
                if constant.is_finite is not True or constant.is_real is not True:
                    return unknown("unresolved-source-finiteness")
        # Reality must hold on the domain, not just be assumed from the API.
        # continuous_domain(log(x)) establishes the positive real branch.
        if real_f.is_real is False:
            return unknown("nonreal-output")
        if real_f.has(sp.I) and certify_zero(sp.im(real_f)) is not True:
            return unknown("unresolved-output-reality")
        effective = sp.Intersection(D, natural)
        return DomainRecord(
            f, x, requested, natural, effective, True, tuple(exclusions)
        )
    except (TypeError, ValueError, NotImplementedError, sp.PolynomialError):
        return unknown("unsupported-definition-domain")


def smooth_domain_record(expr, var, domain, order):
    """Return provenance only after proving C^order on the entire interval."""
    if type(order) is not int or order < 0 or not isinstance(domain, sp.Interval):
        return None
    record = track_domain(expr, var, domain)
    if not record.complete or record.effective != domain:
        return None
    if sp.sympify(expr).has(sp.erf, sp.erfc):
        from .coverage_checker import regular_on_cell

        return record if regular_on_cell(expr, var, domain, order) else None
    axis = sp.Dummy("smooth_coordinate", real=True)
    f = normalize_arithmetic(sp.sympify(expr)).xreplace({var: axis})
    try:
        for k in range(0, order + 1):
            if (
                sp.calculus.util.continuous_domain(
                    differentiate(f, axis, k), axis, domain
                )
                != domain
            ):
                return None
        return record
    except (TypeError, ValueError, NotImplementedError, sp.PolynomialError):
        return None


def _positive_power_coverage(f, x, domain):
    """Prove requested coverage for real constant powers; no global-domain claim."""
    from .real_analysis.common import condition_to_set

    D = condition_to_set(sp.S.true if domain is None else domain, x)
    if not isinstance(D, sp.Set) or not coordinate_domain_compatible(x, D):
        return None

    def guarded(base, relation):
        if not _parameter_guard_safe(base, x):
            return False
        guard = condition_to_set(relation(base), x)
        return isinstance(guard, sp.Set) and sp.Complement(D, guard) is sp.S.EmptySet

    def defined(node):
        if node.func is sp.log and len(node.args) == 2:
            return defined(logarithm_quotient(node))
        if not node.has(x):
            return finite_constant_source(node) and node.is_real is True
        if node == x:
            return True
        if node.is_Add or node.is_Mul:
            return all(defined(arg) for arg in node.args)
        if node.is_Pow:
            if (
                node.exp.has(x)
                or node.exp.is_real is not True
                or node.exp.is_finite is not True
                or not defined(node.base)
            ):
                return False
            if node.exp.is_integer is True:
                return node.exp.is_nonnegative is True or guarded(
                    node.base, lambda b: sp.Ne(b, 0)
                )
            # Zero belongs to the principal real domain for positive exponents.
            # An exponent with unresolved sign still requires a positive base.
            return guarded(
                node.base, lambda b: b >= 0 if node.exp.is_positive is True else b > 0
            )
        if node.func in (sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh, sp.tanh, sp.Abs):
            return all(defined(arg) for arg in node.args)
        if node.func is sp.log:
            return defined(node.args[0]) and guarded(node.args[0], lambda b: b > 0)
        return False

    if defined(f):
        return DomainRecord(f, x, domain, None, D, True, natural_complete=False)
    return None


@budgeted_operation
def track_domain(expr, var, domain=sp.S.Reals):
    """Certify exact natural domains or coverage of a requested Piecewise set.

    Local records have natural=None and natural_complete=False: they do not
    purport to describe points outside the requested set, or continuity.
    """
    from .real_analysis.common import condition_to_set

    f, x = sp.sympify(expr), sp.sympify(var)
    result = _global_domain(f, x, domain)
    if result.reason in ("inexact-requested-domain", "inexact-source-expression"):
        return result
    if not result.complete and any(
        isinstance(n, sp.Pow) and n.exp.is_Rational is not True
        for n in sp.preorder_traversal(f)
    ):
        try:
            power_record = _positive_power_coverage(f, x, domain)
            if power_record is not None:
                return power_record
        except (TypeError, ValueError, NotImplementedError, sp.PolynomialError):
            pass

    if (
        result.complete
        or result.reason == "requested-domain-conflicts-with-coordinate-assumptions"
        or not f.has(sp.Piecewise)
    ):
        return result
    try:
        D = condition_to_set(sp.S.true if domain is None else domain, x)
        if not isinstance(D, sp.Set):
            return result

        shared = _domain_from_condition(f, x, domain, D, local=True)
        if shared is not None:
            return shared
    except (TypeError, ValueError, NotImplementedError, sp.PolynomialError):
        pass
    return result


def _entire_composition_domain(node, x):
    """Definition sets for the newly enclosed entire primitives, before rewrites."""
    if not node.has(sp.erf, sp.erfc):
        record = _global_domain(node, x)
        return record.natural if record.complete else None
    if node.func in (sp.erf, sp.erfc, sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh):
        return _entire_composition_domain(node.args[0], x)
    if node.is_Add or node.is_Mul:
        parts = [_entire_composition_domain(a, x) for a in node.args]
        return sp.Intersection(*parts) if all(p is not None for p in parts) else None
    if node.is_Pow and node.exp.is_Integer and node.exp.is_nonnegative:
        return _entire_composition_domain(node.base, x)
    return None


def coordinate_domain_compatible(variable, domain):
    """Require requested real points to respect intrinsic Symbol assumptions.

    Assumption-based simplification can occur before differentiation or source
    normalization; a held source cannot restore validity outside those premises.
    """
    if not isinstance(variable, sp.Symbol) or not isinstance(domain, sp.Set):
        return False
    if domain is sp.S.EmptySet:
        return True
    real_axis_facts = {
        "commutative": True,
        "complex": True,
        "extended_real": True,
        "finite": True,
        "hermitian": True,
        "imaginary": False,
        "infinite": False,
        "real": True,
    }
    if any(
        variable.assumptions0.get(fact, expected) is not expected
        for fact, expected in real_axis_facts.items()
    ):
        return False
    covered_facts = {
        "commutative",
        "complex",
        "extended_real",
        "finite",
        "hermitian",
        "imaginary",
        "infinite",
        "real",
        "zero",
        "nonzero",
        "positive",
        "negative",
        "nonnegative",
        "nonpositive",
        "extended_positive",
        "extended_negative",
        "extended_nonnegative",
        "extended_nonpositive",
        "extended_nonzero",
        "integer",
        "noninteger",
        "rational",
        "irrational",
    }
    if not isinstance(domain, sp.FiniteSet) and any(
        fact not in covered_facts for fact in variable.assumptions0
    ):
        return False
    allowed = sp.S.Reals
    positive = sp.Interval.open(0, sp.oo)
    negative = sp.Interval.open(-sp.oo, 0)
    nonnegative = sp.Interval(0, sp.oo)
    nonpositive = sp.Interval(-sp.oo, 0)
    nonzero = sp.S.Reals - sp.FiniteSet(0)
    constraint_sets = {
        "zero": sp.FiniteSet(0),
        "nonzero": nonzero,
        "positive": positive,
        "negative": negative,
        "nonnegative": nonnegative,
        "nonpositive": nonpositive,
        "extended_positive": positive,
        "extended_negative": negative,
        "extended_nonnegative": nonnegative,
        "extended_nonpositive": nonpositive,
        "extended_nonzero": nonzero,
        "integer": sp.S.Integers,
        "noninteger": sp.S.Reals - sp.S.Integers,
        "rational": sp.S.Rationals,
        "irrational": sp.S.Reals - sp.S.Rationals,
    }
    for fact, region in constraint_sets.items():
        premise = variable.assumptions0.get(fact)
        if premise is True:
            allowed = sp.Intersection(allowed, region)
        elif premise is False:
            allowed = sp.Complement(allowed, region)
    try:
        if sp.Complement(domain, allowed) is not sp.S.EmptySet:
            return False
        if isinstance(domain, sp.FiniteSet):
            # Discrete assumptions (prime, odd, etc.) may also have enabled
            # source simplifications. Check every retained point independently.
            for fact, expected in variable.assumptions0.items():
                predicate = getattr(sp.Q, fact, None)
                if predicate is not None and fact != "commutative":
                    for point in domain:
                        if sp.ask(predicate(point)) is not expected:
                            return False
        return True
    except (TypeError, ValueError, NotImplementedError):
        return False
