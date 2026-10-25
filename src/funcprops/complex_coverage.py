"""Exact polynomial root coverage of closed complex rectangles.

Shared edges are allowed only because each counted rectangle proves its entire
boundary root-free. Counts distinguish distinct roots from multiplicities.
"""

import itertools
from dataclasses import dataclass

import sympy as sp

from .root_coverage import _ERRORS


@dataclass(frozen=True)
class CoverageRectangle:
    """Represent a rational closed rectangle by opposite complex corners."""

    lower_left: sp.Expr
    upper_right: sp.Expr

    def bounds(self):
        return (
            sp.re(self.lower_left),
            sp.im(self.lower_left),
            sp.re(self.upper_right),
            sp.im(self.upper_right),
        )

    def valid(self):
        a, b, c, d = self.bounds()
        return (
            all(q.is_Rational for q in (a, b, c, d))
            and (a < c) is sp.S.true
            and (b < d) is sp.S.true
        )

    def contains_rectangle(self, other):
        """Check inclusion of the other closed rectangle in this rectangle."""

        a, b, c, d = self.bounds()
        e, f, g, h = other.bounds()
        return all(q is sp.S.true for q in (a <= e, b <= f, g <= c, h <= d))


def _counts(expr, var, rectangle):
    from .meromorphic_contours import _boundary_clear

    f = sp.sympify(expr)
    if (
        not isinstance(var, sp.Symbol)
        or var.assumptions0 != {"commutative": True}
        or not rectangle.valid()
        or f.has(sp.Float)
        or f.free_symbols - {var}
    ):
        return None
    # Do not let polynomial construction cancel original coordinate holes.
    if any(
        isinstance(n, sp.Pow) and n.exp.is_negative and n.base.has(var)
        for n in sp.preorder_traversal(f)
    ):
        return None
    p = sp.Poly(f, var, domain=sp.QQ)
    if p.is_zero or not _boundary_clear(p, rectangle.lower_left, rectangle.upper_right):
        return None
    count = int(p.sqf_part().count_roots(rectangle.lower_left, rectangle.upper_right))
    multiplicity = int(p.count_roots(rectangle.lower_left, rectangle.upper_right))
    return count, multiplicity


@dataclass(frozen=True)
class ComplexRootRegionProof:
    """Bind a rectangle's root count to its declared complex evidence."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    root_count: int
    multiplicity_count: int

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return (
                type(self) is ComplexRootRegionProof
                and type(self.rectangle) is CoverageRectangle
                and type(self.root_count) is int
                and type(self.multiplicity_count) is int
                and _counts(self.expression, self.variable, self.rectangle)
                == (self.root_count, self.multiplicity_count)
            )
        except _ERRORS:
            return False


def _partition(target, rectangles):
    if type(target) is not CoverageRectangle or any(
        type(r) is not CoverageRectangle for r in rectangles
    ):
        return False
    if not target.valid() or any(
        not r.valid() or not target.contains_rectangle(r) for r in rectangles
    ):
        return False
    for r, s in itertools.combinations(rectangles, 2):
        a, b, c, d = r.bounds()
        e, f, g, h = s.bounds()
        if max(a, e) < min(c, g) and max(b, f) < min(d, h):
            return False
    # A finite grid is an exact tiling test, including seams and outer corners.
    xs = sorted(
        {q for r in (target, *rectangles) for q in (r.bounds()[0], r.bounds()[2])}
    )
    ys = sorted(
        {q for r in (target, *rectangles) for q in (r.bounds()[1], r.bounds()[3])}
    )
    samples_x = xs + [(a + b) / 2 for a, b in itertools.pairwise(xs)]
    samples_y = ys + [(a + b) / 2 for a, b in itertools.pairwise(ys)]
    return all(
        any(
            a <= x <= c and b <= y <= d
            for a, b, c, d in (r.bounds() for r in rectangles)
        )
        for x in samples_x
        for y in samples_y
    )


@dataclass(frozen=True)
class ComplexRootCoverage:
    """Assemble counted and unresolved regions of a complex root query."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    regions: tuple[ComplexRootRegionProof, ...] = ()
    unresolved: tuple[CoverageRectangle, ...] = ()
    complete: bool = False
    root_count: int | None = None
    multiplicity_count: int | None = None

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "polynomial-root-coverage-on-closed-complex-rectangle"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                type(self) is not ComplexRootCoverage
                or not isinstance(self.variable, sp.Symbol)
                or self.variable.assumptions0 != {"commutative": True}
                or type(self.rectangle) is not CoverageRectangle
                or type(self.regions) is not tuple
                or type(self.unresolved) is not tuple
                or any(type(r) is not ComplexRootRegionProof for r in self.regions)
                or any(type(r) is not CoverageRectangle for r in self.unresolved)
            ):
                return False
            if any(
                value is not None and type(value) is not int
                for value in (self.root_count, self.multiplicity_count)
            ):
                return False
            if type(self.complete) is not bool or not _partition(
                self.rectangle,
                tuple(r.rectangle for r in self.regions) + self.unresolved,
            ):
                return False
            if any(
                r.expression != self.expression
                or r.variable != self.variable
                or not r.verify()
                for r in self.regions
            ):
                return False
            complete = not self.unresolved
            count = sum(r.root_count for r in self.regions) if complete else None
            multiplicity = (
                sum(r.multiplicity_count for r in self.regions) if complete else None
            )
            return (
                self.complete is complete
                and self.root_count == count
                and self.multiplicity_count == multiplicity
            )
        except _ERRORS:
            return False


def complex_root_coverage(expr, var, lower_left, upper_right):
    """Certify polynomial rectangle counts; boundary roots remain unresolved."""
    f, x = sp.sympify(expr), sp.sympify(var)
    rectangle = CoverageRectangle(sp.sympify(lower_left), sp.sympify(upper_right))
    if not rectangle.valid():
        raise ValueError("rectangle corners must be ordered Gaussian rationals")
    try:
        data = _counts(f, x, rectangle)
    except _ERRORS:
        data = None
    if data is None:
        return ComplexRootCoverage(f, x, rectangle, unresolved=(rectangle,))
    proof = ComplexRootRegionProof(f, x, rectangle, *data)
    return ComplexRootCoverage(f, x, rectangle, (proof,), (), True, *data)
