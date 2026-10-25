"""Arithmetic rebuilding for calculations, with the raw source kept separately."""

from dataclasses import fields, is_dataclass
from functools import lru_cache

import sympy as sp


def same_data(actual, expected):
    """Compare canonical proof data without invoking container-subclass equality.

    Concrete record/tuple/scalar types must match. Symbolic expression semantics
    remain trusted, as in the arithmetic checkers using this comparison.
    """
    if type(actual) is not type(expected):
        return False
    if type(expected) is tuple:
        return len(actual) == len(expected) and all(
            same_data(a, b) for a, b in zip(actual, expected, strict=True)
        )
    if is_dataclass(expected):
        return all(
            same_data(getattr(actual, f.name), getattr(expected, f.name))
            for f in fields(expected)
        )
    return actual == expected


def normalize_arithmetic(node):
    """Rebuild held arithmetic without asking assumption or simplify oracles.

    This is a computational formula, never a replacement for source-domain
    tracking. In particular x/x may become 1 here: all guards must still come
    from the original source tree. Rebuilding also avoids querying inconsistent
    cached integer-parity assumptions on held zero products in SymPy.
    """
    if not node.args:
        return node
    args = tuple(normalize_arithmetic(arg) for arg in node.args)
    if node.is_Add or node.is_Mul or node.is_Pow or args != node.args:
        return node.func(*args)
    if node.func is sp.log and len(args) == 2:
        return sp.log(args[0]) / sp.log(args[1])
    return node


def logarithm_quotient(expression):
    """Expand a two-argument logarithm while retaining both source logarithms."""
    argument, base = expression.args
    return sp.Mul(
        sp.log(argument, evaluate=False),
        sp.Pow(sp.log(base, evaluate=False), -1, evaluate=False),
        evaluate=False,
    )


def expand_log_bases(expression):
    """Replace held logarithm bases without evaluating other source operations."""
    if not expression.has(sp.log):
        return expression
    arguments = tuple(expand_log_bases(argument) for argument in expression.args)
    if expression.func is sp.log and len(arguments) == 2:
        return logarithm_quotient(sp.log(*arguments, evaluate=False))
    if arguments == expression.args:
        return expression
    if (
        expression.is_Add
        or expression.is_Mul
        or expression.is_Pow
        or expression.is_Function
    ):
        return expression.func(*arguments, evaluate=False)
    return expression.func(*arguments)


def finite_constant_source(expression):
    """Check finite scalar constants before a held operation erases its operands."""
    if expression.func is sp.log and len(expression.args) == 2:
        return finite_constant_source(logarithm_quotient(expression))
    if (
        expression.is_Add
        or expression.is_Mul
        or expression.is_Pow
        or expression.is_Function
    ) and not all(
        isinstance(argument, sp.Expr) and finite_constant_source(argument)
        for argument in expression.args
    ):
        return False
    value = (
        normalize_arithmetic(expression)
        if expression.is_Add or expression.is_Mul or expression.is_Pow
        else expression
    )
    return value.is_finite is True


@lru_cache(maxsize=1024)
def _logarithm_formula(expression):
    """Expand held logarithm bases once, retaining ordinary derivative inputs."""
    if any(len(node.args) == 2 for node in expression.atoms(sp.log)):
        return normalize_arithmetic(expression)
    return expression


def differentiate(expression, *variables, **options):
    """Differentiate a computational formula with explicit logarithm-base semantics.

    SymPy's derivative of an unevaluated two-argument log can omit the base.
    Source-bound consumers keep the original expression for definition checks.
    """
    return sp.diff(_logarithm_formula(sp.sympify(expression)), *variables, **options)
