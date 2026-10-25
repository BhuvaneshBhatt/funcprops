"""Immutable root-coverage records, separated from search and proof construction."""

from dataclasses import dataclass
from enum import Enum

import sympy as sp


class CheckOutcome(str, Enum):
    """Classify proof validity, coverage, unsupported premises and exhausted effort."""

    LOCAL_VALID = "valid-local-proof"
    COMPLETE = "complete-coverage"
    INADMISSIBLE = "proved-inadmissible-stratum"
    REJECTED = "rejected-evidence"
    UNSUPPORTED = "unsupported-replay"
    EXHAUSTED = "resource-exhaustion"


@dataclass(frozen=True)
class CheckResult:
    """Report replay validity separately from exhaustive coverage and its reason."""

    outcome: CheckOutcome
    certified: bool | None
    complete: bool
    reason: str | None = None


@dataclass(frozen=True)
class CoverageContext:
    """Bind a real root query to its source, domains, assumptions and branch premises."""

    expression: sp.Expr
    variable: sp.Symbol
    requested: sp.Set
    effective: sp.Set
    domain_record: object
    source_syntax: str
    coordinate_assumptions: tuple
    parameter_guard: object = sp.S.true
    substitutions: tuple = ()
    branch_context: object = None


@dataclass(frozen=True)
class EnclosureWitness:
    """Bound the source image on one real cell by exact rational endpoints."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    lower: sp.Rational
    upper: sp.Rational
    precision: int
    max_series_terms: int = 4096
    grammar_version: int = 1
    branch_context: object = None

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        from .coverage_checker import check_enclosure

        return check_enclosure(self)


@dataclass(frozen=True)
class CellDomainWitness:
    """Full requested-cell definition from raw-source outward evaluations."""

    expression: sp.Expr
    variable: sp.Symbol
    requested: sp.Set
    cells: tuple
    schema_version: int = 1

    @property
    def effective(self):
        return self.requested

    @property
    def complete(self):
        return True

    @property
    def reason(self):
        return None

    @property
    def natural_complete(self):
        return False

    @property
    def natural(self):
        return None

    @property
    def scope(self):
        return "definition-on-requested-cells"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        from .coverage_checker import check_cell_domain

        return check_cell_domain(self)


@dataclass(frozen=True)
class MonotoneWitness:
    """Store derivative and endpoint bounds for a monotone root count."""

    derivative: EnclosureWitness
    left: EnclosureWitness
    right: EnclosureWitness


@dataclass(frozen=True)
class NewtonWitness:
    """Store the midpoint, interval derivative and checked real Newton image."""

    midpoint: sp.Expr
    derivative: EnclosureWitness
    value: EnclosureWitness
    image_lower: sp.Expr
    image_upper: sp.Expr


@dataclass(frozen=True)
class TaylorWitness:
    """Store a Taylor polynomial and outward Lagrange remainder bounds."""

    center: sp.Expr
    order: int
    coefficients: tuple
    polynomial: sp.Expr
    derivative: EnclosureWitness
    polynomial_bound: EnclosureWitness
    remainder_lower: sp.Expr
    remainder_upper: sp.Expr


@dataclass(frozen=True)
class RationalWitness:
    """Bind a rational function to exact numerator and denominator coefficients."""

    numerator: tuple
    denominator: tuple


@dataclass(frozen=True)
class ZeroSubsetWitness:
    """Transfer a zero count from a checked parent to a subset."""

    parent: object


@dataclass(frozen=True)
class SourceFormulaWitness:
    """Bind a local count to an exact source-formula proof."""

    proof: object


@dataclass(frozen=True)
class LocatedSubsetWitness:
    """Locate a parent's unique root and retain its excluded complement."""

    parent: object
    locator: object


@dataclass(frozen=True)
class PowerFactorWitness:
    """Relate root multiplicity to a power factor and a nonvanishing unit."""

    base: sp.Expr
    exponent: int
    unit: sp.Expr
    base_proof: object
    unit_bound: EnclosureWitness


@dataclass(frozen=True)
class TaylorDeflationWitness:
    """Prove an exact root order from jets and a bounded Taylor remainder."""

    center: sp.Expr
    order: int
    jets: tuple
    derivative: EnclosureWitness
    unit_lower: sp.Expr
    unit_upper: sp.Expr


@dataclass(frozen=True)
class CoverageLeaf:
    """Bind a local real root count to a theorem, region and witness."""

    context: CoverageContext
    region: sp.Set
    theorem: str
    root_count: object
    multiplicity_count: object
    witness: object
    roots: tuple = ()
    schema_version: int = 1

    @property
    def expression(self):
        return self.context.expression

    @property
    def variable(self):
        return self.context.variable

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "local-real-root-count"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        from .coverage_checker import check_leaf

        return check_leaf(self).certified is True


@dataclass(frozen=True)
class CoverageProof:
    """Assemble local counts and unresolved regions over an effective real domain."""

    context: CoverageContext
    leaves: tuple = ()
    unresolved: sp.Set = sp.S.EmptySet
    complete: bool = False
    root_count: object = None
    multiplicity_count: object = None
    exhaustion: str | None = None
    schema_version: int = 1

    @property
    def expression(self):
        return self.context.expression

    @property
    def variable(self):
        return self.context.variable

    @property
    def scope(self):
        return "real-root-coverage-on-effective-domain"

    @property
    def certified(self):
        return self.verify()

    @property
    def obligations(self):
        if self.complete:
            return ()
        if not self.context.domain_record.complete:
            return (self.context.domain_record.reason,)
        from .enclosures import grammar_obligations

        return grammar_obligations(self.expression, self.variable) or (
            self.exhaustion or "unresolved-root-domain-or-branch-premises",
        )

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        from .coverage_checker import check_coverage

        return check_coverage(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


@dataclass(frozen=True)
class InadmissibleProof:
    """A real-valued query whose exact constant source is nonreal."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    source_syntax: str
    reason: str = "nonreal-constant-source"
    schema_version: int = 1

    @property
    def complete(self):
        return False

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "inadmissible-real-valued-stratum"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        from .coverage_checker import check_inadmissible

        return check_inadmissible(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True
