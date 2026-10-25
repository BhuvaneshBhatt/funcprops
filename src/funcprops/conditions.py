"""Semantic predicates and parsing for the bundled property catalogue.

Catalogue conditions are stored as SymPy constructor expressions.  The custom
Boolean predicates below preserve mathematical assumptions that do not map
cleanly to ordinary ``Symbol`` assumptions until the proof engine has enough
context to reduce them.
"""

from __future__ import annotations

from functools import lru_cache

from sympy import S, sympify
from sympy.core.relational import Relational
from sympy.logic.boolalg import Boolean, BooleanFunction


class IntegerCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are integer-valued explicit until evaluation."""

    pass


class RationalCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are rational-valued explicit until evaluation."""

    pass


class RealCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are real-valued explicit until evaluation."""

    pass


class RealIfDefinedCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are real-valued wherever defined explicit until evaluation."""

    pass


class AlgebraicCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are algebraic-valued explicit until evaluation."""

    pass


class NonintegerCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are noninteger-valued explicit until evaluation."""

    pass


class PositiveCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are positive explicit until evaluation."""

    pass


class NegativeCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are negative explicit until evaluation."""

    pass


class NonpositiveCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are nonpositive explicit until evaluation."""

    pass


class NonnegativeCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are nonnegative explicit until evaluation."""

    pass


class EvenCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are an even integer explicit until evaluation."""

    pass


class OddCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are an odd integer explicit until evaluation."""

    pass


class UnequalCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are unequal explicit until evaluation."""

    pass


class EqualCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are equal explicit until evaluation."""

    pass


class AssumedCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are entailed by the query assumptions explicit until evaluation."""

    pass


class AssumedInequalityCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are an entailed inequality explicit until evaluation."""

    pass


class NonterminatingCondition(BooleanFunction):
    """Keep the condition that catalogue arguments are a nonterminating series explicit until evaluation."""

    pass


_PREDICATE_TYPES = (
    IntegerCondition,
    RationalCondition,
    RealCondition,
    RealIfDefinedCondition,
    AlgebraicCondition,
    NonintegerCondition,
    PositiveCondition,
    NegativeCondition,
    NonpositiveCondition,
    NonnegativeCondition,
    EvenCondition,
    OddCondition,
    UnequalCondition,
    EqualCondition,
    AssumedCondition,
    AssumedInequalityCondition,
    NonterminatingCondition,
)
_PREDICATES = {cls.__name__: cls for cls in _PREDICATE_TYPES}


@lru_cache(maxsize=8192)
def parse_catalogue_expression(text: str):
    """Parse one bundled catalogue value or condition into a SymPy object.

    The catalogue uses ``srepr``-compatible constructor syntax, so parsing is
    deterministic and does not require a second symbolic-language grammar.
    Custom semantic predicates remain explicit ``BooleanFunction`` nodes.
    """
    source = text.strip()
    if not source:
        return S.true
    return sympify(source, locals=_PREDICATES, evaluate=False)


def is_boolean_expr(expr) -> bool:
    """Return whether ``expr`` is a Boolean or relational SymPy expression."""
    return isinstance(expr, (Boolean, Relational)) or expr in (S.true, S.false)
