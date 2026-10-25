"""Uniform parameter theorems and exact exceptional-cell coverage replay."""

import itertools

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, DomainError

from .coverage_contract import CheckOutcome, CheckResult, EnclosureWitness
from .domain_tracking import coordinate_domain_compatible
from .parameter_contract import (
    BoxEnclosureWitness,
    ExponentialParameterWitness,
    MonotoneParameterWitness,
    ParameterCoverageProof,
    ParameterRootCell,
    PolynomialParameterWitness,
    PolynomialSignWitness,
    UniformParameterCertificate,
    UniformParameterCover,
    UniformParameterWitness,
    UniformZeroSubsetWitness,
)
from .source_syntax import differentiate, logarithm_quotient, normalize_arithmetic
from .transcendental.real_interval import certified_real_box_evaluate


def _result(reason, *, unsupported=False):
    return CheckResult(
        CheckOutcome.UNSUPPORTED if unsupported else CheckOutcome.REJECTED,
        None if unsupported else False,
        False,
        reason,
    )


def _exact_set(d, variables=()):
    return (
        isinstance(d, sp.Set)
        and not d.has(sp.Float)
        and not d.free_symbols.intersection(variables)
    )


def check_box_enclosure(w):
    """Check the stored box enclosure premises and report their replay outcome."""

    try:
        if (
            not isinstance(w, BoxEnclosureWitness)
            or type(w.schema_version) is not int
            or w.schema_version != 1
            or not isinstance(w.domains, tuple)
            or not w.domains
            or len({x for x, _ in w.domains}) != len(w.domains)
            or w.expression.has(sp.Float)
            or w.expression.free_symbols - {x for x, _ in w.domains}
            or not isinstance(w.lower, sp.Rational)
            or not isinstance(w.upper, sp.Rational)
            or w.lower > w.upper
            or type(w.precision) is not int
            or w.precision < 2
            or type(w.max_series_terms) is not int
            or w.max_series_terms < 0
        ):
            return False
        actual = certified_real_box_evaluate(
            w.expression,
            w.domains,
            precision=w.precision,
            max_series_terms=w.max_series_terms,
        )
        return actual is not None and w.lower <= actual[0] <= actual[1] <= w.upper
    except (AttributeError, ValueError, TypeError, ArithmeticError):
        return False


def _box_matches(w, f, domains):
    return (
        isinstance(w, BoxEnclosureWitness)
        and w.expression == f
        and w.domains == domains
        and check_box_enclosure(w)
    )


def _box_regular(f, domains, order, precision, terms):
    from .enclosures import PRIMITIVES

    symbols = {x for x, _ in domains}

    def bounds(g):
        return certified_real_box_evaluate(
            g, domains, precision=precision, max_series_terms=terms
        )

    def visit(node):
        if node in symbols or isinstance(node, sp.Rational) or node in (sp.pi, sp.E):
            return True
        if node.is_Add or node.is_Mul:
            return all(visit(a) for a in node.args)
        if node.is_Pow:
            if not all(visit(a) for a in node.args):
                return False
            if node.exp.is_Integer and node.exp >= 0:
                return True
            b = bounds(node.base)
            if b is None:
                return False
            if node.exp.is_Integer:
                return b[0] > 0 or b[1] < 0
            return b[0] >= 0 if order == 0 and node.exp.is_positive else b[0] > 0
        if node.func in (sp.log, sp.Abs, sp.asin, sp.acos):
            if node.func is sp.log and len(node.args) == 2:
                return visit(logarithm_quotient(node))
            b = bounds(node.args[0])
            if b is None or not visit(node.args[0]):
                return False
            if node.func is sp.log:
                return b[0] > 0
            if node.func is sp.Abs:
                return order == 0 or b[0] > 0 or b[1] < 0
            return -1 <= b[0] <= b[1] <= 1 if order == 0 else -1 < b[0] <= b[1] < 1
        return node.func in PRIMITIVES and all(visit(a) for a in node.args)

    return not f.has(sp.Float) and f.free_symbols <= symbols and visit(f)


def box_derivative(f, x, domains, precision, terms):
    """Differentiate a source under supported uniform-box regularity premises."""

    from .enclosures import preserve_replace

    if not _box_regular(f, domains, 1, precision, terms):
        return None
    replacements = {}
    for node in sp.postorder_traversal(f):
        if node.func is sp.Abs:
            b = certified_real_box_evaluate(
                node.args[0], domains, precision=precision, max_series_terms=terms
            )
            if b is None or b[0] <= 0 <= b[1]:
                return None
            replacements[node] = preserve_replace(node.args[0], replacements) * (
                1 if b[0] > 0 else -1
            )
    return differentiate(normalize_arithmetic(preserve_replace(f, replacements)), x)


def uniform_counts(cert):
    """Reconstruct a uniform root count from parameter-box witnesses."""

    f, x, D, parameters, w = (
        cert.expression,
        cert.variable,
        cert.domain,
        cert.parameter_domains,
        cert.witness,
    )
    if not isinstance(w, UniformParameterWitness):
        return None
    domains = ((x, D.closure), *parameters)
    if not _box_matches(w.value, f, domains):
        return None
    if w.value.lower > 0 or w.value.upper < 0:
        return (
            (0, 0)
            if w.derivative is None and w.left is None and w.right is None
            else None
        )
    if not isinstance(w.derivative, BoxEnclosureWitness):
        return None
    derivative = box_derivative(
        f, x, domains, w.derivative.precision, w.derivative.max_series_terms
    )
    if (
        derivative is None
        or not _box_matches(w.derivative, derivative, domains)
        or w.derivative.lower <= 0 <= w.derivative.upper
    ):
        return None
    if not _box_matches(
        w.left, f, ((x, sp.FiniteSet(D.start)), *parameters)
    ) or not _box_matches(w.right, f, ((x, sp.FiniteSet(D.end)), *parameters)):
        return None
    a, b = w.left, w.right
    if (a.upper < 0 and b.lower > 0) or (a.lower > 0 and b.upper < 0):
        return 1, 1
    if (not D.left_open and a.lower == a.upper == 0) or (
        not D.right_open and b.lower == b.upper == 0
    ):
        return 1, 1
    if w.derivative.lower > 0:
        absent = (
            a.lower > 0
            or (a.lower >= 0 and D.left_open)
            or b.upper < 0
            or (b.upper <= 0 and D.right_open)
        )
    else:
        absent = (
            a.upper < 0
            or (a.upper <= 0 and D.left_open)
            or b.lower > 0
            or (b.lower >= 0 and D.right_open)
        )
    return (0, 0) if absent else None


def check_uniform_parameters(cert):
    """Check the stored uniform parameters premises and report their replay outcome."""

    try:
        if (
            type(cert) is not UniformParameterCertificate
            or type(cert.schema_version) is not int
            or cert.schema_version != 1
        ):
            return _result("unsupported-uniform-parameter-version", unsupported=True)
        f, x, D, pars = (
            cert.expression,
            cert.variable,
            cert.domain,
            cert.parameter_domains,
        )
        if (
            not isinstance(x, sp.Symbol)
            or not isinstance(pars, tuple)
            or not isinstance(D, sp.Interval)
            or not D.start.is_finite
            or not D.end.is_finite
        ):
            return _result("unsupported-finite-variable-box", unsupported=True)
        symbols = (x, *tuple(a for a, _ in pars))
        if (
            len(set(symbols)) != len(symbols)
            or any(not isinstance(a, sp.Symbol) for a in symbols)
            or f.has(sp.Float)
            or f.free_symbols - set(symbols)
            or cert.source_syntax != sp.srepr(f)
            or cert.coordinate_assumptions
            != tuple((a, tuple(sorted(a.assumptions0.items()))) for a in symbols)
        ):
            return _result("source-or-parameter-mismatch")
        if any(
            not _exact_set(d, symbols)
            or d.free_symbols
            or not isinstance(d, (sp.Interval, sp.FiniteSet))
            or not coordinate_domain_compatible(a, d)
            for a, d in ((x, D), *pars)
        ):
            return _result("unsupported-real-box-geometry", unsupported=True)
        if (
            cert.obligations
            and cert.root_count is None
            and cert.multiplicity_count is None
            and cert.witness is None
        ):
            exhausted = cert.obligations in (("cell-budget",), ("wall-budget",))
            return CheckResult(
                CheckOutcome.EXHAUSTED if exhausted else CheckOutcome.UNSUPPORTED,
                False if exhausted else None,
                False,
                "; ".join(cert.obligations),
            )
        if (
            cert.obligations
            or type(cert.root_count) is not int
            or type(cert.multiplicity_count) is not int
        ):
            return _result("invalid-uniform-count")
        if isinstance(cert.witness, UniformZeroSubsetWitness):
            from .coverage_checker import _subset

            parent = cert.witness.parent
            if (
                type(parent) is not UniformParameterCertificate
                or parent.expression != f
                or parent.variable != x
                or parent.parameter_domains != pars
                or parent.root_count != 0
                or not parent.verify()
                or not _subset(D, parent.domain)
            ):
                return _result("invalid-uniform-zero-subset")
            data = (0, 0)
        else:
            data = uniform_counts(cert)
        if data != (cert.root_count, cert.multiplicity_count):
            return _result("false-uniform-parameter-premise")
        return CheckResult(CheckOutcome.COMPLETE, True, True)
    except (
        AttributeError,
        TypeError,
        ValueError,
        ArithmeticError,
        NotImplementedError,
        sp.PolynomialError,
        CoercionFailed,
        DomainError,
    ):
        return _result("malformed-uniform-parameter-proof")


def polynomial_source(node, symbols):
    """Extract an exact supported polynomial family without losing source guards."""

    if node in symbols or isinstance(node, sp.Rational):
        return True
    if node.is_Add or node.is_Mul:
        return all(polynomial_source(a, symbols) for a in node.args)
    return (
        node.is_Pow
        and node.exp.is_Integer
        and node.exp >= 0
        and polynomial_source(node.base, symbols)
    )


def polynomial_events(f, x, a):
    """Derive degree, discriminant and endpoint events for a polynomial family."""

    if not polynomial_source(f, {x, a}):
        return None
    p = sp.Poly(normalize_arithmetic(f), x)
    if p.degree() > 2:
        return None
    A, B, C = (p.nth(k) for k in (2, 1, 0))
    return tuple(sp.Poly(g, a, domain=sp.QQ) for g in (A, B, C, B * B - 4 * A * C))


def _sign_at(expr):
    return (
        0
        if expr.is_zero is True
        else 1
        if expr.is_positive is True
        else -1
        if expr.is_negative is True
        else None
    )


def _sign_valid(w, p, region):
    from .coverage_checker import _distinct_count

    if (
        not isinstance(w, PolynomialSignWitness)
        or w.coefficients != tuple(p.all_coeffs())
        or type(w.sign) is not int
        or w.sign not in (-1, 0, 1)
        or not isinstance(w.sample, sp.Expr)
        or w.sample.has(sp.Float)
        or w.sample.free_symbols
        or w.sample.is_real is not True
        or w.sample.is_finite is not True
        or region.contains(w.sample) is not sp.S.true
    ):
        return False
    if _sign_at(p.eval(w.sample)) != w.sign:
        return False
    if isinstance(region, sp.FiniteSet) and len(region) == 1:
        return True
    return isinstance(region, sp.Interval) and (
        p.is_zero if w.sign == 0 else _distinct_count(p.sqf_part(), region) == 0
    )


def polynomial_parameter_counts(proof, cell):
    """Reconstruct polynomial root counts on a guarded parameter cell."""

    if proof.domain != sp.S.Reals or not isinstance(
        cell.witness, PolynomialParameterWitness
    ):
        return None
    events = polynomial_events(proof.expression, proof.variable, proof.parameter)
    if (
        events is None
        or not isinstance(cell.witness.signs, tuple)
        or len(cell.witness.signs) != 4
    ):
        return None
    if not all(
        _sign_valid(w, p, cell.region)
        for w, p in zip(cell.witness.signs, events, strict=True)
    ):
        return None
    A, B, C, disc = (w.sign for w in cell.witness.signs)
    if A:
        return (2, 2) if disc > 0 else (1, 2) if disc == 0 else (0, 0)
    if B:
        return 1, 1
    return (sp.oo, None) if C == 0 else (0, 0)


def translation_source_regular(f, x, a, support, precision, terms):
    """Check regularity needed to translate a parameterized source."""

    from .coverage_checker import regular_on_cell

    if not f.has(a):
        return regular_on_cell(
            f, x, support, 1, precision=precision, max_series_terms=terms
        )
    if f == a:
        return True
    if f.is_Add or f.is_Mul:
        return all(
            translation_source_regular(n, x, a, support, precision, terms)
            for n in f.args
        )
    return (
        f.is_Pow
        and f.exp.is_Integer
        and f.exp >= 0
        and translation_source_regular(f.base, x, a, support, precision, terms)
    )


def exponential_parameter_data(f, x, a):
    """Extract the coefficients of a supported exponential parameter family."""

    base = normalize_arithmetic(f + a)
    atoms = tuple(e for e in base.atoms(sp.exp) if e.has(x))
    if base.free_symbols - {x} or len(atoms) != 1:
        return None
    atom = atoms[0]
    t = sp.Dummy("exponential_parameter_level")
    linear = sp.Poly(base.xreplace({atom: t}), t, domain=sp.QQ)
    phase = sp.Poly(atom.args[0], x, domain=sp.QQ)
    if linear.degree() != 1 or phase.degree() != 1:
        return None
    rate, shift, scale, offset = (
        phase.nth(1),
        phase.nth(0),
        linear.nth(1),
        linear.nth(0),
    )
    if (
        rate == 0
        or scale == 0
        or not translation_source_regular(f, x, a, sp.S.Reals, 30, 4096)
    ):
        return None
    return rate, shift, scale, offset


def exponential_parameter_counts(proof, cell):
    """Reconstruct root counts for a supported guarded exponential family."""

    from .coverage_checker import _subset

    w = cell.witness
    if proof.domain != sp.S.Reals or not isinstance(w, ExponentialParameterWitness):
        return None
    if any(
        not isinstance(v, sp.Rational) for v in (w.rate, w.phase, w.scale, w.offset)
    ):
        return None
    data = exponential_parameter_data(proof.expression, proof.variable, proof.parameter)
    if data != (w.rate, w.phase, w.scale, w.offset):
        return None
    for band, count in (
        (sp.Interval.open(-sp.oo, w.offset), int(w.scale.is_negative)),
        (sp.FiniteSet(w.offset), 0),
        (sp.Interval.open(w.offset, sp.oo), int(w.scale.is_positive)),
    ):
        if _subset(cell.region, band):
            return count, count
    return None


def monotone_parameter_counts(proof, cell):
    """Reconstruct uniform root counts from guarded monotonicity premises."""

    from .coverage_checker import _bound_matches, _subset, derivative_formula_on_cell

    w, f, x, a, D = (
        cell.witness,
        proof.expression,
        proof.variable,
        proof.parameter,
        proof.domain,
    )
    if (
        not isinstance(w, MonotoneParameterWitness)
        or not isinstance(w.derivative, EnclosureWitness)
        or not isinstance(D, sp.Interval)
        or not D.start.is_finite
        or not D.end.is_finite
    ):
        return None
    if (
        w.base != normalize_arithmetic(f + a)
        or w.base.free_symbols - {x}
        or not translation_source_regular(
            f, x, a, D.closure, w.derivative.precision, w.derivative.max_series_terms
        )
    ):
        return None
    derivative = derivative_formula_on_cell(
        w.base,
        x,
        D.closure,
        precision=w.derivative.precision,
        max_series_terms=w.derivative.max_series_terms,
    )
    if (
        derivative is None
        or not _bound_matches(w.derivative, derivative, x, D.closure)
        or w.derivative.lower <= 0 <= w.derivative.upper
    ):
        return None
    left, right = (
        normalize_arithmetic(w.base).subs(x, D.start),
        normalize_arithmetic(w.base).subs(x, D.end),
    )
    if (w.left_value, w.right_value) != (left, right) or any(
        v.has(sp.Float)
        or v.free_symbols
        or v.is_real is not True
        or v.is_finite is not True
        for v in (left, right)
    ):
        return None
    low, high, owns_low, owns_high = (
        (left, right, not D.left_open, not D.right_open)
        if w.derivative.lower > 0
        else (right, left, not D.right_open, not D.left_open)
    )
    bands = (
        (sp.Interval.open(-sp.oo, low), 0),
        (sp.FiniteSet(low), int(owns_low)),
        (sp.Interval.open(low, high), 1),
        (sp.FiniteSet(high), int(owns_high)),
        (sp.Interval.open(high, sp.oo), 0),
    )
    for band, count in bands:
        if _subset(cell.region, band):
            return count, count
    return None


def check_parameter_coverage(proof):
    """Check the stored parameter coverage premises and report their replay outcome."""

    from .coverage_checker import _empty, _subset

    try:
        if (
            type(proof) is not ParameterCoverageProof
            or type(proof.schema_version) is not int
            or proof.schema_version != 1
        ):
            return _result("unsupported-parameter-coverage-version", unsupported=True)
        f, x, a, D, P = (
            proof.expression,
            proof.variable,
            proof.parameter,
            proof.domain,
            proof.parameter_domain,
        )
        if (
            not isinstance(x, sp.Symbol)
            or not isinstance(a, sp.Symbol)
            or x == a
            or not isinstance(f, sp.Expr)
            or f.has(sp.Float)
            or f.free_symbols - {x, a}
            or proof.source_syntax != sp.srepr(f)
            or proof.coordinate_assumptions
            != tuple((s, tuple(sorted(s.assumptions0.items()))) for s in (x, a))
        ):
            return _result("source-or-coordinate-mismatch")
        if (
            not _exact_set(D, (x, a))
            or D.free_symbols
            or not _exact_set(P, (x, a))
            or P.free_symbols
            or not coordinate_domain_compatible(x, D)
            or not coordinate_domain_compatible(a, P)
        ):
            return _result("unsupported-exact-real-parameter-domain", unsupported=True)
        if (
            type(proof.complete) is not bool
            or not isinstance(proof.cells, tuple)
            or not isinstance(proof.unresolved, sp.Set)
        ):
            return _result("malformed-parameter-cover")
        regions = [proof.unresolved]
        for cell in proof.cells:
            if (
                type(cell) is not ParameterRootCell
                or not isinstance(cell.region, (sp.Interval, sp.FiniteSet))
                or _empty(cell.region)
            ):
                return _result("invalid-parameter-cell")
            if (
                cell.root_count is not sp.oo
                and (type(cell.root_count) is not int or cell.root_count < 0)
            ) or (
                cell.multiplicity_count is not None
                and cell.multiplicity_count is not sp.oo
                and (
                    type(cell.multiplicity_count) is not int
                    or cell.multiplicity_count < 0
                )
            ):
                return _result("invalid-parameter-count")
            if cell.theorem == "polynomial-parameter":
                data = polynomial_parameter_counts(proof, cell)
            elif cell.theorem == "monotone-parameter":
                data = monotone_parameter_counts(proof, cell)
            elif cell.theorem == "exponential-parameter":
                data = exponential_parameter_counts(proof, cell)
            elif cell.theorem == "uniform-parameter-box":
                w = cell.witness
                if (
                    type(w) not in (UniformParameterCertificate, UniformParameterCover)
                    or w.expression != f
                    or w.variable != x
                    or w.domain != D
                    or w.parameter_domains != ((a, cell.region.closure),)
                    or not w.verify()
                ):
                    return _result("uniform-box-source-mismatch")
                data = w.root_count, w.multiplicity_count
            else:
                return _result("unsupported-parameter-theorem", unsupported=True)
            if data != (cell.root_count, cell.multiplicity_count):
                return _result("false-parameter-cell-premise")
            regions.append(cell.region)
        if (
            any(not _subset(r, P) for r in regions)
            or any(
                not _empty(sp.Intersection(u, v))
                for u, v in itertools.combinations(regions, 2)
            )
            or not _empty(sp.Complement(P, sp.Union(*regions)))
        ):
            return _result("omitted-or-overlapping-parameter-regions")
        complete = _empty(proof.unresolved)
        if proof.complete is not complete or (
            proof.exhaustion is not None
            and (
                complete
                or proof.exhaustion
                not in ("cell-budget", "depth-budget", "wall-budget")
            )
        ):
            return _result("false-parameter-completeness")
        return CheckResult(
            CheckOutcome.COMPLETE
            if complete
            else CheckOutcome.EXHAUSTED
            if proof.exhaustion
            else CheckOutcome.LOCAL_VALID,
            True,
            complete,
            proof.exhaustion,
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        ArithmeticError,
        NotImplementedError,
        sp.PolynomialError,
        CoercionFailed,
        DomainError,
    ):
        return _result("malformed-or-inconclusive-parameter-proof")


def check_uniform_cover(proof):
    """Check the stored uniform cover premises and report their replay outcome."""

    from .coverage_checker import _empty, _subset

    try:
        if (
            type(proof) is not UniformParameterCover
            or type(proof.schema_version) is not int
            or proof.schema_version != 1
        ):
            return _result("unsupported-uniform-cover-version", unsupported=True)
        header = UniformParameterCertificate(
            proof.expression,
            proof.variable,
            proof.domain,
            proof.parameter_domains,
            proof.source_syntax,
            proof.coordinate_assumptions,
            obligations=("unresolved-variable-region",),
        )
        status = check_uniform_parameters(header)
        if status.reason != "unresolved-variable-region":
            return status
        if (
            not isinstance(proof.leaves, tuple)
            or not isinstance(proof.unresolved, sp.Set)
            or type(proof.complete) is not bool
            or type(proof.tested) is not int
            or proof.tested < 0
        ):
            return _result("malformed-uniform-cover")
        regions = [proof.unresolved]
        for leaf in proof.leaves:
            if (
                type(leaf) is not UniformParameterCertificate
                or leaf.expression != proof.expression
                or leaf.variable != proof.variable
                or leaf.parameter_domains != proof.parameter_domains
                or not leaf.complete
                or not leaf.verify()
            ):
                return _result("invalid-uniform-cover-leaf")
            regions.append(leaf.domain)
        if (
            any(not _subset(r, proof.domain) for r in regions)
            or any(
                not _empty(sp.Intersection(u, v))
                for u, v in itertools.combinations(regions, 2)
            )
            or not _empty(sp.Complement(proof.domain, sp.Union(*regions)))
        ):
            return _result("omitted-or-overlapping-uniform-variable-regions")
        complete = _empty(proof.unresolved)
        count = sum(a.root_count for a in proof.leaves) if complete else None
        mult = sum(a.multiplicity_count for a in proof.leaves) if complete else None
        if (
            proof.complete is not complete
            or proof.root_count != count
            or proof.multiplicity_count != mult
            or (proof.root_count is not None and type(proof.root_count) is not int)
            or (
                proof.multiplicity_count is not None
                and type(proof.multiplicity_count) is not int
            )
        ):
            return _result("false-uniform-cover-total")
        if proof.exhaustion is not None and (
            complete or proof.exhaustion not in ("cell-budget", "depth-budget")
        ):
            return _result("false-uniform-cover-exhaustion")
        return CheckResult(
            CheckOutcome.COMPLETE
            if complete
            else CheckOutcome.EXHAUSTED
            if proof.exhaustion
            else CheckOutcome.LOCAL_VALID,
            True,
            complete,
            proof.exhaustion,
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        ArithmeticError,
        NotImplementedError,
    ):
        return _result("malformed-uniform-cover")
