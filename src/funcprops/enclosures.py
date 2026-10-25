"""Declared compact real grammar and immutable, premise-keyed enclosure leaves."""

from dataclasses import dataclass, replace
from functools import lru_cache

import sympy as sp

from .coverage_contract import CheckOutcome, EnclosureWitness
from .domain_tracking import coordinate_domain_compatible
from .enclosure_policy import EnclosurePolicy
from .transcendental.real_interval import certified_real_interval_evaluate

GRAMMAR_VERSION = 1
PRIMITIVES = (
    sp.exp,
    sp.sin,
    sp.cos,
    sp.asin,
    sp.acos,
    sp.atan,
    sp.log,
    sp.Abs,
    sp.sinh,
    sp.cosh,
    sp.tanh,
    sp.erf,
    sp.erfc,
)


def preserve_replace(node, replacements):
    """Specialize parameters without evaluating away raw arithmetic holes."""
    if node in replacements:
        return replacements[node]
    if not node.args:
        return node
    args = tuple(preserve_replace(a, replacements) for a in node.args)
    if args == node.args:
        return node
    if node.is_Add or node.is_Mul or node.is_Pow or isinstance(node, sp.Function):
        return node.func(*args, evaluate=False)
    return node.func(*args)


def grammar_obligations(expr, var):
    """Syntax obligations only; branch and regularity premises are additional."""
    f, x = sp.sympify(expr), sp.sympify(var)
    missing = []

    def visit(node):
        if node == x or isinstance(node, sp.Rational) or node in (sp.pi, sp.E):
            return
        if node.has(sp.Float):
            missing.append("inexact-coefficient")
            return
        if node.is_Pow:
            if (
                node.exp.free_symbols
                or node.exp.is_real is not True
                or node.exp.is_finite is not True
            ):
                missing.append("constant-real-exponent-required")
            else:
                visit(node.exp)
            visit(node.base)
            return
        if node.is_Add or node.is_Mul or node.func in PRIMITIVES:
            for arg in node.args:
                visit(arg)
            return
        missing.append("unsupported-primitive:" + str(node.func))

    visit(f)
    return tuple(dict.fromkeys(missing))


@lru_cache(maxsize=1024)
def _enclosure_leaf(
    expr, var, domain, source_syntax, assumptions, precision, max_terms
):
    # Raw syntax and intrinsic assumptions distinguish otherwise equal expressions
    # whose source definition or coordinate domain differs.
    if source_syntax != sp.srepr(expr) or assumptions != tuple(
        sorted(var.assumptions0.items())
    ):
        return None
    result = certified_real_interval_evaluate(
        expr, var, domain, precision=precision, max_series_terms=max_terms
    )
    if result is None:
        return None
    lo, hi = sp.sympify(result.lower), sp.sympify(result.upper)
    if not isinstance(lo, sp.Rational) or not isinstance(hi, sp.Rational) or lo > hi:
        return None
    return EnclosureWitness(expr, var, domain, lo, hi, precision, max_terms)


def enclosure_witness(expr, var, domain, precision=30, max_series_terms=4096):
    """Construct one outward real enclosure leaf in the supported grammar."""

    f, x = sp.sympify(expr), sp.sympify(var)
    if (
        not isinstance(x, sp.Symbol)
        or not isinstance(domain, sp.Set)
        or not coordinate_domain_compatible(x, domain)
        or grammar_obligations(f, x)
    ):
        return None
    return _enclosure_leaf(
        f,
        x,
        domain,
        sp.srepr(f),
        tuple(sorted(x.assumptions0.items())),
        precision,
        max_series_terms,
    )


@dataclass(frozen=True)
class EnclosureResult:
    """Intersect checked value enclosures and retain unresolved arithmetic obligations."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    witnesses: tuple = ()
    obligations: tuple = ()
    outcome: CheckOutcome = CheckOutcome.UNSUPPORTED

    @property
    def schema_version(self):
        return 1

    @property
    def lower(self):
        return max(w.lower for w in self.witnesses) if self.witnesses else None

    @property
    def upper(self):
        return min(w.upper for w in self.witnesses) if self.witnesses else None

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "compact-real-value-enclosure"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        from .coverage_checker import check_enclosure

        return bool(
            type(self) is EnclosureResult
            and bool(self.witnesses)
            and isinstance(self.witnesses, tuple)
            and self.outcome is CheckOutcome.LOCAL_VALID
            and not self.obligations
            and all(
                isinstance(w, EnclosureWitness)
                and w.expression == self.expression
                and w.variable == self.variable
                and w.domain == self.domain
                and check_enclosure(w)
                for w in self.witnesses
            )
            and self.lower <= self.upper
        )


def enclose_expression(expr, var, domain, *, policy=None):
    """Intersect valid precision leaves; failed refinement retains earlier proof.

    Complete here means a value enclosure on this cell, not root completeness.
    Refinement intersections are nested by construction, and replay checks every
    constituent outward enclosure independently of this scheduler/cache.
    """
    policy = EnclosurePolicy() if policy is None else policy
    if not isinstance(policy, EnclosurePolicy):
        raise TypeError("policy must be an EnclosurePolicy")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "enclose_expression",
            expr,
            (var, domain),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    f, x = sp.sympify(expr), sp.sympify(var)
    obligations = grammar_obligations(f, x)
    if obligations:
        return EnclosureResult(f, x, domain, obligations=obligations)
    if policy.max_cells == 0:
        return EnclosureResult(
            f, x, domain, obligations=("cell-budget",), outcome=CheckOutcome.EXHAUSTED
        )
    witnesses = []
    for precision in policy.precisions:
        w = enclosure_witness(f, x, domain, precision, policy.max_series_terms)
        if w is None:
            break
        witnesses.append(w)
    if not witnesses:
        return EnclosureResult(
            f, x, domain, obligations=("domain-branch-or-enclosure-obligation",)
        )
    return EnclosureResult(
        f, x, domain, tuple(witnesses), outcome=CheckOutcome.LOCAL_VALID
    )


@dataclass(frozen=True)
class DerivativeEnclosure:
    """Bind derivative bounds to the original source and regularity premises."""

    expression: sp.Expr
    variable: sp.Symbol
    domain: sp.Set
    order: int
    derivative: sp.Expr | None
    enclosure: EnclosureResult | None
    source_syntax: str
    regularity_precision: int = 30
    max_series_terms: int = 4096
    obligations: tuple = ()
    schema_version: int = 1

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "source-bound-real-derivative-enclosure"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        from .coverage_checker import _formula_equal, derivative_formula_on_cell

        try:
            if (
                type(self) is not DerivativeEnclosure
                or type(self.schema_version) is not int
                or self.schema_version != 1
                or type(self.regularity_precision) is not int
                or self.regularity_precision < 2
                or type(self.max_series_terms) is not int
                or self.max_series_terms < 0
                or self.source_syntax != sp.srepr(self.expression)
                or type(self.enclosure) is not EnclosureResult
            ):
                return False
            actual = derivative_formula_on_cell(
                self.expression,
                self.variable,
                self.domain,
                self.order,
                precision=self.regularity_precision,
                max_series_terms=self.max_series_terms,
            )
            return bool(
                actual is not None
                and self.derivative is not None
                and _formula_equal(actual, self.derivative)
                and self.enclosure.expression == self.derivative
                and self.enclosure.variable == self.variable
                and self.enclosure.domain == self.domain
                and self.enclosure.verify()
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


def enclose_derivative(expr, var, domain, *, order=1, policy=None):
    """Return an enclosure bound to the source and its full-cell regularity."""
    from .coverage_checker import derivative_formula_on_cell

    policy = EnclosurePolicy() if policy is None else policy
    if not isinstance(policy, EnclosurePolicy):
        raise TypeError("policy must be an EnclosurePolicy")
    if type(order) is not int or order < 0:
        raise ValueError("order must be a nonnegative integer")
    if order > policy.max_taylor_order + 1:
        raise ValueError("derivative order exceeds the query order budget")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "enclose_derivative",
            expr,
            (var, domain),
            {"order": order, "policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    f, x = sp.sympify(expr), sp.sympify(var)
    if policy.max_cells == 0:
        return DerivativeEnclosure(
            f, x, domain, order, None, None, sp.srepr(f), obligations=("cell-budget",)
        )
    for precision in policy.precisions:
        derivative = derivative_formula_on_cell(
            f,
            x,
            domain,
            order,
            precision=precision,
            max_series_terms=policy.max_series_terms,
        )
        if derivative is not None:
            result = enclose_expression(derivative, x, domain, policy=policy)
            if result.verify():
                return DerivativeEnclosure(
                    f,
                    x,
                    domain,
                    order,
                    derivative,
                    result,
                    sp.srepr(f),
                    precision,
                    policy.max_series_terms,
                )
    return DerivativeEnclosure(
        f,
        x,
        domain,
        order,
        None,
        None,
        sp.srepr(f),
        obligations=("source-regularity-or-derivative-enclosure-obligation",),
    )
