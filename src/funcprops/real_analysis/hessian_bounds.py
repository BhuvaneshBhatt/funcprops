"""Exact interval Hessian bounds for a small real C2 box grammar."""

import sympy as sp
from sympy import S

from ..domain_tracking import coordinate_domain_compatible
from ..enclosures import enclosure_witness
from ..results import Convexity
from ..source_syntax import differentiate
from .advanced_convexity import ConvexityCertificate
from .common import condition_to_set


def _box_axes(variables, domain):
    if not 2 <= len(variables) <= 4:
        return None
    if isinstance(domain, sp.ProductSet):
        axes = domain.args
    elif isinstance(domain, sp.logic.boolalg.Boolean):
        if domain.free_symbols.difference(variables):
            return None
        clauses = sp.And.make_args(domain)
        if any(
            len(clause.free_symbols.intersection(variables)) > 1 for clause in clauses
        ):
            return None
        axes = tuple(
            condition_to_set(sp.And(*(c for c in clauses if v in c.free_symbols)), v)
            for v in variables
        )
    else:
        return None
    if len(axes) != len(variables):
        return None
    for variable, axis in zip(variables, axes, strict=True):
        if (
            not isinstance(axis, sp.Interval)
            or not all(
                p.is_Rational
                and max(abs(int(p.p)).bit_length(), int(p.q).bit_length()) <= 512
                for p in (axis.start, axis.end)
            )
            or not coordinate_domain_compatible(variable, axis)
        ):
            return None
    return tuple(axes)


def _box_bound(expression, coordinates):
    """Bound raw arithmetic while proving each operation is real and C2."""
    for index, _ in enumerate(sp.preorder_traversal(expression)):
        if index == 96:
            return None

    def bounded(value):
        return (
            value
            if max(
                max(abs(int(p.p)).bit_length(), int(p.q).bit_length()) for p in value
            )
            <= 4096
            else None
        )

    def bound(node):
        if node in coordinates:
            interval = coordinates[node]
            return interval.start, interval.end
        if node is sp.E:
            axis = sp.Symbol("constant_axis", real=True)
            witness = enclosure_witness(node, axis, sp.Interval(0, 1), precision=20)
            return (witness.lower, witness.upper) if witness is not None else None
        if node.is_Rational:
            if max(abs(int(node.p)).bit_length(), int(node.q).bit_length()) > 512:
                return None
            return node, node
        if node.is_Add or node.is_Mul:
            result = (S.Zero, S.Zero) if node.is_Add else (S.One, S.One)
            for argument in node.args:
                value = bound(argument)
                if value is None:
                    return None
                if node.is_Add:
                    result = result[0] + value[0], result[1] + value[1]
                else:
                    products = [a * b for a in result for b in value]
                    result = min(products), max(products)
            return bounded(result)
        if node.is_Pow and node.exp.is_Integer and abs(node.exp) <= 8:
            value = bound(node.base)
            if value is None:
                return None
            exponent = int(node.exp)
            if exponent < 0 and value[0] <= 0 <= value[1]:
                return None
            power = abs(exponent)
            endpoints = [p**power for p in value]
            lower = (
                S.Zero
                if power and power % 2 == 0 and value[0] <= 0 <= value[1]
                else min(endpoints)
            )
            result = lower, max(endpoints)
            return bounded((1 / result[1], 1 / result[0]) if exponent < 0 else result)
        if node.func in (sp.exp, sp.log, sp.sin, sp.cos) and len(node.args) == 1:
            value = bound(node.args[0])
            if value is None or (node.func is sp.log and value[0] <= 0):
                return None
            if max(abs(p) for p in value) > 128:
                return None
            axis = sp.Symbol("box_axis", real=True)
            witness = enclosure_witness(
                node.func(axis), axis, sp.Interval(*value), precision=20
            )
            return (witness.lower, witness.upper) if witness is not None else None
        return None

    return bound(expression)


def hessian_dominance_data(expression, variables, domain):
    """Reconstruct raw-source C2, entry bounds and a uniform Gershgorin margin.

    Every primitive must be defined on the box closure. Known off-diagonal
    signs retain the corresponding formulas in each row margin; otherwise an
    absolute upper bound is used. Inconclusive bounds return no certificate.
    """
    axes = _box_axes(variables, domain)
    if axes is None:
        return None
    coordinates = dict(zip(variables, axes, strict=True))
    if _box_bound(expression, coordinates) is None:
        return None
    entries = [[] for _ in variables]
    formulas = [[] for _ in variables]
    # The raw-source C2 check makes mixed partials symmetric on the box.
    for i, u in enumerate(variables):
        for j in range(i, len(variables)):
            formula = differentiate(expression, u, variables[j])
            value = _box_bound(formula, coordinates)
            if value is None:
                return None
            entries[i].append(value)
            formulas[i].append(formula)
            if i != j:
                entries[j].append(value)
                formulas[j].append(formula)
    entries = tuple(tuple(row) for row in entries)
    positive = []
    negative = []
    margins = []
    for i, row in enumerate(entries):
        radius = S.Zero
        for j, (lower, upper) in enumerate(row):
            if i == j:
                continue
            # Known off-diagonal signs retain correlations in the row margin.
            # For example (exp(u+v)+2)-abs(exp(u+v)) reduces exactly to 2.
            radius += (
                formulas[i][j]
                if lower >= 0
                else -formulas[i][j]
                if upper <= 0
                else max(abs(lower), abs(upper))
            )
        lower_bound = _box_bound(formulas[i][i] - radius, coordinates)
        upper_bound = _box_bound(-formulas[i][i] - radius, coordinates)
        if lower_bound is None or upper_bound is None:
            return None
        positive.append(lower_bound[0])
        negative.append(upper_bound[0])
        margins.append((lower_bound, upper_bound))
    if min(positive) > 0:
        classification, modulus = Convexity.STRONGLY_CONVEX, min(positive)
    elif min(negative) > 0:
        classification, modulus = Convexity.STRONGLY_CONCAVE, min(negative)
    else:
        return None
    return (
        classification,
        modulus,
        (expression, variables, axes, entries, tuple(margins)),
    )


def hessian_dominance_certificate(expression, variables, domain):
    """Build a replayable uniform convexity/concavity bound on a rational box."""
    data = hessian_dominance_data(expression, variables, domain)
    if data is None:
        return None
    classification, modulus, proof = data
    return ConvexityCertificate(
        classification, domain, "box-hessian-dominance", modulus, proof
    )


def hessian_counterexample_data(expression, variables, domain):
    """Check an indefinite two-coordinate Hessian section at the box midpoint.

    A negative principal determinant gives positive and negative directional
    curvature at an interior point, excluding both convexity and concavity.
    """
    if not expression.is_polynomial(*variables) or expression.has(sp.Float):
        return None
    axes = _box_axes(variables, domain)
    if axes is None:
        return None
    coordinates = dict(zip(variables, axes, strict=True))
    if _box_bound(expression, coordinates) is None:
        return None
    point = tuple((axis.start + axis.end) / 2 for axis in axes)
    substitutions = dict(zip(variables, point, strict=True))
    for i, u in enumerate(variables):
        for j in range(i + 1, len(variables)):
            v = variables[j]
            entries = tuple(
                differentiate(expression, a, b).subs(substitutions)
                for a, b in ((u, u), (u, v), (v, v))
            )
            if (
                all(e.is_Rational for e in entries)
                and entries[0] * entries[2] - entries[1] ** 2 < 0
            ):
                return (
                    Convexity.NEITHER,
                    None,
                    (expression, variables, axes, point, (i, j), entries),
                )
    return None


def exponential_hessian_data(expression, variables, domain):
    """Bound a quadratic plus positive exponentials of real quadratic forms.

    For c exp(g), its Hessian is c exp(g) times the sum of Hess(g) and
    grad(g) grad(g)^T. The outer product is positive semidefinite. A constant
    Hessian lower bound and bounds for g therefore give a uniform modulus.
    """
    terms = sp.Add.make_args(expression)
    if not any(term.has(sp.exp) for term in terms):
        return None
    axes = _box_axes(variables, domain)
    if axes is None:
        return None
    coordinates = dict(zip(variables, axes, strict=True))
    if _box_bound(expression, coordinates) is None:
        return None
    remainder = S.Zero
    exponentials = []
    for term in terms:
        coefficient, factor = term.as_coeff_Mul()
        if factor.func is not sp.exp:
            remainder += term
            continue
        if not coefficient.is_Rational or coefficient <= 0:
            return None
        exponentials.append((coefficient, factor.args[0]))
    if not exponentials:
        return None

    def quadratic_margin(formula):
        try:
            polynomial = sp.Poly(formula, *variables, domain=sp.QQ)
        except (sp.PolynomialError, sp.CoercionFailed):
            return None
        if polynomial.total_degree() > 2:
            return None
        hessian = sp.hessian(formula, variables)
        return min(
            hessian[i, i]
            - sum(abs(hessian[i, j]) for j in range(len(variables)) if j != i)
            for i in range(len(variables))
        )

    modulus = quadratic_margin(remainder)
    if modulus is None:
        return None
    bounds = []
    for coefficient, argument in exponentials:
        margin = quadratic_margin(argument)
        enclosure = _box_bound(argument, coordinates)
        if margin is None or enclosure is None:
            return None
        endpoint = enclosure[0] if margin >= 0 else enclosure[1]
        modulus += coefficient * margin * sp.exp(endpoint)
        bounds.append((coefficient, argument, margin, enclosure))
    positivity = _box_bound(modulus, {})
    if positivity is None or positivity[0] <= 0:
        return None
    return (
        Convexity.STRONGLY_CONVEX,
        modulus,
        (expression, variables, axes, remainder, tuple(bounds)),
    )


def structural_hessian_certificate(expression, variables, domain):
    """Assemble a uniform exponential bound or an exact interior counterexample."""
    for method, check in (
        ("exponential-hessian-bound", exponential_hessian_data),
        ("interior-hessian-counterexample", hessian_counterexample_data),
    ):
        data = check(expression, variables, domain)
        if data is not None:
            classification, modulus, proof = data
            return ConvexityCertificate(classification, domain, method, modulus, proof)
    return None
