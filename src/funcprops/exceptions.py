"""Expected failures from optional or undecidable symbolic computations.

Fallback code should catch the smallest operation-specific family that can
legitimately be raised by the SymPy operation being attempted.  Use ``SYMBOLIC_QUERY_ERRORS`` at orchestration boundaries only; proof steps
should catch the narrower operation-specific groups below.
"""

from sympy.core.function import PoleError
from sympy.core.sympify import SympifyError
from sympy.polys.polyerrors import PolynomialError

SYMPIFY_ERRORS = (SympifyError, TypeError)
POLYNOMIAL_ERRORS = (PolynomialError, ValueError)
SIMPLIFICATION_ERRORS = (TypeError, ValueError, NotImplementedError, RecursionError)
SET_OPERATION_ERRORS = (TypeError, ValueError, NotImplementedError)
LIMIT_ERRORS = (PoleError, ValueError, NotImplementedError)
BACKEND_QUERY_ERRORS = (ValueError, NotImplementedError, ArithmeticError)

# Syntax errors indicate malformed source, not an undecided symbolic query.
SYMBOLIC_QUERY_ERRORS = (
    *SIMPLIFICATION_ERRORS,
    ArithmeticError,
    SympifyError,
    PolynomialError,
    PoleError,
)
