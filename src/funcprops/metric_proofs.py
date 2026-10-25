"""Direct replay for finite metric bounds and finite branch/jump variation."""

from dataclasses import dataclass
from itertools import pairwise

import sympy as sp

from .coverage_contract import CheckOutcome, CheckResult
from .exactness import certify_equal, certify_identity_equal
from .source_syntax import differentiate, same_data
from .work_budget import budgeted_operation

_ERRORS = (AttributeError, TypeError, ValueError, ArithmeticError, NotImplementedError)


def _outcome(valid, reason):
    return CheckResult(
        CheckOutcome.COMPLETE if valid else CheckOutcome.REJECTED,
        bool(valid),
        bool(valid),
        None if valid else reason,
    )


def _finite_data(expression, variable, requested):
    from .real_analysis.domain import domain
    from .results import PropertyResult

    if (
        not isinstance(variable, sp.Symbol)
        or not (isinstance(requested, sp.FiniteSet) or requested is sp.S.EmptySet)
        or expression.has(sp.Float)
        or requested.has(sp.Float)
    ):
        return None
    from .domain_tracking import coordinate_domain_compatible

    if not coordinate_domain_compatible(variable, requested):
        return None
    natural = domain(expression, variable)
    if isinstance(natural, PropertyResult):
        natural = domain(expression, variable, domain=sp.S.Complexes)
    if isinstance(natural, PropertyResult):
        return None
    values = []
    for p in requested:
        if p.is_real is not True or p.is_finite is not True:
            return None
        defined = sp.simplify(natural.subs(variable, p))
        if defined is sp.S.false:
            continue
        if defined is not sp.S.true:
            return None
        v = sp.simplify(expression.subs(variable, p))
        if v.is_real is not True or v.is_finite is not True:
            return None
        values.append((p, v))
    ratios = []
    for i, (p, v) in enumerate(values):
        for q, w in values[:i]:
            distance = sp.Abs(p - q)
            if distance.is_positive is not True:
                return None
            ratios.append(sp.simplify(sp.Abs(v - w) / distance))
    return (
        sp.FiniteSet(*(p for p, _ in values)),
        tuple(values),
        tuple(ratios),
        sp.Max(*ratios) if ratios else sp.S.Zero,
    )


@dataclass(frozen=True)
class FiniteLipschitzProof:
    """Bind an optimal pairwise constant to all defined points of a finite query."""

    expression: sp.Expr
    variable: sp.Symbol
    requested: sp.Set
    effective: sp.Set
    values: tuple
    ratios: tuple
    constant: sp.Expr

    @property
    def complete(self):
        return True

    @property
    def scope(self):
        return "optimal-lipschitz-constant-on-effective-finite-domain"

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay source definition, all values, all pairs and their exact maximum."""
        try:
            data = _finite_data(self.expression, self.variable, self.requested)
            valid = (
                type(self) is FiniteLipschitzProof
                and data is not None
                and same_data(
                    (self.effective, self.values, self.ratios, self.constant), data
                )
            )
            return _outcome(valid, "false-finite-lipschitz-proof")
        except _ERRORS:
            return _outcome(False, "false-finite-lipschitz-proof")

    def verify(self):
        """Return whether every finite-domain replay obligation is established."""
        return self.check().certified is True


@budgeted_operation
def certify_finite_lipschitz(expression, variable, requested):
    """Return an optimal finite-domain proof, or None if exact data is unresolved."""
    expression, variable = sp.sympify(expression), sp.sympify(variable)
    data = _finite_data(expression, variable, requested)
    return (
        None
        if data is None
        else FiniteLipschitzProof(expression, variable, requested, *data)
    )


@dataclass(frozen=True)
class VariationMotion:
    """Store a C1 monotone formula and its two limits on an open interval."""

    expression: sp.Expr
    interval: sp.Interval
    derivative: sp.Expr
    direction: int
    left: sp.Expr
    right: sp.Expr
    variation: sp.Expr


def _motion_direction(derivative, variable, interval):
    from .real_analysis.sign import sign
    from .results import Sign

    if certify_equal(derivative, 0) is True:
        return 0
    result = sign(derivative, variable, domain=interval)
    if result in (Sign.POSITIVE, Sign.NONNEGATIVE):
        return 1
    if result in (Sign.NEGATIVE, Sign.NONPOSITIVE):
        return -1
    return None


def _motion_valid(motion, variable):
    from .coverage_checker import derivative_formula_on_cell
    from .real_analysis.common import condition_to_set
    from .real_analysis.domain import domain

    if (
        type(motion) is not VariationMotion
        or type(motion.direction) is not int
        or motion.direction not in (-1, 0, 1)
    ):
        return False
    interval = motion.interval
    if (
        not isinstance(interval, sp.Interval)
        or not interval.left_open
        or not interval.right_open
    ):
        return False
    natural = condition_to_set(domain(motion.expression, variable), variable)
    if natural is None or interval.is_subset(natural) is not True:
        return False
    derivative = derivative_formula_on_cell(motion.expression, variable, interval, 1)
    if (
        derivative is None
        or certify_identity_equal(derivative, motion.derivative) is not True
    ):
        return False
    if _motion_direction(derivative, variable, interval) != motion.direction:
        return False
    left = sp.limit(motion.expression, variable, interval.start, dir="+")
    right = sp.limit(motion.expression, variable, interval.end, dir="-")
    if any(v.is_real is not True or v.is_finite is not True for v in (left, right)):
        return False
    return all(
        certify_equal(a, b) is True
        for a, b in (
            (left, motion.left),
            (right, motion.right),
            (sp.Abs(right - left), motion.variation),
        )
    )


def _variation_total(cells, points, support):
    total = sum((c.variation for c in cells), sp.S.Zero)
    owned = dict(points)
    boundaries = (cells[0].interval.start, *(c.interval.end for c in cells))
    for i, p in enumerate(boundaries):
        left = cells[i - 1].right if i else None
        right = cells[i].left if i < len(cells) else None
        if support.contains(p) is sp.S.true:
            if p not in owned:
                return None
            if left is not None:
                total += sp.Abs(owned[p] - left)
            if right is not None:
                total += sp.Abs(right - owned[p])
        elif left is not None and right is not None:
            total += sp.Abs(right - left)
    return sp.simplify(total)


@dataclass(frozen=True)
class JumpVariationProof:
    """Cover a bounded interval by monotone motions and all owned point values."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    cells: tuple
    points: tuple
    total_variation: sp.Expr

    @property
    def complete(self):
        return True

    @property
    def scope(self):
        return "finite-monotone-motion-and-owned-jump-variation"

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay exact coverage, local motion, endpoint values and every jump."""
        from .domain_tracking import coordinate_domain_compatible
        from .real_analysis.common import condition_to_set
        from .real_analysis.domain import domain
        from .real_analysis.piecewise import piecewise_branches

        try:
            f, x, support = self.expression, self.variable, self.domain
            if (
                type(self) is not JumpVariationProof
                or not isinstance(x, sp.Symbol)
                or not isinstance(support, sp.Interval)
                or not all(p.is_finite is True for p in (support.start, support.end))
                or f.has(sp.Float)
                or support.has(sp.Float)
                or type(self.cells) is not tuple
                or not self.cells
                or type(self.points) is not tuple
                or not coordinate_domain_compatible(x, support)
            ):
                return _outcome(False, "invalid-variation-header")
            natural = condition_to_set(domain(f, x), x)
            if natural is None or support.is_subset(natural) is not True:
                return _outcome(False, "unproved-variation-source-domain")
            folded = sp.piecewise_fold(f)
            branches = (
                piecewise_branches(folded, x, support)
                if isinstance(folded, sp.Piecewise)
                else ()
            )
            for cell in self.cells:
                if not _motion_valid(cell, x):
                    return _outcome(False, "invalid-variation-motion")
                if branches:
                    owners = [
                        b
                        for b in branches
                        if b.domain is not None
                        and cell.interval.is_subset(b.domain) is True
                    ]
                    if (
                        len(owners) != 1
                        or certify_identity_equal(owners[0].expression, cell.expression)
                        is not True
                    ):
                        return _outcome(False, "variation-branch-mismatch")
                elif certify_identity_equal(folded, cell.expression) is not True:
                    return _outcome(False, "variation-source-mismatch")
            if (
                self.cells[0].interval.start != support.start
                or self.cells[-1].interval.end != support.end
                or any(
                    a.interval.end != b.interval.start for a, b in pairwise(self.cells)
                )
            ):
                return _outcome(False, "variation-cover-gap")
            cuts = (self.cells[0].interval.start, *(c.interval.end for c in self.cells))
            expected = tuple(
                (p, sp.simplify(f.subs(x, p)))
                for p in cuts
                if support.contains(p) is sp.S.true
            )
            if any(
                v.is_real is not True or v.is_finite is not True for _, v in expected
            ) or not same_data(self.points, expected):
                return _outcome(False, "variation-point-mismatch")
            if (
                sp.Union(
                    *(c.interval for c in self.cells),
                    sp.FiniteSet(*(p for p, _ in expected)),
                )
                != support
            ):
                return _outcome(False, "incomplete-variation-cover")
            total = _variation_total(self.cells, self.points, support)
            return _outcome(
                total is not None
                and certify_equal(total, self.total_variation) is True,
                "false-variation-total",
            )
        except _ERRORS:
            return _outcome(False, "false-jump-variation-proof")

    def verify(self):
        """Return whether the source-bound variation assembly is certified."""
        return self.check().certified is True


@budgeted_operation
def certify_jump_variation(expression, variable, domain):
    """Construct a finite variation proof using branch monotonic partitions."""
    from .real_analysis.common import exact_order_real_points
    from .real_analysis.monotonic_certificates import monotonic_partition
    from .real_analysis.piecewise import piecewise_branches

    f, x = sp.sympify(expression), sp.sympify(variable)
    if not isinstance(domain, sp.Interval) or not all(
        p.is_finite is True for p in (domain.start, domain.end)
    ):
        return None
    try:
        folded = sp.piecewise_fold(f)
        branches = (
            piecewise_branches(folded, x, domain)
            if isinstance(folded, sp.Piecewise)
            else ()
        )
        regions = (
            [(b.expression, b.domain) for b in branches]
            if branches
            else [(folded, domain)]
        )
        cuts = {domain.start, domain.end}
        for g, region in regions:
            if isinstance(region, sp.FiniteSet):
                cuts.update(region)
            elif isinstance(region, sp.Interval):
                cuts.update((region.start, region.end))
                if g.has(x):
                    part = monotonic_partition(g, x, domain=region, return_result=True)
                    if part.complete and part.indexed is None:
                        cuts.update(c.interval.start for c in part.cells)
                        cuts.update(c.interval.end for c in part.cells)
            else:
                return None
        ordered = exact_order_real_points(cuts)
        if ordered is None:
            return None
        cells = []
        for a, b in pairwise(ordered):
            interval = sp.Interval.open(a, b)
            owners = [g for g, region in regions if interval.is_subset(region) is True]
            if len(owners) != 1:
                return None
            g = owners[0]
            derivative = differentiate(g, x)
            direction = _motion_direction(derivative, x, interval)
            if direction is None:
                return None
            left = sp.limit(g, x, a, dir="+")
            right = sp.limit(g, x, b, dir="-")
            cells.append(
                VariationMotion(
                    g,
                    interval,
                    derivative,
                    direction,
                    left,
                    right,
                    sp.simplify(sp.Abs(right - left)),
                )
            )
        points = tuple(
            (p, sp.simplify(f.subs(x, p)))
            for p in ordered
            if domain.contains(p) is sp.S.true
        )
        total = _variation_total(cells, points, domain)
        proof = JumpVariationProof(f, x, domain, tuple(cells), points, total)
        return proof if proof.verify() else None
    except _ERRORS:
        return None
