"""Real coverage checker, independent of search, isolation and model factories.

Trusted dependencies: exact SymPy arithmetic, differentiation, set/domain
decisions and polynomial Sturm counts; mpmath outward interval primitives.
This is a checkable CAS proof contract, not a formal proof-assistant kernel.
"""

import itertools

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, DomainError

from .coverage_contract import (
    CellDomainWitness,
    CheckOutcome,
    CheckResult,
    CoverageContext,
    CoverageLeaf,
    CoverageProof,
    EnclosureWitness,
    InadmissibleProof,
    MonotoneWitness,
    NewtonWitness,
    RationalWitness,
    TaylorWitness,
)
from .domain_tracking import DomainRecord, coordinate_domain_compatible, track_domain
from .enclosures import PRIMITIVES, grammar_obligations, preserve_replace
from .infinite_contract import PeriodicDomainWitness
from .source_syntax import (
    differentiate,
    logarithm_quotient,
    normalize_arithmetic,
    same_data,
)
from .transcendental.real_interval import certified_real_interval_evaluate

_ERRORS = (
    AttributeError,
    TypeError,
    ValueError,
    NotImplementedError,
    ArithmeticError,
    sp.PolynomialError,
    CoercionFailed,
    DomainError,
    RecursionError,
)
THEOREMS = (
    "interval-exclusion",
    "monotone-crossing",
    "interval-newton",
    "taylor-exclusion",
    "rational-sturm",
    "point-zero",
    "point-exclusion",
    "exponential-tail",
    "periodic-rational",
    "source-formula",
    "zero-subset",
    "located-subset",
    "power-factor",
    "taylor-deflation",
)


def _reject(reason):
    return CheckResult(CheckOutcome.REJECTED, False, False, reason)


def _unsupported(reason):
    return CheckResult(CheckOutcome.UNSUPPORTED, None, False, reason)


def _empty(region):
    return region is sp.S.EmptySet or region == sp.S.EmptySet


def _subset(a, b):
    return _empty(sp.Complement(a, b))


def _formula_equal(a, b):
    # No heuristic zero sampling is used by the versioned kernel.
    return a == b or sp.cancel(sp.expand(a - b)).is_zero is True


def specialized_source(context):
    """Specialize exact parameters without discarding the bound source syntax."""

    return preserve_replace(context.expression, dict(context.substitutions))


def _context_status(context):
    """Check source binding, coordinate assumptions and exact effective-domain evidence."""

    if type(context) is not CoverageContext:
        return _reject("malformed-context")
    x, f = context.variable, context.expression
    if not isinstance(x, sp.Symbol) or not isinstance(f, sp.Expr):
        return _reject("malformed-source")
    if context.source_syntax != sp.srepr(f) or context.coordinate_assumptions != tuple(
        sorted(x.assumptions0.items())
    ):
        return _reject("source-or-assumptions-mismatch")
    if context.branch_context is not None:
        return _unsupported("real-checker-requires-principal-real-branch")
    if not isinstance(context.substitutions, tuple):
        return _reject("malformed-substitutions")
    replacements = dict(context.substitutions)
    if len(replacements) != len(context.substitutions) or x in replacements:
        return _reject("invalid-parameter-specialization")
    if any(
        not isinstance(k, sp.Symbol)
        or k not in f.free_symbols
        or v.free_symbols
        or v.has(sp.Float)
        or v.is_real is not True
        or v.is_finite is not True
        for k, v in context.substitutions
    ):
        return _reject("invalid-parameter-specialization")
    guard = sp.And(*(sp.Eq(k, v) for k, v in context.substitutions))
    if guard is sp.S.false or context.parameter_guard != guard:
        return _reject("parameter-premise-mismatch")
    actual = specialized_source(context)
    if actual.free_symbols - {x}:
        return _unsupported("unspecialized-parameters")
    requested = preserve_replace(context.requested, replacements)
    record = context.domain_record
    if (
        not isinstance(context.requested, sp.Set)
        or not isinstance(context.effective, sp.Set)
        or type(record) not in (DomainRecord, CellDomainWitness, PeriodicDomainWitness)
    ):
        return _reject("malformed-domain")
    if not record.complete:
        return _unsupported("unresolved-definition-domain")
    if isinstance(record, PeriodicDomainWitness):
        if (
            record.expression != actual
            or record.variable != x
            or record.requested != requested
            or record.effective != context.effective
            or not record.verify()
        ):
            return _reject("periodic-domain-premise-mismatch")
        return None
    if isinstance(record, CellDomainWitness):
        if (
            record.expression != actual
            or record.variable != x
            or record.requested != requested
            or record.effective != context.effective
            or not check_cell_domain(record)
        ):
            return _reject("domain-premise-mismatch")
        return None
    current = track_domain(actual, x, requested)
    if not record.matches(current) or record.effective != context.effective:
        return _reject("domain-premise-mismatch")
    return None


def _bounds(expr, var, domain, precision=30, max_terms=4096):
    if grammar_obligations(expr, var) or not coordinate_domain_compatible(var, domain):
        return None
    r = certified_real_interval_evaluate(
        expr, var, domain, precision=precision, max_series_terms=max_terms
    )
    if r is None:
        return None
    a, b = sp.sympify(r.lower), sp.sympify(r.upper)
    return (
        (a, b)
        if isinstance(a, sp.Rational) and isinstance(b, sp.Rational) and a <= b
        else None
    )


def check_enclosure(witness):
    """Replay raw syntax with primitive evaluators; never consult the leaf cache."""
    try:
        w = witness
        if (
            not isinstance(w, EnclosureWitness)
            or type(w.grammar_version) is not int
            or w.grammar_version != 1
            or w.branch_context is not None
            or type(w.precision) is not int
            or w.precision < 2
            or type(w.max_series_terms) is not int
            or w.max_series_terms < 0
            or not isinstance(w.lower, sp.Rational)
            or not isinstance(w.upper, sp.Rational)
            or w.lower > w.upper
        ):
            return False
        actual = _bounds(
            w.expression, w.variable, w.domain, w.precision, w.max_series_terms
        )
        return bool(actual is not None and w.lower <= actual[0] <= actual[1] <= w.upper)
    except _ERRORS:
        return False


def check_cell_domain(record):
    """Check the stored cell domain premises and report their replay outcome."""

    try:
        if (
            type(record) is not CellDomainWitness
            or type(record.schema_version) is not int
            or record.schema_version != 1
            or not isinstance(record.cells, tuple)
        ):
            return False
        if not isinstance(record.requested, sp.Set) or not coordinate_domain_compatible(
            record.variable, record.requested
        ):
            return False
        for w in record.cells:
            if (
                not isinstance(w, EnclosureWitness)
                or w.expression != record.expression
                or w.variable != record.variable
                or not check_enclosure(w)
            ):
                return False
        return sp.Union(*(w.domain for w in record.cells)) == record.requested
    except _ERRORS:
        return False


def regular_on_cell(expr, var, domain, order=1, *, precision=30, max_series_terms=4096):
    """Sufficient C^order premise from analytic grammar, with strict branch guards.

    Abs at a possible zero is not promoted from continuous to C1.
    The same is true of sqrt at a zero endpoint and of unsplit Piecewise seams.
    """
    if type(order) is not int or order < 0 or grammar_obligations(expr, var):
        return False
    if not coordinate_domain_compatible(var, domain):
        return False

    def visit(node):
        if node == var or isinstance(node, sp.Rational) or node in (sp.pi, sp.E):
            return True
        if node.is_Add or node.is_Mul:
            return all(visit(a) for a in node.args)
        if node.is_Pow:
            if not visit(node.base) or not visit(node.exp):
                return False
            if node.exp.is_Integer and node.exp.is_nonnegative:
                return True
            b = _bounds(node.base, var, domain, precision, max_series_terms)
            if b is None:
                return False
            if node.exp.is_Integer:
                return b[0] > 0 or b[1] < 0
            return b[0] >= 0 if order == 0 and node.exp.is_positive else b[0] > 0
        if node.func is sp.log:
            if len(node.args) == 2:
                return visit(logarithm_quotient(node))
            b = _bounds(node.args[0], var, domain, precision, max_series_terms)
            return visit(node.args[0]) and b is not None and b[0] > 0
        if node.func in (sp.asin, sp.acos):
            b = _bounds(node.args[0], var, domain, precision, max_series_terms)
            return (
                visit(node.args[0])
                and b is not None
                and (-1 <= b[0] <= b[1] <= 1 if order == 0 else -1 < b[0] <= b[1] < 1)
            )
        if node.func is sp.Abs:
            b = _bounds(node.args[0], var, domain, precision, max_series_terms)
            return (
                visit(node.args[0])
                and b is not None
                and (order == 0 or b[0] > 0 or b[1] < 0)
            )
        return node.func in PRIMITIVES and all(visit(a) for a in node.args)

    try:
        return bool(visit(sp.sympify(expr)))
    except _ERRORS:
        return False


def derivative_formula_on_cell(
    expr, var, domain, order=1, *, precision=30, max_series_terms=4096
):
    """Differentiate only after real source/regularity guards have been proved."""
    if not regular_on_cell(
        expr, var, domain, order, precision=precision, max_series_terms=max_series_terms
    ):
        return None
    f = sp.sympify(expr)
    if order == 0:
        return f
    replacements = {}
    for node in sp.postorder_traversal(f):
        if node.func is sp.Abs:
            arg = node.args[0]
            b = _bounds(arg, var, domain, precision, max_series_terms)
            if b is None or b[0] <= 0 <= b[1]:
                return None
            replacements[node] = preserve_replace(arg, replacements) * (
                1 if b[0] > 0 else -1
            )
    return differentiate(
        normalize_arithmetic(preserve_replace(f, replacements)), var, order
    )


def cell_expression(context, region):
    """Resolve the active source expression on a checked owned cell."""

    f = specialized_source(context)
    if not f.has(sp.Piecewise):
        return f
    from .coverage_cells import source_cells

    data = source_cells(f, context.variable, context.effective)
    if data is None:
        return None
    for branch, active in data:
        if _subset(region, active):
            return branch
    return None


def _bound_matches(w, f, x, region):
    return (
        isinstance(w, EnclosureWitness)
        and w.expression == f
        and w.variable == x
        and w.domain == region
        and check_enclosure(w)
    )


def _regular_with_witness(f, x, domain, w, order=1):
    return isinstance(w, EnclosureWitness) and regular_on_cell(
        f, x, domain, order, precision=w.precision, max_series_terms=w.max_series_terms
    )


def _rational_polys(f, x, witness):
    if (
        not isinstance(witness, RationalWitness)
        or not isinstance(witness.numerator, tuple)
        or not isinstance(witness.denominator, tuple)
        or not witness.denominator
        or not witness.numerator
    ):
        return None
    if any(
        not isinstance(a, sp.Rational) for a in witness.numerator + witness.denominator
    ):
        return None
    n, d = (
        sp.Poly.from_list(list(cs), x, domain=sp.QQ)
        for cs in (witness.numerator, witness.denominator)
    )
    if d.is_zero:
        return None
    num, den = sp.fraction(sp.cancel(normalize_arithmetic(f)))
    pn, pd = sp.Poly(num, x, domain=sp.QQ), sp.Poly(den, x, domain=sp.QQ)
    # Exact normalized coefficients bind the submitted algebraic witness.
    return (n, d) if n == pn and d == pd else None


def _root_at(poly, value):
    if isinstance(value, sp.Rational):
        return poly.eval(value).is_zero is True
    if value.is_algebraic is not True or value.is_real is not True:
        return False
    minimal = sp.Poly(sp.minpoly(value, poly.gen), poly.gen, domain=sp.QQ)
    return poly.rem(minimal).is_zero


def _distinct_count(poly, region):
    if isinstance(region, sp.Union):
        return sum(_distinct_count(poly, part) for part in region.args)
    if isinstance(region, sp.FiniteSet):
        return sum(_root_at(poly, p) for p in region)
    if not isinstance(region, sp.Interval):
        raise ValueError("unsupported Sturm cell")
    # SymPy's Sturm primitive counts distinct real roots in the closed interval.
    count = int(poly.count_roots(region.start, region.end))
    for point, opened in (
        (region.start, region.left_open),
        (region.end, region.right_open),
    ):
        if opened and point.is_finite is True and _root_at(poly, point):
            count -= 1
    return count


def _rational_counts(poly, region):
    if poly.is_zero:
        if isinstance(region, sp.FiniteSet):
            return len(region), None
        return sp.oo, None
    if poly.degree() == 0:
        return 0, 0
    distinct = _distinct_count(poly.sqf_part(), region)
    multiplicity = sum(
        m * _distinct_count(factor, region) for factor, m in poly.sqf_list()[1]
    )
    return distinct, multiplicity


def _local_counts(leaf, f):
    """Reconstruct local distinct and multiplicity counts from theorem-specific witnesses."""

    x, region, w = leaf.variable, leaf.region, leaf.witness
    if leaf.theorem in ("exponential-tail", "periodic-rational"):
        from .infinite_checker import periodic_counts, tail_counts

        data = (
            tail_counts(leaf, f)
            if leaf.theorem == "exponential-tail"
            else periodic_counts(leaf, f)
        )
        return data if not leaf.roots else None
    if leaf.theorem in (
        "source-formula",
        "zero-subset",
        "located-subset",
        "power-factor",
        "taylor-deflation",
    ):
        from .multiple_root_checker import multiple_counts

        data = multiple_counts(leaf, f)
        if leaf.theorem == "taylor-deflation":
            expected = (
                ((w.center, w.order),) if data is not None and data[0] == 1 else ()
            )
            return data if same_data(leaf.roots, expected) else None
        return data if not leaf.roots else None
    if leaf.theorem == "rational-sturm":
        polys = _rational_polys(f, x, w)
        if polys is None:
            return None
        poly, _ = polys
        counts = _rational_counts(poly, region)
        if leaf.roots:
            if len({r for r, _ in leaf.roots}) != len(leaf.roots):
                return None
            for root, mult in leaf.roots:
                if region.contains(root) is not sp.S.true or not _root_at(poly, root):
                    return None
                if poly.is_zero or leaf.expression.has(sp.Piecewise):
                    if mult is not None:
                        return None
                elif (
                    type(mult) is not int
                    or mult <= 0
                    or any(
                        not _root_at(poly.diff((x, k)), root) for k in range(1, mult)
                    )
                    or _root_at(poly.diff((x, mult)), root)
                ):
                    return None
            if len(leaf.roots) != counts[0]:
                return None
        return (
            (counts[0], None)
            if counts[0] and leaf.expression.has(sp.Piecewise)
            else counts
        )
    if leaf.roots:
        # A numerical count locates a root within the cell without specifying its exact value.
        return None
    if leaf.theorem == "interval-exclusion":
        return (
            (0, 0)
            if _bound_matches(w, f, x, region) and (w.lower > 0 or w.upper < 0)
            else None
        )
    if leaf.theorem in ("point-zero", "point-exclusion"):
        if not isinstance(region, sp.FiniteSet) or len(region) != 1:
            return None
        if leaf.theorem == "point-exclusion":
            return (
                (0, 0)
                if _bound_matches(w, f, x, region) and (w.lower > 0 or w.upper < 0)
                else None
            )
        value = f.subs(x, next(iter(region)))
        return (1, None) if w == value and value.is_zero is True else None
    if (
        not isinstance(region, sp.Interval)
        or region.start.is_finite is not True
        or region.end.is_finite is not True
    ):
        return None
    closed = region.closure
    if leaf.theorem == "monotone-crossing":
        if not isinstance(w, MonotoneWitness) or not _regular_with_witness(
            f, x, closed, w.derivative
        ):
            return None
        if not (
            _bound_matches(
                w.derivative,
                derivative_formula_on_cell(
                    f,
                    x,
                    closed,
                    precision=w.derivative.precision,
                    max_series_terms=w.derivative.max_series_terms,
                ),
                x,
                closed,
            )
            and _bound_matches(w.left, f, x, sp.FiniteSet(region.start))
            and _bound_matches(w.right, f, x, sp.FiniteSet(region.end))
        ):
            return None
        if w.derivative.lower <= 0 <= w.derivative.upper:
            return None
        a, b = w.left, w.right
        if (a.upper < 0 and b.lower > 0) or (a.lower > 0 and b.upper < 0):
            return 1, 1
        if (not region.left_open and a.lower == a.upper == 0) or (
            not region.right_open and b.lower == b.upper == 0
        ):
            return 1, 1
        if w.derivative.lower > 0:
            absent = (
                a.lower > 0
                or (a.lower >= 0 and region.left_open)
                or b.upper < 0
                or (b.upper <= 0 and region.right_open)
            )
        else:
            absent = (
                a.upper < 0
                or (a.upper <= 0 and region.left_open)
                or b.lower > 0
                or (b.lower >= 0 and region.right_open)
            )
        return (0, 0) if absent else None
    if leaf.theorem == "interval-newton":
        if not isinstance(w, NewtonWitness) or not _regular_with_witness(
            f, x, closed, w.derivative
        ):
            return None
        mid = (region.start + region.end) / 2
        if (
            w.midpoint != mid
            or not _bound_matches(
                w.derivative,
                derivative_formula_on_cell(
                    f,
                    x,
                    closed,
                    precision=w.derivative.precision,
                    max_series_terms=w.derivative.max_series_terms,
                ),
                x,
                closed,
            )
            or not _bound_matches(w.value, f, x, sp.FiniteSet(mid))
        ):
            return None
        if w.derivative.lower <= 0 <= w.derivative.upper:
            return None
        ratios = [
            a / b
            for a in (w.value.lower, w.value.upper)
            for b in (w.derivative.lower, w.derivative.upper)
        ]
        low, high = mid - max(ratios), mid - min(ratios)
        if w.image_lower != low or w.image_upper != high:
            return None
        if high < region.start or low > region.end:
            return 0, 0
        return (1, 1) if low > region.start and high < region.end else None
    if leaf.theorem == "taylor-exclusion":
        if (
            not isinstance(w, TaylorWitness)
            or not isinstance(w.coefficients, tuple)
            or type(w.order) is not int
            or w.order < 0
            or len(w.coefficients) != w.order + 1
        ):
            return None
        if closed.contains(w.center) is not sp.S.true or not _regular_with_witness(
            f, x, closed, w.derivative, w.order + 1
        ):
            return None
        expected = tuple(
            differentiate(normalize_arithmetic(f), x, k).subs(x, w.center)
            / sp.factorial(k)
            for k in range(w.order + 1)
        )
        if not all(
            _formula_equal(a, b) for a, b in zip(expected, w.coefficients, strict=True)
        ):
            return None
        poly = sum(a * (x - w.center) ** k for k, a in enumerate(expected))
        if (
            not _formula_equal(poly, w.polynomial)
            or not _bound_matches(
                w.derivative,
                differentiate(normalize_arithmetic(f), x, w.order + 1),
                x,
                closed,
            )
            or not _bound_matches(w.polynomial_bound, w.polynomial, x, region)
        ):
            return None
        n = w.order + 1
        powers = [(region.start - w.center) ** n, (region.end - w.center) ** n]
        if n % 2 == 0:
            powers.append(sp.S.Zero)
        products = [
            a * b / sp.factorial(n)
            for a in (w.derivative.lower, w.derivative.upper)
            for b in (min(powers), max(powers))
        ]
        low, high = min(products), max(products)
        if w.remainder_lower != low or w.remainder_upper != high:
            return None
        b = w.polynomial_bound
        return (
            (0, 0)
            if (b.lower + low).is_positive is True
            or (b.upper + high).is_negative is True
            else None
        )
    return None


def _check_leaf(leaf, *, _checked_context=None):
    try:
        if (
            type(leaf) is not CoverageLeaf
            or type(leaf.schema_version) is not int
            or leaf.schema_version != 1
        ):
            return _unsupported("unsupported-leaf-version")
        status = (
            None if _checked_context == leaf.context else _context_status(leaf.context)
        )
        if status is not None:
            return status
        if leaf.theorem not in THEOREMS:
            return _unsupported("unsupported-theorem")
        if type(leaf.roots) is not tuple or any(
            type(pair) is not tuple or len(pair) != 2 for pair in leaf.roots
        ):
            return _reject("mutable-root-witness-container")
        if (
            not isinstance(leaf.region, sp.Set)
            or _empty(leaf.region)
            or not _subset(leaf.region, leaf.context.effective)
        ):
            return _reject("invalid-cell")
        if (
            leaf.root_count is not sp.oo
            and (type(leaf.root_count) is not int or leaf.root_count < 0)
        ) or (
            leaf.multiplicity_count is not None
            and leaf.multiplicity_count is not sp.oo
            and (
                type(leaf.multiplicity_count) is not int or leaf.multiplicity_count < 0
            )
        ):
            return _reject("invalid-count-type")
        f = cell_expression(leaf.context, leaf.region)
        if f is None:
            return _unsupported("unsplit-piecewise-cell")
        data = _local_counts(leaf, f)
        if data is not None and data[0] and leaf.expression.has(sp.Piecewise):
            data = (data[0], None)
        if data != (leaf.root_count, leaf.multiplicity_count):
            return _reject("false-or-unbound-leaf-premise")
        return CheckResult(CheckOutcome.LOCAL_VALID, True, False)
    except _ERRORS:
        return _reject("malformed-or-inconclusive-leaf")


def check_leaf(leaf):
    """Check both context and theorem premises for one proposed leaf."""
    return _check_leaf(leaf)


def check_coverage(proof):
    """Check the stored coverage premises and report their replay outcome."""

    try:
        if (
            type(proof) is not CoverageProof
            or type(proof.schema_version) is not int
            or proof.schema_version != 1
        ):
            return _unsupported("unsupported-coverage-version")
        status = _context_status(proof.context)
        if status is not None:
            return status
        if (
            type(proof.complete) is not bool
            or not isinstance(proof.leaves, tuple)
            or not isinstance(proof.unresolved, sp.Set)
        ):
            return _reject("malformed-cover")
        if isinstance(proof.root_count, bool) or isinstance(
            proof.multiplicity_count, bool
        ):
            return _reject("invalid-total-type")
        if any(
            value is not None
            and value is not sp.oo
            and type(value) is not int
            and not isinstance(value, sp.Integer)
            for value in (proof.root_count, proof.multiplicity_count)
        ):
            return _reject("invalid-total-type")
        domain = proof.context.effective
        if not _subset(proof.unresolved, domain):
            return _reject("unresolved-outside-domain")
        regions = []
        for leaf in proof.leaves:
            if type(leaf) is not CoverageLeaf or leaf.context != proof.context:
                return _reject("leaf-context-mismatch")
            checked = _check_leaf(leaf, _checked_context=proof.context)
            if checked.certified is not True:
                return checked
            regions.append(leaf.region)
        regions.append(proof.unresolved)
        if any(
            not _empty(sp.Intersection(a, b))
            for a, b in itertools.combinations(regions, 2)
        ):
            return _reject("overlapping-or-duplicated-cells")
        if not _empty(sp.Complement(domain, sp.Union(*regions))):
            return _reject("omitted-domain-cells")
        complete = _empty(proof.unresolved)
        count = (
            sum((a.root_count for a in proof.leaves), sp.S.Zero) if complete else None
        )
        ms = [a.multiplicity_count for a in proof.leaves]
        mult = (
            sum(ms, sp.S.Zero) if complete and all(a is not None for a in ms) else None
        )
        if (
            proof.complete is not complete
            or proof.root_count != count
            or proof.multiplicity_count != mult
        ):
            return _reject("false-completeness-or-total")
        if proof.exhaustion is not None and (
            complete
            or proof.exhaustion
            not in (
                "cell-budget",
                "depth-budget",
                "precision-or-order-budget",
                "wall-budget",
            )
        ):
            return _reject("invalid-exhaustion-claim")
        outcome = (
            CheckOutcome.COMPLETE
            if complete
            else CheckOutcome.EXHAUSTED
            if proof.exhaustion
            else CheckOutcome.LOCAL_VALID
        )
        return CheckResult(outcome, True, complete, proof.exhaustion)
    except _ERRORS:
        return _reject("malformed-or-inconclusive-cover")


def check_inadmissible(proof):
    """Check the stored inadmissible premises and report their replay outcome."""

    try:
        if (
            not isinstance(proof, InadmissibleProof)
            or proof.schema_version != 1
            or type(proof.schema_version) is not int
        ):
            return _unsupported("unsupported-inadmissibility-version")
        f = proof.expression
        if (
            proof.reason != "nonreal-constant-source"
            or proof.source_syntax != sp.srepr(f)
            or not isinstance(proof.variable, sp.Symbol)
            or not isinstance(proof.domain, sp.Set)
            or _empty(proof.domain)
            or f.free_symbols
            or f.has(sp.Float)
            or f.is_finite is not True
            or f.is_real is not False
        ):
            return _reject("invalid-inadmissibility-witness")
        return CheckResult(CheckOutcome.INADMISSIBLE, True, False, proof.reason)
    except _ERRORS:
        return _reject("malformed-inadmissibility-witness")
