"""Exact zero implications and orders at an implicitly isolated simple root.

An entire identity proves a minimum order at the unique base zero. An exhaustive
component count equal to that order makes the location and order exact. No root
coordinate, analytic gcd or numerical coincidence test is involved.
"""

from dataclasses import dataclass

import sympy as sp

from .complex_coverage import CoverageRectangle
from .complex_interval import entire_source
from .complex_newton import _ERRORS, _valid_region
from .coverage_contract import CheckOutcome, CheckResult
from .implicit_orders import ImplicitMultiplicityProof, ImplicitRootValueProof
from .source_syntax import differentiate


class _Replay:
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
            None if valid else "false-implicit-zero-premise",
        )


@dataclass(frozen=True)
class SharedZeroImplication(_Replay):
    """Prove a lower zero order at an implicitly isolated base root."""

    expression: sp.Expr
    variable: sp.Symbol
    base_region: object
    minimum_order: int
    method: str = "factor"
    cofactor: sp.Expr | None = None
    outer_variable: sp.Symbol | None = None
    outer: sp.Expr | None = None
    jets: tuple = ()
    schema_version: int = 1

    @property
    def rectangle(self):
        return self.base_region.rectangle

    @property
    def scope(self):
        return "entire-zero-implication-at-one-implicit-simple-root"

    @property
    def complete(self):
        # A minimum order at the base zero does not exclude other zeros of F.
        return False

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        valid = self.verify()
        return CheckResult(
            CheckOutcome.LOCAL_VALID if valid else CheckOutcome.REJECTED,
            valid,
            False,
            None if valid else "false-implicit-zero-premise",
        )

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return _valid_implication(self, {})


def _valid_implication(c, memo):
    try:
        if (
            type(c) is not SharedZeroImplication
            or type(c.schema_version) is not int
            or c.schema_version != 1
            or type(c.minimum_order) is not int
            or c.minimum_order < 1
            or not entire_source(c.expression, c.variable)
            or c.expression.has(sp.Float)
            or c.expression.free_symbols - {c.variable}
            or type(c.jets) is not tuple
        ):
            return False
        b = c.base_region
        if (
            b.variable != c.variable
            or not _valid_region(b, b.expression, c.variable, memo)
            or b.zero_count != 1
            or type(b.rectangle) is not CoverageRectangle
        ):
            return False
        if c.method == "factor":
            return (
                c.outer_variable is None
                and c.outer is None
                and not c.jets
                and isinstance(c.cofactor, sp.Expr)
                and entire_source(c.cofactor, c.variable)
                and not c.cofactor.has(sp.Float)
                and not c.cofactor.free_symbols - {c.variable}
                and sp.expand(c.expression - b.expression**c.minimum_order * c.cofactor)
                == 0
            )
        if c.method != "composition" or c.cofactor is not None:
            return False
        u, h = c.outer_variable, c.outer
        if (
            type(u) is not sp.Symbol
            or u == c.variable
            or u.assumptions0 != {"commutative": True}
            or not entire_source(h, u)
            or h.has(sp.Float)
            or h.free_symbols - {u}
            or len(c.jets) != c.minimum_order
            or sp.expand(c.expression - h.xreplace({u: b.expression})) != 0
        ):
            return False
        jets = tuple(differentiate(h, u, k).subs(u, 0) for k in range(c.minimum_order))
        return c.jets == jets and all(v == 0 for v in jets)
    except (*_ERRORS, sp.PolynomialError):
        return False


@dataclass(frozen=True)
class SharedZeroOrderProof(_Replay):
    """Combine a shared-zero implication with an exhaustive count to prove exact order."""

    parent: object
    implication: (
        SharedZeroImplication | ImplicitRootValueProof | ImplicitMultiplicityProof
    )
    schema_version: int = 1

    @property
    def expression(self):
        return self.parent.expression

    @property
    def variable(self):
        return self.parent.variable

    @property
    def rectangle(self):
        return self.parent.rectangle

    @property
    def base_region(self):
        return self.implication.base_region

    @property
    def zero_count(self):
        return self.parent.zero_count

    @property
    def known_distinct(self):
        return 1

    @property
    def multiplicity_count(self):
        return self.zero_count

    @property
    def root_count(self):
        return 1

    @property
    def scope(self):
        return "exhaustive-order-at-one-implicit-simple-root"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return _valid_shared_region(self, {})


@dataclass(frozen=True)
class SharedZeroRegion(_Replay):
    """Transfer a checked shared-order conclusion to a root or pole region."""

    order_proof: SharedZeroOrderProof
    base_region: object
    schema_version: int = 1

    @property
    def expression(self):
        return self.order_proof.expression

    @property
    def variable(self):
        return self.order_proof.variable

    @property
    def rectangle(self):
        return self.base_region.rectangle

    @property
    def zero_count(self):
        return self.order_proof.zero_count * self.base_region.zero_count

    @property
    def known_distinct(self):
        return self.base_region.zero_count

    @property
    def root_count(self):
        return self.known_distinct

    @property
    def multiplicity_count(self):
        return self.zero_count

    @property
    def scope(self):
        return "implicit-shared-zero-transferred-region-count"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return _valid_shared_region(self, {})


@dataclass(frozen=True)
class ComplexZeroSubsetProof(_Replay):
    """Transfer complex root exclusion from a checked parent region."""

    parent: object
    rectangle: CoverageRectangle
    schema_version: int = 1

    @property
    def expression(self):
        return self.parent.expression

    @property
    def variable(self):
        return self.parent.variable

    @property
    def zero_count(self):
        return 0

    @property
    def known_distinct(self):
        return 0

    @property
    def root_count(self):
        return 0

    @property
    def multiplicity_count(self):
        return 0

    @property
    def scope(self):
        return "entire-zero-free-closed-rectangle-subset"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return _valid_shared_region(self, {})


def _valid_shared_region(c, memo):
    key = id(c)
    if key in memo:
        return memo[key]
    memo[key] = False
    try:
        if type(c.schema_version) is not int or c.schema_version != 1:
            return False
        if type(c) is SharedZeroOrderProof:
            p, w = c.parent, c.implication
            valid = (
                _valid_region(p, p.expression, p.variable, memo)
                and valid_zero_implication(w, memo)
                and w.expression == p.expression
                and w.variable == p.variable
                and w.rectangle == p.rectangle
                and type(p.zero_count) is int
                and p.zero_count == w.minimum_order
            )
        elif type(c) is SharedZeroRegion:
            p, b = c.order_proof, c.base_region
            valid = (
                type(p) is SharedZeroOrderProof
                and _valid_shared_region(p, memo)
                and _valid_region(b, p.base_region.expression, p.variable, memo)
                and b.zero_count in (0, 1)
                and p.rectangle.contains_rectangle(b.rectangle)
            )
        elif type(c) is ComplexZeroSubsetProof:
            p = c.parent
            valid = (
                _valid_region(p, p.expression, p.variable, memo)
                and p.zero_count == 0
                and type(c.rectangle) is CoverageRectangle
                and c.rectangle.valid()
                and p.rectangle.contains_rectangle(c.rectangle)
            )
        else:
            return False
        memo[key] = bool(valid)
        return bool(valid)
    except (*_ERRORS, sp.PolynomialError):
        return False


def valid_zero_implication(proof, memo):
    """Declared zero-at-base proof types; no provider callbacks are trusted."""
    from .implicit_orders import (
        ImplicitMultiplicityProof,
        ImplicitRootValueProof,
        _valid_local,
    )

    if type(proof) is SharedZeroImplication:
        return _valid_implication(proof, memo)
    if type(proof) in (ImplicitMultiplicityProof, ImplicitRootValueProof):
        return _valid_local(proof, memo) and proof.minimum_order >= 1
    return False


def shared_base(region):
    """Return a certified simple base for positive implicitly located counts."""
    from .complex_multiplicity import ComplexPowerRootRegion

    if type(region) in (SharedZeroOrderProof, SharedZeroRegion) and region.zero_count:
        return region.base_region
    if type(region) is ComplexPowerRootRegion and region.zero_count:
        return region.base_region
    return region if region.zero_count == 1 else None


def same_base(a, b):
    """Check whether shared-zero evidence refers to the same bound base root."""

    return (
        a is not None
        and b is not None
        and a.expression == b.expression
        and a.variable == b.variable
        and a.rectangle == b.rectangle
        and a.zero_count == b.zero_count == 1
    )


def _propose_implication(f, base, order, *, max_order=8):
    """Bounded caller charges this identity heuristic; replay never calls it."""
    z = base.variable
    if sp.count_ops(f) + sp.count_ops(base.expression) > 512:
        return None
    try:
        h = f / base.expression**order
        if not entire_source(h, z) and order <= max_order:
            h = sp.cancel(h)
        if entire_source(h, z):
            c = SharedZeroImplication(f, z, base, order, cofactor=h)
            if c.verify():
                return c
        if order > max_order:
            return None
        u = sp.Symbol("_shared_zero_coordinate")
        if u == z:
            u = sp.Symbol("_shared_zero_coordinate_2")
        outers = [f.xreplace({base.expression: u})]
        # Cancellation can expand exp(a+b). Recover an affine inner formula
        # through an exact polynomial substitution, never a transcendental inverse.
        atoms = (
            z,
            *sorted(base.expression.atoms(sp.Function), key=sp.default_sort_key),
        )
        for atom in atoms[:8]:
            try:
                polynomial = sp.Poly(base.expression, atom)
                if polynomial.degree() != 1:
                    continue
                slope, offset = polynomial.nth(1), polynomial.nth(0)
                if (
                    slope.has(z)
                    or offset.has(z)
                    or slope == 0
                    or not all(
                        isinstance(v, sp.Rational) for v in (sp.re(slope), sp.im(slope))
                    )
                ):
                    continue
                outers.append(
                    sp.expand(f.xreplace({atom: sp.expand((u - offset) / slope)}))
                )
            except sp.PolynomialError:
                continue
        for h in outers:
            if not h.free_symbols - {u} and entire_source(h, u):
                jets = tuple(differentiate(h, u, k).subs(u, 0) for k in range(order))
                c = SharedZeroImplication(
                    f,
                    z,
                    base,
                    order,
                    "composition",
                    outer_variable=u,
                    outer=h,
                    jets=jets,
                )
                if c.verify():
                    return c
    except (*_ERRORS, sp.PolynomialError):
        pass
    if order <= max_order:
        from .implicit_orders import certify_implicit_multiplicity, certify_root_value

        if order == 1:
            proof = certify_root_value(f, base)
            if proof is not None and proof.value == 0:
                return proof
        else:
            proof = certify_implicit_multiplicity(f, base, max_order=order)
            if proof.minimum_order == order:
                return proof
    return None
