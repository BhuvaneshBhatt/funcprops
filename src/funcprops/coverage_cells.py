"""Exact first-match source cells, without folding or normalizing branch values."""

import sympy as sp

from .real_analysis.common import condition_to_set


def source_cells(expression, variable, domain):
    """Decompose source restrictions into owned branch cells and exceptional points."""

    if not isinstance(expression, sp.Piecewise):
        return None if expression.has(sp.Piecewise) else ((expression, domain),)
    remaining, cells = domain, []
    for branch, condition in expression.args:
        guard = condition_to_set(condition, variable)
        if not isinstance(guard, sp.Set):
            return None
        active = sp.Intersection(remaining, guard)
        parts = active.args if isinstance(active, sp.Union) else (active,)
        for part in parts:
            if part is not sp.S.EmptySet:
                if not isinstance(part, (sp.Interval, sp.FiniteSet)):
                    return None
                cells.append((branch, part))
        remaining = sp.Complement(remaining, guard)
    return tuple(cells) if remaining is sp.S.EmptySet else None
