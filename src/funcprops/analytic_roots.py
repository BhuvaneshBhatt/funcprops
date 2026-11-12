"""Exact real roots and values specified by checked isolating intervals."""

from functools import lru_cache

import sympy as sp


def _function(function):
    if not isinstance(function, sp.Lambda) or len(function.variables) != 1:
        raise TypeError("function must be a scalar Lambda")
    x = function.variables[0]
    if (
        not isinstance(x, sp.Symbol)
        or not isinstance(function.expr, sp.Expr)
        or function.free_symbols
        or function.expr.has(sp.Float)
        or x.is_real is False
    ):
        raise ValueError("an exact fixed real function is required")
    return function.expr, x


@lru_cache(maxsize=512)
def _root_cover(function, interval):
    """Construct a small checked cover; cached evidence is replayed separately."""
    from .adaptive_roots import adaptive_root_coverage
    from .coverage_checker import check_coverage
    from .enclosure_policy import EnclosurePolicy

    f, x = _function(function)
    if isinstance(interval, sp.Interval):
        rational = all(
            end.is_Rational is True for end in (interval.start, interval.end)
        )
    else:
        rational = (
            isinstance(interval, sp.FiniteSet)
            and len(interval) == 1
            and next(iter(interval)).is_Rational is True
        )
    if not rational:
        raise ValueError("a finite rational isolating region is required")
    proof = adaptive_root_coverage(
        f,
        x,
        interval,
        policy=EnclosurePolicy(
            precision=40, max_cells=64, max_depth=8, max_refinements=1
        ),
    ).proof
    if (
        not proof.complete
        or proof.context.effective != interval
        or proof.root_count != 1
        or check_coverage(proof).certified is not True
    ):
        raise ValueError("the interval must contain exactly one verified root")
    return proof


def root_region(evidence):
    """Return the region whose single-root claim is carried by coverage evidence."""
    from .coverage_contract import CoverageLeaf

    return (
        evidence.region
        if type(evidence) is CoverageLeaf
        else evidence.context.effective
    )


def check_root_evidence(evidence, function, region=None):
    """Bind a checked unique-root leaf or complete cover to an exact function."""
    from .coverage_checker import check_coverage, check_leaf
    from .coverage_contract import CoverageLeaf, CoverageProof
    from .source_syntax import same_data

    if type(evidence) not in (CoverageLeaf, CoverageProof):
        return False
    f, x = _function(function)
    context = evidence.context
    return (
        evidence.root_count == 1
        and (type(evidence) is CoverageLeaf or evidence.complete)
        and same_data((evidence.expression, evidence.variable), (f, x))
        and not context.substitutions
        and context.parameter_guard is sp.true
        and context.branch_context is None
        and (region is None or root_region(evidence) == region)
        and (
            check_leaf(evidence)
            if type(evidence) is CoverageLeaf
            else check_coverage(evidence)
        ).certified
        is True
    )


def _explicit_location(evidence):
    """Recover a kernel-bound exact coordinate through location/factor witnesses."""
    from .coverage_contract import (
        CoverageLeaf,
        LocatedSubsetWitness,
        PowerFactorWitness,
        SourceFormulaWitness,
    )

    if type(evidence) is not CoverageLeaf or evidence.root_count != 1:
        return None
    if len(evidence.roots) == 1:
        point = evidence.roots[0][0]
    elif type(evidence.witness) is LocatedSubsetWitness:
        locator = evidence.witness.locator
        point = (
            next(iter(locator))
            if isinstance(locator, sp.FiniteSet) and len(locator) == 1
            else _explicit_location(evidence.witness.parent)
        )
    elif type(evidence.witness) is PowerFactorWitness:
        point = _explicit_location(evidence.witness.base_proof)
    elif type(evidence.witness) is SourceFormulaWitness:
        point = _explicit_location(evidence.witness.proof)
    else:
        point = None
    if point is None or evidence.region.contains(point) is not sp.true:
        return None
    from .exactness import certify_zero

    return (
        point
        if certify_zero(evidence.expression.subs(evidence.variable, point)) is True
        else None
    )


@lru_cache(maxsize=1024)
def _refined_root(function, interval, precision, evidence=None):
    """Refine stored uniqueness evidence with checked Newton subset witnesses."""
    from .analysis import derivative_on_domain, value_enclosure
    from .coverage_contract import CoverageLeaf, LocatedSubsetWitness, NewtonWitness
    from .coverage_search import _accepted
    from .multiple_root_checker import location_base

    original = _root_cover(function, interval) if evidence is None else evidence
    leaf = (
        original
        if type(original) is CoverageLeaf
        else next((a for a in original.leaves if a.root_count == 1), None)
    )
    if leaf is None:
        return original
    tolerance = sp.Rational(1, 10) ** precision
    for _ in range(precision + 8):
        region = leaf.region
        if isinstance(region, sp.FiniteSet) or region.measure <= tolerance:
            break
        if not isinstance(region, sp.Interval):
            break
        exact = _explicit_location(leaf)
        if exact is not None:
            value = leaf.expression.subs(leaf.variable, exact)
            point = _accepted(
                leaf.context, sp.FiniteSet(exact), "point-zero", 1, None, value
            )
            if point is not None:
                return point
            break
        else:
            # A multiple-root witness can expose a simple zero-location factor.
            f, x = location_base(leaf), leaf.variable
            if f is None:
                break
            derivative = derivative_on_domain(f, x, region.closure)
            if derivative is None:
                break
            middle = (region.start + region.end) / 2
            df = value_enclosure(
                derivative, x, region.closure, precision=precision + 16
            )
            fm = value_enclosure(f, x, sp.FiniteSet(middle), precision=precision + 16)
            if df is None or fm is None or df.lower <= 0 <= df.upper:
                break
            ratios = [a / b for a in (fm.lower, fm.upper) for b in (df.lower, df.upper)]
            low, high = middle - max(ratios), middle - min(ratios)
            narrowed = sp.Intersection(region, sp.Interval(low, high))
            locator = NewtonWitness(middle, df, fm, low, high)
        if narrowed is sp.S.EmptySet or narrowed == region:
            break
        child = _accepted(
            leaf.context,
            narrowed,
            "located-subset",
            1,
            leaf.multiplicity_count,
            LocatedSubsetWitness(leaf, locator),
        )
        if child is None:
            break
        leaf = child
    return leaf


def _restore_root(function, interval, evidence, refinement=None):
    root = ImplicitRealRoot(function, interval, evidence=evidence)
    if refinement is not None:
        if (
            not check_root_evidence(refinement, function)
            or root_region(refinement).is_subset(interval) is not True
        ):
            raise ValueError("invalid transported root refinement")
        root._refinement = refinement
    return root


def _same_location(first, second, function, variable):
    """Compare proved root-containing regions using inclusion or monotonicity."""
    if first.is_subset(second) is True or second.is_subset(first) is True:
        return True
    if sp.Intersection(first, second) is sp.S.EmptySet:
        return False
    union = sp.Union(first, second)
    if isinstance(union, sp.Interval):
        from .analysis import derivative_on_domain, value_enclosure

        derivative = derivative_on_domain(function, variable, union.closure)
        bound = (
            value_enclosure(derivative, variable, union.closure)
            if derivative is not None
            else None
        )
        if bound is not None and (bound.lower > 0 or bound.upper < 0):
            return True
    return None


class ImplicitRealRoot(sp.Expr):
    """An exact unique real zero specified by a checked isolating interval.

    Direct construction searches a rational interval. from_cover reuses checked
    evidence and accepts exact nonrational bounds without another search.
    The bound coordinate is carried by a Lambda, not a free symbol.
    Different isolating descriptions need not compare equal structurally.
    """

    is_real = True
    is_finite = True
    is_number = True
    __slots__ = ("_proof", "_refinement")

    def __new__(cls, function, interval, *, evidence=None):
        function = sp.sympify(function)
        interval = sp.sympify(interval)
        if not isinstance(interval, sp.Interval):
            raise ValueError("a finite rational isolating interval is required")
        if evidence is None:
            proof = _root_cover(function, interval)
        else:
            _function(function)
            if any(
                end.is_finite is not True
                or end.is_real is not True
                or end.has(sp.Float)
                for end in (interval.start, interval.end)
            ) or not check_root_evidence(evidence, function, interval):
                raise ValueError(
                    "evidence must prove a unique root on the exact isolating interval"
                )
            proof = evidence
        obj = sp.Expr.__new__(cls, function, interval)
        obj._proof = proof
        obj._refinement = None
        return obj

    @property
    def function(self):
        """Bound function specifying the exact root or value."""
        return self.args[0]

    @property
    def interval(self):
        """Isolating interval carried by the exact root description."""
        return self.args[1]

    @property
    def free_symbols(self):
        """Free coordinates; implicitly bound root coordinates are excluded."""
        return set()

    @classmethod
    def from_cover(cls, cover, region=None):
        """Reuse a checked unique-root cover or one of its owned leaf regions.

        Exact nonrational interval bounds are accepted without a new root search.
        The selected region must itself carry an exhaustive single-root claim.
        """
        from .coverage_contract import CoverageLeaf, CoverageProof

        if type(cover) is CoverageProof and region is not None:
            if not cover.verify():
                raise ValueError("invalid coverage proof")
            cover = next(
                (a for a in cover.leaves if a.region == region and a.root_count == 1),
                None,
            )
        if type(cover) not in (CoverageLeaf, CoverageProof):
            raise ValueError("a checked unique-root leaf or cover is required")
        region = root_region(cover)
        return cls(sp.Lambda(cover.variable, cover.expression), region, evidence=cover)

    @property
    def expression(self):
        """Expression to which the stored evidence applies."""
        return self.function.expr

    @property
    def variable(self):
        """Coordinate used by the source and its evidence."""
        return self.function.variables[0]

    @property
    def evidence(self):
        """Premises retained for checking the result."""
        return self._proof

    def __reduce_ex__(self, protocol):
        return _restore_root, (
            self.function,
            self.interval,
            self._proof,
            self._refinement,
        )

    def verify(self):
        """Replay the stored uniqueness evidence without root discovery."""
        try:
            return type(self) is ImplicitRealRoot and check_root_evidence(
                self._proof, self.function, self.interval
            )
        except (
            TypeError,
            ValueError,
            AttributeError,
            ArithmeticError,
            NotImplementedError,
        ):
            return False

    def same_root(self, other):
        """Return True/False for proved same/distinct roots, otherwise None."""
        if (
            type(other) is not ImplicitRealRoot
            or not self.verify()
            or not other.verify()
        ):
            return None
        if not self.function.dummy_eq(other.function):
            return None
        first, second = self.enclosure(12), other.enclosure(12)
        return _same_location(first, second, self.expression, self.variable)

    def _refined_evidence(self, precision):
        """Reuse the strongest checked contraction held by this number object."""
        seed = self._proof if self._refinement is None else self._refinement
        if root_region(seed).measure <= sp.Rational(1, 10) ** precision:
            return seed
        result = _refined_root(self.function, self.interval, precision, seed)
        self._refinement = result
        return result

    def enclosure(self, precision=30):
        """Return a checked isolating interval or exact singleton containing this root."""
        if type(precision) is not int or precision < 2:
            raise ValueError("precision must be an integer at least two")
        return root_region(self._refined_evidence(precision))

    def _eval_subs(self, old, new):
        return self

    def _xreplace(self, rule):
        return (rule[self], True) if self in rule else (self, False)

    def _eval_evalf(self, prec):
        digits = max(2, int(prec * 0.30103) + 4)
        region = self.enclosure(digits)
        if isinstance(region, sp.FiniteSet):
            return next(iter(region))._eval_evalf(prec)
        if region.measure > sp.Rational(1, 10) ** digits:
            return None
        return ((region.start + region.end) / 2)._eval_evalf(prec)

    def _eval_is_positive(self):
        if self.interval.start > 0 or (
            self.interval.start == 0 and self.interval.left_open
        ):
            return True
        if self.interval.end <= 0:
            return False

    def _eval_is_negative(self):
        if self.interval.end < 0 or (
            self.interval.end == 0 and self.interval.right_open
        ):
            return True
        if self.interval.start >= 0:
            return False


def implicit_real_root(expression, variable, interval):
    """Return the exact unique root on a checked finite rational interval."""
    return ImplicitRealRoot(
        sp.Lambda(sp.sympify(variable), sp.sympify(expression)), interval
    )


class CriticalValue(sp.Expr):
    """An exact function value at a verified implicit real root."""

    is_real = True
    is_finite = True
    is_number = True

    def __new__(cls, function, root):
        from .analysis import derivative_on_domain

        function = sp.sympify(function)
        f, x = _function(function)
        if type(root) is not ImplicitRealRoot or not root.verify():
            raise ValueError("root must be a verified ImplicitRealRoot")
        if derivative_on_domain(f, x, root.interval, 0) is None:
            raise ValueError("function must be real and defined throughout the bracket")
        return sp.Expr.__new__(cls, function, root)

    @property
    def function(self):
        """Bound function specifying the exact root or value."""
        return self.args[0]

    @property
    def root(self):
        """Exact root description used to define this value."""
        return self.args[1]

    @property
    def free_symbols(self):
        """Free coordinates; implicitly bound root coordinates are excluded."""
        return set()

    def enclosure(self, precision=30):
        """Return outward value bounds with replayable root and image evidence."""
        from .analysis import value_enclosure
        from .real_images.critical_values import CriticalValueEnclosure

        if type(precision) is not int or precision < 2:
            raise ValueError("precision must be an integer at least two")
        cover = self.root._refined_evidence(precision + 4)
        f, x = _function(self.function)
        witness = value_enclosure(
            f, x, root_region(cover).closure, precision=precision + 8
        )
        if witness is None:
            return None
        return CriticalValueEnclosure(self, cover, witness)

    def _eval_subs(self, old, new):
        return self

    def _xreplace(self, rule):
        return (rule[self], True) if self in rule else (self, False)

    def _eval_evalf(self, prec):
        digits = max(2, int(prec * 0.30103) + 4)
        evidence = self.enclosure(digits)
        if (
            evidence is None
            or evidence.upper - evidence.lower > sp.Rational(1, 10) ** digits
        ):
            return None
        return ((evidence.lower + evidence.upper) / 2)._eval_evalf(prec)

    def _eval_is_positive(self):
        evidence = self.enclosure(8)
        if evidence is not None:
            return (
                True if evidence.lower > 0 else False if evidence.upper <= 0 else None
            )

    def _eval_is_negative(self):
        evidence = self.enclosure(8)
        if evidence is not None:
            return (
                True if evidence.upper < 0 else False if evidence.lower >= 0 else None
            )


def critical_value(expression, variable, root):
    """Represent an exact real function value at an implicit root."""
    return CriticalValue(sp.Lambda(sp.sympify(variable), sp.sympify(expression)), root)


def critical_values_equal(first, second):
    """Prove selected common-root or reflected-root value identities.

    None denotes an unproved identity. Structural equality, shared unique roots
    and a verified reflection symmetry are supported; arbitrary analytic value
    equality is outside this rule.
    """
    from .analysis import verify_real_identity

    if not isinstance(first, sp.Expr) or not isinstance(second, sp.Expr):
        return None
    if first == second:
        return True
    if type(first) is not CriticalValue or type(second) is not CriticalValue:
        return None
    r, q = first.root, second.root
    if not r.verify() or not q.verify():
        return None
    x, z = first.function.variables[0], second.function.variables[0]
    if first.function.dummy_eq(second.function) and r.same_root(q) is True:
        return True
    rf = r.expression.subs(r.variable, -z)
    if not (
        verify_real_identity(rf, q.expression)
        or verify_real_identity(rf, -q.expression)
    ):
        return None
    if not verify_real_identity(first.function.expr.subs(x, -z), second.function.expr):
        return None
    interval = r.enclosure(12)
    reflected = (
        sp.FiniteSet(*(-a for a in interval))
        if isinstance(interval, sp.FiniteSet)
        else sp.Interval(
            -interval.end, -interval.start, interval.right_open, interval.left_open
        )
    )
    return (
        True
        if _same_location(reflected, q.enclosure(12), q.expression, q.variable) is True
        else None
    )
