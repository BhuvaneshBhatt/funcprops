"""Certified total variation for real univariate functions."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

import sympy as sp
from sympy import S

from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..results import Continuity, Monotonicity, TruthValue
from ..source_syntax import differentiate
from .common import condition_to_set, exact_order_real_points, normalize_domain_set
from .domain import domain as real_domain
from .monotonicity import monotonicity
from .piecewise import piecewise_branches
from .smoothness import smoothness


@dataclass(frozen=True)
class VariationResult:
    """Record total variation, including owned Piecewise jumps and endpoint values."""

    bounded_variation: TruthValue
    total_variation: sp.Expr | None
    domain: object
    source: str | None = None
    evidence: tuple[object, ...] = ()
    proof: object = None

    @property
    def expression(self):
        return getattr(self.proof, "expression", None)

    @property
    def variable(self):
        return getattr(self.proof, "variable", None)

    @property
    def complete(self):
        return self.verify()

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "finite-jump-variation-replay"

    def verify(self):
        """Replay a finite motion/jump proof and its public summary fields."""
        from ..metric_proofs import JumpVariationProof
        from ..source_syntax import same_data

        return (
            type(self) is VariationResult
            and type(self.proof) is JumpVariationProof
            and self.proof.verify()
            and self.bounded_variation is TruthValue.TRUE
            and same_data(self.total_variation, self.proof.total_variation)
            and same_data(self.domain, self.proof.domain)
            and same_data(self.evidence, (self.proof,))
            and self.source == "piecewise-jumps"
        )


def _variation_result(value, domain, source, evidence=()):
    if value is S.Infinity:
        return VariationResult(TruthValue.FALSE, value, domain, source, evidence)
    if value.is_finite is True and value.is_nonnegative is True:
        return VariationResult(TruthValue.TRUE, value, domain, source, evidence)
    return VariationResult(TruthValue.UNKNOWN, None, domain, "unresolved", evidence)


def _piecewise_variation(expr, var, support):
    if not expr.has(sp.Piecewise) or not isinstance(support, sp.Interval):
        return None
    if support.start.is_finite is not True or support.end.is_finite is not True:
        return None
    try:
        from ..metric_proofs import certify_jump_variation

        proof = certify_jump_variation(expr, var, support)
        if proof is not None:
            return VariationResult(
                TruthValue.TRUE,
                proof.total_variation,
                support,
                "piecewise-jumps",
                (proof,),
                proof,
            )
        natural = condition_to_set(real_domain(expr, var), var)
        if natural is None or support.is_subset(natural) is not True:
            return None
        expr = sp.piecewise_fold(expr)
        if not isinstance(expr, sp.Piecewise):
            return variation(expr, var, domain=support, return_result=True)
        branches = piecewise_branches(expr, var, support)
        if not branches or any(b.domain is None for b in branches):
            return None
        if sp.Union(*(b.domain for b in branches)) != support:
            return None
        points = {support.start, support.end}
        for branch in branches:
            if isinstance(branch.domain, sp.Interval):
                points.update((branch.domain.start, branch.domain.end))
            elif isinstance(branch.domain, sp.FiniteSet):
                points.update(branch.domain)
            else:
                return None
        ordered = exact_order_real_points(points)
        if ordered is None:
            return None
        intervals = []
        total = S.Zero
        evidence = []
        for left, right in pairwise(ordered):
            cell = sp.Interval.open(left, right)
            owners = [b for b in branches if cell.is_subset(b.domain) is True]
            if len(owners) != 1:
                return None
            branch = owners[0]
            part = variation(branch.expression, var, domain=cell, return_result=True)
            if part.total_variation is None:
                return None
            total += part.total_variation
            lv = sp.limit(branch.expression, var, left, dir="+")
            rv = sp.limit(branch.expression, var, right, dir="-")
            if lv.is_real is not True or rv.is_real is not True:
                return None
            intervals.append((lv, rv))
            evidence.append(part)
        for i, point in enumerate(ordered):
            left = intervals[i - 1][1] if i else None
            right = intervals[i][0] if i < len(intervals) else None
            if support.contains(point) is S.true:
                value = sp.simplify(expr.subs(var, point))
                if value.is_real is not True or value.is_finite is not True:
                    return None
                if left is not None:
                    total += sp.Abs(value - left)
                if right is not None:
                    total += sp.Abs(right - value)
            elif left is not None and right is not None:
                total += sp.Abs(right - left)
        return _variation_result(
            sp.simplify(total), support, "piecewise-jumps", tuple(evidence)
        )
    except SYMBOLIC_QUERY_ERRORS:
        return None


def variation(expr, var, *, domain=S.Reals, return_result=False):
    """Return certified total variation; ``oo`` denotes infinite variation."""
    expr, var = sp.sympify(expr), sp.sympify(var)
    try:
        d = normalize_domain_set(domain, var)
    except (TypeError, ValueError, NotImplementedError):
        d = None
    piecewise = _piecewise_variation(expr, var, d)
    if piecewise is not None:
        result = piecewise
    elif expr.has(sp.Piecewise):
        result = VariationResult(
            TruthValue.UNKNOWN, None, domain, "unproved-piecewise-seams"
        )
    elif not expr.has(var):
        result = VariationResult(TruthValue.TRUE, S.Zero, domain, "constant")
    elif (
        isinstance(d, sp.Interval)
        and d.start.is_finite is True
        and d.end.is_finite is True
    ):
        derivative = differentiate(expr, var)
        order = monotonicity(expr, var, domain=d)
        if order in (
            Monotonicity.CONSTANT,
            Monotonicity.NONDECREASING,
            Monotonicity.NONINCREASING,
            Monotonicity.STRICTLY_INCREASING,
            Monotonicity.STRICTLY_DECREASING,
        ):
            left = (
                sp.limit(expr, var, d.start, dir="+")
                if d.left_open
                else expr.subs(var, d.start)
            )
            right = (
                sp.limit(expr, var, d.end, dir="-")
                if d.right_open
                else expr.subs(var, d.end)
            )
            result = _variation_result(
                sp.simplify(sp.Abs(right - left)), domain, "monotone-interval"
            )
        else:
            regularity = smoothness(
                expr, var, domain=d, max_order=1, return_result=True
            )
            degree = regularity.differentiability_order
            if (
                regularity.continuity is not Continuity.CONTINUOUS
                or degree is None
                or not (degree == sp.oo or degree >= 1)
            ):
                result = VariationResult(
                    TruthValue.UNKNOWN, None, domain, "absolute-continuity-unproved"
                )
                return result if return_result else result.total_variation
            try:
                value = sp.integrate(sp.Abs(derivative), (var, d.start, d.end))
            except (TypeError, ValueError, NotImplementedError):
                value = sp.Integral(sp.Abs(derivative), (var, d.start, d.end))
            result = (
                VariationResult(
                    TruthValue.TRUE,
                    sp.simplify(value),
                    domain,
                    "absolute-derivative-integral",
                )
                if not isinstance(value, sp.Integral) and value.is_finite is True
                else VariationResult(TruthValue.UNKNOWN, None, domain, "unresolved")
            )
    else:
        result = VariationResult(TruthValue.UNKNOWN, None, domain, "unresolved")
    return result if return_result else result.total_variation
