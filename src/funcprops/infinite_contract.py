"""Tail-exclusion and exhaustive periodic-family witnesses."""

from dataclasses import dataclass

import sympy as sp


@dataclass(frozen=True)
class ExponentialTailWitness:
    """Prove eventual root exclusion for a supported exponential-polynomial tail."""

    direction: int
    threshold: sp.Rational
    sign: int
    groups: tuple
    coefficient_bounds: tuple
    constant_lower: sp.Rational
    remainder_upper: sp.Rational


@dataclass(frozen=True)
class PeriodicDomainWitness:
    """Preserve source exclusions under a periodic rational-trigonometric substitution."""

    expression: sp.Expr
    variable: sp.Symbol
    requested: sp.Set
    effective: sp.Set
    excluded: sp.Set
    kind: str
    rate: sp.Rational
    phase: sp.Expr
    numerator: tuple
    denominator: tuple
    guards: tuple
    poles: tuple
    schema_version: int = 1

    @property
    def complete(self):
        return True

    @property
    def natural_complete(self):
        return True

    @property
    def reason(self):
        return None

    @property
    def scope(self):
        return "exhaustive-periodic-definition-domain"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        from .infinite_checker import check_periodic_domain

        return check_periodic_domain(self)


@dataclass(frozen=True)
class IntegerEndpointWitness:
    """Decide an exact lattice endpoint comparison."""

    quotient: sp.Expr
    floor: int
    enclosure: object = None


@dataclass(frozen=True)
class IndexRangeWitness:
    """Bind an indexed root family to its owned domain range."""

    region: sp.Set
    lower: object
    upper: object
    left: object = None
    right: object = None


@dataclass(frozen=True)
class CoveredRootFamily:
    """Represent an exhaustive indexed family with multiplicities and index bounds."""

    offset: sp.Expr
    period: sp.Expr
    multiplicity: int | None
    ranges: tuple

    def as_set(self):
        """Express the represented domain or root family as a SymPy set."""

        n = sp.Dummy("period_index", integer=True)
        pieces = []
        for w in self.ranges:
            indices = (
                sp.Range(w.lower, w.upper + 1)
                if w.lower is not sp.S.NegativeInfinity and w.upper is not sp.oo
                else sp.Intersection(sp.S.Integers, sp.Interval(w.lower, w.upper))
            )
            pieces.append(
                sp.ImageSet(sp.Lambda(n, self.offset + n * self.period), indices)
            )
        return sp.Union(*pieces)


@dataclass(frozen=True)
class PeriodicRootWitness:
    """Bind rational-trigonometric zeros to exhaustive periodic families."""

    levels: tuple
    families: tuple
    zero_function: bool = False
