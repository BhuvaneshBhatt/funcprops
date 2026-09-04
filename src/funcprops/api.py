"""Public routing layer for function-property queries.

Each public query has a single implementation in either :mod:`funcprops.singularities`
or :mod:`funcprops.real_analysis`.  This module only re-exports those implementations
so callers have one stable import surface without duplicating property logic.
"""

from __future__ import annotations

from .real_analysis.boundedness import function_boundedness
from .real_analysis.convexity import function_convexity
from .real_analysis.differentiability import function_differentiability
from .real_analysis.domain import function_domain
from .real_analysis.mapping import (
    function_bijective,
    function_injective,
    function_surjective,
)
from .real_analysis.monotonicity import function_monotonicity
from .real_analysis.oscillation import function_oscillation
from .real_analysis.range import function_range
from .real_analysis.sign import function_sign
from .real_analysis.smoothness import function_smoothness
from .real_analysis.structural_properties import (
    function_homogeneity,
    function_periodicity,
    function_symmetry,
)
from .real_analysis.zeros import function_zeros
from .singularities import (
    function_analytic,
    function_branchcuts,
    function_branchpoints,
    function_continuous,
    function_discontinuities,
    function_meromorphic,
    function_poles,
    function_singularities,
    function_singularity_analysis,
)
from .transcendental.complex_roots import function_complex_zeros

__all__ = [
    "function_analytic",
    "function_bijective",
    "function_boundedness",
    "function_branchcuts",
    "function_branchpoints",
    "function_complex_zeros",
    "function_continuous",
    "function_convexity",
    "function_differentiability",
    "function_discontinuities",
    "function_domain",
    "function_homogeneity",
    "function_injective",
    "function_meromorphic",
    "function_monotonicity",
    "function_oscillation",
    "function_periodicity",
    "function_poles",
    "function_range",
    "function_sign",
    "function_singularities",
    "function_singularity_analysis",
    "function_smoothness",
    "function_surjective",
    "function_symmetry",
    "function_zeros",
]
