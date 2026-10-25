"""Bounded exact real coefficient fields encoded by a uniquely isolated generator."""

from dataclasses import dataclass
from functools import lru_cache

import sympy as sp
from sympy.polys.numberfields import to_number_field

from .enclosures import preserve_replace
from .exactness import certify_equal
from .source_syntax import finite_constant_source, same_data
from .work_budget import budgeted_operation

_ERRORS = (
    AttributeError,
    TypeError,
    ValueError,
    ArithmeticError,
    NotImplementedError,
    sp.PolynomialError,
)


def _constants(nodes):
    values = set()

    def visit(node):
        if node in (sp.S.true, sp.S.false, sp.oo, -sp.oo) or isinstance(
            node, sp.Symbol
        ):
            return
        if node.is_number:
            if (
                not finite_constant_source(node)
                or node.has(sp.Float)
                or node.is_real is not True
                or node.is_algebraic is not True
            ):
                raise ValueError("unsupported exact coefficient")
            if node.is_Rational is not True:
                values.add(node)
            return
        for arg in node.args:
            visit(arg)

    for node in nodes:
        visit(node)
    return tuple(sorted(values, key=sp.default_sort_key))


@dataclass(frozen=True)
class AlgebraicCoefficientEncoding:
    """Represent a bounded real number field by its minimal polynomial and root interval."""

    inputs: tuple
    variables: tuple
    generator: sp.Symbol
    root: sp.Expr
    polynomial: sp.Expr
    interval: tuple
    representations: tuple
    transformed: tuple

    @property
    def guard(self):
        lo, hi = self.interval
        return sp.And(
            sp.Eq(self.polynomial, 0), self.generator > lo, self.generator < hi
        )

    @property
    def complete(self):
        return True

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "real-algebraic-coefficients-in-field-of-degree-at-most-four"

    def verify(self):
        """Check the unique real generator and every original coefficient representation."""
        try:
            if (
                type(self) is not AlgebraicCoefficientEncoding
                or any(
                    type(v) is not tuple
                    for v in (
                        self.inputs,
                        self.variables,
                        self.interval,
                        self.representations,
                        self.transformed,
                    )
                )
                or not isinstance(self.generator, sp.Symbol)
                or self.generator in self.variables
                or any(not isinstance(x, sp.Symbol) for x in self.variables)
                or any(n.free_symbols - set(self.variables) for n in self.inputs)
                or self.root.free_symbols
                or self.root.is_real is not True
                or self.root.is_finite is not True
            ):
                return False
            p = sp.Poly(self.polynomial, self.generator, domain=sp.QQ)
            lo, hi = self.interval
            if not (
                1 < p.degree() <= 4
                and all(v.is_Rational for v in (lo, hi))
                and lo < hi
                and p.is_irreducible
                and p.count_roots(lo, hi) == 1
            ):
                return False
            if (
                sp.Gt(self.root, lo) is not sp.S.true
                or sp.Lt(self.root, hi) is not sp.S.true
                or certify_equal(p.as_expr().subs(self.generator, self.root), 0)
                is not True
            ):
                return False
            constants = _constants(self.inputs)
            if (
                not (0 < len(constants) <= 4)
                or tuple(c for c, _ in self.representations) != constants
            ):
                return False
            for constant, formula in self.representations:
                poly = sp.Poly(formula, self.generator, domain=sp.QQ)
                if (
                    poly.degree() >= p.degree()
                    or certify_equal(
                        poly.as_expr().subs(self.generator, self.root), constant
                    )
                    is not True
                ):
                    return False
            expected = tuple(
                preserve_replace(n, dict(self.representations)) for n in self.inputs
            )
            return same_data(self.transformed, expected)
        except _ERRORS:
            return False


@lru_cache(maxsize=128)
def _encoding(inputs, variables):
    if (
        any(n.free_symbols - set(variables) for n in inputs)
        or sum(sp.count_ops(n) for n in inputs) > 80
    ):
        return None
    try:
        constants = _constants(inputs)
        if not (0 < len(constants) <= 4):
            return None
        field = to_number_field(constants)
        if not (1 < field.minpoly.degree() <= 4):
            return None
        generator = sp.Dummy("coefficient", real=True)
        polynomial = field.minpoly.as_expr().subs(field.minpoly.gen, generator)
        root = field.root
        interval = next(
            (
                (a, b)
                for ((a, b), m) in field.minpoly.intervals()
                if a < b and sp.Gt(root, a) is sp.S.true and sp.Lt(root, b) is sp.S.true
            ),
            None,
        )
        if interval is None:
            return None
        representations = []
        for c in constants:
            p = to_number_field(c, field).as_poly()
            representations.append((c, p.as_expr().subs(p.gen, generator)))
        substitutions = dict(representations)
        proof = AlgebraicCoefficientEncoding(
            inputs,
            variables,
            generator,
            root,
            polynomial,
            interval,
            tuple(representations),
            tuple(preserve_replace(n, substitutions) for n in inputs),
        )
        return proof if proof.verify() else None
    except _ERRORS:
        return None


@budgeted_operation
def encode_algebraic_coefficients(inputs, variables):
    """Encode up to four real algebraic constants in one field of degree at most four.

    All remaining symbols must be declared query coordinates. Inexact, nonreal,
    transcendental and larger fields decline before a rational backend is loaded.
    """
    return _encoding(tuple(map(sp.sympify, inputs)), tuple(map(sp.sympify, variables)))
