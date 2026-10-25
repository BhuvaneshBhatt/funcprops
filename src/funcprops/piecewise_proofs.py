"""Shared finite branch coverage, source definition and seam proof assembly."""

from dataclasses import dataclass

import sympy as sp

from .domain_tracking import (
    coordinate_domain_compatible,
    smooth_domain_record,
    track_domain,
)
from .exactness import certify_identity_equal
from .real_analysis.common import condition_to_set
from .real_analysis.piecewise import (
    certify_piecewise_boundaries,
    piecewise_decomposition,
)


def piecewise_cells(expression, variable, domain):
    """Partition first-match Piecewise branches into exact owned source cells."""

    folded = sp.piecewise_fold(expression)
    if not isinstance(folded, sp.Piecewise):
        return None
    decomposition = piecewise_decomposition(folded, variable, domain)
    if not decomposition.complete or not decomposition.branches:
        return None
    cells = tuple(
        (branch.expression, branch.domain) for branch in decomposition.branches
    )
    if any(not isinstance(region, (sp.Interval, sp.FiniteSet)) for _, region in cells):
        return None
    if sp.Union(*(region for _, region in cells)) != domain:
        return None
    return decomposition, cells


@dataclass(frozen=True)
class PiecewiseRegularityCertificate:
    """Assemble branch regularity and first-match seam evidence."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    cells: tuple
    seams: tuple
    domain_record: object
    order: int = 1

    @property
    def complete(self):
        return self.verify()

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "continuous-piecewise-C1-on-requested-interval"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            actual = certify_piecewise_regular(
                self.expression, self.variable, self.domain
            )
            return (
                type(self.order) is int
                and self.order == 1
                and actual is not None
                and self.cells == actual.cells
                and self.seams == actual.seams
                and self.domain_record.matches(actual.domain_record)
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


def certify_piecewise_regular(expression, variable, domain):
    """Prove continuous finite piecewise C1 structure; corners are allowed."""
    f, x = sp.sympify(expression), sp.sympify(variable)
    if (
        not isinstance(domain, sp.Interval)
        or domain.start.is_finite is not True
        or domain.end.is_finite is not True
    ):
        return None
    record = track_domain(f, x, domain)
    if not record.complete or record.effective != domain:
        return None
    data = piecewise_cells(f, x, domain)
    if data is None:
        return None
    decomposition, cells = data
    for branch, region in cells:
        if isinstance(region, sp.Interval):
            if smooth_domain_record(branch, x, region.closure, 1) is None:
                return None
        elif any(branch.subs(x, p).is_finite is not True for p in region):
            return None
    seams = certify_piecewise_boundaries(decomposition, max_order=0)
    if len(seams) != len(decomposition.boundaries):
        return None
    for seam in seams:
        p = seam.boundary.point
        if domain.interior.contains(p) is sp.S.true:
            if seam.continuous is not True:
                return None
        elif p == domain.start:
            if certify_identity_equal(seam.value, seam.right_limit) is not True:
                return None
        elif p == domain.end:
            if certify_identity_equal(seam.value, seam.left_limit) is not True:
                return None
        else:
            return None
    return PiecewiseRegularityCertificate(f, x, domain, cells, seams, record)


def real_path_piecewise_c1(expression, variable, domain):
    """Check Piecewise C1 premises along a supported real contour parameterization."""

    return (
        smooth_domain_record(expression, variable, domain, 1) is not None
        or certify_piecewise_regular(expression, variable, domain) is not None
    )


def complex_source_defined(expression, variable, domain):
    """Retain raw complex source holes, including inactive Piecewise branches."""
    from .source_syntax import finite_constant_source, logarithm_quotient

    if not coordinate_domain_compatible(variable, domain):
        return False
    axis = sp.Dummy("source_coordinate", real=True)

    def nonzero(base, region):
        try:
            return (
                sp.solveset(base.xreplace({variable: axis}), axis, domain=region)
                is sp.S.EmptySet
            )
        except (TypeError, ValueError, NotImplementedError):
            return False

    def defined(node, region):
        if region is sp.S.EmptySet:
            return True
        if node == variable:
            return True
        if not isinstance(node, sp.Expr):
            return False
        if node.func is sp.log and len(node.args) == 2:
            return defined(logarithm_quotient(node), region)
        if not node.has(variable):
            return finite_constant_source(node)
        if isinstance(node, sp.Piecewise):
            remaining = region
            for branch, condition in node.args:
                if remaining is sp.S.EmptySet:
                    break
                for relation in condition.atoms(sp.core.relational.Relational):
                    for operand in (relation.lhs, relation.rhs):
                        record = track_domain(operand, variable, remaining)
                        if not record.complete or record.effective != remaining:
                            return False
                guard = condition_to_set(condition, variable)
                if not isinstance(guard, sp.Set):
                    return False
                if not defined(branch, sp.Intersection(remaining, guard)):
                    return False
                remaining = sp.Complement(remaining, guard)
            return remaining is sp.S.EmptySet
        if node.is_Add or node.is_Mul:
            return all(defined(arg, region) for arg in node.args)
        if node.is_Pow:
            if (
                node.exp.has(variable)
                or not finite_constant_source(node.exp)
                or not defined(node.base, region)
            ):
                return False
            return node.exp.is_positive is True or nonzero(node.base, region)
        if node.func in (sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh, sp.Abs):
            return all(defined(arg, region) for arg in node.args)
        if node.func is sp.log:
            return defined(node.args[0], region) and nonzero(node.args[0], region)
        return False

    try:
        return defined(sp.sympify(expression), domain)
    except (
        AttributeError,
        TypeError,
        ValueError,
        NotImplementedError,
        ArithmeticError,
    ):
        return False


def complex_avoids_value(expression, variable, domain, value):
    """Prove path avoidance cell by cell, retaining exact seam ownership."""
    axis = sp.Dummy("avoidance_coordinate", real=True)
    data = (
        piecewise_cells(expression, variable, domain)
        if expression.has(sp.Piecewise)
        else None
    )
    if expression.has(sp.Piecewise) and data is None:
        return False
    cells = data[1] if data is not None else ((expression, domain),)
    try:
        return all(
            sp.solveset(branch.xreplace({variable: axis}) - value, axis, domain=region)
            is sp.S.EmptySet
            for branch, region in cells
        )
    except (TypeError, ValueError, NotImplementedError):
        return False
