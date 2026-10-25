"""Krawczyk refinement of a joint numerator/denominator/source ledger.

The chosen simple base transfers its count and all certified shared orders.
Other components need independent counts or checked zero-free subset transfers.
The four complement strips remain part of the exhaustive proof.
"""

from dataclasses import dataclass, replace

from .analytic_contours import (
    AnalyticContourCertificate,
    certify_analytic_contour,
    check_analytic_contour,
)
from .complex_coverage import CoverageRectangle, _partition
from .complex_multiplicity import ComplexPowerRootRegion
from .complex_newton import ComplexNewtonRefinement, _propose_refinement
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy
from .quotient_isolation import (
    _ERRORS,
    DenominatorExclusionProof,
    ExactLocalZeroProof,
    QuotientCellProof,
    QuotientIsolationProof,
    QuotientIsolationState,
    QuotientSourceProof,
    _cell_data,
    _valid_cell,
)
from .shared_zeros import (
    ComplexZeroSubsetProof,
    SharedZeroOrderProof,
    SharedZeroRegion,
    same_base,
    shared_base,
)


def _transfer(region, base, child):
    if region.zero_count == 0:
        return ComplexZeroSubsetProof(region, child.rectangle)
    if not same_base(shared_base(region), base):
        return None
    if type(region) is SharedZeroOrderProof:
        return SharedZeroRegion(region, child)
    if type(region) is SharedZeroRegion:
        return SharedZeroRegion(region.order_proof, child)
    if type(region) is ComplexPowerRootRegion:
        return ComplexPowerRootRegion(region.factorization, child)
    return child if region.expression == base.expression else None


def _source_evidence(source, parent, n, d):
    """Transfer only premises valid on this child; its counts are checked later."""
    cell = QuotientCellProof(n, d)
    if len(parent.exclusions) == len(source.guards):
        cell = replace(
            cell,
            exclusions=tuple(
                DenominatorExclusionProof(
                    w.expression, w.variable, cell.rectangle, w.contour
                )
                for w in parent.exclusions
            ),
        )
    locations = {}
    for name, old, r in (
        ("numerator_location", parent.numerator_location, n),
        ("denominator_location", parent.denominator_location, d),
    ):
        if old is not None and r.zero_count:
            loc = ExactLocalZeroProof(r, old.center, old.jets)
            if loc.verify():
                locations[name] = loc
    cell = replace(cell, **locations)
    if n.zero_count and d.zero_count == 0:
        if parent.guard_zero is not None:
            base = shared_base(n)
            if base is not None:
                from .implicit_orders import (
                    ImplicitMultiplicityProof,
                    ImplicitRootValueProof,
                    rebase_implicit_proof,
                )

                w = (
                    rebase_implicit_proof(parent.guard_zero, base)
                    if type(parent.guard_zero)
                    in (ImplicitRootValueProof, ImplicitMultiplicityProof)
                    else replace(parent.guard_zero, base_region=base)
                )
                if w is not None and w.verify():
                    cell = replace(cell, guard_zero=w)
        if parent.excluded_guard is not None:
            if parent.guard_cofactor is not None or cell.numerator_location is not None:
                cell = replace(
                    cell,
                    excluded_guard=parent.excluded_guard,
                    guard_cofactor=parent.guard_cofactor,
                )
    return cell


@dataclass(frozen=True)
class QuotientNewtonRefinement:
    """Refine a joint zero/pole cell while retaining source guards and counts."""

    source: QuotientSourceProof
    parent: QuotientCellProof
    refinement: ComplexNewtonRefinement
    cells: tuple
    guard_contours: tuple
    tested: int = 0
    schema_version: int = 1

    @property
    def expression(self):
        return self.source.expression

    @property
    def variable(self):
        return self.source.variable

    @property
    def rectangle(self):
        return self.parent.rectangle

    @property
    def child_rectangle(self):
        return self.refinement.child_rectangle

    @property
    def scope(self):
        return "joint-quotient-Krawczyk-divisor-and-source-transfer"

    @property
    def complete(self):
        return self.verify()

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        valid = self.verify()
        return CheckResult(
            CheckOutcome.COMPLETE if valid else CheckOutcome.REJECTED,
            valid,
            valid,
            None if valid else "false-joint-quotient-refinement",
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            if (
                type(self) is not QuotientNewtonRefinement
                or type(self.schema_version) is not int
                or self.schema_version != 1
                or type(self.source) is not QuotientSourceProof
                or not self.source.verify()
                or not _valid_cell(self.source, self.parent)
                or type(self.refinement) is not ComplexNewtonRefinement
                or not self.refinement.verify()
                or self.refinement.rectangle != self.rectangle
                or type(self.cells) is not tuple
                or len(self.cells) != 5
                or type(self.guard_contours) is not tuple
                or len(self.guard_contours) != len(self.source.guards)
                or type(self.tested) is not int
                or self.tested < 2
            ):
                return False
            for g, w in zip(self.source.guards, self.guard_contours, strict=True):
                if (
                    type(w) is not AnalyticContourCertificate
                    or not w.complete
                    or w.expression != g
                    or w.variable != self.variable
                    or type(w.rectangle) is not CoverageRectangle
                    or not w.rectangle.contains_rectangle(self.rectangle)
                    or check_analytic_contour(w).certified is not True
                ):
                    return False
            base = self.refinement.parent
            if not any(
                same_base(shared_base(r), base)
                for r in (self.parent.numerator, self.parent.denominator)
            ):
                return False
            for cell, b in zip(self.cells, self.refinement.regions, strict=True):
                if not _valid_cell(self.source, cell) or cell.rectangle != b.rectangle:
                    return False
                for old, new in (
                    (self.parent.numerator, cell.numerator),
                    (self.parent.denominator, cell.denominator),
                ):
                    expected = _transfer(old, base, b)
                    if expected is not None and new != expected:
                        return False
            if not _partition(self.rectangle, tuple(c.rectangle for c in self.cells)):
                return False
            if any(
                sum(getattr(c, name).zero_count for c in self.cells)
                != getattr(self.parent, name).zero_count
                for name in ("numerator", "denominator")
            ):
                return False
            before = _cell_data(self.source, self.parent)
            after = [_cell_data(self.source, c) for c in self.cells]
            if before is not None:
                if any(a is None for a in after) or any(
                    sum(a[k] for a in after) != before[k] for k in range(3)
                ):
                    return False
            return True
        except _ERRORS:
            return False


def _propose_quotient_refinement(
    source, parent, guards, policy, count, max_box_width=None, max_box_diameter=None
):
    used = 0
    for r in (parent.numerator, parent.denominator):
        if used + 2 > policy.max_cells:
            break
        base = shared_base(r)
        if base is None:
            continue
        refinement, spent = _propose_refinement(
            base,
            replace(policy, max_cells=policy.max_cells - used, seconds=None),
            max_box_width,
            max_box_diameter,
        )
        used += spent
        if refinement is None:
            continue
        cells = []
        for b in refinement.regions:
            records = []
            for component in (parent.numerator, parent.denominator):
                c = _transfer(component, base, b)
                if c is None:
                    c, spent = count(
                        component.expression,
                        b.rectangle,
                        max(0, policy.max_cells - used),
                    )
                    used += spent
                if c is None:
                    break
                records.append(c)
            if len(records) != 2:
                break
            cells.append(_source_evidence(source, parent, *records))
        if len(cells) != 5:
            continue
        proof = QuotientNewtonRefinement(
            source, parent, refinement, tuple(cells), guards, used
        )
        if proof.verify():
            return proof, used
    return None, used


def certify_quotient_refinement(parent, *, cell_index=0, policy=None):
    """Refine a checked joint cell, retaining both divisor counts and its holes."""
    if type(parent) is QuotientIsolationState:
        parent = parent.proof
    if type(parent) is not QuotientIsolationProof:
        raise ValueError("require a checked quotient isolation proof or state")
    if type(cell_index) is not int or not 0 <= cell_index < len(parent.cells):
        raise ValueError("invalid quotient cell index")
    policy = EnclosurePolicy() if policy is None else policy
    if type(policy) is not EnclosurePolicy:
        raise TypeError("policy must be an EnclosurePolicy")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_quotient_refinement",
            parent,
            (),
            {"cell_index": cell_index, "policy": replace(policy, seconds=None)},
            policy.seconds,
        )

    if not parent.verify():
        raise ValueError("require a checked quotient isolation proof or state")

    def count(f, rectangle, quota):
        if quota < 1:
            return None, 0
        c = certify_analytic_contour(
            f,
            parent.variable,
            rectangle.lower_left,
            rectangle.upper_right,
            policy=replace(policy, max_cells=quota),
        )
        return (c if c.complete else None), c.tested

    return _propose_quotient_refinement(
        parent.source,
        parent.cells[cell_index],
        parent.outer[2:],
        policy,
        count,
        parent.max_box_width,
        parent.max_box_diameter,
    )[0]
