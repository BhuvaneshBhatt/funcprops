from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from sympy import Basic, Piecewise, S, sympify


class TruthValue(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


class Analyticity(str, Enum):
    ANALYTIC = "analytic"
    NOT_ANALYTIC = "not_analytic"
    UNKNOWN = "unknown"


class Meromorphicity(str, Enum):
    MEROMORPHIC = "meromorphic"
    NOT_MEROMORPHIC = "not_meromorphic"
    UNKNOWN = "unknown"


class Monotonicity(str, Enum):
    STRICTLY_INCREASING = "strictly_increasing"
    NONDECREASING = "nondecreasing"
    CONSTANT = "constant"
    NONINCREASING = "nonincreasing"
    STRICTLY_DECREASING = "strictly_decreasing"
    NOT_MONOTONE = "not_monotone"
    UNKNOWN = "unknown"


class Convexity(str, Enum):
    STRONGLY_CONVEX = "strongly_convex"
    STRICTLY_CONVEX = "strictly_convex"
    CONVEX = "convex"
    AFFINE = "affine"
    CONCAVE = "concave"
    STRICTLY_CONCAVE = "strictly_concave"
    STRONGLY_CONCAVE = "strongly_concave"
    LOG_CONVEX = "log_convex"
    LOG_CONCAVE = "log_concave"
    QUASICONVEX = "quasiconvex"
    QUASICONCAVE = "quasiconcave"
    PSEUDOCONVEX = "pseudoconvex"
    PSEUDOCONCAVE = "pseudoconcave"
    NEITHER = "neither"
    UNKNOWN = "unknown"


class Sign(str, Enum):
    POSITIVE = "positive"
    NONNEGATIVE = "nonnegative"
    ZERO = "zero"
    NONPOSITIVE = "nonpositive"
    NEGATIVE = "negative"
    SIGN_CHANGING = "sign_changing"
    UNKNOWN = "unknown"


class Boundedness(str, Enum):
    BOUNDED = "bounded"
    BOUNDED_ABOVE = "bounded_above"
    BOUNDED_BELOW = "bounded_below"
    UNBOUNDED = "unbounded"
    UNKNOWN = "unknown"


class Oscillation(str, Enum):
    NONOSCILLATORY = "nonoscillatory"
    FINITELY_OSCILLATORY = "finitely_oscillatory"
    OSCILLATORY = "oscillatory"
    UNKNOWN = "unknown"


class Periodicity(str, Enum):
    CONSTANT = "constant"
    PERIODIC = "periodic"
    APERIODIC = "aperiodic"
    UNKNOWN = "unknown"


class Symmetry(str, Enum):
    EVEN = "even"
    ODD = "odd"
    BOTH = "both"
    NEITHER = "neither"
    CENTRAL = "central"
    UNKNOWN = "unknown"


class Homogeneity(str, Enum):
    HOMOGENEOUS = "homogeneous"
    NOT_HOMOGENEOUS = "not_homogeneous"
    UNKNOWN = "unknown"


class Continuity(str, Enum):
    CONTINUOUS = "continuous"
    DISCONTINUOUS = "discontinuous"
    UNKNOWN = "unknown"


class Differentiability(str, Enum):
    SMOOTH = "smooth"
    CK = "Ck"
    DIFFERENTIABLE = "differentiable"
    NOT_DIFFERENTIABLE = "not_differentiable"
    UNKNOWN = "unknown"


class SingularityKind(str, Enum):
    POLE = "pole"
    ESSENTIAL = "essential"
    BRANCH_POINT = "branch_point"
    BRANCH_CUT = "branch_cut"
    DEFINITION_CUT = "definition_cut"
    REMOVABLE = "removable"
    DISCONTINUITY = "discontinuity"


@dataclass(frozen=True)
class ConditionalValue:
    value: Any
    condition: Basic = S.true


@dataclass(frozen=True)
class Singularity:
    kind: SingularityKind
    condition: Basic
    guard: Basic = S.true
    multiplicity: int | Basic | None = None
    source: str | None = None

    @property
    def locus(self):
        return self.condition


@dataclass(frozen=True)
class PropertyResult:
    primary: Any
    cases: tuple[ConditionalValue, ...] = ()
    all_properties: tuple[Any, ...] = ()
    source: str | None = None
    exceptions: tuple[Any, ...] = ()
    evidence: tuple[Any, ...] = ()

    def as_detailed_result(self):
        """Project this result onto the package-wide detailed-result protocol."""
        return as_detailed_result(self)

    def as_piecewise(self):
        if not self.cases:
            return self.primary
        pairs = []
        for c in self.cases:
            if isinstance(c.value, Basic):
                v = c.value
            elif isinstance(c.value, Enum):
                v = sympify(c.value.value, evaluate=False)
            else:
                v = sympify(c.value, evaluate=False)
            pairs.append((v, c.condition))
        return Piecewise(*pairs)


@dataclass(frozen=True)
class DetailedPropertyResult:
    """Uniform non-breaking view of detailed property-analysis output.

    Public property functions may keep returning their compact enums, sets, or
    specialized result dataclasses.  ``as_detailed_result`` projects any such
    value onto this common protocol for downstream orchestration.
    """

    primary: Any
    cases: tuple[ConditionalValue, ...] = ()
    domain: Any = None
    complete: bool | None = None
    source: str | None = None
    evidence: tuple[Any, ...] = ()
    certificate: Any = None
    exceptions: tuple[Any, ...] = ()
    all_properties: tuple[Any, ...] = ()


@runtime_checkable
class SupportsDetailedPropertyResult(Protocol):
    """Structural protocol implemented by objects exposing detailed results."""

    def as_detailed_result(self) -> DetailedPropertyResult: ...


def as_detailed_result(value, *, domain=None, source=None, complete=None):
    """Return a uniform detailed view without changing compact public APIs."""
    if isinstance(value, DetailedPropertyResult):
        return value
    if isinstance(value, PropertyResult):
        certificate = next(
            (
                item
                for item in value.evidence
                if hasattr(item, "verify") or hasattr(item, "proof")
            ),
            None,
        )
        return DetailedPropertyResult(
            primary=value.primary,
            cases=value.cases,
            domain=domain,
            complete=complete,
            source=source or value.source,
            evidence=value.evidence,
            certificate=certificate,
            exceptions=value.exceptions,
            all_properties=value.all_properties,
        )
    primary = getattr(value, "classification", value)
    evidence = tuple(getattr(value, "evidence", ()))
    exceptions = tuple(getattr(value, "exceptional_loci", ()))
    result_domain = domain if domain is not None else getattr(value, "domain", None)
    return DetailedPropertyResult(
        primary=primary,
        cases=tuple(getattr(value, "cases", ())),
        domain=result_domain,
        complete=complete,
        source=source or getattr(value, "source", None),
        evidence=evidence,
        certificate=getattr(value, "certificate", None),
        exceptions=exceptions,
        all_properties=tuple(getattr(value, "all_properties", ())),
    )
