"""Conservative real inequality proofs preserving source domains and coverage."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .certified_balls import RealBallCertificate, certified_real_ball
from .component_optimization import ComponentMinimumResult, finite_component_minimum
from .domain_tracking import DomainRecord, track_domain
from .exactness import certify_identity_equal
from .results import TruthValue
from .root_coverage import RootCoverageCertificate, root_coverage
from .source_syntax import normalize_arithmetic
from .work_budget import budgeted_operation

_RELATIONS = {">", "<", ">=", "<="}


def _proved(ball, relation):
    return {
        ">": ball.lower.is_positive is True,
        "<": ball.upper.is_negative is True,
        ">=": ball.lower.is_nonnegative is True,
        "<=": ball.upper.is_nonpositive is True,
    }.get(relation, False)


def _violated(value, relation):
    return {
        ">": value.is_nonpositive is True,
        "<": value.is_nonnegative is True,
        ">=": value.is_negative is True,
        "<=": value.is_positive is True,
    }[relation]


def _minimum_proves(result, relation):
    if not result.complete or result.infimum is None:
        return False
    bound = result.infimum
    if relation in (">=", "<="):
        return bound.is_nonnegative is True
    return bound.is_positive is True or (bound == 0 and not result.attained)


@dataclass(frozen=True)
class _FiniteSignCertificate:
    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.FiniteSet
    relation: str

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        record = track_domain(self.expression, self.variable, self.domain)
        if not record.complete or record.effective != self.domain:
            return False
        return all(
            _value_proves(self.expression.subs(self.variable, p), self.relation)
            for p in self.domain
        )


def _value_proves(value, relation):
    if value.is_finite is not True or value.is_real is not True:
        return False
    return {
        ">": value.is_positive is True,
        "<": value.is_negative is True,
        ">=": value.is_nonnegative is True,
        "<=": value.is_nonpositive is True,
    }[relation]


@dataclass(frozen=True)
class InequalityCertificate:
    """Bind a real inequality to its expression, domain and sufficient theorem."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Interval
    relation: str
    classification: TruthValue
    source: str
    evidence: object = None
    source_expression: sp.Expr | None = None
    domain_record: DomainRecord | None = None

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "inequality-on-requested-interval"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return self._verify()
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
            RecursionError,
        ):
            return False

    def _verify(self):
        # UNKNOWN is a result, not a proof; FALSE requires a point witness.
        if (
            self.classification not in (TruthValue.TRUE, TruthValue.FALSE)
            or self.relation not in _RELATIONS
            or not isinstance(self.domain, sp.Interval)
        ):
            return False
        original = (
            self.expression
            if self.source_expression is None
            else self.source_expression
        )
        record = track_domain(original, self.variable, self.domain)
        if not record.complete or record.effective != self.domain:
            return False
        if self.domain_record is not None and not self.domain_record.matches(record):
            return False
        # Check the identity only after the raw source domain above. Calling
        # general simplify on held `1 - 1*0` can raise InconsistentAssumptions
        # inside SymPy's integer-parity deductions, depending on cache history.
        # The exact identity oracle accepts this syntax directly; the extra
        # simplify was unnecessary and made valid replay intermittently fail.
        if (
            certify_identity_equal(normalize_arithmetic(original), self.expression)
            is not True
        ):
            return False
        if self.source == "point-counterexample":
            if (
                self.classification is not TruthValue.FALSE
                or not isinstance(self.evidence, tuple)
                or len(self.evidence) != 2
            ):
                return False
            point, value = self.evidence
            return (
                self.domain.contains(point) is sp.S.true
                and value == self.expression.subs(self.variable, point)
                and value.is_real is True
                and value.is_finite is True
                and _violated(value, self.relation)
            )
        if self.classification is not TruthValue.TRUE:
            return False
        if self.source == "piecewise-assembly":
            from .piecewise_proofs import piecewise_cells

            data = piecewise_cells(self.expression, self.variable, self.domain)
            if (
                data is None
                or not isinstance(self.evidence, tuple)
                or len(self.evidence) != len(data[1])
            ):
                return False
            for (branch, region), child in zip(data[1], self.evidence, strict=True):
                if not isinstance(
                    child, (InequalityCertificate, _FiniteSignCertificate)
                ):
                    return False
                if (
                    isinstance(child, InequalityCertificate)
                    and child.classification is not TruthValue.TRUE
                ):
                    return False
                if (
                    child.expression != sp.simplify(branch)
                    or child.variable != self.variable
                    or child.domain != region
                    or child.relation != self.relation
                    or not child.verify()
                ):
                    return False
            return True
        if self.source == "nonnegative-with-zero-exclusion":
            if (
                self.relation not in (">", "<")
                or not isinstance(self.evidence, tuple)
                or len(self.evidence) != 2
            ):
                return False
            ball, coverage = self.evidence
            return (
                isinstance(ball, RealBallCertificate)
                and ball.verify()
                and ball.expression == self.expression
                and ball.variable == self.variable
                and ball.domain == self.domain
                and _proved(ball, ">=" if self.relation == ">" else "<=")
                and isinstance(coverage, RootCoverageCertificate)
                and coverage.verify()
                and coverage.complete
                and coverage.root_count == 0
                and coverage.expression == self.expression
                and coverage.variable == self.variable
                and coverage.domain == self.domain
            )
        if self.source == "exact-minimum":
            minimum = self.evidence
            target = (
                self.expression if self.relation in (">", ">=") else -self.expression
            )
            return (
                isinstance(minimum, ComponentMinimumResult)
                and minimum.expression == target
                and minimum.variable == self.variable
                and minimum.domain == self.domain
                and minimum.verify()
                and _minimum_proves(minimum, self.relation)
            )
        if self.source == "outward-interval":
            ball = self.evidence
            return (
                isinstance(ball, RealBallCertificate)
                and ball.expression == self.expression
                and ball.variable == self.variable
                and ball.domain == self.domain
                and ball.verify()
                and _proved(ball, self.relation)
            )
        if self.source == "interval-subdivision":
            if not isinstance(self.evidence, tuple) or len(self.evidence) not in (2, 3):
                return False
            children = self.evidence[:2]
            if any(
                not isinstance(c, InequalityCertificate)
                or c.classification is not TruthValue.TRUE
                or c.variable != self.variable
                or c.relation != self.relation
                or c.expression != self.expression
                or (
                    c.source_expression
                    if c.source_expression is not None
                    else c.expression
                )
                != original
                or not c.verify()
                for c in children
            ):
                return False
            return (
                all(
                    sp.Complement(c.domain, self.domain) is sp.S.EmptySet
                    for c in children
                )
                and sp.Union(*(c.domain for c in children)) == self.domain
            )
        return False


@budgeted_operation
def certify_inequality(
    lhs,
    rhs,
    var,
    domain,
    *,
    relation=">",
    max_depth=8,
    precision=30,
    max_precision=240,
    max_refinements=3,
):
    """Prove a supported real inequality on its effective source domain."""

    if relation not in _RELATIONS:
        raise ValueError("relation must be >, <, >= or <=")
    if type(max_depth) is not int or max_depth < 0:
        raise ValueError("max_depth must be a nonnegative integer")
    if (
        type(precision) is not int
        or precision < 2
        or type(max_precision) is not int
        or max_precision < precision
    ):
        raise ValueError("invalid precision bounds")
    if type(max_refinements) is not int or max_refinements < 0:
        raise ValueError("max_refinements must be a nonnegative integer")
    lhs, rhs, x = sp.sympify(lhs), sp.sympify(rhs), sp.sympify(var)
    original = sp.Add(lhs, sp.Mul(-1, rhs, evaluate=False), evaluate=False)
    record = track_domain(original, x, domain)
    f = sp.simplify(normalize_arithmetic(original))

    def result(classification, source, evidence=None):
        return InequalityCertificate(
            f, x, domain, relation, classification, source, evidence, original, record
        )

    if (
        not isinstance(domain, sp.Interval)
        or not record.complete
        or record.effective != domain
    ):
        return result(TruthValue.UNKNOWN, "unresolved-source-domain")
    target = f if relation in (">", ">=") else -f
    minimum = finite_component_minimum(target, x, domain)
    if _minimum_proves(minimum, relation):
        return result(TruthValue.TRUE, "exact-minimum", minimum)
    points = [sp.S.Zero, sp.S.One, -sp.S.One, domain.start, domain.end]
    if domain.start.is_finite is True and domain.end.is_finite is True:
        points.append((domain.start + domain.end) / 2)
    if minimum.complete and isinstance(minimum.minimizers, sp.FiniteSet):
        points.extend(minimum.minimizers)
    for point in points:
        if domain.contains(point) is sp.S.true:
            value = f.subs(x, point)
            if (
                value.is_real is True
                and value.is_finite is True
                and _violated(value, relation)
            ):
                return result(TruthValue.FALSE, "point-counterexample", (point, value))
    if f.has(sp.Piecewise):
        from .piecewise_proofs import piecewise_cells

        data = piecewise_cells(f, x, domain)
        if data is not None:
            children = []
            for branch, region in data[1]:
                if isinstance(region, sp.FiniteSet):
                    child = _FiniteSignCertificate(
                        sp.simplify(branch), x, region, relation
                    )
                else:
                    child = certify_inequality(
                        branch,
                        0,
                        x,
                        region,
                        relation=relation,
                        max_depth=max_depth,
                        precision=precision,
                        max_precision=max_precision,
                        max_refinements=max_refinements,
                    )
                    if (
                        child.classification is TruthValue.FALSE
                        and child.source == "point-counterexample"
                    ):
                        point, _ = child.evidence
                        return result(
                            TruthValue.FALSE,
                            "point-counterexample",
                            (point, f.subs(x, point)),
                        )
                children.append(child)
            if all(
                c.verify()
                and (
                    not isinstance(c, InequalityCertificate)
                    or c.classification is TruthValue.TRUE
                )
                for c in children
            ):
                return result(TruthValue.TRUE, "piecewise-assembly", tuple(children))
    ball = certified_real_ball(
        f,
        x,
        domain,
        precision=precision,
        max_precision=max_precision,
        max_refinements=max_refinements,
        relation=relation,
    )
    if ball is not None and _proved(ball, relation):
        return result(TruthValue.TRUE, "outward-interval", ball)
    if (
        ball is not None
        and relation in (">", "<")
        and _proved(ball, ">=" if relation == ">" else "<=")
    ):
        coverage = root_coverage(f, x, domain, max_depth=max_depth)
        if coverage.complete and coverage.root_count == 0 and coverage.verify():
            return result(
                TruthValue.TRUE, "nonnegative-with-zero-exclusion", (ball, coverage)
            )
    if ball is not None:
        opposite = {
            ">": ball.upper.is_nonpositive is True,
            "<": ball.lower.is_nonnegative is True,
            ">=": ball.upper.is_negative is True,
            "<=": ball.lower.is_positive is True,
        }[relation]
        if opposite:
            return result(TruthValue.UNKNOWN, "inconclusive")
    # Subdivision tightens enclosures when the exact and coverage routes decline.
    if max_depth and domain.start.is_finite is True and domain.end.is_finite is True:
        mid = (domain.start + domain.end) / 2
        if (mid > domain.start) is sp.S.true and (mid < domain.end) is sp.S.true:
            left = sp.Interval(domain.start, mid, domain.left_open, False)
            right = sp.Interval(mid, domain.end, False, domain.right_open)
            a = certify_inequality(
                lhs,
                rhs,
                x,
                left,
                relation=relation,
                max_depth=max_depth - 1,
                precision=precision,
                max_precision=max_precision,
                max_refinements=max_refinements,
            )
            b = certify_inequality(
                lhs,
                rhs,
                x,
                right,
                relation=relation,
                max_depth=max_depth - 1,
                precision=precision,
                max_precision=max_precision,
                max_refinements=max_refinements,
            )
            if (
                a.classification is TruthValue.TRUE
                and b.classification is TruthValue.TRUE
            ):
                return result(TruthValue.TRUE, "interval-subdivision", (a, b))
    return result(TruthValue.UNKNOWN, "inconclusive")
