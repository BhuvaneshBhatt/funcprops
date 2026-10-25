"""Global metric regularity: Lipschitz, uniform, and Hölder continuity."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp
from sympy import S

from ..exceptions import SYMBOLIC_QUERY_ERRORS
from ..proof_cache import cached_domain_record
from ..results import (
    Boundedness,
    Continuity,
    DetailedPropertyResult,
    TruthValue,
)
from ..singularities import continuous
from ..source_syntax import differentiate
from .boundedness import boundedness
from .common import condition_to_set, normalize_domain_set
from .domain import domain as real_domain


@dataclass(frozen=True)
class LipschitzResult:
    """Record a Lipschitz classification, constant and source-domain evidence."""

    value: TruthValue
    constant: sp.Expr | None = None
    optimal: TruthValue = TruthValue.UNKNOWN
    domain: object = S.Reals
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
        return (
            "limiting-gap-lipschitz-replay"
            if self.source == "separated-limits"
            else "finite-domain-lipschitz-replay"
        )

    def verify(self):
        """Replay a finite-domain proof and its public summary fields."""
        from ..metric_proofs import FiniteLipschitzProof
        from ..seam_regularity import SeamRegularityProof
        from ..source_syntax import same_data

        if type(self.proof) is SeamRegularityProof:
            return (
                type(self) is LipschitzResult
                and self.proof.conclusion == "separated-limits"
                and self.proof.verify()
                and self.value is TruthValue.FALSE
                and self.constant is None
                and self.optimal is TruthValue.UNKNOWN
                and same_data(self.domain, self.proof.domain)
                and same_data(self.evidence, (self.proof,))
                and self.source == "separated-limits"
            )
        return (
            type(self) is LipschitzResult
            and type(self.proof) is FiniteLipschitzProof
            and self.proof.verify()
            and self.value is TruthValue.TRUE
            and self.optimal is TruthValue.TRUE
            and same_data(self.constant, self.proof.constant)
            and same_data(self.domain, self.proof.effective)
            and same_data(self.evidence, self.proof.ratios)
            and self.source == "finite-pairwise"
        )


@dataclass(frozen=True)
class HolderRegularityResult:
    """Record a Hölder exponent, constant and sufficient domain premises."""

    exponent: sp.Expr | None
    constant: sp.Expr | None = None
    optimal: TruthValue = TruthValue.UNKNOWN
    domain: object = S.Reals
    source: str | None = None
    evidence: tuple[object, ...] = ()


def _domain_set(domain, var):
    try:
        return normalize_domain_set(domain, var)
    except (TypeError, ValueError, NotImplementedError):
        return None


def _compact(domain, var):
    d = _domain_set(domain, var)
    return bool(
        d is not None
        and d.is_subset(S.Reals) is True
        and getattr(d, "is_closed", None) is True
        and d.inf.is_finite is True
        and d.sup.is_finite is True
    )


def _derivative_bound(expr, var, domain):
    # A derivative bound controls pairs of points only along an interval.
    d = _domain_set(domain, var)
    if d is None:
        return None, False
    record = cached_domain_record(expr, var, d)
    if record.complete:
        d = record.effective
    else:
        natural = condition_to_set(real_domain(expr, var), var)
        if not isinstance(natural, sp.Set) or natural.has(sp.ConditionSet):
            return None, False
        d = sp.Intersection(d, natural)
    if not isinstance(d, sp.Interval):
        return None, False
    if continuous(expr, var, domain=d) is not Continuity.CONTINUOUS:
        return None, False
    derivative = differentiate(expr, var)
    if not derivative.has(var):
        return sp.Abs(derivative), True
    if derivative.func in (sp.sin, sp.cos) or (
        derivative.is_Mul and any(a.func in (sp.sin, sp.cos) for a in derivative.args)
    ):
        if any(
            atom.args[0].is_real is not True
            for atom in derivative.atoms(sp.sin, sp.cos)
        ):
            return None, False
        coefficient = derivative
        for atom in derivative.atoms(sp.sin, sp.cos):
            coefficient = coefficient / atom
        if not coefficient.has(var):
            return sp.Abs(sp.simplify(coefficient)), True
    try:
        upper = sp.calculus.util.function_range(sp.Abs(derivative), var, d).sup
        if upper.is_finite is True and upper.is_nonnegative is True:
            return sp.simplify(upper), True
    except SYMBOLIC_QUERY_ERRORS:
        pass
    try:
        if boundedness(sp.Abs(derivative), var, domain=d) is Boundedness.BOUNDED:
            return None, True
    except SYMBOLIC_QUERY_ERRORS:
        pass
    return None, False


def _finite_lipschitz(expr, var, support):
    from ..metric_proofs import certify_finite_lipschitz

    proof = certify_finite_lipschitz(expr, var, support)
    if proof is None:
        return None
    return LipschitzResult(
        TruthValue.TRUE,
        proof.constant,
        TruthValue.TRUE,
        proof.effective,
        "finite-pairwise",
        proof.ratios,
        proof,
    )


def _limiting_gap(expr, var, support):
    if not isinstance(support, sp.Union):
        return None
    from ..seam_regularity import seam_regularity_proof

    return seam_regularity_proof(expr, var, support, "separated-limits")


def lipschitz(expr, var, *, domain=S.Reals, return_result=False):
    """Certify Lipschitz regularity and return a certified constant when known."""
    expr, var = sp.sympify(expr), sp.sympify(var)
    support = _domain_set(domain, var)
    finite = _finite_lipschitz(expr, var, support)
    gap = _limiting_gap(expr, var, support) if finite is None else None
    if finite is not None:
        result = finite
    elif gap is not None:
        result = LipschitzResult(
            TruthValue.FALSE,
            domain=gap.domain,
            source="separated-limits",
            evidence=(gap,),
            proof=gap,
        )
    elif not expr.has(var):
        result = LipschitzResult(
            TruthValue.TRUE, S.Zero, TruthValue.TRUE, domain, "constant"
        )
    elif continuous(expr, var, domain=domain) is Continuity.DISCONTINUOUS:
        result = LipschitzResult(
            TruthValue.FALSE, domain=domain, source="discontinuity"
        )
    else:
        constant, ok = _derivative_bound(expr, var, domain)
        optimal = TruthValue.UNKNOWN
        if ok and constant is not None and expr.is_polynomial(var):
            polynomial = sp.Poly(expr, var)
            if polynomial.degree() == 1 and all(
                c.is_real is True and c.is_finite is True
                for c in polynomial.all_coeffs()
            ):
                record = cached_domain_record(expr, var, _domain_set(domain, var))
                support = record.effective if record.complete else None
                # Symbolic interval endpoints can coincide under specialization.
                # Optimality needs two distinct inputs, not just an upper bound.
                if (
                    isinstance(support, sp.Interval)
                    and (support.end > support.start) is S.true
                ):
                    optimal = TruthValue.TRUE
        result = (
            LipschitzResult(
                TruthValue.TRUE,
                constant,
                optimal,
                domain,
                "bounded-derivative",
            )
            if ok
            else LipschitzResult(TruthValue.UNKNOWN, domain=domain, source="unresolved")
        )
    if return_result:
        return result
    return (
        result.constant
        if result.value is TruthValue.TRUE and result.constant is not None
        else result.value
    )


def uniformly_continuous(expr, var, *, domain=S.Reals, return_result=False):
    """Certify uniform continuity on the requested domain."""
    expr, var = sp.sympify(expr), sp.sympify(var)
    polynomial = sp.Poly(expr, var) if expr.is_polynomial(var) else None
    support = _domain_set(domain, var)
    finite = _finite_lipschitz(expr, var, support)
    gap = _limiting_gap(expr, var, support) if finite is None else None
    if finite is not None:
        continuity = Continuity.CONTINUOUS
        value, source, evidence = TruthValue.TRUE, "finite-domain", (finite,)
    elif gap is not None:
        value, source, evidence = TruthValue.FALSE, "separated-limits", (gap,)
    elif (
        domain == S.Reals
        and polynomial is not None
        and polynomial.degree() > 1
        and polynomial.LC().is_nonzero is True
    ):
        continuity = Continuity.CONTINUOUS
        value, source, evidence = TruthValue.FALSE, "nonlinear-polynomial-on-reals", ()
    else:
        continuity = continuous(expr, var, domain=domain)
        value = source = evidence = None
    if value is not None:
        pass
    elif continuity is Continuity.DISCONTINUOUS:
        value, source, evidence = TruthValue.FALSE, "discontinuity", ()
    elif _compact(domain, var) and continuity is Continuity.CONTINUOUS:
        value, source, evidence = TruthValue.TRUE, "heine-cantor", ()
    else:
        lip = lipschitz(expr, var, domain=domain, return_result=True)
        if lip.value is TruthValue.TRUE:
            value, source, evidence = TruthValue.TRUE, "lipschitz", (lip,)
        else:
            value, source, evidence = TruthValue.UNKNOWN, "unresolved", ()
    return (
        DetailedPropertyResult(value, domain=domain, source=source, evidence=evidence)
        if return_result
        else value
    )


def _power_holder(expr, var, domain):
    if isinstance(expr, sp.Pow):
        base, exponent = expr.args
    elif expr.func is sp.Abs and isinstance(expr.args[0], sp.Pow):
        base, exponent = expr.args[0].args
    else:
        return None
    if base not in (var, -var, sp.Abs(var)) or exponent.is_real is not True:
        return None
    if (
        sp.ask(sp.Q.positive(exponent)) is not True
        or sp.ask(sp.Q.lt(exponent, 1)) is not True
    ):
        return None
    d = _domain_set(domain, var)
    natural = condition_to_set(real_domain(expr, var), var)
    if d is None or natural is None:
        return None
    effective = sp.Intersection(d, natural)
    components = effective.args if isinstance(effective, sp.Union) else (effective,)
    approaches_zero = any(
        isinstance(cell, sp.Interval)
        and cell.closure.contains(0) is S.true
        and (
            cell.end is S.Infinity
            or cell.start is S.NegativeInfinity
            or cell.end.is_positive is True
            or cell.start.is_negative is True
        )
        for cell in components
    )
    if not approaches_zero:
        return None
    return exponent


def holder_regularity(expr, var, *, domain=S.Reals, return_result=False):
    """Return the strongest certified Hölder exponent in ``(0, 1]``."""
    expr, var = sp.sympify(expr), sp.sympify(var)
    finite = _finite_lipschitz(expr, var, _domain_set(domain, var))
    if finite is not None:
        result = HolderRegularityResult(
            S.One,
            finite.constant,
            TruthValue.TRUE,
            finite.domain,
            "finite-domain",
            (finite,),
        )
        return result if return_result else result.exponent
    exponent = _power_holder(expr, var, domain)
    if exponent is not None:
        result = HolderRegularityResult(
            exponent, S.One, TruthValue.TRUE, domain, "power-cusp"
        )
    else:
        lip = lipschitz(expr, var, domain=domain, return_result=True)
        result = (
            HolderRegularityResult(
                S.One, lip.constant, lip.optimal, domain, "lipschitz", (lip,)
            )
            if lip.value is TruthValue.TRUE
            else HolderRegularityResult(None, domain=domain, source="unresolved")
        )
    return result if return_result else result.exponent
