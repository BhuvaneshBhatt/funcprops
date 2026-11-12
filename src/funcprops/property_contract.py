"""Native property-level coverage contract; geometry is never an optimum proof alone."""

from dataclasses import dataclass

import sympy as sp


@dataclass(frozen=True)
class PropertyPiece:
    """Record a supported property conclusion on an owned domain component."""

    expression: sp.Expr
    domain: sp.Set
    critical_coverage: object = None
    critical_points: tuple | None = None
    zero_coverage: object = None
    zero_points: tuple | None = None
    derivative_samples: tuple = ()
    sign_samples: tuple = ()


@dataclass(frozen=True)
class PropertyConclusion:
    """Store an assembled mathematical value and its proof status."""

    name: str
    value: object = None
    complete: bool = False
    obligations: tuple = ()


@dataclass(frozen=True)
class PropertyCoverageProof:
    """Bind property conclusions to source domains, root coverage and value bounds."""

    expression: sp.Expr
    variable: sp.Symbol
    requested: sp.Set
    domain_record: object
    source_syntax: str
    coordinate_assumptions: tuple
    pieces: tuple = ()
    candidate_order: tuple | None = None
    comparisons: tuple = ()
    conclusions: tuple = ()
    tested: int = 0
    exhaustion: str | None = None
    schema_version: int = 1

    def conclusion(self, name):
        """Select the recorded property conclusion by name."""
        return next(c for c in self.conclusions if c.name == name)

    @property
    def complete(self):
        """Completion status for this record's stated scope; replay validity is separate."""
        return len(self.conclusions) == 5 and all(c.complete for c in self.conclusions)

    @property
    def range_complete(self):
        """Whether the requested image is established completely."""
        return self.conclusion("range").complete

    @property
    def optimization_complete(self):
        """Whether the stated optimization conclusion is complete."""
        return (
            self.conclusion("minimum").complete and self.conclusion("maximum").complete
        )

    @property
    def sign_complete(self):
        """Whether sign information covers the requested source."""
        return self.conclusion("sign").complete

    @property
    def monotonicity_complete(self):
        """Whether monotonicity information covers the requested source."""
        return self.conclusion("monotonicity").complete

    @property
    def image(self):
        """Image set established on the effective source."""
        return self.conclusion("range").value

    @property
    def infimum(self):
        """Established lower extremal value, with attainment reported separately."""
        value = self.conclusion("minimum").value
        return None if value is None else value[0]

    @property
    def minimizers(self):
        """Source points proved to attain the infimum."""
        value = self.conclusion("minimum").value
        return None if value is None else value[1]

    @property
    def supremum(self):
        """Established upper extremal value, with attainment reported separately."""
        value = self.conclusion("maximum").value
        return None if value is None else value[0]

    @property
    def maximizers(self):
        """Source points proved to attain the supremum."""
        value = self.conclusion("maximum").value
        return None if value is None else value[1]

    @property
    def scope(self):
        """Scope identifier: ``finite-component-property-coverage``."""
        return "finite-component-property-coverage"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        from .property_checker import check_property_coverage

        return check_property_coverage(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    @property
    def certified(self):
        """Replay acceptance; a valid partial record need not be complete."""
        return self.verify()
