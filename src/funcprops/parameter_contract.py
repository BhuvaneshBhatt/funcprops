"""Source-bound uniform box and exact parameter-partition certificates."""

from dataclasses import dataclass

import sympy as sp

from .coverage_contract import CheckOutcome, CheckResult


@dataclass(frozen=True)
class BoxEnclosureWitness:
    """Enclose an expression over a real coordinate/parameter box."""

    expression: sp.Expr
    domains: tuple
    lower: sp.Rational
    upper: sp.Rational
    precision: int
    max_series_terms: int = 4096
    schema_version: int = 1

    @property
    def scope(self):
        return "outward-value-enclosure-on-real-box"

    @property
    def complete(self):
        return self.verify()

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        from .parameter_checker import check_box_enclosure

        return check_box_enclosure(self)


@dataclass(frozen=True)
class UniformParameterWitness:
    """Prove a root count uniformly across a parameter box."""

    value: BoxEnclosureWitness
    derivative: BoxEnclosureWitness | None = None
    left: BoxEnclosureWitness | None = None
    right: BoxEnclosureWitness | None = None


@dataclass(frozen=True)
class UniformZeroSubsetWitness:
    """Transfer uniform root exclusion to a subset."""

    parent: object


@dataclass(frozen=True)
class UniformParameterCertificate:
    """Bind a uniform root count to parameter and coordinate premises."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    parameter_domains: tuple
    source_syntax: str
    coordinate_assumptions: tuple
    root_count: object = None
    multiplicity_count: object = None
    witness: UniformParameterWitness | None = None
    obligations: tuple = ()
    schema_version: int = 1

    @property
    def complete(self):
        return self.root_count is not None and not self.obligations

    @property
    def scope(self):
        return "uniform-root-count-on-real-parameter-box"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        from .parameter_checker import check_uniform_parameters

        return check_uniform_parameters(self)

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


@dataclass(frozen=True)
class UniformParameterCover:
    """Assemble a complete coordinate cover over a parameter box."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    parameter_domains: tuple
    source_syntax: str
    coordinate_assumptions: tuple
    leaves: tuple = ()
    unresolved: sp.Set = sp.S.EmptySet
    complete: bool = False
    root_count: object = None
    multiplicity_count: object = None
    tested: int = 0
    exhaustion: str | None = None
    schema_version: int = 1

    @property
    def scope(self):
        return "uniform-parameter-root-count-with-full-variable-cover"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        from .parameter_checker import check_uniform_cover

        return check_uniform_cover(self)

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


@dataclass(frozen=True)
class PolynomialSignWitness:
    """Prove a polynomial coefficient or discriminant sign on a stratum."""

    coefficients: tuple
    sample: sp.Expr
    sign: int


@dataclass(frozen=True)
class PolynomialParameterWitness:
    """Count polynomial roots under a checked parameter condition."""

    signs: tuple


@dataclass(frozen=True)
class MonotoneParameterWitness:
    """Prove a uniform monotone root count under a parameter guard."""

    base: sp.Expr
    derivative: object
    left_value: sp.Expr
    right_value: sp.Expr


@dataclass(frozen=True)
class ExponentialParameterWitness:
    """Count a supported exponential family on a parameter stratum."""

    rate: sp.Rational
    phase: sp.Rational
    scale: sp.Rational
    offset: sp.Rational


@dataclass(frozen=True)
class ParameterRootCell:
    """Record one guarded parameter cell and its root count witness."""

    region: sp.Set
    theorem: str
    root_count: object
    multiplicity_count: object
    witness: object


@dataclass(frozen=True)
class ParameterCoverageProof:
    """Assemble guarded root counts over exhaustive parameter strata."""

    expression: sp.Expr
    variable: sp.Symbol
    parameter: sp.Symbol
    domain: sp.Set
    parameter_domain: sp.Set
    source_syntax: str
    coordinate_assumptions: tuple
    cells: tuple = ()
    unresolved: sp.Set = sp.S.EmptySet
    complete: bool = False
    exhaustion: str | None = None
    schema_version: int = 1

    @property
    def scope(self):
        return "exact-one-real-parameter-root-coverage"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        from .parameter_checker import check_parameter_coverage

        return check_parameter_coverage(self)

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


@dataclass(frozen=True)
class SpecializedParameterProof:
    """Bind a parameter proof to exact substitutions satisfying its guard."""

    parent: ParameterCoverageProof
    value: sp.Expr
    schema_version: int = 1

    @property
    def expression(self):
        from .enclosures import preserve_replace

        return preserve_replace(
            self.parent.expression, {self.parent.parameter: self.value}
        )

    @property
    def variable(self):
        return self.parent.variable

    @property
    def parameter_guard(self):
        return sp.Eq(self.parent.parameter, self.value)

    @property
    def cell(self):
        if (
            not isinstance(self.value, sp.Expr)
            or self.value.has(sp.Float)
            or self.value.free_symbols
            or self.value.is_real is not True
            or self.value.is_finite is not True
        ):
            return None
        matches = [
            c for c in self.parent.cells if c.region.contains(self.value) is sp.S.true
        ]
        return matches[0] if len(matches) == 1 else None

    @property
    def root_count(self):
        return self.cell.root_count if self.cell else None

    @property
    def multiplicity_count(self):
        return self.cell.multiplicity_count if self.cell else None

    @property
    def complete(self):
        return self.cell is not None

    @property
    def scope(self):
        return "exact-parameter-specialization-of-checked-stratum"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        if (
            type(self) is not SpecializedParameterProof
            or type(self.schema_version) is not int
            or self.schema_version != 1
        ):
            return CheckResult(
                CheckOutcome.UNSUPPORTED,
                None,
                False,
                "unsupported-specialization-version",
            )
        if type(self.parent) is not ParameterCoverageProof:
            return CheckResult(
                CheckOutcome.REJECTED, False, False, "invalid-specialization-parent"
            )
        checked = self.parent.check()
        if checked.certified is not True:
            return checked
        if self.cell is None:
            return CheckResult(
                CheckOutcome.UNSUPPORTED,
                None,
                False,
                "unresolved-or-inadmissible-parameter-value",
            )
        return CheckResult(CheckOutcome.COMPLETE, True, True)

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True
