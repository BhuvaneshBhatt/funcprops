"""Independent assembly of property claims from source, roots and value orders.

The supported class consists of finite real components with C1 extensions of
all interval branches to their closures. No search or root enumeration occurs
in replay. Endpoint values and singleton seams are explicit candidates.
"""

import itertools

import sympy as sp

from .coverage_cells import source_cells
from .coverage_checker import (
    _bound_matches,
    _formula_equal,
    check_coverage,
    check_enclosure,
    derivative_formula_on_cell,
    regular_on_cell,
)
from .coverage_contract import (
    CheckOutcome,
    CheckResult,
    CoverageProof,
    EnclosureWitness,
)
from .domain_tracking import DomainRecord
from .enclosures import preserve_replace
from .property_contract import PropertyConclusion, PropertyCoverageProof, PropertyPiece
from .source_syntax import normalize_arithmetic, same_data

_AUX = sp.Symbol("_property_order", real=True)
_NAMES = ("range", "minimum", "maximum", "sign", "monotonicity")
_ERRORS = (
    AttributeError,
    TypeError,
    ValueError,
    ArithmeticError,
    NotImplementedError,
    sp.PolynomialError,
)


def property_cells(f, x, D):
    """Extract exact owned real cells from a domain record."""

    cells = source_cells(f, x, D)
    if cells is None:
        return None
    result = []
    for g, region in cells:
        for part in region.args if isinstance(region, sp.Union) else (region,):
            if part is sp.S.EmptySet:
                continue
            if not isinstance(part, (sp.Interval, sp.FiniteSet)):
                return None
            result.append((g, part))
    return tuple(result)


def value_at(f, x, point):
    """Evaluate a source at a site or its indicated one-sided limit."""

    return normalize_arithmetic(preserve_replace(f, {x: point})).doit()


def geometry(piece, x):
    """Extract the owned interval and point geometry of a property proof."""

    D = piece.domain
    if isinstance(D, sp.FiniteSet):
        return None
    closed = sp.Interval(D.start, D.end)
    if not regular_on_cell(piece.expression, x, closed, 1):
        return None
    derivative = derivative_formula_on_cell(piece.expression, x, closed, 1)
    if derivative is None:
        return None
    return closed, derivative, sp.Interval.open(D.start, D.end)


def locations(coverage, points, g, x, interior):
    """A checked total count plus equally many distinct exact zeros is exhaustive."""
    if coverage is None:
        if points is not None:
            raise ValueError("locations-without-cover")
        return None
    if (
        not isinstance(coverage, CoverageProof)
        or coverage.expression != g
        or coverage.variable != x
        or coverage.context.requested != interior
        or coverage.context.effective != interior
        or check_coverage(coverage).certified is not True
    ):
        raise ValueError("critical-or-root-cover-mismatch")
    if points is None:
        return None
    if (
        not isinstance(points, tuple)
        or not coverage.complete
        or (
            type(coverage.root_count) is not int
            and not isinstance(coverage.root_count, sp.Integer)
        )
        or len(points) != coverage.root_count
        or len(set(points)) != len(points)
    ):
        raise ValueError("nonexhaustive-locations")
    for point in points:
        if (
            not isinstance(point, sp.Expr)
            or point.free_symbols
            or point.has(sp.Float)
            or point.is_real is not True
            or point.is_finite is not True
            or interior.contains(point) is not sp.S.true
            or not _formula_equal(value_at(g, x, point), sp.S.Zero)
        ):
            raise ValueError("false-root-location")
    if any((a < b) is not sp.S.true for a, b in itertools.pairwise(points)):
        raise ValueError("unordered-root-locations")
    return points


def cells_between(D, points):
    """Split a component at exact ordered critical points with endpoint ownership."""

    cuts = (D.start, *points, D.end)
    return tuple(sp.Interval.open(a, b) for a, b in itertools.pairwise(cuts))


def samples_status(samples, g, x, cells):
    """Check sample signs used by a supported property assembly theorem."""

    if not isinstance(samples, tuple):
        raise ValueError("mutable-samples")
    if not samples:
        return None
    if len(samples) != len(cells):
        raise ValueError("sample-partition-mismatch")
    signs = []
    for bound, cell in zip(samples, cells, strict=True):
        point = (cell.start + cell.end) / 2
        if not _bound_matches(bound, g, x, sp.FiniteSet(point)):
            raise ValueError("false-sign-sample")
        if bound.lower > 0:
            signs.append(1)
        elif bound.upper < 0:
            signs.append(-1)
        else:
            raise ValueError("unproved-sample-sign")
    return tuple(zip(cells, signs, strict=True))


def candidates(proof):
    """Canonical candidates: (piece index, point, value, attained, constant region)."""
    out = []
    x = proof.variable
    for i, piece in enumerate(proof.pieces):
        f, D = piece.expression, piece.domain
        if isinstance(D, sp.FiniteSet):
            for p in sorted(D, key=sp.default_sort_key):
                out.append((i, p, value_at(f, x, p), True, None))
            continue
        data = geometry(piece, x)
        if data is None:
            return None
        _closed, derivative, interior = data
        critical = locations(
            piece.critical_coverage, piece.critical_points, derivative, x, interior
        )
        # The identically zero derivative has every interior point critical;
        # its raw regularity/identity proves a constant branch directly.
        constant = _formula_equal(derivative, sp.S.Zero)
        if critical is None and not constant:
            return None
        points = (D.start, *(critical or ()), D.end)
        for p in points:
            out.append((i, p, value_at(f, x, p), D.contains(p) is sp.S.true, None))
        if constant:
            p = (D.start + D.end) / 2
            out.append((i, p, value_at(f, x, p), True, D))
    return tuple(out)


def _order(proof, values):
    order, comparisons = proof.candidate_order, proof.comparisons
    if order is None:
        if comparisons:
            raise ValueError("comparisons-without-order")
        return None
    if (
        values is None
        or not isinstance(order, tuple)
        or not isinstance(comparisons, tuple)
        or any(type(i) is not int for i in order)
        or set(order) != set(range(len(values)))
        or len(order) != len(values)
        or len(comparisons) != max(0, len(order) - 1)
    ):
        raise ValueError("candidate-order-mismatch")
    for left, right, bound in zip(order, order[1:], comparisons, strict=False):
        a, b = values[left][2], values[right][2]
        if bound is None:
            if not _formula_equal(a, b):
                raise ValueError("unproved-equal-values")
        elif (
            not _bound_matches(bound, a - b, _AUX, sp.FiniteSet(0)) or bound.upper >= 0
        ):
            raise ValueError("unproved-value-order")
    return order


def _point_sign(value, proof):
    if _formula_equal(value, sp.S.Zero):
        return 0
    # Endpoint comparison to zero uses the same supplied, replayed sample
    # witnesses as other signs; no numeric or assumptions-based sign oracle.
    for piece in proof.pieces:
        for bound in piece.sign_samples:
            if _bound_matches(bound, value, _AUX, sp.FiniteSet(0)):
                return 1 if bound.lower > 0 else -1 if bound.upper < 0 else None
    return None


def derive_conclusions(proof):
    """Deterministic theorem assembly, also used to label a producer's proposal."""
    values = candidates(proof)
    order = _order(proof, values)
    result = {}
    if order is not None:
        images = []
        for i, piece in enumerate(proof.pieces):
            local = [k for k in order if values[k][0] == i]
            if not local:
                continue
            lo, hi = values[local[0]][2], values[local[-1]][2]
            attained_lo = any(
                values[k][3] and _formula_equal(values[k][2], lo) for k in local
            )
            attained_hi = any(
                values[k][3] and _formula_equal(values[k][2], hi) for k in local
            )
            images.append(
                sp.FiniteSet(*(values[k][2] for k in local))
                if isinstance(piece.domain, sp.FiniteSet)
                else sp.Interval(lo, hi, not attained_lo, not attained_hi)
            )
        image = (
            sp.Union(*images, evaluate=False)
            if len(images) > 1
            else (images[0] if images else sp.S.EmptySet)
        )
        result["range"] = PropertyConclusion("range", image, True)
        for name, index in (("minimum", 0), ("maximum", -1)):
            if not order:
                value, owners = (sp.oo if name == "minimum" else -sp.oo), sp.S.EmptySet
            else:
                value = values[order[index]][2]
                owners = sp.Union(
                    *(
                        v[4] if v[4] is not None else sp.FiniteSet(v[1])
                        for v in values
                        if v[3] and _formula_equal(v[2], value)
                    )
                )
            result[name] = PropertyConclusion(name, (value, owners), True)
    else:
        for name in ("range", "minimum", "maximum"):
            result[name] = PropertyConclusion(
                name, obligations=("incomplete-critical-geometry-or-candidate-order",)
            )
    sign_regions, monotone_regions = [], []
    sign_ok, monotone_ok = True, True
    for piece in proof.pieces:
        f, D, x = piece.expression, piece.domain, proof.variable
        if isinstance(D, sp.FiniteSet):
            if (
                piece.critical_coverage is not None
                or piece.critical_points is not None
                or piece.zero_coverage is not None
                or piece.zero_points is not None
                or piece.derivative_samples
            ):
                raise ValueError("unexpected-point-geometry")
            for point in D:
                sign = _point_sign(value_at(f, x, point), proof)
                if sign is None:
                    sign_ok = False
                else:
                    sign_regions.append((sp.FiniteSet(point), sign))
                monotone_regions.append((sp.FiniteSet(point), None))
            continue
        data = geometry(piece, x)
        if data is None:
            if (
                piece.critical_coverage is not None
                or piece.zero_coverage is not None
                or piece.critical_points is not None
                or piece.zero_points is not None
                or piece.derivative_samples
            ):
                raise ValueError("geometry-without-regularity")
            sign_ok = monotone_ok = False
            continue
        _, derivative, interior = data
        for name, g, coverage, points, samples, regions in (
            (
                "sign",
                f,
                piece.zero_coverage,
                piece.zero_points,
                piece.sign_samples,
                sign_regions,
            ),
            (
                "monotonicity",
                derivative,
                piece.critical_coverage,
                piece.critical_points,
                piece.derivative_samples,
                monotone_regions,
            ),
        ):
            roots = locations(coverage, points, g, x, interior)
            # Endpoint sign witnesses are appended to sign_samples and checked
            # separately; the interval samples always form its prefix.
            constzero = _formula_equal(g, sp.S.Zero)
            if constzero:
                regions.append((interior, 0))
            elif roots is None:
                if name == "sign":
                    sign_ok = False
                else:
                    monotone_ok = False
            else:
                cells = cells_between(D, roots)
                interval_samples = samples[: len(cells)] if name == "sign" else samples
                status = samples_status(interval_samples, g, x, cells)
                if status is None:
                    if name == "sign":
                        sign_ok = False
                    else:
                        monotone_ok = False
                else:
                    regions.extend(status)
                    regions.extend((sp.FiniteSet(p), 0) for p in roots)
        for point, opened in ((D.start, D.left_open), (D.end, D.right_open)):
            if not opened:
                sign = _point_sign(value_at(f, x, point), proof)
                if sign is None:
                    sign_ok = False
                else:
                    sign_regions.append((sp.FiniteSet(point), sign))
                monotone_regions.append((sp.FiniteSet(point), None))
    for name, ok, regions in (
        ("sign", sign_ok, sign_regions),
        ("monotonicity", monotone_ok, monotone_regions),
    ):
        if ok and sp.Union(*(D for D, _ in regions)) != proof.domain_record.effective:
            raise ValueError("incomplete-property-partition")
        result[name] = PropertyConclusion(
            name,
            tuple(regions) if ok else None,
            ok,
            () if ok else ("incomplete-root-or-sign-partition",),
        )
    return tuple(result[name] for name in _NAMES)


def check_property_coverage(proof):
    """Check the stored property coverage premises and report their replay outcome."""

    reject = CheckResult(CheckOutcome.REJECTED, False, False, "false-property-premise")
    try:
        if (
            type(proof) is not PropertyCoverageProof
            or type(proof.schema_version) is not int
            or proof.schema_version != 1
        ):
            return CheckResult(
                CheckOutcome.UNSUPPORTED, None, False, "unsupported-property-schema"
            )
        f, x, record = proof.expression, proof.variable, proof.domain_record
        if (
            not isinstance(x, sp.Symbol)
            or f.free_symbols - {x}
            or f.has(sp.Float)
            or proof.source_syntax != sp.srepr(f)
            or proof.coordinate_assumptions != tuple(sorted(x.assumptions0.items()))
            or type(record) is not DomainRecord
            or record.expression != f
            or record.variable != x
            or record.requested != proof.requested
            or type(proof.tested) is not int
            or proof.tested < 0
            or proof.exhaustion not in (None, "cell-budget", "wall-budget")
        ):
            return reject
        if not record.complete:
            return (
                CheckResult(
                    CheckOutcome.UNSUPPORTED, None, False, "unresolved-source-domain"
                )
                if not proof.complete
                else reject
            )
        if (
            not record.verify()
            or not isinstance(proof.pieces, tuple)
            or not isinstance(proof.conclusions, tuple)
            or any(
                type(p) is not PropertyPiece
                or not isinstance(p.sign_samples, tuple)
                or not isinstance(p.derivative_samples, tuple)
                for p in proof.pieces
            )
            or any(type(c) is not PropertyConclusion for c in proof.conclusions)
        ):
            return reject
        cells = property_cells(f, x, record.effective)
        if cells is None:
            return (
                CheckResult(
                    CheckOutcome.UNSUPPORTED, None, False, "unsupported-property-domain"
                )
                if not proof.complete
                else reject
            )
        if tuple((p.expression, p.domain) for p in proof.pieces) != tuple(
            (g, D) for g, D in cells if D is not sp.S.EmptySet
        ):
            return reject
        if any(
            isinstance(D, sp.Interval)
            and (D.start.is_finite is not True or D.end.is_finite is not True)
            for _, D in cells
        ):
            return (
                CheckResult(
                    CheckOutcome.UNSUPPORTED, None, False, "finite-components-required"
                )
                if not proof.complete
                else reject
            )
        # All supplied endpoint witnesses, including unused ones, must replay.
        for p in proof.pieces:
            for bound in p.sign_samples:
                if not isinstance(bound, EnclosureWitness) or not check_enclosure(
                    bound
                ):
                    return reject
        expected = derive_conclusions(proof)
        if not same_data(proof.conclusions, expected) or any(
            type(c.complete) is not bool or not isinstance(c.obligations, tuple)
            for c in proof.conclusions
        ):
            return reject
        complete = all(c.complete for c in expected)
        return CheckResult(
            CheckOutcome.COMPLETE
            if complete
            else CheckOutcome.EXHAUSTED
            if proof.exhaustion
            else CheckOutcome.LOCAL_VALID,
            True,
            complete,
            proof.exhaustion,
        )
    except _ERRORS:
        return reject
