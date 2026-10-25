"""Compact-core and strict-tail proofs with source and coverage binding."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .asymptotic_tails import TailSignCertificate, certify_tail_sign
from .certified_inequalities import InequalityCertificate, certify_inequality
from .domain_tracking import track_domain
from .exactness import certify_identity_equal
from .results import TruthValue


@dataclass(frozen=True)
class GlobalInequalityCertificate:
    """Combine a compact inequality proof with rigorous tail bounds."""

    expression: sp.Expr
    variable: sp.Symbol
    relation: str
    core: sp.Interval
    core_certificate: InequalityCertificate
    left_tail: TailSignCertificate | None
    right_tail: TailSignCertificate | None
    complete: bool

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return (
            "global-real-positivity"
            if self.complete
            else "proved-core-and-recorded-tails"
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                type(self.complete) is not bool
                or self.relation != ">"
                or not isinstance(self.core, sp.Interval)
            ):
                return False
            if (
                self.core.left_open
                or self.core.right_open
                or self.core.start.is_finite is not True
                or self.core.end.is_finite is not True
            ):
                return False
            cc = self.core_certificate
            if (
                not isinstance(cc, InequalityCertificate)
                or cc.classification is not TruthValue.TRUE
                or cc.relation != ">"
                or cc.variable != self.variable
                or cc.domain != self.core
                or not cc.verify()
            ):
                return False
            original = (
                cc.source_expression
                if cc.source_expression is not None
                else cc.expression
            )
            if certify_identity_equal(cc.expression, self.expression) is not True:
                return False
            # Binding the original source to the core prevents cancellation from
            # restoring holes; complete global claims also require definition on R.
            source_record = track_domain(self.expression, self.variable, self.core)
            if not source_record.complete or source_record.effective != self.core:
                return False
            if (
                certify_identity_equal(sp.simplify(original), self.expression)
                is not True
            ):
                return False
            for tail, direction, boundary in [
                (self.left_tail, -1, self.core.start),
                (self.right_tail, 1, self.core.end),
            ]:
                if tail is None:
                    continue
                if (
                    not isinstance(tail, TailSignCertificate)
                    or tail.expression != self.expression
                    or tail.variable != self.variable
                    or type(tail.direction) is not int
                    or tail.direction != direction
                    or tail.sign != 1
                    or not tail.verify()
                ):
                    return False
                T = sp.Abs(tail.threshold)
                if T.is_finite is not True or T.is_real is not True:
                    return False
                if (
                    T <= -boundary if direction == -1 else T <= boundary
                ) is not sp.S.true:
                    return False
            complete = self.left_tail is not None and self.right_tail is not None
            if self.complete is not complete:
                return False
            if complete:
                record = track_domain(self.expression, self.variable, sp.S.Reals)
                return record.complete and record.effective is sp.S.Reals
            return True
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


def certify_global_positive(expr, var, *, core_radius=8):
    """Combine a compact positivity proof with rigorous tail exclusions."""

    x, f, R = sp.sympify(var), sp.sympify(expr), sp.sympify(core_radius)
    if R.is_positive is not True or R.is_finite is not True or R.is_real is not True:
        raise ValueError("core_radius must be positive, real and finite")
    core = sp.Interval(-R, R)
    cc = certify_inequality(f, 0, x, core, relation=">", max_depth=10)
    lt = certify_tail_sign(f, x, direction=-1, threshold=-R)
    rt = certify_tail_sign(f, x, direction=1, threshold=R)
    complete = (
        cc.classification is TruthValue.TRUE and lt is not None and rt is not None
    )
    out = GlobalInequalityCertificate(f, x, ">", core, cc, lt, rt, complete)
    if complete and not out.verify():
        from dataclasses import replace

        out = replace(out, complete=False)
    return out
