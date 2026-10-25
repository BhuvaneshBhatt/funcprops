"""Independent subset, localization and real multiplicity theorem premises."""

import sympy as sp

from .coverage_contract import (
    CoverageLeaf,
    LocatedSubsetWitness,
    NewtonWitness,
    PowerFactorWitness,
    SourceFormulaWitness,
    TaylorDeflationWitness,
    ZeroSubsetWitness,
)
from .source_syntax import differentiate, normalize_arithmetic

THEOREMS = (
    "zero-subset",
    "located-subset",
    "power-factor",
    "taylor-deflation",
    "source-formula",
)


def location_base(parent):
    """A source with exactly the same root on the parent's certified cell."""
    if parent.theorem == "power-factor" and isinstance(
        parent.witness, PowerFactorWitness
    ):
        return parent.witness.base
    if parent.theorem == "located-subset" and isinstance(
        parent.witness, LocatedSubsetWitness
    ):
        return location_base(parent.witness.parent)
    if parent.theorem == "source-formula" and isinstance(
        parent.witness, SourceFormulaWitness
    ):
        return location_base(parent.witness.proof)
    from .coverage_checker import cell_expression

    return cell_expression(parent.context, parent.region)


def newton_locus(f, x, support, witness):
    """Extract the root-containing locus from a checked real Newton witness."""

    from .coverage_checker import _bound_matches, derivative_formula_on_cell

    if not isinstance(support, sp.Interval) or not isinstance(witness, NewtonWitness):
        return None
    if support.start.is_finite is not True or support.end.is_finite is not True:
        return None
    mid = (support.start + support.end) / 2
    derivative = derivative_formula_on_cell(
        f,
        x,
        support.closure,
        precision=witness.derivative.precision,
        max_series_terms=witness.derivative.max_series_terms,
    )
    if (
        derivative is None
        or witness.midpoint != mid
        or not _bound_matches(witness.derivative, derivative, x, support.closure)
        or not _bound_matches(witness.value, f, x, sp.FiniteSet(mid))
    ):
        return None
    d = witness.derivative
    if d.lower <= 0 <= d.upper:
        return None
    ratios = [
        a / b
        for a in (witness.value.lower, witness.value.upper)
        for b in (d.lower, d.upper)
    ]
    low, high = mid - max(ratios), mid - min(ratios)
    if witness.image_lower != low or witness.image_upper != high:
        return None
    return sp.Intersection(support, sp.Interval(low, high))


def multiple_counts(leaf, f):
    """Reconstruct a multiple-root count from checked factor or deflation data."""

    from .coverage_checker import (
        _bound_matches,
        _empty,
        _formula_equal,
        _subset,
        check_leaf,
        derivative_formula_on_cell,
        regular_on_cell,
    )

    w, x, region = leaf.witness, leaf.variable, leaf.region
    if leaf.theorem == "source-formula":
        if not isinstance(w, SourceFormulaWitness) or not isinstance(
            w.proof, CoverageLeaf
        ):
            return None
        p = w.proof
        if (
            p.expression != normalize_arithmetic(f)
            or p.variable != x
            or p.region != region
            or p.context.substitutions
            or p.context.branch_context is not None
            or not check_leaf(p).certified
        ):
            return None
        mult = p.multiplicity_count
        if p.root_count and (
            type(mult) is not int
            or not regular_on_cell(
                f,
                x,
                region.closure if isinstance(region, sp.Interval) else region,
                mult,
            )
        ):
            mult = None
        return p.root_count, mult
    if leaf.theorem in ("zero-subset", "located-subset"):
        expected = (
            ZeroSubsetWitness if leaf.theorem == "zero-subset" else LocatedSubsetWitness
        )
        if not isinstance(w, expected) or not isinstance(w.parent, CoverageLeaf):
            return None
        parent = w.parent
        if (
            parent.context != leaf.context
            or not _subset(region, parent.region)
            or not check_leaf(parent).certified
        ):
            return None
        if isinstance(w, ZeroSubsetWitness):
            return (0, 0) if parent.root_count == 0 else None
        if parent.root_count != 1:
            return None
        if isinstance(w.locator, sp.FiniteSet):
            if len(parent.roots) != 1 or w.locator != sp.FiniteSet(parent.roots[0][0]):
                return None
            locus = w.locator
        else:
            base = location_base(parent)
            locus = (
                newton_locus(base, x, parent.region, w.locator)
                if base is not None
                else None
            )
        if locus is None or _empty(locus):
            return None
        if _subset(locus, region):
            return 1, parent.multiplicity_count
        return (0, 0) if _empty(sp.Intersection(region, locus)) else None
    if f.has(sp.Piecewise) or leaf.expression.has(sp.Piecewise):
        return None
    support = region.closure if isinstance(region, sp.Interval) else region
    if leaf.theorem == "power-factor":
        if (
            not isinstance(w, PowerFactorWitness)
            or type(w.exponent) is not int
            or w.exponent <= 0
            or not isinstance(w.base_proof, CoverageLeaf)
            or w.base_proof.region != region
            or w.base_proof.expression != w.base
            or w.base_proof.variable != x
            or w.base_proof.context.substitutions
            or w.base_proof.context.branch_context is not None
            or not check_leaf(w.base_proof).certified
        ):
            return None
        if not _formula_equal(normalize_arithmetic(f), w.base**w.exponent * w.unit):
            return None
        bound = w.unit_bound
        if (
            not _subset(support, bound.domain)
            or not _bound_matches(bound, w.unit, x, bound.domain)
            or bound.lower <= 0 <= bound.upper
        ):
            return None
        if not regular_on_cell(
            f,
            x,
            support,
            w.exponent,
            precision=bound.precision,
            max_series_terms=bound.max_series_terms,
        ):
            return None
        if not regular_on_cell(
            w.base,
            x,
            support,
            w.exponent,
            precision=bound.precision,
            max_series_terms=bound.max_series_terms,
        ) or not regular_on_cell(
            w.unit,
            x,
            support,
            w.exponent,
            precision=bound.precision,
            max_series_terms=bound.max_series_terms,
        ):
            return None
        if w.base_proof.root_count == 0:
            return 0, 0
        return (
            (1, w.exponent)
            if w.base_proof.root_count == 1 and w.base_proof.multiplicity_count == 1
            else None
        )
    if leaf.theorem == "taylor-deflation":
        if (
            not isinstance(w, TaylorDeflationWitness)
            or not isinstance(w.jets, tuple)
            or type(w.order) is not int
            or w.order < 2
            or len(w.jets) != w.order
            or not isinstance(w.center, sp.Expr)
            or w.center.has(sp.Float)
            or w.center.free_symbols
            or w.center.is_real is not True
            or w.center.is_finite is not True
        ):
            return None
        if support.contains(w.center) is not sp.S.true:
            return None
        d = derivative_formula_on_cell(
            f,
            x,
            support,
            w.order,
            precision=w.derivative.precision,
            max_series_terms=w.derivative.max_series_terms,
        )
        if (
            d is None
            or not _bound_matches(w.derivative, d, x, support)
            or w.derivative.lower <= 0 <= w.derivative.upper
        ):
            return None
        for k, value in enumerate(w.jets):
            actual = differentiate(normalize_arithmetic(f), x, k).subs(x, w.center)
            if not _formula_equal(actual, value) or not _formula_equal(
                value, sp.S.Zero
            ):
                return None
        if w.unit_lower != w.derivative.lower / sp.factorial(
            w.order
        ) or w.unit_upper != w.derivative.upper / sp.factorial(w.order):
            return None
        contains = region.contains(w.center)
        if contains is sp.S.true:
            return 1, w.order
        return (0, 0) if contains is sp.S.false else None
    return None
