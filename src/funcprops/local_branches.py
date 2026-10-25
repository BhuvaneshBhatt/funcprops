"""Explicit local logarithmic branches, bound to a finite basepoint."""

from dataclasses import dataclass

import sympy as sp

from .exactness import certify_identity_equal
from .local_analyticity import _punctured_source_defined, complex_meromorphic_germ


@dataclass(frozen=True)
class LocalBranchContext:
    """Choose log(base(point)) explicitly for selected Log/power bases.

    ``logarithms`` is a tuple of (source base expression, chosen log value).
    exp(value)=base(point) must be proved exactly. All entries must be used.
    The resulting theorem concerns this analytic germ, not the principal
    expression throughout a neighborhood crossing its old cut.
    """

    point: sp.Expr
    logarithms: tuple

    def apply(self, expression, variable, point):
        """Apply the selected local branch context after checking its source and base values."""

        try:
            return self._apply(
                sp.sympify(expression), sp.sympify(variable), sp.sympify(point)
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return None

    def _apply(self, expression, variable, point):
        if (
            type(self) is not LocalBranchContext
            or not isinstance(variable, sp.Symbol)
            or sp.sympify(self.point) != point
            or point.has(variable)
            or point.is_finite is not True
            or point.has(sp.Float)
            or expression.has(sp.Float)
            or type(self.logarithms) is not tuple
            or not self.logarithms
            or not _punctured_source_defined(expression, variable, point)
        ):
            return None
        choices = {}
        for entry in self.logarithms:
            if type(entry) is not tuple or len(entry) != 2:
                return None
            base, value = map(sp.sympify, entry)
            if (
                base in choices
                or base.has(sp.Float)
                or value.has(sp.Float)
                or value.has(variable)
                or value.is_finite is not True
            ):
                return None
            choices[base] = value
        used = set()

        def visit(node):
            if not isinstance(node, sp.Expr) or not node.has(variable):
                return node
            original_base = (
                node.args[0]
                if node.func is sp.log
                else node.base
                if node.is_Pow and node.exp.is_integer is not True
                else None
            )
            args = tuple(
                visit(arg) if isinstance(arg, sp.Expr) else arg for arg in node.args
            )
            if any(arg is None for arg in args):
                return None
            if original_base is not None and original_base in choices:
                base = args[0]
                value = choices[original_base]
                at_point = sp.simplify(base.subs(variable, point))
                if (
                    not complex_meromorphic_germ(base, variable, point)
                    or at_point.is_finite is not True
                    or at_point.is_zero is not False
                    or certify_identity_equal(sp.exp(value), at_point) is not True
                ):
                    return None
                used.add(original_base)
                local_log = value + sp.log(base / at_point)
                return local_log if node.func is sp.log else sp.exp(args[1] * local_log)
            return node.func(*args) if args else node

        transformed = visit(expression)
        if transformed is None or used != set(choices):
            return None
        return (
            transformed
            if complex_meromorphic_germ(transformed, variable, point)
            else None
        )
