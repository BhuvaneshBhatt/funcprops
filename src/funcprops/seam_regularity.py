"""Bounded branch assembly for continuity and separated limiting values."""

from dataclasses import dataclass

import sympy as sp

from .domain_tracking import coordinate_domain_compatible, track_domain
from .exactness import certify_equal
from .proof_cache import cached_endpoint_limit
from .real_analysis.common import normalize_domain_set
from .source_syntax import same_data

_ERRORS = (TypeError, ValueError, AttributeError, ArithmeticError, NotImplementedError)


def _source_defined(expression, variable, support):
    """Check raw real definitions using the domains of individual primitives."""
    if expression == variable or expression.is_Rational:
        return True
    if expression.is_Add or expression.is_Mul:
        return all(_source_defined(a, variable, support) for a in expression.args)
    if expression.func in (sp.sin, sp.cos, sp.exp, sp.atan, sp.sign):
        return _source_defined(expression.args[0], variable, support)
    if expression.is_Pow or expression.func is sp.log:
        if expression.is_Pow and not (
            expression.exp.is_Integer and abs(expression.exp) <= 8
        ):
            return False
        inner = expression.base if expression.is_Pow else expression.args[0]
        if not _source_defined(inner, variable, support):
            return False
        record = track_domain(expression, variable, support)
        return record.complete and record.effective == support
    if isinstance(expression, sp.Piecewise):
        from .real_analysis.piecewise import piecewise_decomposition

        def defined_guard(guard):
            if guard in (sp.S.true, sp.S.false):
                return True
            if isinstance(guard, (sp.And, sp.Or, sp.Not)):
                return all(defined_guard(a) for a in guard.args)
            if not isinstance(guard, sp.core.relational.Relational):
                return False
            try:
                sp.Poly(guard.lhs, variable, domain=sp.QQ)
                sp.Poly(guard.rhs, variable, domain=sp.QQ)
            except (sp.PolynomialError, sp.CoercionFailed):
                return False
            return _source_defined(guard.lhs, variable, support) and _source_defined(
                guard.rhs, variable, support
            )

        if not all(defined_guard(guard) for _, guard in expression.args):
            return False
        decomposition = piecewise_decomposition(expression, variable, support)
        return (
            decomposition.complete
            and sp.Union(*(b.domain for b in decomposition.branches)) == support
            and all(
                _source_defined(b.expression, variable, b.domain)
                for b in decomposition.branches
            )
        )
    return False


def _smooth_branch(expression, variable, support):
    """Real arithmetic and smooth heads are smooth wherever their sources exist."""
    return not expression.has(sp.sign, sp.Piecewise) and _source_defined(
        expression, variable, support
    )


def _seam_data(expression, variable, domain, conclusion):
    """Rebuild exact first-match cells, relative seams and finite limits.

    Continuity uses only sides accumulating in the requested set and checks
    the owned value. A limiting gap needs two intervals approaching the same
    point; their finite unequal limits disprove uniform continuity and hence
    Lipschitz regularity even when that point is excluded.
    """
    from .piecewise_proofs import piecewise_cells

    if (
        not isinstance(variable, sp.Symbol)
        or expression.free_symbols.difference({variable})
        or expression.has(sp.Float)
        or sum(1 for _ in sp.preorder_traversal(expression)) > 80
        or not isinstance(domain, sp.Set)
        or not coordinate_domain_compatible(variable, domain)
        or conclusion not in ("continuous", "separated-limits")
    ):
        return None
    if domain.is_empty is not False or not _source_defined(
        expression, variable, domain
    ):
        return None
    replacements = {}
    for atom in expression.atoms(sp.sign):
        try:
            argument = sp.Poly(atom.args[0], variable, domain=sp.QQ)
        except (sp.PolynomialError, sp.CoercionFailed):
            return None
        if argument.degree() != 1:
            return None
        t = atom.args[0]
        replacements[atom] = sp.Piecewise((-1, t < 0), (0, sp.Eq(t, 0)), (1, True))
    folded = sp.piecewise_fold(expression.xreplace(replacements))
    if isinstance(folded, sp.Piecewise):
        assembled = piecewise_cells(folded, variable, domain)
        if assembled is None:
            return None
        cells = tuple(assembled[1])
    else:
        components = domain.args if isinstance(domain, sp.Union) else (domain,)
        cells = tuple((folded, component) for component in components)
    if len(cells) > 12 or sp.Union(*(d for _, d in cells)) != domain:
        return None
    for formula, cell in cells:
        if isinstance(cell, sp.Interval):
            if not _smooth_branch(formula, variable, cell):
                return None
        elif isinstance(cell, sp.FiniteSet):
            if any(
                formula.subs(variable, p).is_real is not True
                or formula.subs(variable, p).is_finite is not True
                for p in cell
            ):
                return None
        else:
            return None
    endpoints = {
        p
        for _, d in cells
        if isinstance(d, sp.Interval)
        for p in (d.start, d.end)
        if p.is_finite is True
    }
    seams = []
    for point in sp.ordered(endpoints):
        if point.is_Rational is not True:
            return None
        left = [f for f, d in cells if isinstance(d, sp.Interval) and d.end == point]
        right = [f for f, d in cells if isinstance(d, sp.Interval) and d.start == point]
        # A component can pass through a boundary introduced by a point cell.
        for f, d in cells:
            if isinstance(d, sp.Interval) and d.interior.contains(point) is sp.S.true:
                left.append(f)
                right.append(f)
        if len(left) > 1 or len(right) > 1:
            return None
        limits = tuple(
            cached_endpoint_limit(
                f[0], variable, point, direction=direction, attained=False
            )
            if f
            else None
            for f, direction in ((left, "-"), (right, "+"))
        )
        if any(
            value is not None
            and (value.is_real is not True or value.is_finite is not True)
            for value in limits
        ):
            return None
        owned = domain.contains(point) is sp.S.true
        value = expression.subs(variable, point) if owned else None
        seam = (point, tuple(left), tuple(right), limits, value)
        if conclusion == "separated-limits":
            if (
                left
                and right
                and all(v is not None for v in limits)
                and certify_equal(*limits) is False
            ):
                return cells, (seam,)
        elif owned:
            if value.is_real is not True or value.is_finite is not True:
                return None
            if any(
                certify_equal(limit, value) is not True
                for side, limit in zip((left, right), limits, strict=True)
                if side
            ):
                return None
        seams.append(seam)
    return (cells, tuple(seams)) if conclusion == "continuous" else None


@dataclass(frozen=True)
class SeamRegularityProof:
    """Bind a continuity assembly or a nonzero limiting gap to its source set."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    conclusion: str
    cells: tuple
    seams: tuple

    def verify(self):
        """Check branch coverage, real source definitions and relative seam limits."""
        try:
            data = _seam_data(
                self.expression, self.variable, self.domain, self.conclusion
            )
            return (
                type(self) is SeamRegularityProof
                and data is not None
                and same_data(data, (self.cells, self.seams))
            )
        except _ERRORS:
            return False

    @property
    def complete(self):
        return self.verify()

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return (
            "real-branch-continuity"
            if self.conclusion == "continuous"
            else "nonuniform-continuity-by-separated-limits"
        )


def seam_regularity_proof(expression, variable, domain, conclusion):
    """Propose bounded sign/Piecewise continuity or a two-sided limiting gap."""
    if conclusion == "continuous" and (
        expression.func is sp.sign or not expression.has(sp.sign, sp.Piecewise)
    ):
        return None
    if (
        conclusion == "separated-limits"
        and not expression.has(sp.sign, sp.Piecewise)
        and not any(p.exp.is_Integer and p.exp < 0 for p in expression.atoms(sp.Pow))
    ):
        return None
    try:
        support = normalize_domain_set(domain, variable)
        if conclusion == "separated-limits":
            if not isinstance(support, sp.Union) or len(support.args) > 12:
                return None
            intervals = [d for d in support.args if isinstance(d, sp.Interval)]
            if not any(
                left.end == right.start and left.end.is_Rational
                for left in intervals
                for right in intervals
            ):
                return None
        data = _seam_data(expression, variable, support, conclusion)
        return (
            SeamRegularityProof(expression, variable, support, conclusion, *data)
            if data is not None
            else None
        )
    except _ERRORS:
        return None
