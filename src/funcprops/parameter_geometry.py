"""Checked root-count geometry for bounded polynomial families with real parameters.

Hermite trace forms reduce distinct real-root counts to signatures of real
symmetric matrices. Characteristic-polynomial sign partitions include degree
loss, multiple roots and endpoint roots; unfinished sign trees remain explicit.
"""

from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise

import sympy as sp

from .coverage_contract import CheckOutcome, CheckResult
from .domain_tracking import coordinate_domain_compatible
from .parameter_checker import polynomial_source
from .source_syntax import normalize_arithmetic
from .work_budget import budgeted_operation

_ERRORS = (
    AttributeError,
    TypeError,
    ValueError,
    ArithmeticError,
    NotImplementedError,
    sp.PolynomialError,
)


def _variations(signs):
    signs = tuple(v for v in signs if v)
    return sum(a != b for a, b in pairwise(signs))


def _signature(signs):
    # A symmetric matrix has real eigenvalues. Descartes' sign rule is exact
    # for its characteristic polynomial and for the polynomial at -lambda.
    positive = _variations((1, *signs))
    negative = _variations((1, *(v * (-1) ** i for i, v in enumerate(signs, 1))))
    return positive - negative


def _header(expression, variable, parameters, domain, condition):
    if (
        not isinstance(variable, sp.Symbol)
        or type(parameters) is not tuple
        or not (1 <= len(parameters) <= 4)
        or len(set((variable, *parameters))) != len(parameters) + 1
        or any(
            not isinstance(a, sp.Symbol) or a.is_real is not True for a in parameters
        )
        or not coordinate_domain_compatible(variable, sp.S.Reals)
        or expression.free_symbols - set((variable, *parameters))
        or condition.free_symbols - set(parameters)
        or expression.has(sp.Float)
        or condition.has(sp.Float)
        or not polynomial_source(expression, set((variable, *parameters)))
    ):
        raise ValueError(
            "geometry requires an exact polynomial and one to four real parameters"
        )
    p = sp.Poly(normalize_arithmetic(expression), variable)
    if p.degree() is not sp.S.NegativeInfinity and p.degree() > 4:
        raise NotImplementedError("parameter geometry supports degree at most four")
    if domain is sp.S.Reals:
        domain = sp.Interval(-sp.oo, sp.oo)
    if not isinstance(domain, sp.Interval) or any(
        v not in (sp.oo, -sp.oo) and v.is_Rational is not True
        for v in (domain.start, domain.end)
    ):
        raise ValueError("geometry requires an interval with rational finite endpoints")
    from .real_analysis.common import is_semialgebraic_condition

    if not all(is_semialgebraic_condition(condition, a) for a in parameters):
        raise ValueError("parameter domain must be a rational semialgebraic condition")
    if any(
        not polynomial_source(side, set(parameters))
        for relation in condition.atoms(sp.core.relational.Relational)
        for side in (relation.lhs, relation.rhs)
    ):
        raise ValueError("parameter guards require exact rational polynomial operands")
    if sum(sp.count_ops(c) for c in p.all_coeffs()) > 80:
        raise NotImplementedError("parameter coefficient expression budget exceeded")
    return p, domain


@lru_cache(maxsize=128)
def _events(expression, variable, degree, domain):
    """Construct trace-form characteristic coefficients on a nonzero degree stratum."""
    p = sp.Poly(expression, variable)
    if degree <= 0:
        return (), (), None
    if (
        degree == 2
        and domain.start is sp.S.NegativeInfinity
        and domain.end is sp.S.Infinity
    ):
        return (sp.expand(p.nth(1) ** 2 - 4 * p.nth(2) * p.nth(0)),), (), "quadratic"
    leading = p.nth(degree)
    C = sp.zeros(degree)
    for i in range(1, degree):
        C[i, i - 1] = 1
    for i in range(degree):
        C[i, degree - 1] = -p.nth(i) / leading
    powers = [sp.eye(degree)]
    for _ in range(2 * degree + 1):
        powers.append(powers[-1] * C)
    weights = [sp.eye(degree)]
    a, b = domain.start, domain.end
    endpoints = tuple(v for v in (a, b) if v not in (-sp.oo, sp.oo))
    if endpoints:
        if len(endpoints) == 2:
            weights.append((C - a * sp.eye(degree)) * (b * sp.eye(degree) - C))
        elif a is not sp.S.NegativeInfinity:
            weights.append(C - a * sp.eye(degree))
        else:
            weights.append(b * sp.eye(degree) - C)
    events = []
    t = sp.Dummy("eigenvalue")
    for W in weights:
        H = sp.Matrix(
            degree,
            degree,
            lambda i, j, weight=W: sp.cancel(sp.trace(weight * powers[i + j])),
        )
        coefficients = H.charpoly(t).all_coeffs()[1:]
        # Expanded rational forms survive worker transport unchanged. SymPy's
        # factored products can reevaluate while unpickling their arguments.
        events.extend(sp.cancel(c) for c in coefficients)
    flags = tuple(
        sp.expand(sum(p.nth(i) * v**i for i in range(degree + 1))) for v in endpoints
    )
    return tuple(events), flags, len(weights)


@dataclass(frozen=True)
class ParameterGeometryRegion:
    """A prefix of the exact sign/endpoint partition on a fixed-degree stratum."""

    degree: int
    choices: tuple = ()


@dataclass(frozen=True)
class ParameterGeometryCell:
    """A constant distinct-root count or a proved empty parameter region."""

    region: ParameterGeometryRegion
    root_count: object = None
    empty: bool = False


def _region_data(proof, region):
    p = sp.Poly(normalize_arithmetic(proof.expression), proof.variable)
    d = region.degree
    upper = int(p.degree()) if not p.is_zero else -1
    if (
        type(region) is not ParameterGeometryRegion
        or type(d) is not int
        or not -1 <= d <= upper
        or type(region.choices) is not tuple
    ):
        raise ValueError("invalid geometry region")
    coefficients = tuple(p.nth(i) for i in range(upper + 1))
    degree_guard = sp.And(
        *(sp.Eq(coefficients[i], 0) for i in range(d + 1, upper + 1)),
        sp.Ne(coefficients[d], 0) if d >= 0 else sp.S.true,
    )
    events, flags, _ = _events(p.as_expr(), proof.variable, d, proof.domain)
    options = ((-1, 0, 1),) * len(events) + ((0, 1),) * len(flags)
    if len(region.choices) > len(options) or any(
        type(c) is not int or c not in allowed
        for c, allowed in zip(region.choices, options, strict=False)
    ):
        raise ValueError("invalid geometry choices")
    clauses = []
    for i, c in enumerate(region.choices):
        if i < len(events):
            clauses.append(
                sp.Lt(events[i], 0)
                if c < 0
                else sp.Gt(events[i], 0)
                if c > 0
                else sp.Eq(events[i], 0)
            )
        else:
            v = flags[i - len(events)]
            clauses.append(sp.Eq(v, 0) if c else sp.Ne(v, 0))
    return sp.And(proof.parameter_domain, degree_guard, *clauses), options


def _count(proof, region):
    _, options = _region_data(proof, region)
    if len(region.choices) != len(options):
        return None
    d = region.degree
    if d < 0:
        return sp.oo
    if d == 0:
        return sp.S.Zero
    events, _flags, weights = _events(
        normalize_arithmetic(proof.expression), proof.variable, d, proof.domain
    )
    choices = region.choices
    if weights == "quadratic":
        return sp.Integer({-1: 0, 0: 1, 1: 2}[choices[0]])
    count = _signature(choices[:d])
    if weights == 1:
        return sp.Integer(count) if 0 <= count <= d else None
    signed = _signature(choices[d : 2 * d])
    owned = choices[len(events) :]
    numerator = count + signed - sum(owned)
    if numerator % 2:
        return None
    result = numerator // 2
    for point, zero in zip(
        tuple(
            v
            for v in (proof.domain.start, proof.domain.end)
            if v not in (-sp.oo, sp.oo)
        ),
        owned,
        strict=True,
    ):
        if proof.domain.contains(point) is sp.S.true:
            result += zero
    return sp.Integer(result) if 0 <= result <= d else None


def _empty(guard, parameters):
    if guard is sp.S.false:
        return True
    if len(guard.free_symbols) > 1:
        return False
    try:
        from ._semialg import is_satisfiable

        return not is_satisfiable(guard, parameters)
    except _ERRORS:
        return False


def _covered(prefixes, options, prefix=()):
    """Check an exact prefix-tree cover; duplicates and prefix overlaps reject."""
    exact = sum(p == prefix for p in prefixes)
    if exact:
        return exact == 1 and len(prefixes) == 1
    if len(prefix) >= len(options):
        return False
    return all(
        _covered(
            tuple(p for p in prefixes if p[: len(prefix) + 1] == (*prefix, c)),
            options,
            (*prefix, c),
        )
        for c in options[len(prefix)]
    )


@dataclass(frozen=True)
class ParameterGeometryProof:
    """Bind a multi-parameter root-count partition and its unresolved sign trees."""

    expression: sp.Expr
    variable: sp.Symbol
    parameters: tuple
    domain: sp.Interval
    parameter_domain: sp.Basic
    events: tuple = ()
    cells: tuple = ()
    unresolved: tuple = ()
    tested: int = 0
    exhaustion: str | None = None

    @property
    def complete(self):
        return not self.unresolved

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "bounded-polynomial-multi-parameter-distinct-real-root-geometry"

    @property
    def strata(self):
        from .results import ConditionalExpression

        return tuple(
            ConditionalExpression(c.root_count, _region_data(self, c.region)[0])
            for c in self.cells
            if not c.empty
        )

    @property
    def unresolved_condition(self):
        return sp.Or(*(_region_data(self, r)[0] for r in self.unresolved))

    def specialize(self, substitutions):
        """Return the unique proved count at exact real parameter coordinates."""
        values = {sp.sympify(a): sp.sympify(v) for a, v in dict(substitutions).items()}
        if (
            set(values) != set(self.parameters)
            or any(
                not coordinate_domain_compatible(a, sp.FiniteSet(v))
                for a, v in values.items()
            )
            or any(
                v.free_symbols
                or v.has(sp.Float)
                or v.is_real is not True
                or v.is_finite is not True
                for v in values.values()
            )
            or not self.verify()
        ):
            return None
        counts = [
            c.root_count
            for c in self.cells
            if not c.empty
            and sp.simplify(
                _region_data(self, c.region)[0].subs(values, simultaneous=True)
            )
            is sp.S.true
        ]
        return counts[0] if len(counts) == 1 else None

    def check(self):
        """Replay trace signatures, all guard leaves and exact prefix-tree coverage."""
        reject = CheckResult(
            CheckOutcome.REJECTED, False, False, "false-parameter-geometry"
        )
        try:
            if (
                type(self) is not ParameterGeometryProof
                or type(self.cells) is not tuple
                or type(self.events) is not tuple
                or type(self.unresolved) is not tuple
                or type(self.tested) is not int
                or self.tested < 0
                or self.exhaustion not in (None, "cell-budget", "unresolved-guard")
            ):
                return reject
            p, D = _header(
                self.expression,
                self.variable,
                self.parameters,
                self.domain,
                self.parameter_domain,
            )
            if D != self.domain:
                return reject
            if self.events != _partition_events(p, self.variable, D):
                return reject
            regions = []
            for cell in self.cells:
                if (
                    type(cell) is not ParameterGeometryCell
                    or type(cell.empty) is not bool
                ):
                    return reject
                guard, _ = _region_data(self, cell.region)
                if cell.empty:
                    if cell.root_count is not None or not _empty(
                        guard, self.parameters
                    ):
                        return reject
                elif (
                    cell.root_count is None
                    or type(cell.root_count) is not type(_count(self, cell.region))
                    or cell.root_count != _count(self, cell.region)
                ):
                    return reject
                regions.append(cell.region)
            regions.extend(self.unresolved)
            upper = int(p.degree()) if not p.is_zero else -1
            for d in range(-1, upper + 1):
                initial = ParameterGeometryRegion(d)
                _, options = _region_data(self, initial)
                prefixes = tuple(r.choices for r in regions if r.degree == d)
                if not _covered(prefixes, options):
                    return reject
            if any(type(r) is not ParameterGeometryRegion for r in self.unresolved):
                return reject
            for region in self.unresolved:
                _region_data(self, region)
            return CheckResult(
                CheckOutcome.COMPLETE if self.complete else CheckOutcome.LOCAL_VALID,
                True,
                self.complete,
                self.exhaustion,
            )
        except _ERRORS:
            return reject

    def verify(self):
        """Return whether all supplied geometry claims and coverage bookkeeping replay."""
        return self.check().certified is True


@budgeted_operation
def certify_parameter_geometry(
    expression,
    variable,
    parameters,
    *,
    domain=sp.S.Reals,
    parameter_domain=sp.S.true,
    max_cells=256,
):
    """Boundedly partition polynomial parameter space by certified root counts.

    Up to four real parameters, degree at most four in the root coordinate and
    rational interval endpoints are supported. Counts are distinct-root counts;
    the unresolved frontier retains every region not discharged within the cap.
    """
    f, x = sp.sympify(expression), sp.sympify(variable)
    parameters = tuple(map(sp.sympify, parameters))
    condition = sp.sympify(parameter_domain)
    if type(max_cells) is not int or max_cells < 0:
        raise ValueError("max_cells must be a nonnegative integer")
    p, D = _header(f, x, parameters, domain, condition)
    proof = ParameterGeometryProof(
        f, x, parameters, D, condition, _partition_events(p, x, D)
    )
    return _refine_geometry(proof, max_cells)


def _partition_events(polynomial, variable, domain):
    upper = int(polynomial.degree()) if not polynomial.is_zero else -1
    return (
        tuple(polynomial.all_coeffs()),
        tuple(
            (d, _events(polynomial.as_expr(), variable, d, domain))
            for d in range(-1, upper + 1)
        ),
    )


def _refine_geometry(proof, max_cells):
    p = sp.Poly(normalize_arithmetic(proof.expression), proof.variable)
    f, x, D, parameters, condition = (
        proof.expression,
        proof.variable,
        proof.domain,
        proof.parameters,
        proof.parameter_domain,
    )
    upper = int(p.degree()) if not p.is_zero else -1
    queue = deque(
        proof.unresolved
        if proof.unresolved
        else (ParameterGeometryRegion(d) for d in range(upper, -2, -1))
    )
    cells = list(proof.cells)
    unresolved = []
    tested = 0
    reason = None
    while queue and tested < max_cells:
        region = queue.popleft()
        tested += 1
        guard, options = _region_data(proof, region)
        if guard is sp.S.false:
            cells.append(ParameterGeometryCell(region, empty=True))
            continue
        if len(region.choices) == len(options):
            count = _count(proof, region)
            if count is not None:
                cells.append(ParameterGeometryCell(region, count))
            elif _empty(guard, parameters):
                cells.append(ParameterGeometryCell(region, empty=True))
            else:
                unresolved.append(region)
                reason = "unresolved-guard"
        else:
            queue.extend(
                ParameterGeometryRegion(region.degree, (*region.choices, c))
                for c in options[len(region.choices)]
            )
    if queue:
        unresolved.extend(queue)
        reason = "cell-budget"
    return ParameterGeometryProof(
        f,
        x,
        parameters,
        D,
        condition,
        proof.events,
        tuple(cells),
        tuple(unresolved),
        proof.tested + tested,
        reason,
    )


@budgeted_operation
def resume_parameter_geometry(proof, *, max_cells=256):
    """Refine a checked unresolved parameter frontier with an additional cell budget."""
    if type(proof) is not ParameterGeometryProof or not proof.verify():
        raise ValueError("a checked parameter geometry proof is required")
    if type(max_cells) is not int or max_cells < 0:
        raise ValueError("max_cells must be a nonnegative integer")
    return proof if proof.complete else _refine_geometry(proof, max_cells)
