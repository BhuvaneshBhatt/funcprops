from __future__ import annotations

import contextlib
import itertools
from dataclasses import dataclass

import mpmath as mp
import sympy as sp
from sympy import S

from ..engine import truth_bool
from ..exceptions import SYMBOLIC_QUERY_ERRORS
from .analytic import AnalyticNeighborhoodCertificate, holomorphic_on_rectangle


@dataclass(frozen=True)
class ComplexRectangle:
    """Closed axis-aligned complex rectangle with exact real bounds."""

    re_min: sp.Expr
    re_max: sp.Expr
    im_min: sp.Expr
    im_max: sp.Expr

    @property
    def lower_left(self):
        return self.re_min + sp.I * self.im_min

    @property
    def upper_right(self):
        return self.re_max + sp.I * self.im_max

    @property
    def center(self):
        return (self.re_min + self.re_max) / 2 + sp.I * (self.im_min + self.im_max) / 2

    @property
    def width(self):
        return sp.simplify(self.re_max - self.re_min)

    @property
    def height(self):
        return sp.simplify(self.im_max - self.im_min)

    def as_pair(self):
        return self.lower_left, self.upper_right


@dataclass(frozen=True)
class ArgumentPrincipleCertificate:
    """Store a contour count with its route-specific boundary premises."""

    rectangle: ComplexRectangle
    winding_number: int | None
    zero_count: int | None
    pole_count: int | None = 0
    certified: bool = False
    method: str = "unknown"
    boundary_segments: int = 0
    precision: int | None = None
    analytic_certificate: AnalyticNeighborhoodCertificate | None = None
    evidence: tuple[object, ...] = ()


@dataclass(frozen=True)
class CertifiedComplexRootRectangle:
    """Store a complex root region with count and accuracy evidence."""

    rectangle: ComplexRectangle
    root_count: int
    certificate: object

    @property
    def multiplicity_count(self):
        return self.root_count

    @property
    def distinct_root_count(self):
        return getattr(
            self.certificate, "known_distinct", 1 if self.root_count == 1 else None
        )


@dataclass(frozen=True)
class ComplexRootIsolationResult:
    """Expose route-specific complex root regions, counts and replayable proof data."""

    roots: tuple[sp.Expr, ...] = ()
    rectangles: tuple[CertifiedComplexRootRectangle, ...] = ()
    complete: bool = False
    total_count: int | None = None
    method: str = "unknown"
    evidence: tuple[object, ...] = ()
    certificates: tuple[object, ...] = ()
    distinct_root_count: int | None = None
    isolation_complete: bool = False
    algebraic_certificate: object = None
    isolation_state: object = None

    @property
    def state(self):
        return self.isolation_state

    @property
    def isolation_certificate(self):
        return getattr(self.isolation_state, "proof", None)

    @property
    def proof(self):
        return self.isolation_certificate or self.algebraic_certificate

    @property
    def expression(self):
        return getattr(self.proof, "expression", None)

    @property
    def variable(self):
        return getattr(self.proof, "variable", None)

    @property
    def scope(self):
        return getattr(self.proof, "scope", "factory-complex-root-isolation")

    @property
    def schema_version(self):
        return getattr(self.proof, "schema_version", None)

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        from ..algebraic_complex import AlgebraicComplexRootProof
        from ..complex_isolation import ComplexIsolationState
        from ..coverage_contract import CheckOutcome, CheckResult
        from ..quotient_isolation import QuotientIsolationState

        if self.isolation_state is not None:
            state = self.isolation_state
            if type(state) not in (ComplexIsolationState, QuotientIsolationState):
                return CheckResult(
                    CheckOutcome.REJECTED, False, False, "invalid-isolation-state"
                )
            checked = state.check()
            if checked.certified is not True:
                return checked
            expected = (
                _quotient_result(state)
                if type(state) is QuotientIsolationState
                else _native_result(state)
            )
            if self != expected or self.algebraic_certificate is not None:
                return CheckResult(
                    CheckOutcome.REJECTED, False, False, "false-native-isolation-result"
                )
            # Dataclass equality alone accepts bools as integers and subclasses.
            if (
                any(
                    type(q) is not CertifiedComplexRootRectangle
                    or type(q.rectangle) is not ComplexRectangle
                    or type(q.root_count) is not int
                    for q in self.rectangles
                )
                or any(
                    type(q) is not bool
                    for q in (self.complete, self.isolation_complete)
                )
                or any(
                    q is not None and type(q) is not int
                    for q in (self.total_count, self.distinct_root_count)
                )
            ):
                return CheckResult(
                    CheckOutcome.REJECTED, False, False, "false-native-isolation-types"
                )
            return checked
        p = self.algebraic_certificate
        if type(p) is not AlgebraicComplexRootProof:
            return CheckResult(
                CheckOutcome.UNSUPPORTED,
                None,
                False,
                "unsupported-factory-isolation-replay",
            )
        if (
            self.roots != p.roots
            or self.complete is not p.complete
            or self.total_count != p.total_count
            or self.distinct_root_count != p.distinct_root_count
            or self.isolation_complete is not p.isolation_complete
            or self.rectangles
            or self.certificates
            or self.evidence != (p,)
            or self.method != "algroots_algebraic_complex_roots"
            or (self.total_count is not None and type(self.total_count) is not int)
            or (
                self.distinct_root_count is not None
                and type(self.distinct_root_count) is not int
            )
        ):
            return CheckResult(
                CheckOutcome.REJECTED, False, False, "false-adapted-isolation-result"
            )
        return p.check()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    @property
    def multiplicity_count(self):
        """The total count, consistently including multiplicity on every route."""
        return self.total_count

    @property
    def root_count(self):
        return self.distinct_root_count

    @property
    def coverage_complete(self):
        return (
            self.isolation_certificate.coverage_complete
            if self.isolation_state is not None
            else self.complete
        )

    @property
    def accuracy_complete(self):
        return (
            self.isolation_certificate.accuracy_complete
            if self.isolation_state is not None
            else self.isolation_complete
        )

    @property
    def clusters(self):
        return getattr(self.isolation_certificate, "clusters", ())

    @property
    def unresolved(self):
        return getattr(self.isolation_certificate, "unresolved", ())

    @property
    def refinements(self):
        return getattr(self.isolation_certificate, "refinements", ())

    @property
    def individual_multiplicities(self):
        return getattr(self.proof, "individual_multiplicities", None)

    @property
    def pole_multiplicity_count(self):
        return getattr(self.proof, "pole_multiplicity_count", None)

    @property
    def distinct_pole_count(self):
        return getattr(self.proof, "distinct_pole_count", None)

    @property
    def pole_regions(self):
        return getattr(self.proof, "pole_regions", ())

    @property
    def winding_count(self):
        return getattr(self.proof, "winding_count", None)

    @property
    def certified(self):
        return self.verify() if self.proof is not None else self.complete


def _native_result(state):
    p = state.proof
    rectangles = tuple(
        CertifiedComplexRootRectangle(
            ComplexRectangle(
                c.rectangle.bounds()[0],
                c.rectangle.bounds()[2],
                c.rectangle.bounds()[1],
                c.rectangle.bounds()[3],
            ),
            c.zero_count,
            c,
        )
        for c in (*p.root_regions, *p.clusters)
    )
    return ComplexRootIsolationResult(
        rectangles=rectangles,
        complete=p.complete,
        total_count=p.total_count,
        method="native_entire_complex_isolation",
        evidence=(p,),
        certificates=p.regions,
        distinct_root_count=p.distinct_root_count,
        isolation_complete=p.isolation_complete,
        isolation_state=state,
    )


def _quotient_result(state):
    from ..quotient_isolation import QuotientRegionProof, _cell_data

    p = state.proof
    regions = tuple(
        QuotientRegionProof(p.source, c)
        for c in p.cells
        if (d := _cell_data(p.source, c)) is not None and d[0]
    )
    rectangles = tuple(
        CertifiedComplexRootRectangle(
            ComplexRectangle(
                c.rectangle.bounds()[0],
                c.rectangle.bounds()[2],
                c.rectangle.bounds()[1],
                c.rectangle.bounds()[3],
            ),
            c.zero_count,
            c,
        )
        for c in regions
    )
    return ComplexRootIsolationResult(
        rectangles=rectangles,
        complete=p.complete,
        total_count=p.total_count,
        method="native_quotient_complex_isolation",
        evidence=(p,),
        certificates=regions,
        distinct_root_count=p.distinct_root_count,
        isolation_complete=p.isolation_complete,
        isolation_state=state,
    )


def _timeout_isolation(expr, var, rectangle, kwargs, state=None):
    from ..complex_interval import entire_source
    from ..complex_isolation import _seed, _wall_state
    from ..quotient_isolation import (
        QuotientIsolationState,
        quotient_source_supported,
    )
    from ..quotient_isolation import (
        _seed as quotient_seed,
    )
    from ..quotient_isolation import (
        _wall_state as quotient_wall,
    )

    if type(state) is QuotientIsolationState:
        return _quotient_result(quotient_wall(state))
    rect = _normalize_rectangle(rectangle)
    if (
        state is None
        and rect is not None
        and quotient_source_supported(expr, var)
        and kwargs.get("domain", S.Complexes) == S.Complexes
        and kwargs.get("condition", S.true) is S.true
    ):
        return _quotient_result(
            quotient_wall(
                quotient_seed(
                    expr,
                    var,
                    *rect.as_pair(),
                    max_box_width=kwargs.get("max_box_width"),
                    max_box_diameter=kwargs.get("max_box_diameter"),
                    cancel=False,
                )
            )
        )

    if state is not None:
        return _native_result(_wall_state(state))
    rect = _normalize_rectangle(rectangle)
    f, z = map(sp.sympify, (expr, var))
    if (
        rect is not None
        and entire_source(f, z)
        and kwargs.get("domain", S.Complexes) == S.Complexes
        and sp.sympify(kwargs.get("condition", S.true)) is S.true
    ):
        return _native_result(
            _wall_state(
                _seed(
                    f,
                    z,
                    *rect.as_pair(),
                    kwargs.get("max_box_width"),
                    kwargs.get("max_box_diameter"),
                )
            )
        )
    return ComplexRootIsolationResult(
        method="work-budget-exhausted", evidence=(("query", f, z, rectangle, kwargs),)
    )


def _normalize_rectangle(rectangle):
    if isinstance(rectangle, ComplexRectangle):
        rect = rectangle
    else:
        try:
            a, b = map(sp.sympify, rectangle)
        except (TypeError, ValueError):
            return None
        bounds = tuple(map(sp.simplify, (sp.re(a), sp.re(b), sp.im(a), sp.im(b))))
        if not all(q.is_real is True for q in bounds):
            return None
        rect = ComplexRectangle(
            sp.Min(bounds[0], bounds[1]),
            sp.Max(bounds[0], bounds[1]),
            sp.Min(bounds[2], bounds[3]),
            sp.Max(bounds[2], bounds[3]),
        )
    if truth_bool(rect.re_min < rect.re_max) is not True:
        return None
    if truth_bool(rect.im_min < rect.im_max) is not True:
        return None
    return rect


def _contains(rect: ComplexRectangle, root):
    root = sp.sympify(root)
    checks = (
        rect.re_min <= sp.re(root),
        sp.re(root) <= rect.re_max,
        rect.im_min <= sp.im(root),
        sp.im(root) <= rect.im_max,
    )
    vals = tuple(truth_bool(q) for q in checks)
    if all(v is True for v in vals):
        return True
    if any(v is False for v in vals):
        return False
    return None


def _exact_roots(expr, var, rect):
    from ..certified_operations import _equation_solution_data

    with contextlib.suppress(*SYMBOLIC_QUERY_ERRORS):
        # Shared equation solving tracks the raw source domain before rebuilding
        # held arithmetic, and does not specialize unresolved parameter strata.
        solved, complete, _ = _equation_solution_data(expr, var, S.Complexes)
        if complete and (isinstance(solved, sp.FiniteSet) or solved is S.EmptySet):
            roots = []
            for root in solved:
                inside = _contains(rect, root)
                if inside is None:
                    return None
                if inside:
                    roots.append(root)
            return tuple(sorted(set(roots), key=sp.default_sort_key))
    return None


def _exact_multiplicity_count(expr, var, roots):
    """Polynomial/rational orders at already source-defined exact roots."""
    from ..exactness import certify_zero

    if not roots:
        return 0
    with contextlib.suppress(*SYMBOLIC_QUERY_ERRORS):
        numerator, _ = sp.fraction(sp.cancel(expr))
        p = sp.Poly(numerator, var)
        if not p.is_zero:
            total = 0
            for root in roots:
                derivative = p
                for order in range(p.degree() + 1):
                    zero = certify_zero(derivative.eval(root))
                    if zero is False:
                        total += order
                        break
                    if zero is not True:
                        return None
                    derivative = derivative.diff()
                else:
                    return None
            return total
    return None


def _polygon_winding(values):
    total = mp.mpf("0")
    for a, b in itertools.pairwise(values):
        if a == 0 or b == 0:
            return None
        cross = a.real * b.imag - a.imag * b.real
        dot = a.real * b.real + a.imag * b.imag
        total += mp.atan2(cross, dot)
    turns = total / (2 * mp.pi)
    winding = int(mp.nint(turns))
    if abs(turns - winding) > mp.mpf("1e-20"):
        return None
    return winding


def _numerical_winding(expr, var, rect, *, dps=60, samples=256):
    try:
        f = sp.lambdify(var, expr, "mpmath")
        a = complex(float(sp.N(rect.re_min)), float(sp.N(rect.im_min)))
        b = complex(float(sp.N(rect.re_max)), float(sp.N(rect.im_min)))
        c = complex(float(sp.N(rect.re_max)), float(sp.N(rect.im_max)))
        d = complex(float(sp.N(rect.re_min)), float(sp.N(rect.im_max)))
    except (TypeError, ValueError, NameError):
        return None
    old = mp.mp.dps
    mp.mp.dps = dps
    try:
        points = []
        per_edge = max(8, samples // 4)
        for start, stop in ((a, b), (b, c), (c, d), (d, a)):
            for k in range(per_edge):
                t = k / per_edge
                points.append(start + t * (stop - start))
        points.append(a)
        values = []
        for z in points:
            try:
                values.append(complex(f(z)))
            except (ArithmeticError, TypeError, ValueError, ZeroDivisionError):
                return None
        return _polygon_winding(values)
    finally:
        mp.mp.dps = old


def argument_principle_count(
    expr,
    var,
    rectangle,
    *,
    precision=60,
    max_boundary_depth=14,
):
    """Count zeros in a rectangle by a validated argument-principle contour.

    Positive counts use the native exact boundary-homotopy checker. Rounded
    point evaluations and floating argument sums are diagnostic evidence only.
    Unsupported grammar or geometry remains uncertified.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    rect = _normalize_rectangle(rectangle)
    if rect is None:
        return ArgumentPrincipleCertificate(
            ComplexRectangle(S.Zero, S.One, S.Zero, S.One),
            None,
            None,
            certified=False,
            method="invalid_rectangle",
        )
    analytic = holomorphic_on_rectangle(expr, var, rect.as_pair())
    from ..analytic_contours import certify_analytic_contour
    from ..enclosure_policy import EnclosurePolicy

    native = certify_analytic_contour(
        expr,
        var,
        *rect.as_pair(),
        policy=EnclosurePolicy(
            precision=int(precision),
            max_precision=int(precision),
            max_refinements=0,
            max_depth=max_boundary_depth,
        ),
    )
    if native.complete and native.verify():
        return ArgumentPrincipleCertificate(
            rect,
            native.zero_count,
            native.zero_count,
            0,
            True,
            "validated_interval_argument_principle",
            len(native.images),
            int(precision),
            analytic,
            (("boundary_zero_free", True), ("native_contour", native)),
        )
    estimate = _numerical_winding(expr, var, rect, dps=int(precision))
    return ArgumentPrincipleCertificate(
        rect,
        estimate,
        None,
        0 if analytic.holomorphic is True else None,
        False,
        "numerical_argument_principle_estimate",
        0,
        int(precision),
        analytic,
        (("winding_estimate", estimate),),
    )


def _children(rect, rx, ry):
    x = sp.simplify(rect.re_min + rx * (rect.re_max - rect.re_min))
    y = sp.simplify(rect.im_min + ry * (rect.im_max - rect.im_min))
    return (
        ComplexRectangle(rect.re_min, x, rect.im_min, y),
        ComplexRectangle(x, rect.re_max, rect.im_min, y),
        ComplexRectangle(x, rect.re_max, y, rect.im_max),
        ComplexRectangle(rect.re_min, x, y, rect.im_max),
    )


def isolate_complex_roots(
    expr,
    var,
    rectangle,
    *,
    precision=60,
    max_boundary_depth=14,
    max_isolation_depth=10,
    domain=S.Complexes,
    condition=S.true,
    policy=None,
    max_box_width=None,
    max_box_diameter=None,
    use_newton=True,
    use_multiple=True,
):
    """Return certified complex root rectangles inside ``rectangle``.

    Rectangles with count one isolate a unique simple zero.  A terminal rectangle
    with count greater than one is a certified cluster counted with multiplicity.
    Native ``complete`` requires coverage, individual isolation and requested
    accuracy; ``coverage_complete`` also permits counted clusters. ``total_count``
    includes multiplicity on both exact and contour routes; exact locations have
    a separate ``distinct_root_count``. An unavailable multiplicity stays None.
    """
    expr = sp.sympify(expr)
    var = sp.sympify(var)
    if max_box_width is not None:
        max_box_width = sp.sympify(max_box_width)
        if not isinstance(max_box_width, sp.Rational) or max_box_width <= 0:
            raise ValueError("max_box_width must be a positive exact rational")
    if max_box_diameter is not None:
        max_box_diameter = sp.sympify(max_box_diameter)
        if not isinstance(max_box_diameter, sp.Rational) or max_box_diameter <= 0:
            raise ValueError("max_box_diameter must be a positive exact rational")
    if type(use_newton) is not bool:
        raise ValueError("use_newton must be a bool")
    if type(use_multiple) is not bool:
        raise ValueError("use_multiple must be a bool")
    if policy is not None and policy.seconds is not None:
        from dataclasses import replace

        from ..work_budget import bounded_query

        return bounded_query(
            "isolate_complex_roots",
            expr,
            (var, rectangle),
            {
                "precision": precision,
                "max_boundary_depth": max_boundary_depth,
                "max_isolation_depth": max_isolation_depth,
                "domain": domain,
                "condition": condition,
                "policy": replace(policy, seconds=None),
                "max_box_width": max_box_width,
                "max_box_diameter": max_box_diameter,
                "use_newton": use_newton,
                "use_multiple": use_multiple,
            },
            policy.seconds,
        )
    rect = _normalize_rectangle(rectangle)
    if rect is None:
        return ComplexRootIsolationResult(method="invalid_rectangle")

    from ..algebraic_complex import (
        algebraic_complex_supported,
        certify_algebraic_complex_roots,
    )
    from ..complex_coverage import CoverageRectangle

    domain, condition = map(sp.sympify, (domain, condition))
    if algebraic_complex_supported(
        expr, var, CoverageRectangle(*rect.as_pair()), domain, condition
    ):
        p = certify_algebraic_complex_roots(
            expr, var, rect, domain=domain, condition=condition
        )
        return ComplexRootIsolationResult(
            roots=p.roots,
            complete=p.complete,
            total_count=p.total_count,
            method="algroots_algebraic_complex_roots",
            evidence=(p,),
            distinct_root_count=p.distinct_root_count,
            isolation_complete=p.isolation_complete,
            algebraic_certificate=p,
        )
    if domain != S.Complexes or condition is not S.true:
        return ComplexRootIsolationResult(
            method="unsupported-restricted-complex-isolation"
        )

    from ..complex_interval import entire_source
    from ..complex_isolation import certify_complex_isolation
    from ..enclosure_policy import EnclosurePolicy
    from ..quotient_isolation import (
        certify_quotient_isolation,
        quotient_source_supported,
    )

    if (
        quotient_source_supported(expr, var)
        and CoverageRectangle(*rect.as_pair()).valid()
    ):
        return _quotient_result(
            certify_quotient_isolation(
                expr,
                var,
                *rect.as_pair(),
                max_box_width=max_box_width,
                max_box_diameter=max_box_diameter,
                use_multiple=use_multiple,
                policy=policy
                if policy is not None
                else EnclosurePolicy(
                    precision=precision,
                    max_precision=max(precision, 240),
                    max_depth=max_isolation_depth,
                ),
                max_boundary_depth=max_boundary_depth,
            )
        )

    if entire_source(expr, var) and CoverageRectangle(*rect.as_pair()).valid():
        native_policy = (
            policy
            if policy is not None
            else EnclosurePolicy(
                precision=precision,
                max_precision=max(precision, 240),
                max_depth=max_isolation_depth,
            )
        )
        return _native_result(
            certify_complex_isolation(
                expr,
                var,
                *rect.as_pair(),
                max_box_width=max_box_width,
                max_box_diameter=max_box_diameter,
                use_newton=use_newton,
                use_multiple=use_multiple,
                policy=native_policy,
                max_boundary_depth=max_boundary_depth,
            )
        )

    exact = _exact_roots(expr, var, rect)
    if exact is not None:
        return ComplexRootIsolationResult(
            exact,
            complete=True,
            total_count=_exact_multiplicity_count(expr, var, exact),
            method="exact_complex_roots",
            evidence=(("rectangle", rect),),
            distinct_root_count=len(exact),
            isolation_complete=True,
        )

    cache = {}

    def count(r):
        key = (r.re_min, r.re_max, r.im_min, r.im_max)
        if key not in cache:
            cache[key] = argument_principle_count(
                expr,
                var,
                r,
                precision=precision,
                max_boundary_depth=max_boundary_depth,
            )
        return cache[key]

    parent = count(rect)
    if not parent.certified or parent.zero_count is None:
        return ComplexRootIsolationResult(
            complete=False,
            total_count=None,
            method="uncertified_complex_isolation",
            evidence=(parent,),
            certificates=(parent,),
        )
    if parent.zero_count == 0:
        return ComplexRootIsolationResult(
            complete=True,
            total_count=0,
            method="validated_argument_principle",
            evidence=(parent,),
            certificates=(parent,),
            distinct_root_count=0,
            isolation_complete=True,
        )

    leaves = []
    certs = [parent]
    split_ratios = (
        (sp.Rational(1, 2), sp.Rational(1, 2)),
        (sp.Rational(2, 5), sp.Rational(2, 5)),
        (sp.Rational(3, 5), sp.Rational(3, 5)),
        (sp.Rational(2, 5), sp.Rational(3, 5)),
        (sp.Rational(3, 5), sp.Rational(2, 5)),
    )

    def rec(r, cert, depth):
        n = cert.zero_count
        if n is None or n == 0:
            return True
        if n == 1:
            leaves.append(CertifiedComplexRootRectangle(r, 1, cert))
            return True
        if depth >= max_isolation_depth:
            leaves.append(CertifiedComplexRootRectangle(r, n, cert))
            return True
        for rx, ry in split_ratios:
            child_rects = _children(r, rx, ry)
            child_certs = tuple(count(q) for q in child_rects)
            if not all(c.certified and c.zero_count is not None for c in child_certs):
                continue
            if sum(c.zero_count for c in child_certs) != n:
                continue
            certs.extend(child_certs)
            return all(
                rec(q, c, depth + 1)
                for q, c in zip(child_rects, child_certs, strict=True)
            )
        leaves.append(CertifiedComplexRootRectangle(r, n, cert))
        return True

    complete = rec(rect, parent, 0)
    return ComplexRootIsolationResult(
        rectangles=tuple(leaves),
        complete=complete,
        total_count=parent.zero_count,
        method="validated_complex_rectangle_isolation",
        evidence=(parent,),
        certificates=tuple(certs),
        distinct_root_count=len(leaves)
        if all(q.root_count == 1 for q in leaves)
        else None,
        isolation_complete=complete and all(q.root_count == 1 for q in leaves),
    )


def complex_zeros(
    expr,
    var,
    *,
    rectangle,
    return_result=False,
    precision=60,
    max_boundary_depth=14,
    max_isolation_depth=10,
    domain=S.Complexes,
    condition=S.true,
    policy=None,
    max_box_width=None,
    max_box_diameter=None,
    use_newton=True,
    use_multiple=True,
):
    """Return zeros in a closed complex rectangle, with certification when needed."""
    result = isolate_complex_roots(
        expr,
        var,
        rectangle,
        precision=precision,
        max_boundary_depth=max_boundary_depth,
        max_isolation_depth=max_isolation_depth,
        domain=domain,
        condition=condition,
        policy=policy,
        max_box_width=max_box_width,
        max_box_diameter=max_box_diameter,
        use_newton=use_newton,
        use_multiple=use_multiple,
    )
    if return_result:
        return result
    if result.complete and result.roots:
        return sp.FiniteSet(*result.roots)
    if result.complete and result.total_count == 0:
        return S.EmptySet
    return result
