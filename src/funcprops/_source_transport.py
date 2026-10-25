"""Worker transport that retains held SymPy operations and source-definition holes."""

import io
import pickle

import sympy as sp
from sympy.core.relational import Relational


class _SourcePickler(pickle.Pickler):
    """Retain raw operands without changing global SymPy serialization rules.

    The default SymPy reducers rebuild arithmetic and functions with evaluation
    enabled. That can cancel a denominator, erase an inactive-looking operand,
    or evaluate a held guard before the worker can inspect its definition.
    Atoms keep their native reducers; polynomial records restore their exact
    coefficient domains explicitly.
    """

    def reducer_override(self, value):
        if isinstance(value, sp.Poly):
            domain = value.domain
            if domain.is_AlgebraicField:
                domain = (domain.dom, tuple(domain.orig_ext))
            return _restore_polynomial, (
                type(value),
                value.as_dict(),
                value.gens,
                domain,
            )
        if (
            isinstance(value, sp.Basic)
            and value.args
            and (
                isinstance(
                    value,
                    (sp.Add, sp.Mul, sp.Pow, sp.Function, Relational, sp.Derivative),
                )
                or value.func
                in (
                    sp.And,
                    sp.Or,
                    sp.Not,
                    sp.Xor,
                    sp.Implies,
                    sp.Equivalent,
                    sp.Contains,
                    sp.Min,
                    sp.Max,
                )
            )
        ):
            return _restore_node, (value.func, value.args)
        return NotImplemented


def _restore_node(constructor, arguments):
    return constructor(*arguments, evaluate=False)


def _restore_polynomial(constructor, coefficients, generators, domain):
    if type(domain) is tuple:
        base, extensions = domain
        domain = base.algebraic_field(*extensions)
    return constructor.from_dict(coefficients, generators, domain=domain)


def _dumps(value):
    """Encode trusted worker data while retaining the original source operands."""
    stream = io.BytesIO()
    _SourcePickler(stream, protocol=pickle.HIGHEST_PROTOCOL).dump(value)
    return stream.getvalue()
