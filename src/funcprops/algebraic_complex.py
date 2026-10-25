"""Source-bound adaptation of algroots' exact algebraic root certificates.

This is declared-backend replay, not the native interval/contour proof kernel.
All algebraic branches are enumerated before principal-branch/domain filtering.
"""

from dataclasses import dataclass
from math import prod

import sympy as sp

from .complex_coverage import CoverageRectangle
from .coverage_contract import CheckOutcome, CheckResult
from .engine import truth_bool
from .exactness import certify_zero

_ERRORS = (AttributeError, TypeError, ValueError, ArithmeticError, NotImplementedError)
_BACKEND = "algroots-exact-rur"


def _zero(value):
    if value.is_zero is not None:
        return value.is_zero
    try:
        return certify_zero(value)
    except (sp.PolynomialError, *_ERRORS):
        if value.is_algebraic is True and not value.free_symbols:
            field = sp.QQ.algebraic_field(value)
            return field.from_sympy(value) == field.zero
        return None


def _equal(left, right):
    if left == right:
        return True
    if (
        isinstance(left, sp.CRootOf)
        and isinstance(right, sp.CRootOf)
        and left.poly == right.poly
    ):
        return left.index == right.index
    return _zero(left - right)


def algebraic_source(f, z):
    """Recognize finite exact algebraic arithmetic without rebuilding its source."""
    if f == z:
        return True
    if not f.has(z):
        return (
            not f.free_symbols
            and f.is_algebraic is True
            and f.is_finite is True
            and not f.has(sp.Float)
        )
    if f.is_Add or f.is_Mul:
        return all(algebraic_source(a, z) for a in f.args)
    return f.is_Pow and isinstance(f.exp, sp.Rational) and algebraic_source(f.base, z)


def _condition_supported(c, z):
    if c in (sp.S.true, sp.S.false):
        return True
    if isinstance(c, (sp.Equality, sp.Unequality)):
        return all(algebraic_source(a, z) for a in c.args)
    return isinstance(c, (sp.And, sp.Or, sp.Not)) and all(
        _condition_supported(a, z) for a in c.args
    )


def _domain_supported(domain):
    if domain in (sp.S.Complexes, sp.S.Reals, sp.S.EmptySet):
        return True
    if isinstance(domain, sp.FiniteSet):
        return all(
            v.is_algebraic is True
            and v.is_finite is True
            and not v.free_symbols
            and not v.has(sp.Float)
            for v in domain
        )
    if isinstance(domain, sp.Interval):
        return all(
            v in (-sp.oo, sp.oo)
            or (
                v.is_algebraic is True
                and v.is_real is True
                and not v.free_symbols
                and not v.has(sp.Float)
            )
            for v in (domain.start, domain.end)
        )
    return isinstance(domain, (sp.Union, sp.Intersection, sp.Complement)) and all(
        _domain_supported(a) for a in domain.args
    )


def algebraic_complex_supported(f, z, rectangle, domain, condition):
    """Test whether exact algebraic complex-root enumeration can handle the source."""

    return (
        isinstance(z, sp.Symbol)
        and z.assumptions0 == {"commutative": True}
        and isinstance(f, sp.Expr)
        and not f.free_symbols - {z}
        and algebraic_source(f, z)
        and isinstance(rectangle, CoverageRectangle)
        and rectangle.valid()
        and isinstance(domain, sp.Set)
        and _domain_supported(domain)
        and not domain.free_symbols
        and not domain.has(sp.Float)
        and _condition_supported(condition, z)
    )


def _value_at(node, z, root):
    """Evaluate the raw source, declining holes before arithmetic cancellation."""
    if node == z:
        return "defined", root
    if not node.has(z):
        return ("defined", node) if node.is_finite is True else ("undefined", None)
    values = [_value_at(a, z, root) for a in node.args]
    if any(status == "undefined" for status, _ in values):
        return "undefined", None
    if any(status != "defined" for status, _ in values):
        return "unknown", None
    args = tuple(v for _, v in values)
    if node.is_Pow and node.exp.is_negative:
        zero = _zero(args[0])
        if zero is True:
            return "undefined", None
        if zero is not False:
            return "unknown", None
    value = node.func(*args)
    if value.is_finite is True:
        return "defined", value
    return ("undefined", None) if value.is_finite is False else ("unknown", None)


def _condition_value(c, z, root):
    if c is sp.S.true:
        return True
    if c is sp.S.false:
        return False
    if isinstance(c, (sp.Equality, sp.Unequality)):
        left, right = (_value_at(a, z, root) for a in c.args)
        if "undefined" in (left[0], right[0]):
            return "undefined"
        if left[0] != "defined" or right[0] != "defined":
            return None
        same = _equal(left[1], right[1])
        return same if isinstance(c, sp.Equality) or same is None else not same
    values = [_condition_value(a, z, root) for a in c.args]
    if "undefined" in values:
        return "undefined"
    if isinstance(c, sp.Not):
        return None if values[0] is None else not values[0]
    if isinstance(c, sp.And):
        return False if False in values else None if None in values else True
    return True if True in values else None if None in values else False


def _condition_at(c, z, root):
    value = _condition_value(c, z, root)
    return False if value == "undefined" else value


def _inside(rectangle, root):
    a, b, c, d = rectangle.bounds()
    values = [
        truth_bool(q)
        for q in (
            a <= sp.re(root),
            sp.re(root) <= c,
            b <= sp.im(root),
            sp.im(root) <= d,
        )
    ]
    return (
        False if False in values else True if all(v is True for v in values) else None
    )


def _multiplicity(f, z, root):
    # Augmented-system multiplicities need not be orders of the principal source
    # at a branch point. Transfer only for rational functions with finite source.
    if any(
        n.is_Pow and n.has(z) and not n.exp.is_Integer for n in sp.preorder_traversal(f)
    ):
        return None
    try:
        numerator, denominator = sp.fraction(sp.cancel(f))
        if _zero(denominator.subs(z, root)) is not False:
            return None
        p = sp.Poly(numerator, z, extension=True)
        for order in range(p.degree() + 1):
            zero = _zero(p.eval(root))
            if zero is False:
                return order if order > 0 else None
            if zero is not True:
                return None
            p = p.diff()
    except (sp.PolynomialError, *_ERRORS):
        pass
    return None


def _size_ok(f, limit):
    if sp.count_ops(f) > 100:
        return False

    def degree(n):
        if not n.args:
            return 1 if n.free_symbols else 0
        if n.is_Add:
            return min(limit + 1, sum(degree(a) for a in n.args))
        if n.is_Mul:
            return min(limit + 1, sum(degree(a) for a in n.args))
        if n.is_Pow:
            if abs(n.exp.p) > limit or n.exp.q > limit:
                return limit + 1
            return min(limit + 1, max(abs(n.exp.p), n.exp.q) * max(1, degree(n.base)))
        return 0

    return degree(f) <= limit


def _backend_problem(f, z, auxiliary_limit, dimension_limit):
    from algroots.algebraization import algebraize_system
    from algroots.rational_univariate import (
        compute_rational_univariate_representation,
        solve_rur_points,
    )

    if not _size_ok(f, dimension_limit):
        raise ValueError("algebraic-source-size-limit")
    system = algebraize_system((f,), (z,), max_auxiliary_variables=auxiliary_limit)
    degrees = [
        max(1, sp.Poly(e, *system.augmented_variables).total_degree())
        for e in system.polynomial_equations
    ]
    if prod(degrees) > dimension_limit:
        raise ValueError("algebraic-degree-bound-limit")
    representation = compute_rational_univariate_representation(
        system.polynomial_equations, system.augmented_variables
    )
    if representation.dimension > dimension_limit:
        raise ValueError("algebraic-quotient-dimension-limit")
    points = tuple(p.coordinates for p in solve_rur_points(representation, real=False))
    if len(points) != representation.solution_count:
        raise ValueError("incomplete-algebraic-enumeration")
    return system, representation, points


def _decision(proof, system, point):
    root = point[0]
    inside = _inside(proof.rectangle, root)
    if inside is False:
        return "outside-rectangle", None
    contained = truth_bool(proof.domain.contains(root))
    condition = _condition_at(proof.condition, proof.variable, root)
    if contained is False or condition is False:
        return "outside-restriction", None
    status, value = _value_at(proof.expression, proof.variable, root)
    if status == "undefined":
        return "source-undefined", None
    if status != "defined":
        return "unresolved-source-value", None
    zero = _zero(value)
    if zero is False:
        return "principal-branch-rejected", None
    if zero is not True:
        return "unresolved-source-equation", None
    assignment = dict(zip(system.augmented_variables, point, strict=True))
    for auxiliary, lift in zip(
        system.auxiliary_variables, system.auxiliary_lift_expressions, strict=True
    ):
        same = _equal(assignment[auxiliary], lift.subs(assignment, simultaneous=True))
        if same is False:
            return "principal-lift-rejected", None
        if same is not True:
            return "unresolved-principal-lift", None
    if inside is None or contained is None or condition is None:
        return "unresolved-restriction", None
    return "accepted", _multiplicity(proof.expression, proof.variable, root)


@dataclass(frozen=True)
class AlgebraicRootDecision:
    """Record whether an algebraic candidate satisfies source, domain and branch guards."""

    point: tuple
    disposition: str
    multiplicity: int | None = None
    certificate: object = None


@dataclass(frozen=True)
class AlgebraicComplexRootProof:
    """Adapt exact algebraic enumeration to source-preserving complex root coverage."""

    expression: sp.Expr
    variable: sp.Symbol
    rectangle: CoverageRectangle
    domain: sp.Set
    condition: sp.Basic
    source_syntax: str
    coordinate_assumptions: tuple
    system: object = None
    representation: object = None
    decisions: tuple = ()
    roots: tuple = ()
    multiplicities: tuple = ()
    complete: bool = False
    obligations: tuple = ("unresolved-algebraic-backend",)
    max_auxiliary_variables: int = 8
    max_quotient_dimension: int = 256
    backend: str = _BACKEND
    schema_version: int = 1

    @property
    def root_count(self):
        return len(self.roots) if self.complete else None

    @property
    def distinct_root_count(self):
        return self.root_count

    @property
    def multiplicity_count(self):
        return (
            sum(self.multiplicities)
            if self.complete and all(type(m) is int for m in self.multiplicities)
            else None
        )

    @property
    def total_count(self):
        return self.multiplicity_count

    @property
    def isolation_complete(self):
        return self.complete

    @property
    def coverage_complete(self):
        return self.complete

    @property
    def scope(self):
        return "algroots-backed-algebraic-roots-on-restricted-closed-rectangle"

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        return check_algebraic_complex_roots(self)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


def _assembled(decisions):
    accepted = [d for d in decisions if d.disposition == "accepted"]
    roots, multiplicities = [], []
    for d in accepted:
        root = d.point[0]
        # The principal lifts are unique. Still require exact distinctness;
        # syntactic inequality is not an algebraic separation proof.
        for old in roots:
            same = _equal(root, old)
            if same is not False:
                raise ValueError("unseparated-algebraic-projections")
        roots.append(root)
        multiplicities.append(d.multiplicity)
    obligations = tuple(
        d.disposition for d in decisions if d.disposition.startswith("unresolved-")
    )
    return tuple(roots), tuple(multiplicities), not obligations, obligations


def check_algebraic_complex_roots(proof):
    """Check the stored algebraic complex roots premises and report their replay outcome."""

    rejected = CheckResult(
        CheckOutcome.REJECTED, False, False, "false-algebraic-adapter-premise"
    )
    try:
        if (
            type(proof) is not AlgebraicComplexRootProof
            or type(proof.schema_version) is not int
            or proof.schema_version != 1
        ):
            return CheckResult(
                CheckOutcome.UNSUPPORTED,
                None,
                False,
                "unsupported-algebraic-adapter-schema",
            )
        if (
            proof.backend != _BACKEND
            or proof.source_syntax != sp.srepr(proof.expression)
            or proof.coordinate_assumptions
            != tuple(sorted(proof.variable.assumptions0.items()))
            or type(proof.max_auxiliary_variables) is not int
            or not 0 <= proof.max_auxiliary_variables <= 16
            or type(proof.max_quotient_dimension) is not int
            or not 1 <= proof.max_quotient_dimension <= 256
        ):
            return rejected
        if not algebraic_complex_supported(
            proof.expression,
            proof.variable,
            proof.rectangle,
            proof.domain,
            proof.condition,
        ):
            return (
                CheckResult(
                    CheckOutcome.UNSUPPORTED,
                    None,
                    False,
                    "unsupported-algebraic-source-or-restriction",
                )
                if proof.system is None and not proof.complete and not proof.roots
                else rejected
            )
        if proof.system is None:
            return (
                CheckResult(
                    CheckOutcome.UNSUPPORTED,
                    None,
                    False,
                    "unresolved-algebraic-backend",
                )
                if not proof.complete
                and not proof.roots
                and not proof.decisions
                and proof.obligations
                else rejected
            )
        from algroots.certification import IsolatedRootCertificate

        system, representation, points = _backend_problem(
            proof.expression,
            proof.variable,
            proof.max_auxiliary_variables,
            proof.max_quotient_dimension,
        )
        if (
            type(proof.system) is not type(system)
            or type(proof.representation) is not type(representation)
            or proof.system != system
            or proof.representation != representation
            or type(proof.complete) is not bool
            or not isinstance(proof.decisions, tuple)
            or len(proof.decisions) != len(points)
            or not isinstance(proof.roots, tuple)
            or not isinstance(proof.multiplicities, tuple)
            or any(
                m is not None and (type(m) is not int or m < 1)
                for m in proof.multiplicities
            )
        ):
            return rejected
        for d, point in zip(proof.decisions, points, strict=True):
            pending = (
                type(d) is AlgebraicRootDecision
                and d.disposition
                in (
                    "unresolved-source-value",
                    "unresolved-source-equation",
                    "unresolved-principal-lift",
                    "unresolved-restriction",
                )
                and d.multiplicity is None
            )
            if (
                type(d) is not AlgebraicRootDecision
                or (
                    d.multiplicity is not None
                    and (type(d.multiplicity) is not int or d.multiplicity < 1)
                )
                or d.point != point
                or (
                    not pending
                    and (d.disposition, d.multiplicity)
                    != _decision(proof, system, point)
                )
            ):
                return rejected
            if d.disposition == "accepted":
                c = d.certificate
                if (
                    type(c) is not IsolatedRootCertificate
                    or any(
                        type(getattr(c, field)) is not int
                        for field in (
                            "multiplicity",
                            "quotient_dimension",
                            "geometric_solution_count",
                            "jacobian_rank",
                        )
                    )
                    or c.equations != system.polynomial_equations
                    or c.variables != system.augmented_variables
                    or c.point != point
                    or not c.verify(max_quotient_dimension=proof.max_quotient_dimension)
                ):
                    return rejected
            elif d.certificate is not None:
                return rejected
        roots, multiplicities, complete, obligations = _assembled(proof.decisions)
        if (proof.roots, proof.multiplicities, proof.complete, proof.obligations) != (
            roots,
            multiplicities,
            complete,
            obligations,
        ):
            return rejected
        return CheckResult(
            CheckOutcome.COMPLETE if complete else CheckOutcome.LOCAL_VALID,
            True,
            complete,
            "; ".join(obligations) or None,
        )
    except (ImportError, *_ERRORS, sp.PolynomialError):
        return rejected


def certify_algebraic_complex_roots(
    expr,
    var,
    rectangle,
    *,
    domain=sp.S.Complexes,
    condition=sp.S.true,
    max_auxiliary_variables=8,
    max_quotient_dimension=256,
):
    """Adapt exact algroots enumeration, source filtering and local certificates.

    Rational powers retain principal-branch semantics. Multiplicity transfers
    only for rational sources; augmented-system orders are otherwise separate.
    """
    from dataclasses import replace

    from .transcendental.complex_roots import _normalize_rectangle

    f, z, domain, condition = map(sp.sympify, (expr, var, domain, condition))
    if (
        type(max_auxiliary_variables) is not int
        or not 0 <= max_auxiliary_variables <= 16
        or type(max_quotient_dimension) is not int
        or not 1 <= max_quotient_dimension <= 256
    ):
        raise ValueError(
            "require 0 <= auxiliary limit <= 16 and 1 <= dimension limit <= 256"
        )
    rect = _normalize_rectangle(rectangle)
    box = (
        CoverageRectangle(*rect.as_pair())
        if rect is not None
        else CoverageRectangle(0, 0)
    )
    seed = AlgebraicComplexRootProof(
        f,
        z,
        box,
        domain,
        condition,
        sp.srepr(f),
        tuple(sorted(z.assumptions0.items())) if isinstance(z, sp.Symbol) else (),
        max_auxiliary_variables=max_auxiliary_variables,
        max_quotient_dimension=max_quotient_dimension,
    )
    if not algebraic_complex_supported(f, z, box, domain, condition):
        return replace(
            seed, obligations=("unsupported-algebraic-source-or-restriction",)
        )
    try:
        from algroots.certification import certify_isolated_root

        system, representation, points = _backend_problem(
            f, z, max_auxiliary_variables, max_quotient_dimension
        )
        decisions = []
        for point in points:
            disposition, multiplicity = _decision(seed, system, point)
            c = (
                certify_isolated_root(
                    system.polynomial_equations,
                    system.augmented_variables,
                    point,
                    max_quotient_dimension=max_quotient_dimension,
                )
                if disposition == "accepted"
                else None
            )
            decisions.append(AlgebraicRootDecision(point, disposition, multiplicity, c))
        decisions = tuple(decisions)
        roots, multiplicities, complete, obligations = _assembled(decisions)
        result = replace(
            seed,
            system=system,
            representation=representation,
            decisions=decisions,
            roots=roots,
            multiplicities=multiplicities,
            complete=complete,
            obligations=obligations,
        )
        return (
            result
            if result.verify()
            else replace(seed, obligations=("algebraic-replay-failed",))
        )
    except (ImportError, *_ERRORS, sp.PolynomialError):
        return seed
