"""Adapter to semialg's public exact real-function API.

funcprops owns the public property vocabulary and evidence objects. semialg
provides the exact backend for semialgebraic functions on semialgebraic real
domains, including domain, range, sign, monotonicity, convexity, smoothness,
and mapping-property calculations. Imports remain lazy so catalogue and
complex_analysis queries do not load the backend until a real-domain proof
needs it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import cache, lru_cache, wraps

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, DomainError


@dataclass(frozen=True)
class CoefficientProfile:
    """Separate exact coefficient fields from symbolic parameter coordinates."""

    kind: str
    parameters: tuple = ()


def _numeric_coefficient_kind(expression):
    """Classify a scalar constant after checking its unreduced source operands."""
    from .source_syntax import finite_constant_source, normalize_arithmetic

    if expression.has(sp.Float):
        return "inexact"
    if expression.is_Rational:
        return "rational"
    if not finite_constant_source(expression):
        return "undefined" if expression.is_finite is False else "unknown"
    value = normalize_arithmetic(expression)
    if value.is_real is False:
        return "nonreal"
    if value.is_real is not True:
        return "unknown"
    if value.is_Rational:
        return "rational"
    if value.is_algebraic is True:
        return "algebraic"
    if value.is_algebraic is False:
        return "transcendental"
    return "unknown"


@lru_cache(maxsize=1024)
def _coefficient_profile(expression, variables, conditions):
    ranks = {
        "rational": 0,
        "algebraic": 1,
        "transcendental": 2,
        "unknown": 3,
        "nonreal": 4,
        "inexact": 5,
        "undefined": 6,
    }
    kinds = ["rational"]

    def visit(node, *, boundary=False):
        if node in (sp.S.true, sp.S.false) or isinstance(node, sp.Symbol):
            return
        if boundary and node in (sp.oo, -sp.oo):
            return
        if node.is_number:
            kinds.append(_numeric_coefficient_kind(node))
            return
        if isinstance(node, sp.Function) and node.func not in (
            sp.Abs,
            sp.Min,
            sp.Max,
            sp.Piecewise,
        ):
            kinds.append("unknown")
        for argument in node.args:
            visit(argument, boundary=boundary)

    visit(expression)
    for condition in conditions:
        visit(condition, boundary=True)
    symbols = expression.free_symbols.union(*(c.free_symbols for c in conditions))
    parameters = tuple(sorted(symbols - set(variables), key=sp.default_sort_key))
    return CoefficientProfile(max(kinds, key=ranks.__getitem__), parameters)


def coefficient_profile(expression, variables, *, conditions=()):
    """Classify numeric coefficients once without treating parameters as numbers."""
    variables = (variables,) if isinstance(variables, sp.Symbol) else tuple(variables)
    expression = (
        sp.Tuple(*expression)
        if isinstance(expression, (list, tuple))
        else sp.sympify(expression)
    )
    return _coefficient_profile(
        expression,
        tuple(map(sp.sympify, variables)),
        tuple(
            sp.sympify(True if condition is None else condition)
            for condition in conditions
        ),
    )


def _require_coefficients(expression, variables, *conditions):
    profile = coefficient_profile(expression, variables, conditions=conditions)
    if profile.kind != "rational":
        raise NotImplementedError(
            f"semialg rational portfolio does not accept {profile.kind} coefficients"
        )


def _algebraic_encoding(expression, variable, *conditions):
    if (
        coefficient_profile(expression, variable, conditions=conditions).kind
        != "algebraic"
    ):
        return None
    from .algebraic_coefficients import encode_algebraic_coefficients
    from .real_analysis.common import normalize_domain_condition

    normalized = tuple(normalize_domain_condition(c, variable) for c in conditions)
    return encode_algebraic_coefficients((expression, *normalized), (variable,))


def _algebraic_shape(expr, variable, restriction, *, mode):
    """Use derivative signs only on a connected, fully defined rational source."""
    from .real_analysis.common import condition_to_set
    from .source_syntax import differentiate

    expression = sp.sympify(expr)
    if not expression.is_rational_function(variable):
        raise NotImplementedError("algebraic shape route requires a rational formula")
    natural = domain(expression, variable)
    support = condition_to_set(sp.And(sp.sympify(restriction), natural), variable)
    if not isinstance(support, sp.Interval):
        raise NotImplementedError("algebraic shape route requires one interval")
    order = 1 if mode == "monotonicity" else 2
    derivative = differentiate(expression, variable, order)
    raw = sign(derivative, variable, assumptions=support.as_relational(variable))
    classification = str(getattr(raw, "classification", raw))
    if mode == "monotonicity":
        return {
            "positive": "strictly_increasing",
            "negative": "strictly_decreasing",
            "zero": "constant",
            "nonnegative": "increasing",
            "nonpositive": "decreasing",
            "mixed": "nonmonotonic",
        }.get(classification, "unknown")
    return {
        "positive": "strictlyconvex",
        "negative": "strictlyconcave",
        "zero": "affine",
        "nonnegative": "convex",
        "nonpositive": "concave",
        "mixed": "neither",
    }.get(classification, "unknown")


class SemialgUnavailable(ImportError):
    """Raised when the required semialg public API cannot be loaded."""


@cache
def _public_function(name: str) -> Callable:
    """Return one function from semialg's documented root API."""
    try:
        import semialg
    except ImportError as exc:
        raise SemialgUnavailable(
            "funcprops real-analysis queries require semialg>=1.3.0"
        ) from exc

    try:
        function = getattr(semialg, name)
    except AttributeError as exc:
        raise SemialgUnavailable(
            f"semialg>=1.3.0 does not provide the required public function {name!r}"
        ) from exc
    if not callable(function):
        raise SemialgUnavailable(f"semialg public attribute {name!r} is not callable")

    @wraps(function)
    def call(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (CoercionFailed, DomainError) as error:
            # Rational-coefficient portfolios may decline an exact algebraic
            # or transcendental coefficient. Keep the other exact routes open.
            raise NotImplementedError(
                f"unsupported semialg {name} coefficients"
            ) from error

    return call


def domain(expr, variable):
    """Return semialg's recognized real-domain condition."""
    encoding = _algebraic_encoding(expr, variable)
    if encoding is not None:
        from .real_analysis.domain import _argument_domains, _piecewise_domain
        from .results import PropertyResult

        source = sp.sympify(expr)
        defined = (
            _piecewise_domain(source, variable, domain=sp.S.Reals)
            if isinstance(source, sp.Piecewise)
            else _argument_domains(source, variable, domain=sp.S.Reals)
        )
        if isinstance(defined, PropertyResult):
            raise NotImplementedError("unresolved algebraic source domain")
        if source.is_Pow and source.exp.is_negative is True:
            defined = sp.And(defined, sp.Ne(source.base, 0))
        value = _public_function("function_domain")(
            encoding.transformed[0], [variable, encoding.generator]
        )
        return sp.And(
            defined, sp.sympify(value).subs(encoding.generator, encoding.root)
        )
    _require_coefficients(expr, variable)
    function = _public_function("function_domain")
    return function(sp.sympify(expr), [variable])


def range(expr, variable, value_symbol, *, constraints=True, method="qe", **kwargs):
    """Return an exact real-range condition from semialg."""
    encoding = _algebraic_encoding(expr, variable, constraints)
    if encoding is not None:
        if method != "qe":
            raise NotImplementedError("algebraic coefficients require exact QE")
        encoding = _algebraic_encoding(
            expr, variable, constraints, domain(expr, variable)
        )
        if encoding is None:
            raise NotImplementedError("algebraic range query exceeds encoding bounds")
        lifted, restriction, defined = encoding.transformed
        kwargs = dict(kwargs)
        return _public_function("function_range")(
            lifted,
            sp.And(restriction, defined, encoding.guard),
            [variable, encoding.generator],
            value_symbol=value_symbol,
            method="cad",
            **kwargs,
        )
    _require_coefficients(expr, variable, constraints)
    function = _public_function("function_range")
    return function(
        sp.sympify(expr),
        constraints,
        [variable],
        value_symbol=value_symbol,
        method=method,
        **kwargs,
    )


def convexity(expr, variable, *, domain=True, strict_inequalities=True, **kwargs):
    """Return semialg's strongest certified convexity classification."""
    properties = kwargs.pop("properties", "primary")
    return_result = kwargs.pop("return_result", False)
    parameters = kwargs.pop("parameters", None)
    if kwargs:
        names = ", ".join(sorted(kwargs))
        raise TypeError(f"unsupported semialg convexity options: {names}")

    # semialg computes the strongest exact class. funcprops weakens the class
    # afterwards when callers request non-strict semantics.
    del strict_inequalities
    encoding = _algebraic_encoding(expr, variable, domain)
    if encoding is not None:
        if parameters:
            raise NotImplementedError(
                "algebraic coefficient parameters are unsupported"
            )
        return _algebraic_shape(expr, variable, domain, mode="convexity")
    _require_coefficients(expr, variable, domain)
    function = _public_function("function_convexity")
    return function(
        sp.sympify(expr),
        [variable],
        domain=domain,
        parameters=parameters,
        return_result=return_result,
        properties=properties,
    )


def monotonicity(expr, variable, *, domain=True, return_result=False):
    """Return semialg's exact monotonicity classification."""
    encoding = _algebraic_encoding(expr, variable, domain)
    if encoding is not None:
        return _algebraic_shape(expr, variable, domain, mode="monotonicity")
    _require_coefficients(expr, variable, domain)
    function = _public_function("function_monotonicity")
    return function(
        sp.sympify(expr),
        variable,
        domain=domain,
        return_result=return_result,
    )


def smoothness(expr, variable, *, domain=True, max_order=6):
    """Return semialg's exact regularity result on a semialgebraic domain."""
    _require_coefficients(expr, variable, domain)
    function = _public_function("function_smoothness")
    return function(
        sp.sympify(expr),
        variable,
        domain=domain,
        max_order=max_order,
    )


def function_mapping_properties(
    expr, variable, *, domain=True, codomain=True, image_variable=None
):
    """Return semialg's exact mapping properties for a semialgebraic map."""
    _require_coefficients(expr, variable, domain, codomain)
    function = _public_function("function_mapping_properties")
    image_variables = None if image_variable is None else (image_variable,)
    return function(
        expr,
        variable,
        domain=domain,
        codomain=codomain,
        image_variables=image_variables,
    )


def eligible_problem(expr, variable, *, domain=True) -> bool:
    """Return whether an expression/domain pair is safe for semialg delegation."""
    from .real_analysis.common import (
        is_semialgebraic_condition,
        is_semialgebraic_expression,
    )

    return (
        is_semialgebraic_expression(expr, variable)
        and is_semialgebraic_condition(domain, variable)
        and coefficient_profile(expr, variable, conditions=(domain,)).kind == "rational"
    )


def is_satisfiable(condition, variables):
    """Decide satisfiability of a semialgebraic parameter guard exactly."""
    function = _public_function("is_satisfiable")
    normalized = tuple(sp.sympify(v) for v in variables)
    from .algebraic_coefficients import encode_algebraic_coefficients

    encoding = encode_algebraic_coefficients((condition,), normalized)
    if encoding is not None:
        return bool(
            function(
                sp.And(encoding.guard, encoding.transformed[0]),
                (*normalized, encoding.generator),
            )
        )
    return bool(function(sp.sympify(condition), normalized))


def sign(expr, variable, *, assumptions=True, return_result=False):
    """Return semialg's canonical exact sign classification."""
    encoding = _algebraic_encoding(expr, variable, assumptions)
    if encoding is not None:
        encoding = _algebraic_encoding(
            expr, variable, assumptions, domain(expr, variable)
        )
        if encoding is None:
            raise NotImplementedError("algebraic sign query exceeds encoding bounds")
        lifted, restriction, defined = encoding.transformed
        return _public_function("function_sign")(
            lifted,
            [variable, encoding.generator],
            assumptions=sp.And(restriction, defined, encoding.guard),
            return_result=return_result,
        )
    _require_coefficients(expr, variable, assumptions)
    function = _public_function("function_sign")
    return function(
        sp.sympify(expr),
        [variable],
        assumptions=assumptions,
        return_result=return_result,
    )


def sign_partition(expr, variable, *, domain=True):
    """Return semialg's exact univariate sign partition."""
    _require_coefficients(expr, variable, domain)
    function = _public_function("function_sign_partition")
    return function(sp.sympify(expr), variable, domain=domain)


def normalize_sign(value):
    """Translate a semialg sign classification into funcprops' Sign enum."""
    from .results import Sign

    classification = getattr(value, "classification", value)
    return {
        "positive": Sign.POSITIVE,
        "negative": Sign.NEGATIVE,
        "zero": Sign.ZERO,
        "nonnegative": Sign.NONNEGATIVE,
        "nonpositive": Sign.NONPOSITIVE,
        "mixed": Sign.SIGN_CHANGING,
    }.get(str(classification), Sign.UNKNOWN)


def normalize_convexity(value):
    """Translate semialg convexity vocabulary into funcprops' enum."""
    from .results import Convexity

    if isinstance(value, Convexity):
        return value
    if hasattr(value, "primary"):
        value = value.primary
    if isinstance(value, int):
        return {
            1: Convexity.STRICTLY_CONVEX,
            2: Convexity.CONVEX,
            -1: Convexity.STRICTLY_CONCAVE,
            -2: Convexity.CONCAVE,
        }.get(int(value), Convexity.UNKNOWN)
    key = str(getattr(value, "name", value)).lower().replace("_", "").replace(" ", "")
    return {
        "stronglyconvex": Convexity.STRONGLY_CONVEX,
        "strictlyconvex": Convexity.STRICTLY_CONVEX,
        "convex": Convexity.CONVEX,
        "affine": Convexity.AFFINE,
        "strictlyconcave": Convexity.STRICTLY_CONCAVE,
        "concave": Convexity.CONCAVE,
        "stronglyconcave": Convexity.STRONGLY_CONCAVE,
        "neither": Convexity.NEITHER,
    }.get(key, Convexity.UNKNOWN)


def normalize_monotonicity(value):
    """Translate semialg monotonicity vocabulary into funcprops' enum."""
    from .results import Monotonicity

    classification = getattr(value, "classification", value)
    return {
        "strictly_increasing": Monotonicity.STRICTLY_INCREASING,
        "increasing": Monotonicity.NONDECREASING,
        "constant": Monotonicity.CONSTANT,
        "decreasing": Monotonicity.NONINCREASING,
        "strictly_decreasing": Monotonicity.STRICTLY_DECREASING,
        "nonmonotonic": Monotonicity.NOT_MONOTONE,
    }.get(str(classification), Monotonicity.UNKNOWN)


def normalize_truth(value):
    """Translate a backend boolean into funcprops' three-valued truth type."""
    from .results import TruthValue

    if value is True:
        return TruthValue.TRUE
    if value is False:
        return TruthValue.FALSE
    return TruthValue.UNKNOWN


def prove_sign(expr, variable, relation, *, assumptions=True):
    """Prove one exact sign relation with semialg's public sign provers."""
    prover_names = {
        "positive": "prove_positive",
        "negative": "prove_negative",
        "nonnegative": "prove_nonnegative",
        "nonpositive": "prove_nonpositive",
    }
    try:
        prover_name = prover_names[relation]
    except KeyError as exc:
        raise ValueError(f"unknown sign relation: {relation!r}") from exc

    encoding = _algebraic_encoding(expr, variable, assumptions)
    if encoding is not None:
        encoding = _algebraic_encoding(
            expr, variable, assumptions, domain(expr, variable)
        )
        if encoding is None:
            raise NotImplementedError("algebraic sign query exceeds encoding bounds")
        lifted, restriction, defined = encoding.transformed
        return _public_function(prover_name)(
            lifted,
            [variable, encoding.generator],
            assumptions=sp.And(restriction, defined, encoding.guard),
        )
    _require_coefficients(expr, variable, assumptions)
    prover = _public_function(prover_name)
    return prover(sp.sympify(expr), [variable], assumptions=assumptions)
