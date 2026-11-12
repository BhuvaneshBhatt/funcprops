"""Public real-analysis primitives shared with numerical and symbolic consumers.

Domain records retain source definedness. Cells and derivative covers describe
real geometry; value enclosures describe a supplied formula on a region. These
operations do not select an optimizer or assert attainment.
"""

from dataclasses import replace
from time import monotonic

import sympy as sp


def condition_to_real_set(condition, variable):
    """Convert a supported real condition to a set, returning None if unresolved.

    Parameter-only guards, typed semantic predicates and incomplete ConditionSet
    answers are not interpreted as empty sets or universal real domains.
    """
    from .real_analysis.common import condition_to_set

    if condition is None:
        return None
    result = condition_to_set(condition, variable)
    return (
        result
        if isinstance(result, sp.Set) and not result.has(sp.ConditionSet)
        else None
    )


def normalize_real_expression(expression):
    """Normalize arithmetic for analytic calculations after recording its domain.

    The returned formula can cancel source holes. Preserve and verify the
    original DomainRecord separately when reasoning about the supplied source.
    """
    from .source_syntax import normalize_arithmetic

    return normalize_arithmetic(sp.sympify(expression))


def analysis_data_equal(left, right):
    """Compare exact analysis payloads without trusting overloaded record equality."""
    from .source_syntax import same_data

    return same_data(left, right)


def function_cells(expression, variable, domain):
    """Return supported formula/region cells, including isolated piecewise seams.

    An empty tuple describes an empty domain. None means that the decomposition
    is unsupported; it supplies no coverage claim. Source definedness remains
    the responsibility of the associated DomainRecord.
    """
    from .property_checker import property_cells

    return property_cells(sp.sympify(expression), sp.sympify(variable), domain)


def derivative_on_domain(expression, variable, domain, order=1):
    """Return a checked real derivative formula on a region, or None.

    This checks the supplied formula, including any required extension to a
    closed region. Original source holes remain in the separate domain record.
    """
    from .coverage_checker import derivative_formula_on_cell

    if type(order) is not int or order < 0:
        raise ValueError("order must be a nonnegative integer")
    return derivative_formula_on_cell(
        sp.sympify(expression), sp.sympify(variable), domain, order
    )


def value_enclosure(
    expression, variable, region, *, precision=30, max_series_terms=4096
):
    """Enclose a real formula on a finite region with replayable outward evidence.

    None denotes unsupported enclosure work. The caller must bind this formula
    and region to an admissible source-domain or extension argument.
    """
    from .enclosures import enclosure_witness

    for name, value, minimum in (
        ("precision", precision, 2),
        ("max_series_terms", max_series_terms, 0),
    ):
        if type(value) is not int or value < minimum:
            raise ValueError(f"{name} must be an integer at least {minimum}")
    return enclosure_witness(
        sp.sympify(expression),
        sp.sympify(variable),
        region,
        precision,
        max_series_terms,
    )


def verify_value_enclosure(witness, expression, variable, region):
    """Replay an enclosure against its exact formula, coordinate and region."""
    from .coverage_checker import _bound_matches
    from .coverage_contract import EnclosureWitness

    if type(witness) is not EnclosureWitness:
        return False
    try:
        return bool(
            _bound_matches(
                witness, sp.sympify(expression), sp.sympify(variable), region
            )
        )
    except (
        AttributeError,
        TypeError,
        ValueError,
        ArithmeticError,
        NotImplementedError,
    ):
        return False


def refine_root_cover(proof, *, policy=None):
    """Refine isolated single-root regions while retaining the original coverage.

    Only independently valid covers are accepted. Existing unresolved regions
    remain explicit. The policy limits contraction attempts and is checked
    between them; one symbolic contraction can overrun its wall-time budget.
    """
    from .adaptive_roots import _contract
    from .coverage_checker import check_coverage
    from .coverage_contract import CoverageProof
    from .coverage_search import _assemble
    from .enclosure_policy import EnclosurePolicy

    policy = EnclosurePolicy() if policy is None else policy
    if type(policy) is not EnclosurePolicy:
        raise TypeError("policy must be an EnclosurePolicy")
    if type(proof) is not CoverageProof or check_coverage(proof).certified is not True:
        raise ValueError("proof must be a valid root cover")
    leaves = []
    attempts = 0
    started = monotonic()
    for leaf in proof.leaves:
        available = attempts < policy.max_cells and (
            policy.seconds is None or monotonic() - started < policy.seconds
        )
        if leaf.root_count == 1 and available:
            attempts += 1
            leaves.extend(_contract(leaf, replace(policy, seconds=None)))
        else:
            leaves.append(leaf)
    unresolved = (
        ()
        if proof.unresolved is sp.S.EmptySet
        else (
            proof.unresolved.args
            if isinstance(proof.unresolved, sp.Union)
            else (proof.unresolved,)
        )
    )
    refined = _assemble(proof.context, leaves, unresolved, proof.exhaustion)
    return refined if check_coverage(refined).certified is True else proof


def verify_real_identity(left, right):
    """Return True only when an exact identity is established; unresolved is False."""
    from .exactness import certify_identity_equal

    result = certify_identity_equal(left, right)
    if result is None:
        reduced = sp.simplify(sp.sympify(left) - sp.sympify(right))
        return certify_identity_equal(reduced, 0) is True
    return result is True


def pack_analysis_data(value):
    """Serialize trusted worker data while preserving held formulas and source holes."""
    from ._source_transport import _dumps

    return _dumps(value)
