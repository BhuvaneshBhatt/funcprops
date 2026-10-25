"""Entire compositions whose even outer series cancels a square-root branch."""

from dataclasses import dataclass

import sympy as sp

from .source_syntax import same_data


def even_root_argument(expression):
    """Match cos/cosh(sqrt(g)) and sin/sinh(sqrt(g)) squared exactly."""
    outer = expression
    template = "even-series"
    if expression.is_Pow and expression.exp == 2:
        outer = expression.base
        if outer.func not in (sp.sin, sp.sinh):
            return None
        template = "squared-odd-series"
    elif outer.func not in (sp.cos, sp.cosh):
        return None
    root = outer.args[0]
    if not root.is_Pow or root.exp != sp.S.Half:
        return None
    return root.base, template


def _entire_data(expression, variable):
    from .regularity_evidence import entire_inner

    matched = even_root_argument(expression)
    if (
        matched is None
        or not isinstance(variable, sp.Symbol)
        or expression.free_symbols.difference({variable})
        or expression.has(sp.Float, sp.oo, -sp.oo, sp.zoo, sp.nan)
        or sum(1 for _ in sp.preorder_traversal(expression)) > 96
        or not entire_inner(matched[0], variable)
    ):
        return None
    return matched


@dataclass(frozen=True)
class EntireCancellationProof:
    """Prove an entire composition by an everywhere convergent even series.

    cos(sqrt(w)) and cosh(sqrt(w)) have series in integer powers of w with
    infinite radius. The squared odd templates follow from the double-angle
    identities. Composing with an entire inner source preserves this property.
    """

    expression: sp.Expr
    variable: sp.Symbol
    inner: sp.Expr
    template: str

    def verify(self):
        """Check the exact template and the global entire-source premise."""
        try:
            data = _entire_data(self.expression, self.variable)
            return (
                type(self) is EntireCancellationProof
                and data is not None
                and same_data(data, (self.inner, self.template))
            )
        except (
            TypeError,
            ValueError,
            AttributeError,
            ArithmeticError,
            NotImplementedError,
        ):
            return False

    @property
    def complete(self):
        return self.verify()

    @property
    def certified(self):
        return self.verify()

    @property
    def scope(self):
        return "entire-by-even-square-root-series"


def entire_cancellation_proof(expression, variable):
    """Return a bounded exact branch-cancellation proof when its premises hold."""
    data = _entire_data(expression, variable)
    return (
        EntireCancellationProof(expression, variable, *data)
        if data is not None
        else None
    )
