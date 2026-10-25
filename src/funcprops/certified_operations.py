"""Replayable high-level certified operations built from Funcprops facts."""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from .exactness import certify_identity_equal
from .integration import ParametricContour, integrate
from .local_analyticity import (
    ENTIRE_FUNCTIONS,
    _punctured_source_defined,
    complex_meromorphic_germ,
    essential_laurent_data,
)
from .local_branches import LocalBranchContext
from .source_syntax import differentiate, expand_log_bases, finite_constant_source
from .work_budget import budgeted_operation


class _ReplayedOperation:
    @property
    def certified(self):
        try:
            return bool(self.verify())
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False

    @property
    def complete(self):
        return self.certified


@dataclass(frozen=True)
class InverseCertificate(_ReplayedOperation):
    """Bind an inverse formula to domain, image and two-sided identity premises."""

    expression: sp.Expr
    variable: sp.Symbol
    value: sp.Symbol
    inverse: sp.Expr
    domain: sp.Set
    image: sp.Set

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        from sympy.calculus.util import function_range as sympy_function_range

        from .domain_tracking import coordinate_domain_compatible, track_domain

        if not isinstance(self.variable, sp.Symbol) or not isinstance(
            self.value, sp.Symbol
        ):
            return False
        record = track_domain(self.expression, self.variable, self.domain)
        if not record.complete or record.effective != self.domain:
            return False
        if not coordinate_domain_compatible(self.value, self.image):
            return False
        inverse_record = track_domain(self.inverse, self.value, self.image)
        if not inverse_record.complete or inverse_record.effective != self.image:
            return False
        try:
            actual_image = sympy_function_range(
                self.expression, self.variable, self.domain
            )
        except (TypeError, ValueError, NotImplementedError, ImportError, RuntimeError):
            return False
        if actual_image != self.image:
            return False
        right = (
            certify_identity_equal(
                self.expression.subs(self.variable, self.inverse), self.value
            )
            is True
        )
        left = (
            certify_identity_equal(
                self.inverse.subs(self.value, self.expression), self.variable
            )
            is True
        )
        return right and left


@budgeted_operation
def inverse(expr, var, *, value=None, domain=sp.S.Reals, return_certificate=False):
    """Return a symbolic inverse after checking supported domain and identity premises."""

    e = sp.sympify(expr)
    x = sp.sympify(var)
    y = sp.Dummy("_inverse_value") if value is None else sp.sympify(value)
    if not isinstance(y, sp.Symbol):
        raise TypeError("value must be a Symbol naming the inverse-function argument")
    from .domain_tracking import track_domain

    record = track_domain(e, x, domain)
    if not record.complete or record.effective != domain:
        return None
    from .api import injective

    inj = injective(e, x, domain=domain)
    # A unique symbolic inverse plus a certified nonzero constant derivative is
    # itself an injectivity proof, avoiding dependence on result presentation.
    d = sp.simplify(differentiate(e, x))
    affine_injective = not d.has(x) and d.is_zero is False
    sol = sp.solve(sp.Eq(e, y), x)
    inj_true = (
        inj is True
        or getattr(inj, "name", "") in ("TRUE", "INJECTIVE")
        or affine_injective
    )
    if len(sol) != 1 or not inj_true:
        return None
    inv = sp.simplify(sol[0])
    # The certificate stores the actual image, so do not substitute a guessed
    # UniversalSet when range computation is unavailable.
    try:
        from sympy.calculus.util import function_range as sympy_function_range

        img = sympy_function_range(e, x, domain)
    except (TypeError, ValueError, NotImplementedError, ImportError, RuntimeError):
        return None
    if not isinstance(img, sp.Set):
        return None
    c = InverseCertificate(e, x, y, inv, domain, img)
    if not c.verify():
        return None
    return c if return_certificate else inv


def _equation_real_domain(expression, variable, domain):
    """Retain active branch exclusions even when the whole query has holes."""
    from .domain_tracking import track_domain
    from .real_analysis.common import condition_to_set

    record = track_domain(expression, variable, domain)
    if record.complete:
        return record.effective
    if not isinstance(expression, sp.Piecewise):
        return None
    remaining, pieces = domain, []
    for branch, condition in expression.args:
        if remaining is sp.S.EmptySet:
            break
        for relation in condition.atoms(sp.core.relational.Relational):
            for operand in (relation.lhs, relation.rhs):
                guard_record = track_domain(operand, variable, remaining)
                if not guard_record.complete or guard_record.effective != remaining:
                    return None
        guard = condition_to_set(condition, variable)
        if not isinstance(guard, sp.Set):
            return None
        active = sp.Intersection(remaining, guard)
        if active is not sp.S.EmptySet:
            branch_domain = _equation_real_domain(branch, variable, active)
            if branch_domain is None:
                return None
            pieces.append(branch_domain)
        remaining = sp.Complement(remaining, guard)
    # Uncovered points have no defined branch (the implicit value is nan).
    return sp.Union(*pieces)


def _equation_solution_data(expression, variable, domain):
    """Preserve source exclusions before giving a normalized formula to SymPy."""
    if not isinstance(variable, sp.Symbol) or not isinstance(domain, sp.Set):
        raise TypeError("equation solving requires a Symbol and a Set domain")
    parameters = expression.free_symbols - {variable}
    parameter_root = None
    normalized = expression
    if parameters:
        safe = False
        coefficient, dependent = expression.as_independent(variable, as_Add=False)
        if (
            coefficient.is_finite is True
            and coefficient.is_zero is False
            and not (dependent.free_symbols - {variable})
        ):
            normalized, safe = dependent, True
        else:
            try:
                polynomial = sp.Poly(expression, variable)
                if polynomial.degree() == 1:
                    slope, offset = polynomial.all_coeffs()
                    if slope.is_zero is False and all(
                        c.is_finite is True for c in (slope, offset)
                    ):
                        parameter_root, safe = -offset / slope, True
            except (sp.PolynomialError, TypeError, ValueError):
                pass
        if not safe:
            return (
                sp.ConditionSet(variable, sp.Eq(expression, 0, evaluate=False), domain),
                False,
                domain,
            )
    real_domain = domain.is_subset(sp.S.Reals) is True
    axis = (
        sp.Dummy("equation_coordinate", real=True)
        if real_domain
        else sp.Dummy("equation_coordinate")
    )
    effective = domain
    exclusions_complete = True
    if real_domain:
        # First-match Piecewise domains must be tracked before traversing poles:
        # an inactive denominator cannot exclude a root of another branch.
        effective = _equation_real_domain(expression, variable, domain)
        if effective is None:
            condition = sp.Eq(expression, 0, evaluate=False)
            return sp.ConditionSet(variable, condition, domain), False, domain
    else:
        from .local_analyticity import complex_definition_domain

        effective = complex_definition_domain(expression, variable, domain)
        if effective is None:
            condition = sp.Eq(expression, 0, evaluate=False)
            return sp.ConditionSet(variable, condition, domain), False, domain
    if parameter_root is not None:
        return sp.Intersection(sp.FiniteSet(parameter_root), effective), True, effective
    if not real_domain and expression.has(sp.Piecewise):
        from .local_analyticity import complex_definition_domain

        cells = []
        folded = sp.piecewise_fold(expression)
        coverage = complex_definition_domain(
            folded, variable, effective, _branch_cells=cells
        )
        if coverage != effective or not cells:
            condition = sp.Eq(expression, 0, evaluate=False)
            return sp.ConditionSet(variable, condition, effective), False, effective
        results = [
            _equation_solution_data(branch, variable, region)
            for branch, region in cells
        ]
        return sp.Union(*(r[0] for r in results)), all(r[1] for r in results), effective
    roots = sp.solveset(normalized.xreplace({variable: axis}), axis, domain=effective)
    return roots, exclusions_complete and not roots.has(sp.ConditionSet), effective


@dataclass(frozen=True)
class EquationSolutionCertificate:
    """Bind a solution set to source definition and exhaustive equation evidence."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    solutions: sp.Set
    complete: bool
    effective_domain: sp.Set | None = None

    @property
    def certified(self):
        """Report successful replay independently of exhaustive solution coverage."""
        return self.verify()

    @property
    def scope(self):
        return "source-domain-and-equation-solution-set"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        if (
            type(self.complete) is not bool
            or not isinstance(self.expression, sp.Basic)
            or not isinstance(self.variable, sp.Symbol)
            or not isinstance(self.domain, sp.Set)
            or not isinstance(self.solutions, sp.Set)
        ):
            return False
        try:
            solutions, complete, effective = _equation_solution_data(
                self.expression, self.variable, self.domain
            )
            return (
                (solutions == self.solutions or solutions.dummy_eq(self.solutions))
                and self.complete is complete
                and (
                    self.effective_domain is None
                    or self.effective_domain == effective
                    or effective.dummy_eq(self.effective_domain)
                )
            )
        except (TypeError, ValueError, NotImplementedError, ArithmeticError):
            return False


@budgeted_operation
def solve(
    expr,
    var,
    *,
    domain=sp.S.Complexes,
    return_certificate=False,
    guarded=False,
    assumptions=True,
):
    """Return a supported equation's solution set, with detailed evidence on request."""

    e = sp.sympify(expr)
    x = sp.sympify(var)
    if guarded:
        from .guarded_affine import affine_equation_cases

        certificate = affine_equation_cases(e, x, domain, assumptions=assumptions)
        return certificate if return_certificate else certificate.as_result()
    if assumptions is not True and assumptions is not sp.S.true:
        raise ValueError("assumptions require guarded=True for equation solving")
    solutions, complete, effective = _equation_solution_data(e, x, domain)
    certificate = EquationSolutionCertificate(
        e, x, domain, solutions, complete, effective
    )
    return certificate if return_certificate else solutions


def _complex_local_series(expression, variable, point, order):
    axis = sp.Dummy("series_coordinate", complex=True)
    normalized = sp.simplify(expression.xreplace({variable: axis}))
    return sp.series(normalized, axis, point, order).xreplace({axis: variable})


def _complex_local_residue(expression, variable, point):
    axis = sp.Dummy("residue_coordinate", complex=True)
    normalized = sp.simplify(expression.xreplace({variable: axis}))
    return sp.residue(normalized, axis, point)


@dataclass(frozen=True)
class LaurentCertificate(_ReplayedOperation):
    """Record a checked local Laurent expansion with branch and order premises."""

    expression: sp.Expr
    variable: sp.Symbol
    point: sp.Expr
    series: sp.Expr
    order: int
    branch_context: LocalBranchContext | None = None

    @property
    def scope(self):
        return (
            "local-selected-meromorphic-germ-series"
            if self.branch_context is not None
            else "local-principal-meromorphic-germ-series"
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            expression = self.expression
            if self.branch_context is not None:
                if type(self.branch_context) is not LocalBranchContext:
                    return False
                expression = self.branch_context.apply(
                    expression, self.variable, self.point
                )
                if expression is None:
                    return False
            special = essential_laurent_data(expression, self.variable, self.point)
            if special is not None:
                return type(self.order) is int and special[0].dummy_eq(self.series)
            return (
                type(self.order) is int
                and complex_meromorphic_germ(expression, self.variable, self.point)
                and _complex_local_series(
                    expression, self.variable, self.point, self.order
                )
                == self.series
            )
        except (TypeError, ValueError, NotImplementedError, ArithmeticError):
            return False


@budgeted_operation
def laurent_series(
    expr, var, point=0, *, order=6, return_certificate=False, branch_context=None
):
    """Return a checked Laurent expansion at an exact point and chosen local branch."""

    e = sp.sympify(expr)
    x = sp.sympify(var)
    p = sp.sympify(point)
    if type(order) is not int:
        raise ValueError("order must be an integer")
    source = e
    if branch_context is not None:
        if type(branch_context) is not LocalBranchContext:
            raise TypeError("branch_context must be a LocalBranchContext")
        e = branch_context.apply(e, x, p)
        if e is None:
            return None
    special = essential_laurent_data(e, x, p)
    if special is not None:
        c = LaurentCertificate(source, x, p, special[0], order, branch_context)
        return c if return_certificate else c.series
    if not complex_meromorphic_germ(e, x, p):
        return None
    result = _complex_local_series(e, x, p, order)
    c = LaurentCertificate(source, x, p, result, order, branch_context)
    return c if return_certificate else result


@dataclass(frozen=True)
class ResidueCertificate(_ReplayedOperation):
    """Bind a residue to a checked local expansion or exact order theorem."""

    expression: sp.Expr
    variable: sp.Symbol
    point: sp.Expr
    residue: sp.Expr
    branch_context: LocalBranchContext | None = None

    @property
    def scope(self):
        return (
            "residue-of-selected-local-branch"
            if self.branch_context is not None
            else "residue-of-principal-local-germ"
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            expression = self.expression
            if self.branch_context is not None:
                if type(self.branch_context) is not LocalBranchContext:
                    return False
                expression = self.branch_context.apply(
                    expression, self.variable, self.point
                )
                if expression is None:
                    return False
            special = essential_laurent_data(expression, self.variable, self.point)
            if special is not None:
                return certify_identity_equal(special[1], self.residue) is True
            return (
                complex_meromorphic_germ(expression, self.variable, self.point)
                and certify_identity_equal(
                    _complex_local_residue(expression, self.variable, self.point),
                    self.residue,
                )
                is True
            )
        except (TypeError, ValueError, NotImplementedError, ArithmeticError):
            return False


@budgeted_operation
def residue(expr, var, point, *, return_certificate=False, branch_context=None):
    """Return a residue from supported exact local-order or Laurent data."""

    e = sp.sympify(expr)
    x = sp.sympify(var)
    p = sp.sympify(point)
    source = e
    if branch_context is not None:
        if type(branch_context) is not LocalBranchContext:
            raise TypeError("branch_context must be a LocalBranchContext")
        e = branch_context.apply(e, x, p)
        if e is None:
            return None
    special = essential_laurent_data(e, x, p)
    if special is not None:
        c = ResidueCertificate(source, x, p, special[1], branch_context)
        return c if return_certificate else c.residue
    if not complex_meromorphic_germ(e, x, p):
        return None
    result = _complex_local_residue(e, x, p)
    c = ResidueCertificate(source, x, p, result, branch_context)
    return c if return_certificate else result


@dataclass(frozen=True)
class WindingCertificate(_ReplayedOperation):
    """Bind an integer winding to a supported closed nonvanishing path."""

    contour: ParametricContour
    point: sp.Expr
    winding: int
    integral: sp.Expr

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        expected = 2 * sp.pi * sp.I * self.winding
        return (
            winding_number(self.contour, self.point) == self.winding
            and certify_identity_equal(self.integral, expected) is True
        )


def _raw_circle_phase(argument):
    """Strip the outer imaginary coefficient without cancelling source holes."""
    if argument is sp.I:
        return sp.S.One
    if argument.is_Mul and sp.I in argument.args:
        factors = list(argument.args)
        factors.remove(sp.I)
        return sp.Mul(*factors, evaluate=False)
    if argument.is_Add:
        terms = [_raw_circle_phase(term) for term in argument.args]
        if all(term is not None for term in terms):
            return sp.Add(*terms, evaluate=False)
    return None


@budgeted_operation
def winding_number(contour, point=0, *, return_certificate=False):
    """Return a checked integer winding for a supported closed nonvanishing path."""

    if not isinstance(contour, ParametricContour) or not contour.closed:
        return None
    p = sp.sympify(point)
    if p.is_finite is not True:
        return None
    t = contour.parameter
    g = contour.gamma
    # Exact affine circle recognition c + A*exp(I*(n*t+phi)).  This path must
    # precede symbolic integration: definite log antiderivatives can erase turns.
    exps = [a for a in g.atoms(sp.exp) if a.args[0].has(t)]
    if len(exps) == 1:
        E = exps[0]
        phi = _raw_circle_phase(E.args[0])
        from .domain_tracking import smooth_domain_record

        if phi is None:
            return None
        a, b = contour.lower, contour.upper
        if any(v.is_real is not True or v.is_finite is not True for v in (a, b)):
            return None
        phase_domain = sp.Interval(sp.Min(a, b), sp.Max(a, b))
        # A real C1 phase is what makes the fixed-radius circle theorem apply.
        # A complex phase changes the radius; endpoint agreement is insufficient.
        if smooth_domain_record(phi, t, phase_domain, 1) is None:
            return None
        # exp(i*phi(t)) has winding (phi(b)-phi(a))/(2*pi) when phi is real
        # on the real parameter interval; no monotonicity is required.
        turns = sp.simplify(
            (phi.subs(t, contour.upper) - phi.subs(t, contour.lower)) / (2 * sp.pi)
        )
        if turns.is_Integer is True:
            n = int(turns)
            center, oscillating = g.as_independent(E, as_Add=True)
            A = oscillating.coeff(E)
            if not center.has(t) and not A.has(t):
                if any(v.is_finite is not True for v in (A, center, p)):
                    return None
                if certify_identity_equal(oscillating, A * E) is not True:
                    return None
                delta = sp.simplify(abs(A) ** 2 - sp.Abs(p - center) ** 2)
                if delta.is_positive is True:
                    w = n
                elif delta.is_negative is True:
                    w = 0
                else:
                    w = None
                if w is not None:
                    c = WindingCertificate(contour, p, w, 2 * sp.pi * sp.I * w)
                    return c if return_certificate else w
        # A failed circle premise must not be restored by an unproved
        # single-exponential integration fallback (including boundary poles).
        return None
    if not _continuation_contour_is_piecewise_c1(contour):
        return None
    from .piecewise_proofs import complex_avoids_value

    interval = sp.Interval(
        sp.Min(contour.lower, contour.upper), sp.Max(contour.lower, contour.upper)
    )
    if not complex_avoids_value(g, t, interval, p):
        return None
    if g.has(sp.Piecewise):
        for direction in (sp.S.One, sp.I, 1 + 2 * sp.I, 2 + sp.I):
            if _cut_system_valid((p,), contour.start, direction):
                word = _cut_crossing_word(contour, (p,), direction)
                if word is not None:
                    count = sum(word)
                    certificate = WindingCertificate(
                        contour, p, count, 2 * sp.pi * sp.I * count
                    )
                    return certificate if return_certificate else count
        return None
    z = sp.Dummy("_z")
    r = integrate(1 / (z - p), (z, contour), return_result=True)
    if not r.complete:
        return None
    n = sp.simplify(r.value / (2 * sp.pi * sp.I))
    if n.is_Integer is not True:
        return None
    c = WindingCertificate(contour, p, int(n), r.value)
    return c if return_certificate else c.winding


@dataclass(frozen=True)
class ArgumentPrincipleResult:
    """Record a contour's zero, pole and winding counts with its evidence."""

    expression: sp.Expr
    variable: sp.Symbol
    contour: ParametricContour
    zeros_minus_poles: int
    certified: bool

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        fresh = argument_principle(self.expression, self.variable, self.contour)
        return (
            self.certified is True
            and type(self.zeros_minus_poles) is int
            and fresh is not None
            and fresh == self.zeros_minus_poles
        )


@budgeted_operation
def argument_principle(
    expr, var, contour, *, return_certificate=False, guarded=False, assumptions=True
):
    """Return supported contour zero/pole counts with their analytic premises."""

    if guarded:
        from .guarded_affine import affine_contour_cases

        certificate = affine_contour_cases(expr, var, contour, assumptions=assumptions)
        return certificate if return_certificate else certificate.as_result()
    if assumptions is not True and assumptions is not sp.S.true:
        raise ValueError(
            "assumptions require guarded=True for argument-principle cases"
        )
    from .meromorphic_contours import _rational_source_polynomials

    e, x = sp.sympify(expr), sp.sympify(var)
    if not _continuation_contour_is_piecewise_c1(contour):
        return None
    try:
        source = _rational_source_polynomials(e, x)
        if source is None:
            return None
        pn, pd, guards = source
        # Source denominator roots on the path remain excluded after cancellation.
        for guard in guards:
            if _divisor_winding(guard.as_expr(), x, contour) is None:
                return None
        nr, dr = sp.roots(pn), sp.roots(pd)
        if sum(nr.values()) != pn.degree() or sum(dr.values()) != pd.degree():
            return None
        total = 0
        for roots, sign in ((nr, 1), (dr, -1)):
            for root, multiplicity in roots.items():
                winding = winding_number(contour, root)
                if winding is None:
                    return None
                total += sign * multiplicity * winding
        c = ArgumentPrincipleResult(e, x, contour, int(total), True)
        return c if return_certificate else c.zeros_minus_poles
    except (
        sp.PolynomialError,
        TypeError,
        ValueError,
        NotImplementedError,
        ArithmeticError,
    ):
        return None


@dataclass(frozen=True)
class HomotopyCertificate(_ReplayedOperation):
    """Certificate for based-loop homotopy in a finitely punctured plane.

    ``word`` is the signed crossing word for a certified system of pairwise
    disjoint parallel cuts from the punctures to infinity.  ``reduced_word``
    is its free reduction.  Equality of reduced words is the complete
    invariant for based loops in ``C \\ punctures``.
    """

    first: ParametricContour
    second: ParametricContour
    punctures: tuple
    cut_direction: sp.Expr | None
    first_word: tuple
    second_word: tuple
    reduced_word: tuple

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        if (
            certify_identity_equal(self.first.start, self.second.start) is not True
            or certify_identity_equal(self.first.end, self.second.end) is not True
            or not self.first.closed
            or not self.second.closed
        ):
            return False
        ps = _distinct_punctures(self.punctures)
        if ps != self.punctures:
            return False
        if self.cut_direction is None:
            if len(ps) > 1:
                return False
            if not ps:
                a = b = ()
            else:
                wa = winding_number(self.first, ps[0])
                wb = winding_number(self.second, ps[0])
                if wa is None or wb is None:
                    return False
                a = tuple(([1] * wa) if wa >= 0 else ([-1] * (-wa)))
                b = tuple(([1] * wb) if wb >= 0 else ([-1] * (-wb)))
        else:
            if not _cut_system_valid(ps, self.first.start, self.cut_direction):
                return False
            a = _cut_crossing_word(self.first, ps, self.cut_direction)
            b = _cut_crossing_word(self.second, ps, self.cut_direction)
            if a is None or b is None:
                return False
        ar = _free_reduce(a)
        br = _free_reduce(b)
        return (
            a == self.first_word
            and b == self.second_word
            and ar == br == self.reduced_word
        )


def _distinct_punctures(punctures):
    out = []
    for p in map(sp.sympify, punctures):
        if not any(certify_identity_equal(p, q) is True for q in out):
            out.append(p)
    return tuple(out)


def _real_imag(expr):
    return tuple(map(sp.simplify, sp.expand_complex(expr).as_real_imag()))


def _strict_sign(expr):
    e = sp.simplify(expr)
    if e.is_positive is True:
        return 1
    if e.is_negative is True:
        return -1
    if e.is_zero is True:
        return 0
    return None


def _cut_system_valid(punctures, basepoint, direction):
    """Prove that parallel cuts p + s*d (s>=0) are disjoint and miss basepoint."""
    d = sp.sympify(direction)
    if certify_identity_equal(d, 0) is True:
        return False
    dc = sp.conjugate(d)
    # Parallel rays are disjoint when no pair of punctures lies on a line
    # parallel to the cut direction.
    for i, p in enumerate(punctures):
        for q in punctures[i + 1 :]:
            _, transverse = _real_imag((p - q) * dc)
            if _strict_sign(transverse) in (None, 0):
                return False
        along, transverse = _real_imag((sp.sympify(basepoint) - p) * dc)
        ts = _strict_sign(transverse)
        if ts == 0 and _strict_sign(along) in (0, 1):
            return False
        if ts is None:
            return False
    return True


def _interior(root, lower, upper):
    """Prove root lies strictly inside the oriented parameter interval."""
    lo = sp.simplify(root - lower)
    hi = sp.simplify(upper - root)
    if _strict_sign(sp.simplify(upper - lower)) == 1:
        return _strict_sign(lo) == 1 and _strict_sign(hi) == 1
    if _strict_sign(sp.simplify(lower - upper)) == 1:
        return _strict_sign(-lo) == 1 and _strict_sign(-hi) == 1
    return False


def _ordered_events(events, lower, upper):
    """Exactly order (parameter, generator, sign) events along orientation."""
    reverse = _strict_sign(sp.simplify(upper - lower)) == -1
    pending = list(events)
    ordered = []
    while pending:
        chosen = None
        for i, event in enumerate(pending):
            t0 = event[0]
            ok = True
            for j, other in enumerate(pending):
                if i == j:
                    continue
                diff = sp.simplify(t0 - other[0])
                sg = _strict_sign(diff)
                if sg is None or sg == 0:
                    ok = False
                    break
                if (not reverse and sg > 0) or (reverse and sg < 0):
                    ok = False
                    break
            if ok:
                chosen = i
                break
        if chosen is None:
            return None
        ordered.append(pending.pop(chosen))
    return ordered


def _cut_crossing_word(contour, punctures, direction):
    """Derive the exact signed cut-crossing word of a based loop.

    This proof path accepts only contours for which SymPy can
    solve every cut-line intersection as a finite exact set and prove every
    retained crossing transverse.  Ambiguous/tangent cases are left unknown.
    """
    if not contour.closed:
        return None
    t = contour.parameter
    # Give real/imag expansion a parameter carrying an explicit real
    # assumption even when the caller's Symbol omitted one.
    tr = sp.Dummy("_t_real", real=True)
    gamma = contour.gamma.xreplace({t: tr})
    a = (
        contour.lower.xreplace({t: tr})
        if isinstance(contour.lower, sp.Basic)
        else contour.lower
    )
    b = (
        contour.upper.xreplace({t: tr})
        if isinstance(contour.upper, sp.Basic)
        else contour.upper
    )
    dc = sp.conjugate(sp.sympify(direction))
    interval = sp.Interval(sp.Min(a, b), sp.Max(a, b))
    events = []
    for j, p in enumerate(punctures, start=1):
        along, transverse = _real_imag((gamma - p) * dc)
        roots = sp.solveset(transverse, tr, domain=interval)
        if not isinstance(roots, sp.FiniteSet):
            return None
        dtrans = differentiate(transverse, tr)
        for root in roots:
            # Endpoints are excluded because a valid cut system misses the
            # common basepoint.  If symbolic equality is undecidable, refuse.
            if (
                certify_identity_equal(root, a) is True
                or certify_identity_equal(root, b) is True
            ):
                continue
            if not _interior(root, a, b):
                return None
            radial = _strict_sign(along.subs(tr, root))
            if radial == 0:
                # The contour hits the puncture, so it is not a loop in the
                # punctured plane at all.
                return None
            if radial == -1:
                continue
            if radial is None:
                return None
            crossing = _strict_sign(dtrans.subs(tr, root))
            if crossing in (None, 0):
                return None
            # Parameter reversal reverses crossing orientation.
            if _strict_sign(sp.simplify(b - a)) == -1:
                crossing = -crossing
            events.append((root, j, crossing))
    ordered = _ordered_events(events, a, b)
    if ordered is None:
        return None
    return tuple(sign * generator for _, generator, sign in ordered)


def _free_reduce(word):
    stack = []
    for letter in word:
        letter = int(letter)
        if letter == 0:
            raise ValueError("free-group letters must be nonzero")
        if stack and stack[-1] == -letter:
            stack.pop()
        else:
            stack.append(letter)
    return tuple(stack)


_CUT_DIRECTIONS = (
    sp.S.One,
    sp.I,
    -sp.S.One,
    -sp.I,
    1 + sp.I,
    -1 + sp.I,
    -1 - sp.I,
    1 - sp.I,
    2 + sp.I,
    1 + 2 * sp.I,
)


@budgeted_operation
def homotopic(contour1, contour2, *, punctures=(), return_certificate=False):
    """Certify based-loop homotopy in ``C`` minus finitely many punctures.

    The implementation uses a certified cut system and the standard free-group
    normal form of ``pi_1(C \\ P)``.  Thus generator order is retained and the
    result is genuinely nonabelian for two or more punctures.  ``None`` means
    that exact crossing geometry could not be certified for the supplied
    symbolic parameterizations; it is not a negative homotopy result.
    """
    if not (
        isinstance(contour1, ParametricContour)
        and isinstance(contour2, ParametricContour)
    ):
        return None
    if (
        certify_identity_equal(contour1.start, contour2.start) is not True
        or certify_identity_equal(contour1.end, contour2.end) is not True
    ):
        return False
    if not contour1.closed or not contour2.closed:
        return None
    ps = _distinct_punctures(punctures)
    # For zero or one puncture the free group is trivial/cyclic, so the exact
    # winding-number certificate is already complete and covers substantially
    # more symbolic contours than explicit cut-intersection solving.
    if len(ps) <= 1:
        if not ps:
            a = b = ()
        else:
            wa = winding_number(contour1, ps[0])
            wb = winding_number(contour2, ps[0])
            if wa is None or wb is None:
                return None
            if wa != wb:
                return False
            a = tuple(([1] * wa) if wa >= 0 else ([-1] * (-wa)))
            b = tuple(([1] * wb) if wb >= 0 else ([-1] * (-wb)))
        cert = HomotopyCertificate(contour1, contour2, ps, None, a, b, _free_reduce(a))
        return cert if return_certificate else True
    base = contour1.start
    for direction in _CUT_DIRECTIONS:
        if not _cut_system_valid(ps, base, direction):
            continue
        a = _cut_crossing_word(contour1, ps, direction)
        b = _cut_crossing_word(contour2, ps, direction)
        if a is None or b is None:
            continue
        ar = _free_reduce(a)
        br = _free_reduce(b)
        if ar != br:
            return False
        cert = HomotopyCertificate(contour1, contour2, ps, direction, a, b, ar)
        return cert if return_certificate else True
    return None


@dataclass(frozen=True)
class ContinuationCertificate(_ReplayedOperation):
    """Record an analytic continuation path and its selected branch data."""

    expression: sp.Expr
    variable: sp.Symbol
    contour: ParametricContour
    continued: sp.Expr
    substitutions: tuple

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        fresh = analytic_continue(
            self.expression, self.variable, self.contour, return_certificate=True
        )
        return (
            fresh is not None
            and isinstance(self.continued, sp.Expr)
            and fresh.continued == self.continued
            and fresh.substitutions == self.substitutions
        )


def _divisor_winding(expr, variable, contour):
    """Return the (possibly rational) winding of an algebraic product/quotient.

    The result is the change of a continuous logarithm divided by ``2*pi*i``.
    Rational powers therefore retain their valuation
    as simple zeros.  ``None`` means that this exact structural proof does not
    cover the expression.
    """
    e = sp.sympify(expr)
    z = sp.sympify(variable)
    if not e.has(z):
        return sp.S.Zero if e.is_zero is False and e.is_finite is True else None
    if e.is_Mul:
        parts = [_divisor_winding(arg, z, contour) for arg in e.args]
        if any(part is None for part in parts):
            return None
        return sp.simplify(sum(parts, sp.S.Zero))
    if e.is_Pow and not e.exp.has(z) and e.exp.is_finite is True:
        base_winding = _divisor_winding(e.base, z, contour)
        if base_winding is None:
            return None
        return sp.simplify(e.exp * base_winding)
    num, den = sp.fraction(sp.cancel(e))
    total = sp.S.Zero
    for poly, sign in ((num, 1), (den, -1)):
        try:
            P = sp.Poly(poly, z)
        except sp.PolynomialError:
            return None
        roots = sp.roots(P)
        if sum(roots.values()) != P.degree():
            return None
        for root, multiplicity in roots.items():
            winding = winding_number(contour, root)
            if winding is None:
                return None
            total += sign * multiplicity * winding
    return sp.simplify(total)


def _continuation_contour_is_piecewise_c1(contour):
    """Check a finite continuous, piecewise C1 closed path and raw source poles."""
    from .domain_tracking import coordinate_domain_compatible

    if not isinstance(contour, ParametricContour) or not contour.closed:
        return False
    t, a, b = contour.parameter, contour.lower, contour.upper
    if any(
        value.is_real is not True or value.is_finite is not True for value in (a, b)
    ):
        return False
    domain = sp.Interval(sp.Min(a, b), sp.Max(a, b))
    if not coordinate_domain_compatible(t, domain):
        return False
    from .piecewise_proofs import complex_source_defined, real_path_piecewise_c1

    if not complex_source_defined(contour.gamma, t, domain):
        return False
    axis = sp.Dummy("contour_coordinate", real=True)
    try:
        gamma = sp.expand_complex(contour.gamma.xreplace({t: axis}))
        return all(
            real_path_piecewise_c1(sp.piecewise_fold(part), axis, domain)
            for part in (sp.re(gamma), sp.im(gamma))
        )
    except (TypeError, ValueError, NotImplementedError):
        return False


@budgeted_operation
def analytic_continue(expr, var, contour, *, return_certificate=False):
    """Continue supported holomorphic operations and constant finite powers."""
    source = sp.sympify(expr)
    e = expand_log_bases(source)
    z = sp.sympify(var)
    if not isinstance(z, sp.Symbol) or not _continuation_contour_is_piecewise_c1(
        contour
    ):
        return None
    allowed_functions = ENTIRE_FUNCTIONS | {sp.log}
    for node in sp.preorder_traversal(e):
        if (
            isinstance(node, sp.Function)
            and node.has(z)
            and node.func not in allowed_functions
        ):
            return None
        if not node.has(z) and not finite_constant_source(node):
            return None
        if isinstance(node, sp.Pow):
            if node.exp.has(z) or not finite_constant_source(node.exp):
                return None
            if (
                not (node.exp.is_integer is True and node.exp.is_nonnegative is True)
                and _divisor_winding(node.base, z, contour) is None
            ):
                return None
    repl = {}
    evidence = []
    atoms = sorted(e.atoms(sp.log), key=sp.default_sort_key)
    for a in atoms:
        arg = a.args[0]
        delta = _divisor_winding(arg, z, contour)
        if delta is None:
            return None
        repl[a] = a + 2 * sp.pi * sp.I * delta
        evidence.append((a, delta))
    # A constant finite exponent q acquires exp(2*pi*i*q*w), including
    # irrational and complex q. Variable-dependent exponents remain unsupported.
    for a in sorted(e.atoms(sp.Pow), key=sp.default_sort_key):
        if a.exp.is_integer is True:
            continue
        if a.exp.has(z) or a.exp.is_finite is not True:
            return None
        delta = _divisor_winding(a.base, z, contour)
        if delta is None:
            return None
        repl[a] = a * sp.exp(2 * sp.pi * sp.I * a.exp * delta)
        evidence.append((a, delta))
    out = sp.expand(e.xreplace(repl))
    c = ContinuationCertificate(source, z, contour, out, tuple(evidence))
    return c if return_certificate else out


@budgeted_operation
def monodromy(expr, var, contour, *, return_certificate=False):
    """Return the branch change from continuation around a supported closed path."""

    return analytic_continue(expr, var, contour, return_certificate=return_certificate)


@dataclass(frozen=True)
class SingularityClassificationCertificate(_ReplayedOperation):
    """Bind a local singularity kind to source definition and isolated order data."""

    expression: sp.Expr
    variable: sp.Symbol
    point: sp.Expr
    kind: str
    order: sp.Expr | None
    branch_context: LocalBranchContext | None = None

    @property
    def scope(self):
        return (
            "classification-of-selected-local-branch"
            if self.branch_context is not None
            else "classification-of-principal-local-germ"
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        if (
            self.branch_context is not None
            and type(self.branch_context) is not LocalBranchContext
        ):
            return False
        fresh = classify_singularity(
            self.expression,
            self.variable,
            self.point,
            return_certificate=True,
            branch_context=self.branch_context,
        )
        return (
            fresh is not None and fresh.kind == self.kind and fresh.order == self.order
        )


@budgeted_operation
def classify_singularity(
    expr, var, point, *, return_certificate=False, branch_context=None
):
    """Classify an isolated point using exact local order and branch structure."""
    from .singularities.records import order_at

    e = sp.sympify(expr)
    z = sp.sympify(var)
    p = sp.sympify(point)
    if (
        not isinstance(z, sp.Symbol)
        or p.is_finite is not True
        or p.has(z, sp.Float)
        or e.has(sp.Float)
    ):
        return None
    if branch_context is not None:
        if type(branch_context) is not LocalBranchContext:
            raise TypeError("branch_context must be a LocalBranchContext")
        transformed = branch_context.apply(e, z, p)
        if transformed is None:
            return None
        actual = classify_singularity(transformed, z, p, return_certificate=True)
        if actual is None:
            return None
        result = SingularityClassificationCertificate(
            e, z, p, actual.kind, actual.order, branch_context
        )
        return result if return_certificate else result.kind
    # Classify the original source, not just a continuation obtained by
    # canceling holes accumulating at the proposed singularity.
    if not _punctured_source_defined(e, z, p, allow_branch_points=True):
        return None
    # Rebase before simplification: real/positive Symbol assumptions do not
    # establish a complex-neighborhood theorem.
    axis = sp.Dummy("singularity_coordinate", complex=True)
    f = sp.simplify(e.xreplace({z: axis}))

    def meromorphic(value):
        return complex_meromorphic_germ(value, axis, p)

    def affine_germ(atom):
        u = sp.Dummy("singular_atom")
        lifted = f.xreplace({atom: u})
        coefficient = sp.simplify(differentiate(lifted, u))
        remainder = sp.simplify(lifted - coefficient * u)
        if coefficient.has(u) or remainder.has(u):
            return False
        if not meromorphic(coefficient) or not meromorphic(remainder):
            return False
        order = order_at(coefficient, axis, p)
        return order is not None and order.is_integer is True

    def result(kind, order):
        certificate = SingularityClassificationCertificate(e, z, p, kind, order)
        return certificate if return_certificate else kind

    # A local order alone does not prove holomorphy (Abs and conjugation can
    # have a one-directional series). Require a complex meromorphic germ.
    if complex_meromorphic_germ(e, z, p):
        if f is sp.S.Zero:
            return result("identically_zero", sp.oo)
        order = order_at(f, axis, p)
        if order is not None and order.is_integer is True:
            return result(
                "pole"
                if order.is_negative
                else "zero"
                if order.is_positive
                else "regular",
                order,
            )
        return None
    for atom in f.atoms(sp.log):
        argument = atom.args[0]
        order = order_at(argument, axis, p) if meromorphic(argument) else None
        if order is not None and order != 0 and affine_germ(atom):
            return result("branch_point", None)
    for atom in f.atoms(sp.Pow):
        if atom.exp.is_Rational is True and atom.exp.is_integer is not True:
            order = order_at(atom.base, axis, p) if meromorphic(atom.base) else None
            if (
                order is not None
                and (atom.exp * order).is_integer is False
                and affine_germ(atom)
            ):
                return result("branch_point", None)
    # An entire transcendental function of a pole is essential. Multiplication
    # and addition by nonzero/finite-order meromorphic germs preserve that type;
    # arbitrary rational compositions may instead have accumulating poles.
    for atom in f.atoms(sp.exp, sp.sin, sp.cos, sp.sinh, sp.cosh):
        argument = atom.args[0]
        order = order_at(argument, axis, p) if meromorphic(argument) else None
        if order is not None and order.is_negative is True and affine_germ(atom):
            return result("essential", None)
    return None


@dataclass(frozen=True)
class ContourDeformationCertificate(_ReplayedOperation):
    """Bind a contour deformation to geometric and analytic premises."""

    expression: sp.Expr
    variable: sp.Symbol
    first: ParametricContour
    second: ParametricContour
    punctures: tuple

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return (
            deform_contour(
                self.expression,
                self.variable,
                self.first,
                self.second,
                punctures=self.punctures,
                return_certificate=False,
            )
            is True
        )


@budgeted_operation
def deform_contour(
    expr, var, first, second, *, punctures=None, return_certificate=False
):
    """Certify contour deformation for rational meromorphic integrands."""
    e = sp.cancel(sp.sympify(expr))
    z = sp.sympify(var)
    _num, den = sp.fraction(e)
    try:
        pd = sp.Poly(den, z)
        roots = sp.roots(pd)
        if sum(roots.values()) != pd.degree():
            return None
        singular = tuple(roots)
    except sp.PolynomialError:
        return None
    # User-supplied punctures are additional forbidden points; they must never
    # replace poles forced by the integrand, or an omitted pole could make an
    # invalid deformation appear certified.
    extra = () if punctures is None else tuple(map(sp.sympify, punctures))
    ps = tuple(dict.fromkeys((*singular, *extra)))
    h = homotopic(first, second, punctures=ps)
    if h is not True:
        return h
    c = ContourDeformationCertificate(e, z, first, second, ps)
    return c if return_certificate else True
