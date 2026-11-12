"""Real interior regularity and one-sided boundary data for image cells."""

from dataclasses import dataclass

import sympy as sp

from ..source_syntax import same_data

_ERRORS = (TypeError, ValueError, AttributeError, ArithmeticError, NotImplementedError)


def interior_derivative(expression, variable, domain):
    """Differentiate on a real open cell using exact continuity-domain backends.

    No smooth extension through the cell boundary is claimed. Distributional
    derivatives and unsupported branch/continuity analysis decline this route.
    """
    from ..domain_tracking import coordinate_domain_compatible, track_domain
    from ..source_syntax import differentiate, normalize_arithmetic

    if (
        not isinstance(variable, sp.Symbol)
        or not isinstance(expression, sp.Expr)
        or expression.free_symbols - {variable}
        or expression.has(sp.Float)
        or not coordinate_domain_compatible(variable, domain)
    ):
        return None
    source = track_domain(expression, variable, domain)
    if not source.complete or source.effective != domain:
        return None
    if (
        not isinstance(domain, sp.Interval)
        or not domain.left_open
        or not domain.right_open
    ):
        return None
    try:
        derivative = differentiate(normalize_arithmetic(expression), variable)
        if derivative.has(sp.Derivative, sp.DiracDelta, sp.Piecewise):
            return None
        continuous = sp.calculus.util.continuous_domain
        if (
            continuous(expression, variable, domain) != domain
            or continuous(derivative, variable, domain) != domain
        ):
            return None
        return derivative
    except _ERRORS:
        return None


def endpoint_value(expression, variable, domain, left):
    """Evaluate an owned endpoint or the limit from within its open source cell."""
    point = domain.start if left else domain.end
    opened = domain.left_open if left else domain.right_open
    value = (
        sp.limit(expression, variable, point, dir="+" if left else "-")
        if opened
        else sp.simplify(expression.subs(variable, point))
    )
    if value.is_extended_real is not True or (
        not opened and value.is_finite is not True
    ):
        return None
    return value


def _strict_sign(expression, variable, domain):
    replacement = None
    if domain.is_subset(sp.Interval.open(0, sp.oo)) is True:
        replacement = sp.Dummy("positive_source", positive=True)
    elif domain.is_subset(sp.Interval.open(-sp.oo, 0)) is True:
        replacement = sp.Dummy("negative_source", negative=True)
    f = expression if replacement is None else expression.subs(variable, replacement)
    return 1 if f.is_positive is True else -1 if f.is_negative is True else None


@dataclass(frozen=True)
class InteriorCriticalCover:
    """Critical geometry on a real open cell with one-sided endpoint analysis.

    Strict-sign proofs use symbolic sign inference. Finite root sets replay the
    exact symbolic solveset backend. Neither route assumes endpoint smoothness.
    None roots explicitly retain unresolved critical geometry.
    """

    source: sp.Expr
    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    roots: object
    sign: object = None

    @property
    def complete(self):
        """Completion status for this record's stated scope; replay validity is separate."""
        return self.roots is not None

    @property
    def root_count(self):
        """Distinct-root count supplied by the record, or None when unresolved."""
        return len(self.roots) if self.complete else None

    def verify(self):
        """Replay interior regularity and the declared sign or exact-root backend."""
        try:
            if (
                type(self) is not InteriorCriticalCover
                or interior_derivative(self.source, self.variable, self.domain)
                != self.expression
            ):
                return False
            return same_data(
                (self.roots, self.sign),
                _critical_data(self.expression, self.variable, self.domain),
            )
        except _ERRORS:
            return False


def interior_critical_cover(source, derivative, variable, domain):
    """Propose a strict-sign or finite symbolic critical cover of an open cell."""
    roots, sign = _critical_data(derivative, variable, domain)
    return InteriorCriticalCover(source, derivative, variable, domain, roots, sign)


def _critical_data(derivative, variable, domain):
    sign = _strict_sign(derivative, variable, domain)
    if sign is not None:
        return (), sign
    try:
        roots = sp.solveset(derivative, variable, domain=domain)
    except _ERRORS:
        roots = None
    return (
        (tuple(sorted(roots, key=sp.default_sort_key)), None)
        if isinstance(roots, sp.FiniteSet) or roots is sp.S.EmptySet
        else (None, None)
    )


def range_cells(expression, variable, domain):
    """Split finite Piecewise and real absolute-value seams into owned cells."""
    from ..analysis import function_cells

    if expression.has(sp.Abs, sp.Min, sp.Max):
        expression = sp.piecewise_fold(expression.rewrite(sp.Piecewise))
    return function_cells(expression, variable, domain)


@dataclass(frozen=True)
class InteriorRootCover:
    """Native numerator-root coverage for a derivative with excluded poles."""

    source: sp.Expr
    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    equation: sp.Expr
    denominator: sp.Expr
    proof: object

    @property
    def complete(self):
        """Completion status for this record's stated scope; replay validity is separate."""
        return self.proof.complete

    @property
    def root_count(self):
        """Distinct-root count supplied by the record, or None when unresolved."""
        return self.proof.root_count

    @property
    def roots(self):
        """Root coordinates or descriptions carried by the checked cover."""
        from .critical_values import root_locations

        return root_locations(self.proof, self.equation, self.variable)

    def verify(self):
        """Check derivative identity, nonvanishing denominator and native cover."""
        from ..coverage_contract import CoverageProof
        from ..domain_tracking import track_domain

        try:
            numerator, denominator = sp.fraction(
                sp.cancel(sp.together(self.expression))
            )
            source = track_domain(1 / denominator, self.variable, self.domain)
            p = self.proof
            return (
                type(self) is InteriorRootCover
                and type(p) is CoverageProof
                and interior_derivative(self.source, self.variable, self.domain)
                == self.expression
                and same_data(
                    (numerator, denominator), (self.equation, self.denominator)
                )
                and source.complete
                and source.effective == self.domain
                and same_data(
                    (
                        p.expression,
                        p.variable,
                        p.context.requested,
                        p.context.effective,
                    ),
                    (self.equation, self.variable, self.domain, self.domain),
                )
                and p.verify()
            )
        except _ERRORS:
            return False


def rational_interior_cover(source, derivative, variable, domain, policy):
    """Reuse entire numerator isolation when a derivative has boundary poles."""
    from ..adaptive_roots import adaptive_root_coverage

    numerator, denominator = sp.fraction(sp.cancel(sp.together(derivative)))
    if denominator == 1:
        return None
    if interior_derivative(source, variable, domain) != derivative:
        return None
    proof = adaptive_root_coverage(numerator, variable, domain, policy=policy).proof
    result = InteriorRootCover(
        source, derivative, variable, domain, numerator, denominator, proof
    )
    return result if result.verify() else None
