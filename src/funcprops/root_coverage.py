"""Checkable real-root coverage with explicit unresolved regions.

The partition checker is independent of the adaptive search that proposes it.
Local counts are bound to their original source expression and exact region.
"""

import itertools
from dataclasses import dataclass

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, DomainError

from .domain_tracking import DomainRecord, track_domain
from .exactness import certify_zero
from .source_syntax import differentiate

_ERRORS = (
    CoercionFailed,
    DomainError,
    AttributeError,
    TypeError,
    ValueError,
    NotImplementedError,
    ArithmeticError,
    sp.PolynomialError,
)


def _empty(s):
    return s is sp.S.EmptySet or s == sp.S.EmptySet


def _subset(a, b):
    return _empty(sp.Complement(a, b))


def _endpoint(f, x, interval, left):
    p = interval.start if left else interval.end
    opened = interval.left_open if left else interval.right_open
    return (
        sp.limit(f, x, p, dir="+" if left else "-")
        if opened
        else sp.simplify(f.subs(x, p))
    )


def _exact_rational_roots(f, x, region):
    if f.free_symbols - {x} or f.has(sp.Float):
        return None
    num, den = sp.fraction(sp.cancel(f))
    try:
        pn, pd = sp.Poly(num, x, domain=sp.QQ), sp.Poly(den, x, domain=sp.QQ)
    except _ERRORS:
        return None
    if pd.is_zero:
        return None
    if pn.is_zero:
        if isinstance(region, sp.FiniteSet):
            return len(region), None, tuple((p, None) for p in region)
        return sp.oo, None, ()
    roots = []
    for root, multiplicity in pn.real_roots(multiple=False):
        membership = region.contains(root)
        if membership is sp.S.true:
            roots.append((root, int(multiplicity)))
        elif membership is not sp.S.false:
            return None
    return len(roots), sum(m for _, m in roots), tuple(roots)


def _local_data(f, x, region, method, witness=None):
    """Reconstruct a local root-count method from its bound source and region data."""

    record = track_domain(f, x, region)
    if not record.complete or record.effective != region or _empty(region):
        return None
    if method == "exact-rational":
        return _exact_rational_roots(f, x, region)
    if method == "point":
        if not isinstance(region, sp.FiniteSet) or len(region) != 1:
            return None
        point = next(iter(region))
        value = f.subs(x, point)
        zero = certify_zero(value)
        if zero is True:
            return 1, None, ((point, None),)
        if zero is False and value.is_finite is True and value.is_real is True:
            return 0, 0, ()
        return None
    if method == "taylor-exclusion":
        from .certified_balls import certified_real_ball
        from .taylor_models import taylor_model

        for order in (1, 2):
            model = taylor_model(f, x, region, order=order)
            if model is None or not model.verify():
                continue
            polynomial = certified_real_ball(model.polynomial, x, region)
            if polynomial is not None and (
                (polynomial.lower + model.remainder_lower).is_positive is True
                or (polynomial.upper + model.remainder_upper).is_negative is True
            ):
                return 0, 0, ()
        return None
    if method == "interval-newton":
        from .verified_roots import interval_newton_count

        count = interval_newton_count(f, x, region)
        return (count, count, ()) if count in (0, 1) else None
    if method == "interval":
        from .certified_balls import certified_real_ball
        from .domain_tracking import smooth_domain_record
        from .verified_roots import verify_real_root_interval

        if (
            not isinstance(region, sp.Interval)
            or region.start.is_finite is not True
            or region.end.is_finite is not True
        ):
            return None
        result = verify_real_root_interval(f, x, region)
        if result.root_count in (0, 1):
            return result.root_count, result.root_count, ()
        # An outward enclosure contains its closure. Prove exclusion separately
        # when its sole possible zero is an unowned endpoint.
        if smooth_domain_record(f, x, region, 1) is None:
            return None
        derivative = certified_real_ball(differentiate(f, x), x, region)
        if derivative is None or not derivative.excludes_zero:
            return None
        a, b = _endpoint(f, x, region, True), _endpoint(f, x, region, False)
        if derivative.sign == -1:
            a, b = -a, -b
        no_root = (
            a.is_positive is True or (a.is_zero is True and region.left_open)
        ) or (b.is_negative is True or (b.is_zero is True and region.right_open))
        return (0, 0, ()) if no_root else None
    if method == "tail":
        from .asymptotic_tails import TailSignCertificate

        if (
            type(witness) is not TailSignCertificate
            or witness.expression != f
            or witness.variable != x
        ):
            return None
        if (
            type(witness.direction) is not int
            or type(witness.sign) is not int
            or not witness.verify()
        ):
            return None
        T = sp.Abs(witness.threshold)
        if T.is_finite is not True or T.is_real is not True:
            return None
        support = (
            sp.Interval(T, sp.oo) if witness.direction == 1 else sp.Interval(-sp.oo, -T)
        )
        return (0, 0, ()) if _subset(region, support) else None
    if method == "periodic-family":
        from .transcendental.roots import RootIsolationResult

        if region is not sp.S.Reals or type(witness) is not RootIsolationResult:
            return None
        if (
            witness.expression != f
            or witness.variable != x
            or witness.domain is not sp.S.Reals
            or witness.complete is not True
            or not witness.verify()
        ):
            return None
        periodic = witness.periodic
        if (
            periodic is None
            or not isinstance(periodic.base, sp.FiniteSet)
            or not periodic.base
        ):
            return None
        return sp.oo, sp.oo, ()
    return None


@dataclass(frozen=True)
class RootRegionProof:
    """Bind a real region's count to a declared theorem and source evidence."""

    expression: sp.Expr
    variable: sp.Symbol
    region: sp.Set
    method: str
    root_count: object
    multiplicity_count: object = None
    roots: tuple = ()
    witness: object = None

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if type(self) is not RootRegionProof or isinstance(
                self.multiplicity_count, bool
            ):
                return False
            if self.root_count is not sp.oo and type(self.root_count) is not int:
                return False
            data = _local_data(
                self.expression, self.variable, self.region, self.method, self.witness
            )
            return data is not None and data == (
                self.root_count,
                self.multiplicity_count,
                self.roots,
            )
        except _ERRORS:
            return False


def _leaf(f, x, region, method, witness=None):
    data = _local_data(f, x, region, method, witness)
    return (
        None if data is None else RootRegionProof(f, x, region, method, *data, witness)
    )


@dataclass(frozen=True)
class RootCoverageCertificate:
    """Assemble real root regions, source restrictions and unresolved coverage."""

    expression: sp.Expr
    variable: sp.Symbol
    domain_record: DomainRecord
    regions: tuple[RootRegionProof, ...] = ()
    unresolved: sp.Set = sp.S.EmptySet
    complete: bool = False
    root_count: object = None
    multiplicity_count: object = None
    reason: str | None = None

    @property
    def domain(self):
        return self.domain_record.effective

    @property
    def scope(self):
        return "real-root-coverage-on-effective-domain"

    @property
    def certified(self):
        return self.verify()

    @property
    def certificate(self):
        return self

    @property
    def known_root_count(self):
        return sum((r.root_count for r in self.regions), sp.S.Zero)

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if isinstance(self.root_count, bool) or isinstance(
                self.multiplicity_count, bool
            ):
                return False
            if (
                type(self) is not RootCoverageCertificate
                or type(self.complete) is not bool
                or type(self.domain_record) is not DomainRecord
                or type(self.regions) is not tuple
            ):
                return False
            if (
                self.domain_record.expression != self.expression
                or self.domain_record.variable != self.variable
            ):
                return False
            if not self.domain_record.verify() or not isinstance(
                self.unresolved, sp.Set
            ):
                return False
            D = self.domain
            sets = [r.region for r in self.regions]
            if not _subset(self.unresolved, D):
                return False
            for leaf in self.regions:
                if (
                    type(leaf) is not RootRegionProof
                    or leaf.expression != self.expression
                    or leaf.variable != self.variable
                    or not leaf.verify()
                    or not _subset(leaf.region, D)
                ):
                    return False
                if not _empty(sp.Intersection(leaf.region, self.unresolved)):
                    return False
            if any(
                not _empty(sp.Intersection(a, b))
                for a, b in itertools.combinations(sets, 2)
            ):
                return False
            if not _empty(sp.Complement(D, sp.Union(*sets, self.unresolved))):
                return False
            complete = _empty(self.unresolved)
            count = self.known_root_count if complete else None
            multiplicities = [r.multiplicity_count for r in self.regions]
            mult = (
                sum(multiplicities, sp.S.Zero)
                if complete and all(m is not None for m in multiplicities)
                else None
            )
            return (
                self.complete is complete
                and self.root_count == count
                and self.multiplicity_count == mult
            )
        except _ERRORS:
            return False


def _assemble(f, x, record, proofs, unresolved, reason=None):
    missing = sp.Union(*unresolved)
    complete = _empty(missing)
    count = sum((p.root_count for p in proofs), sp.S.Zero) if complete else None
    ms = [p.multiplicity_count for p in proofs]
    mult = sum(ms, sp.S.Zero) if complete and all(m is not None for m in ms) else None
    return RootCoverageCertificate(
        f, x, record, tuple(proofs), missing, complete, count, mult, reason
    )


def root_coverage(
    expr,
    var,
    domain=sp.S.Reals,
    *,
    max_depth=10,
    max_cells=1024,
    use_families=True,
    use_tails=True,
):
    """Propose a verified partition; budget exhaustion keeps unresolved cells.

    Multiple roots are supported by exact rational enumeration. Other tangencies
    remain unresolved. Infinite periodic coverage requires an exhaustive existing
    family theorem; strict tail bounds never stand in for the remaining core.
    """
    if (
        type(max_depth) is not int
        or type(max_cells) is not int
        or max_depth < 0
        or max_cells < 0
    ):
        raise ValueError("coverage budgets must be nonnegative integers")
    f, x = sp.sympify(expr), sp.sympify(var)
    record = track_domain(f, x, domain)
    if not record.complete:
        from .real_analysis.common import condition_to_set

        requested = condition_to_set(sp.S.true if domain is None else domain, x)
        return RootCoverageCertificate(
            f,
            x,
            record,
            unresolved=requested if isinstance(requested, sp.Set) else sp.S.Reals,
            reason=record.reason,
        )
    D = record.effective
    if _empty(D):
        return _assemble(f, x, record, [], [])
    if max_cells:
        exact = _leaf(f, x, D, "exact-rational")
        if exact is not None:
            return _assemble(f, x, record, [exact], [])
    if use_families and D is sp.S.Reals and max_cells:
        from .transcendental.roots import transcendental_roots

        family = transcendental_roots(f, x, D, allow_numerical=False)
        leaf = _leaf(f, x, D, "periodic-family", family)
        if leaf is not None:
            return _assemble(f, x, record, [leaf], [])
    parts = list(D.args) if isinstance(D, sp.Union) else [D]
    queue = [(part, 0) for part in reversed(parts)]
    proofs, missing = [], []
    tested = 0
    while queue:
        region, depth = queue.pop()
        if tested >= max_cells:
            missing.append(region)
            continue
        tested += 1
        leaf = _leaf(f, x, region, "exact-rational")
        if leaf is None and isinstance(region, sp.FiniteSet):
            if len(region) > 1:
                queue.extend((sp.FiniteSet(p), depth) for p in region)
                continue
            leaf = _leaf(f, x, region, "point")
        if leaf is None and isinstance(region, sp.Interval):
            if region.start.is_finite is True and region.end.is_finite is True:
                leaf = _leaf(f, x, region, "interval")
                if leaf is None:
                    leaf = _leaf(f, x, region, "interval-newton")
                if leaf is None:
                    leaf = _leaf(f, x, region, "taylor-exclusion")
            elif use_tails:
                from .asymptotic_tails import certify_tail_sign

                direction = (
                    1
                    if region.end is sp.oo and region.start.is_finite
                    else -1
                    if region.start is -sp.oo and region.end.is_finite
                    else None
                )
                if direction:
                    threshold = region.start if direction == 1 else -region.end
                    tail = certify_tail_sign(
                        f, x, direction=direction, threshold=threshold
                    )
                    if tail is not None:
                        leaf = _leaf(f, x, region, "tail", tail)
        if leaf is not None:
            proofs.append(leaf)
        elif (
            isinstance(region, sp.Interval)
            and region.start.is_finite is True
            and region.end.is_finite is True
            and depth < max_depth
        ):
            mid = (region.start + region.end) / 2
            queue.extend(
                [
                    (sp.Interval(mid, region.end, False, region.right_open), depth + 1),
                    (sp.Interval(region.start, mid, region.left_open, True), depth + 1),
                ]
            )
        else:
            missing.append(region)
    return _assemble(
        f, x, record, proofs, missing, "unresolved-regions" if missing else None
    )


@dataclass(frozen=True)
class SpecializedRootCoverage:
    """Bind a guarded real root cover to exact parameter substitutions."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: object
    substitutions: tuple
    coverage: RootCoverageCertificate

    @property
    def guard(self):
        return sp.And(*(sp.Eq(k, v) for k, v in self.substitutions))

    @property
    def complete(self):
        return self.coverage.complete if self.verify() else False

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "root-coverage-under-explicit-parameter-equalities"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                type(self) is not SpecializedRootCoverage
                or type(self.coverage) is not RootCoverageCertificate
                or type(self.substitutions) is not tuple
            ):
                return False
            pairs = dict(self.substitutions)
            if (
                len(pairs) != len(self.substitutions)
                or self.guard is sp.S.false
                or self.variable in pairs
            ):
                return False
            if any(
                not isinstance(k, sp.Symbol)
                or k not in self.expression.free_symbols
                or v.free_symbols
                or v.is_real is not True
                or v.is_finite is not True
                or v.has(sp.Float)
                for k, v in self.substitutions
            ):
                return False
            return (
                self.coverage.expression == self.expression.xreplace(pairs)
                and self.coverage.variable == self.variable
                and self.coverage.domain_record.requested
                == sp.sympify(
                    sp.S.Reals if self.domain is None else self.domain
                ).xreplace(pairs)
                and self.coverage.verify()
            )
        except _ERRORS:
            return False


def specialize_root_coverage(expr, var, substitutions, domain=sp.S.Reals, **kwargs):
    """Restrict a guarded root cover to exact parameter substitutions."""

    f, x = sp.sympify(expr), sp.sympify(var)
    pairs = tuple(
        sorted(
            ((sp.sympify(k), sp.sympify(v)) for k, v in dict(substitutions).items()),
            key=lambda kv: sp.default_sort_key(kv[0]),
        )
    )
    replacement = dict(pairs)
    specialized_domain = sp.sympify(sp.S.Reals if domain is None else domain).xreplace(
        replacement
    )
    coverage = root_coverage(f.xreplace(replacement), x, specialized_domain, **kwargs)
    return SpecializedRootCoverage(f, x, domain, pairs, coverage)
