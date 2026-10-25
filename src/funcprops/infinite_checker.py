"""Tail inequalities and exhaustive periodic root sets; no search imports."""

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, DomainError

from .coverage_contract import EnclosureWitness
from .infinite_contract import (
    CoveredRootFamily,
    ExponentialTailWitness,
    IndexRangeWitness,
    IntegerEndpointWitness,
    PeriodicDomainWitness,
    PeriodicRootWitness,
)
from .source_syntax import normalize_arithmetic

_AUX = sp.Symbol("_infinite_bound", real=True)
_LEVEL = sp.Symbol("_periodic_level", real=True)
_TAIL = sp.Symbol("_tail_distance", nonnegative=True)


def exponential_groups(f, x, direction, threshold, sign):
    """Canonical finite sum p_r(y) exp(r*y), y>=0, with rational rates."""
    if f.free_symbols - {x} or f.has(sp.Float):
        return None
    y = _TAIL
    shifted = sp.expand(
        sign * normalize_arithmetic(f).subs(x, direction * (threshold + y))
    )
    groups = {}
    for term in sp.Add.make_args(shifted):
        rate, coefficient = sp.S.Zero, sp.S.One
        for factor in sp.Mul.make_args(term):
            if factor.func is sp.exp and factor.has(y):
                p = sp.Poly(factor.args[0], y, domain=sp.QQ)
                if p.degree() > 1:
                    return None
                rate += p.nth(1)
                coefficient *= sp.exp(p.nth(0))
            else:
                coefficient *= factor
        p = sp.Poly(coefficient, y)
        if any(
            c.free_symbols
            or c.has(sp.Float)
            or c.is_real is not True
            or c.is_finite is not True
            for c in p.all_coeffs()
        ):
            return None
        groups[rate] = groups.get(rate, 0) + p.as_expr()
    result = tuple(
        (r, tuple(sp.Poly(sp.expand(p), y).all_coeffs()))
        for r, p in sorted(groups.items())
        if sp.expand(p) != 0
    )
    return result or None


def tail_counts(leaf, f):
    """Check a tail-exclusion witness and reconstruct its root count."""

    from .coverage_checker import _bound_matches, _subset

    w = leaf.witness
    if (
        not isinstance(w, ExponentialTailWitness)
        or type(w.direction) is not int
        or w.direction not in (-1, 1)
        or type(w.sign) is not int
        or w.sign not in (-1, 1)
        or not isinstance(w.threshold, sp.Rational)
        or w.threshold < 0
        or not isinstance(w.groups, tuple)
        or not isinstance(w.coefficient_bounds, tuple)
    ):
        return None
    tail = (
        sp.Interval(w.threshold, sp.oo)
        if w.direction == 1
        else sp.Interval(-sp.oo, -w.threshold)
    )
    if not _subset(leaf.region, tail):
        return None
    groups = exponential_groups(f, leaf.variable, w.direction, w.threshold, w.sign)
    if groups is None or groups != w.groups or len(groups) != len(w.coefficient_bounds):
        return None
    for (_, coefficients), bounds in zip(groups, w.coefficient_bounds, strict=True):
        if not isinstance(bounds, tuple) or len(coefficients) != len(bounds):
            return None
        if any(
            not _bound_matches(b, c, _AUX, sp.FiniteSet(0))
            for c, b in zip(coefficients, bounds, strict=True)
        ):
            return None
    dominant_rate, _ = groups[-1]
    dominant = w.coefficient_bounds[-1]
    if any(b.lower < 0 for b in dominant):
        return None
    lower = dominant[-1].lower
    remainder = sp.S.Zero
    for (rate, coefficients), bounds in zip(
        groups[:-1], w.coefficient_bounds[:-1], strict=True
    ):
        delta = dominant_rate - rate
        for i, b in enumerate(bounds):
            power = len(coefficients) - 1 - i
            remainder += max(0, -b.lower) * sp.factorial(power) / delta**power
    if (
        w.constant_lower != lower
        or w.remainder_upper != remainder
        or lower <= remainder
    ):
        return None
    return 0, 0


def _rational_grammar(node, atom):
    if node == atom or isinstance(node, sp.Rational):
        return True
    if node.is_Add or node.is_Mul:
        return all(_rational_grammar(a, atom) for a in node.args)
    return node.is_Pow and node.exp.is_Integer and _rational_grammar(node.base, atom)


def periodic_data(f, x):
    """Raw one-phase rational sin/cos/tan syntax, with every source guard."""
    if f.free_symbols - {x} or f.has(sp.Float):
        return None
    atoms = tuple(f.atoms(sp.sin, sp.cos, sp.tan))
    if len(atoms) != 1 or not _rational_grammar(f, atoms[0]):
        return None
    atom = atoms[0]
    p = sp.Poly(atom.args[0], x)
    rate, phase = p.nth(1), p.nth(0)
    if (
        p.degree() != 1
        or not isinstance(rate, sp.Rational)
        or rate == 0
        or not isinstance(sp.cancel(phase / sp.pi), sp.Rational)
    ):
        return None
    t = _LEVEL
    transformed = f.xreplace({atom: t})
    guards = []
    for node in sp.preorder_traversal(f):
        if node.is_Pow and node.exp.is_negative:
            num, den = sp.fraction(sp.cancel(node.base.xreplace({atom: t})))
            guards.extend(
                (
                    tuple(sp.Poly(num, t, domain=sp.QQ).all_coeffs()),
                    tuple(sp.Poly(den, t, domain=sp.QQ).all_coeffs()),
                )
            )
    num, den = sp.fraction(sp.cancel(transformed))
    n, d = sp.Poly(num, t, domain=sp.QQ), sp.Poly(den, t, domain=sp.QQ)
    if d.is_zero:
        return None
    guards.append(tuple(d.all_coeffs()))
    return (
        atom.func.__name__,
        rate,
        phase,
        tuple(n.all_coeffs()),
        tuple(d.all_coeffs()),
        tuple(sorted(set(guards), key=str)),
    )


def phases(kind, level):
    """Enumerate exact inverse trigonometric phases for a rational level."""

    if kind == "sin":
        a = sp.asin(level)
        return (a,) if level in (-1, 1) else (a, sp.pi - a)
    if kind == "cos":
        if level == -1:
            return (-sp.pi,)
        a = sp.acos(level)
        return (a,) if level == 1 else (a, -a)
    return (sp.atan(level),)


def period(kind, rate):
    """Return the positive coordinate period of an affine trigonometric head."""

    return (sp.pi if kind == "tan" else 2 * sp.pi) / abs(rate)


def lattice_set(offset, step):
    """Represent an affine integer lattice as an exact SymPy set."""

    n = sp.Dummy("periodic_index", integer=True)
    return sp.ImageSet(sp.Lambda(n, offset + n * step), sp.S.Integers)


def pole_set(kind, rate, phase, poles):
    """Assemble denominator exclusions for a rational trigonometric substitution."""

    sets = [
        lattice_set((theta - phase) / rate, period(kind, rate))
        for level in poles
        for theta in phases(kind, level)
    ]
    if kind == "tan":
        sets.append(lattice_set((sp.pi / 2 - phase) / rate, sp.pi / abs(rate)))
    return sp.Union(*sets)


def _polynomial(coefficients):
    if (
        not isinstance(coefficients, tuple)
        or not coefficients
        or any(not isinstance(c, sp.Rational) for c in coefficients)
    ):
        return None
    return sp.Poly.from_list(list(coefficients), _LEVEL, domain=sp.QQ)


def _level_region(kind):
    return sp.S.Reals if kind == "tan" else sp.Interval(-1, 1)


def _level_roots_valid(polynomial, values, kind):
    from .coverage_checker import _distinct_count, _root_at

    if not isinstance(values, tuple) or polynomial.is_zero:
        return False
    region = _level_region(kind)
    if len(set(values)) != len(values) or len(values) != _distinct_count(
        polynomial.sqf_part(), region
    ):
        return False
    return all(
        isinstance(v, sp.Expr)
        and not v.has(sp.Float)
        and region.contains(v) is sp.S.true
        and _root_at(polynomial, v)
        for v in values
    )


def check_periodic_domain(record):
    """Check the stored periodic domain premises and report their replay outcome."""

    from .domain_tracking import coordinate_domain_compatible

    try:
        if (
            not isinstance(record, PeriodicDomainWitness)
            or type(record.schema_version) is not int
            or record.schema_version != 1
        ):
            return False
        if (
            not isinstance(record.requested, sp.Set)
            or record.requested.has(sp.Float)
            or not coordinate_domain_compatible(record.variable, record.requested)
        ):
            return False
        data = periodic_data(record.expression, record.variable)
        if data != (
            record.kind,
            record.rate,
            record.phase,
            record.numerator,
            record.denominator,
            record.guards,
        ):
            return False
        guards = [_polynomial(c) for c in record.guards]
        if any(p is None or p.is_zero for p in guards):
            return False
        combined = sp.Poly(sp.prod(p.as_expr() for p in guards), _LEVEL, domain=sp.QQ)
        if not _level_roots_valid(combined, record.poles, record.kind):
            return False
        excluded = pole_set(record.kind, record.rate, record.phase, record.poles)
        # dummy_eq compares bound integer variables without a search or solver.
        return bool(
            record.excluded.dummy_eq(excluded)
            and record.effective.dummy_eq(sp.Complement(record.requested, excluded))
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        NotImplementedError,
        sp.PolynomialError,
        CoercionFailed,
        DomainError,
    ):
        return False


def _floor_valid(w, q):
    from .coverage_checker import _bound_matches

    if (
        not isinstance(w, IntegerEndpointWitness)
        or w.quotient != q
        or type(w.floor) is not int
    ):
        return False
    if w.enclosure is None:
        return sp.floor(q) == w.floor
    b = w.enclosure
    return (
        isinstance(b, EnclosureWitness)
        and _bound_matches(b, q, _AUX, sp.FiniteSet(0))
        and b.lower >= w.floor
        and b.upper < w.floor + 1
    )


def _index_data(offset, step, w):
    from .coverage_checker import _formula_equal

    """Closed endpoint uses ceil(q)=-floor(-q); open endpoint uses floor+1."""
    if not isinstance(w, IndexRangeWitness):
        return None
    d = w.region
    if isinstance(d, sp.FiniteSet) and len(d) == 1:
        q = sp.cancel((next(iter(d)) - offset) / step)
        if not _floor_valid(w.left, q) or w.right is not None:
            return None
        if q == w.left.floor or _formula_equal(q, sp.Integer(w.left.floor)):
            low = high = w.left.floor
        elif (
            w.left.enclosure is not None and w.left.enclosure.lower > w.left.floor
        ) or q.is_integer is False:
            low, high = 1, 0
        else:
            return None
    elif isinstance(d, sp.Interval):
        if d.start is sp.S.NegativeInfinity:
            low = sp.S.NegativeInfinity
            if w.left is not None:
                return None
        else:
            q = sp.cancel((d.start - offset) / step)
            q = sp.cancel(q if d.left_open else -q)
            if not _floor_valid(w.left, q):
                return None
            low = w.left.floor + 1 if d.left_open else -w.left.floor
        if d.end is sp.oo:
            high = sp.oo
            if w.right is not None:
                return None
        else:
            q = sp.cancel((d.end - offset) / step)
            q = sp.cancel(-q if d.right_open else q)
            if not _floor_valid(w.right, q):
                return None
            high = -w.right.floor - 1 if d.right_open else w.right.floor
    else:
        return None
    if w.lower != low or w.upper != high:
        return None
    return (
        sp.oo
        if low is sp.S.NegativeInfinity or high is sp.oo
        else max(0, high - low + 1)
    )


def periodic_counts(leaf, f):
    """Check an exhaustive periodic-family witness and reconstruct its count."""

    from .coverage_checker import _root_at

    w, record = leaf.witness, leaf.context.domain_record
    if (
        not isinstance(w, PeriodicRootWitness)
        or not isinstance(record, PeriodicDomainWitness)
        or leaf.region != record.effective
        or not check_periodic_domain(record)
    ):
        return None
    n = _polynomial(record.numerator)
    if w.zero_function or n.is_zero:
        # Finite point queries use the ordinary point/sturm portfolio. An open
        # interval minus a finite number of lattice sets has infinitely many
        # defined points, even when every numerator is zero.
        if not w.zero_function or not n.is_zero or w.levels or w.families:
            return None
        parts = (
            record.requested.args
            if isinstance(record.requested, sp.Union)
            else (record.requested,)
        )
        return (
            (sp.oo, None)
            if any(
                isinstance(d, sp.Interval) and d.measure.is_positive is True
                for d in parts
            )
            else None
        )
    if not isinstance(w.levels, tuple) or any(
        not isinstance(a, tuple) or len(a) != 2 for a in w.levels
    ):
        return None
    values = tuple(a for a, _ in w.levels)
    if not _level_roots_valid(n, values, record.kind):
        return None
    expected = []
    guards = [_polynomial(c) for c in record.guards]
    for level, multiplicity in w.levels:
        if (
            type(multiplicity) is not int
            or multiplicity <= 0
            or any(
                not _root_at(n.diff((_LEVEL, k)), level) for k in range(1, multiplicity)
            )
            or _root_at(n.diff((_LEVEL, multiplicity)), level)
        ):
            return None
        if any(_root_at(p, level) for p in guards):
            continue
        m = multiplicity * (2 if record.kind != "tan" and level in (-1, 1) else 1)
        expected.extend(
            ((theta - record.phase) / record.rate, period(record.kind, record.rate), m)
            for theta in phases(record.kind, level)
        )
    if not isinstance(w.families, tuple) or len(w.families) != len(expected):
        return None
    parts = (
        record.requested.args
        if isinstance(record.requested, sp.Union)
        else (record.requested,)
    )
    parts = tuple(
        p
        for d in parts
        for p in ([sp.FiniteSet(a) for a in d] if isinstance(d, sp.FiniteSet) else [d])
    )
    total, mult = 0, 0
    for family, (offset, step, m) in zip(w.families, expected, strict=True):
        if (
            not isinstance(family, CoveredRootFamily)
            or (family.offset, family.period, family.multiplicity) != (offset, step, m)
            or not isinstance(family.ranges, tuple)
            or tuple(r.region for r in family.ranges) != parts
        ):
            return None
        for r in family.ranges:
            count = _index_data(offset, step, r)
            if count is None:
                return None
            total += count
            mult += m * count
    return total, mult
