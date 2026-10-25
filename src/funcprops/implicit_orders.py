"""Congruence proofs of values and derivative orders at one implicit root.

Exact identities and entire-function congruence establish equality at the
certified base zero. Nearby numerical roots never establish a common zero.
Local order is separate from exhaustive counts of other zeros in the rectangle.
"""

from dataclasses import dataclass, replace

import sympy as sp

from .complex_interval import (
    ENTIRE_PRIMITIVES,
    complex_box_taylor,
    entire_source,
    valid_taylor_coefficients,
)
from .complex_newton import _valid_region
from .coverage_contract import CheckOutcome, CheckResult
from .enclosure_policy import EnclosurePolicy
from .results import TruthValue
from .source_syntax import differentiate
from .work_budget import budgeted_operation

_ERRORS = (
    AttributeError,
    TypeError,
    ValueError,
    ArithmeticError,
    NotImplementedError,
    sp.PolynomialError,
)


def _analytic(f, z):
    if f == z:
        return True
    if not f.free_symbols:
        return not f.has(sp.Float) and f.is_finite is True
    if f.is_Add or f.is_Mul:
        return all(_analytic(a, z) for a in f.args)
    if f.is_Pow:
        return isinstance(f.exp, sp.Integer) and f.exp >= 0 and _analytic(f.base, z)
    return f.func in ENTIRE_PRIMITIVES and _analytic(f.args[0], z)


def _base(b, memo):
    return _valid_region(b, b.expression, b.variable, memo) and (
        b.zero_count == 1 or getattr(b, "known_distinct", None) == 1
    )


def _same(a, b):
    return (
        a.expression == b.expression
        and a.variable == b.variable
        and a.rectangle == b.rectangle
    )


class _Local:
    @property
    def complete(self):
        # This record alone does not exclude any other source zeros.
        return False

    @property
    def coverage_complete(self):
        return False

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True

    @property
    def certified(self):
        return self.verify()

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        valid = _valid_local(self, {})
        return CheckResult(
            CheckOutcome.LOCAL_VALID if valid else CheckOutcome.REJECTED,
            valid,
            False,
            None if valid else "false-implicit-root-premise",
        )


@dataclass(frozen=True)
class ImplicitJetWitness:
    """Enclose an analytic derivative jet on a whole complex root box."""

    expression: sp.Expr
    variable: sp.Symbol
    box: tuple
    order: int
    coefficients: tuple
    precision: int
    max_series_terms: int = 4096
    schema_version: int = 1

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            return (
                type(self) is ImplicitJetWitness
                and type(self.schema_version) is int
                and self.schema_version == 1
                and valid_taylor_coefficients(self.coefficients, self.order)
                and self.coefficients
                == complex_box_taylor(
                    self.expression,
                    self.variable,
                    self.box,
                    self.order,
                    precision=self.precision,
                    max_series_terms=self.max_series_terms,
                )
                and bool(self.coefficients)
            )
        except _ERRORS:
            return False

    @property
    def complete(self):
        return self.verify()

    @property
    def scope(self):
        return "normalized-entire-jets-on-closed-complex-box"


@dataclass(frozen=True)
class ImplicitRootValueProof(_Local):
    """Prove a value at an implicit root through exact analytic congruence identities."""

    expression: sp.Expr
    variable: sp.Symbol
    base_region: object
    value: sp.Expr
    quotient: sp.Expr
    children: tuple = ()
    power: int = 1
    schema_version: int = 1

    @property
    def rectangle(self):
        return self.base_region.rectangle

    @property
    def minimum_order(self):
        return int(self.value == 0)

    @property
    def scope(self):
        return "exact-value-at-one-certified-implicit-root"


@dataclass(frozen=True)
class ImplicitMultiplicityProof(_Local):
    """Prove an implicit root's order using zero jets and a nonzero leading jet."""

    expression: sp.Expr
    variable: sp.Symbol
    base_region: object
    zero_jets: tuple = ()
    taylor: ImplicitJetWitness | None = None
    order: int | None = None
    reason: str | None = None
    schema_version: int = 1
    leading_value: ImplicitRootValueProof | None = None

    @property
    def rectangle(self):
        return self.base_region.rectangle

    @property
    def minimum_order(self):
        return len(self.zero_jets)

    @property
    def order_complete(self):
        return self.order is not None

    @property
    def scope(self):
        return "local-zero-order-at-one-certified-implicit-root"


@dataclass(frozen=True)
class CommonZeroProof(_Local):
    """Relate two implicit roots with explicit shared-value and order evidence."""

    base_region: object
    expressions: tuple
    orders: tuple
    schema_version: int = 1

    @property
    def expression(self):
        return sp.Tuple(*self.expressions)

    @property
    def variable(self):
        return self.base_region.variable

    @property
    def rectangle(self):
        return self.base_region.rectangle

    @property
    def common_zero_certified(self):
        return bool(self.orders) and all(p.minimum_order >= 1 for p in self.orders)

    @property
    def orders_complete(self):
        return bool(self.orders) and all(p.order_complete for p in self.orders)

    @property
    def common_zero_excluded(self):
        return any(p.order == 0 for p in self.orders)

    @property
    def common_zero_status(self):
        return (
            TruthValue.FALSE
            if self.common_zero_excluded
            else TruthValue.TRUE
            if self.common_zero_certified
            else TruthValue.UNKNOWN
        )

    @property
    def multiplicities(self):
        return tuple(p.order for p in self.orders)

    @property
    def scope(self):
        return "common-zero-and-local-orders-at-one-implicit-root"


def _valid_local(c, memo):
    """Check exact implicit value identities and zero jets without searching for identities."""

    key = id(c)
    if key in memo:
        return memo[key]
    memo[key] = False
    try:
        if type(c) not in (
            ImplicitRootValueProof,
            ImplicitMultiplicityProof,
            CommonZeroProof,
        ):
            return False
        b = c.base_region
        if (
            type(c.schema_version) is not int
            or c.schema_version != 1
            or not _base(b, memo)
        ):
            return False
        z = b.variable
        if type(c) is CommonZeroProof:
            valid = (
                type(c.expressions) is tuple
                and bool(c.expressions)
                and type(c.orders) is tuple
                and len(c.expressions) == len(c.orders)
                and all(
                    type(p) is ImplicitMultiplicityProof
                    and p.expression == f
                    and _same(p.base_region, b)
                    and _valid_local(p, memo)
                    for f, p in zip(c.expressions, c.orders, strict=True)
                )
            )
        else:
            if (
                c.variable != z
                or c.expression.free_symbols - {z}
                or not _analytic(c.expression, z)
            ):
                return False
            if type(c) is ImplicitRootValueProof:
                if (
                    not isinstance(c.value, sp.Expr)
                    or c.value.free_symbols
                    or not _analytic(c.value, z)
                    or type(c.children) is not tuple
                    or type(c.power) is not int
                    or c.power < 1
                    or not _analytic(c.quotient, z)
                ):
                    return False
                subtrees = set(sp.preorder_traversal(c.expression)) - {c.expression}
                mapping = {}
                for child in c.children:
                    if (
                        type(child) is not ImplicitRootValueProof
                        or child.expression not in subtrees
                        or child.expression in mapping
                        or not _same(child.base_region, b)
                        or not _valid_local(child, memo)
                    ):
                        return False
                    mapping[child.expression] = child.value
                rewritten = c.expression.xreplace(mapping)
                valid = (
                    sp.expand(
                        (rewritten - c.value) ** c.power - c.quotient * b.expression
                    )
                    == 0
                )
            else:
                if not entire_source(c.expression, z) or type(c.zero_jets) is not tuple:
                    return False
                for k, p in enumerate(c.zero_jets):
                    if (
                        type(p) is not ImplicitRootValueProof
                        or p.expression != differentiate(c.expression, z, k)
                        or p.value != 0
                        or not _same(p.base_region, b)
                        or not _valid_local(p, memo)
                    ):
                        return False
                if c.order is None:
                    valid = c.taylor is None and c.leading_value is None
                elif (
                    type(c.order) is int
                    and c.order >= 0
                    and c.order == len(c.zero_jets)
                ):
                    if c.leading_value is not None:
                        p = c.leading_value
                        valid = (
                            c.taylor is None
                            and type(p) is ImplicitRootValueProof
                            and p.expression == differentiate(c.expression, z, c.order)
                            and _same(p.base_region, b)
                            and _valid_local(p, memo)
                            and p.value.is_zero is False
                        )
                    else:
                        w = c.taylor
                        valid = (
                            c.order > 0
                            and type(w) is ImplicitJetWitness
                            and w.expression == c.expression
                            and w.variable == z
                            and w.box == b.rectangle.bounds()
                            and w.order == c.order
                            and w.verify()
                        )
                        if valid:
                            a, d, e, h = w.coefficients[c.order]
                            valid = bool(a > 0 or e < 0 or d > 0 or h < 0)
                else:
                    valid = False
        memo[key] = bool(valid)
        return bool(valid)
    except (*_ERRORS, RecursionError):
        return False


def _remainder(f, base, z):
    atoms = sorted(
        f.atoms(sp.Function) | base.atoms(sp.Function), key=sp.default_sort_key
    )
    mapping = {a: sp.Dummy(f"analytic_atom_{i}") for i, a in enumerate(atoms)}
    mapping[z] = sp.Dummy("analytic_coordinate")
    reverse = {v: k for k, v in mapping.items()}
    generators = tuple(mapping.values())
    quotients, remainder = sp.reduced(
        sp.expand(f.xreplace(mapping)), [sp.expand(base.xreplace(mapping))], *generators
    )
    return (quotients[0] if quotients else sp.S.Zero).xreplace(
        reverse
    ), remainder.xreplace(reverse)


@budgeted_operation
def certify_root_value(expression, base_region, *, max_nodes=128, max_power=4):
    """Bounded congruence/polynomial-identity discovery; None means unresolved."""
    if type(max_nodes) is not int or max_nodes < 0:
        raise ValueError("max_nodes must be a nonnegative integer")
    if type(max_power) is not int or max_power < 1:
        raise ValueError("max_power must be a positive integer")
    if not _base(base_region, {}):
        raise ValueError("base_region must certify one distinct implicit root")
    f, z, remaining, cache = sp.sympify(expression), base_region.variable, max_nodes, {}

    def visit(node):
        nonlocal remaining
        if node in cache:
            return cache[node]
        if remaining <= 0 or not _analytic(node, z) or sp.count_ops(node) > 512:
            return None
        remaining -= 1
        cache[node] = None
        children = []
        if node.free_symbols:
            for arg in node.args:
                if isinstance(arg, sp.Expr) and arg.has(z):
                    p = visit(arg)
                    if p is not None:
                        children.append(p)
        # A nonconstant parent (such as z*exp(exp(z))) may still have
        # provably constant descendants. Keep their congruences for an outer
        # sum, where cancellation can then prove the whole value.
        children, selected = [], set()

        def collect(part):
            proof = cache.get(part)
            if proof is not None:
                if part not in selected:
                    children.append(proof)
                    selected.add(part)
            else:
                for argument in part.args:
                    if isinstance(argument, sp.Expr):
                        collect(argument)

        for argument in node.args:
            if isinstance(argument, sp.Expr):
                collect(argument)
        rewritten = node.xreplace({p.expression: p.value for p in children})
        try:
            q, value = _remainder(rewritten, base_region.expression, z)
            power = 1
            if value.free_symbols or not _analytic(value, z):
                # A radical-ideal identity H**k = Q*G proves H(alpha)=0
                # even when G's unique root has multiplicity greater than one.
                for power in range(2, max_power + 1):
                    q, residue = _remainder(rewritten**power, base_region.expression, z)
                    if residue == 0:
                        value = sp.S.Zero
                        break
                else:
                    return None
            p = ImplicitRootValueProof(
                node, z, base_region, value, q, tuple(children), power
            )
            if p.verify():
                cache[node] = p
                return p
        except _ERRORS:
            pass
        return None

    return visit(f)


def certify_implicit_multiplicity(expression, base_region, *, max_order=8, policy=None):
    """Prove zero jets and a first nonzero jet on the isolating rectangle."""
    policy = EnclosurePolicy() if policy is None else policy
    if type(max_order) is not int or max_order < 1:
        raise ValueError("max_order must be a positive integer")
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_implicit_multiplicity",
            expression,
            (base_region,),
            {"max_order": max_order, "policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    if not _base(base_region, {}):
        raise ValueError("base_region must certify one distinct implicit root")
    f, z = sp.sympify(expression), base_region.variable
    if f.free_symbols - {z} or not entire_source(f, z) or f.has(sp.Float):
        raise ValueError("source must belong to the parameter-free entire grammar")
    zeros, tested = [], 0
    for k in range(max_order + 1):
        p = certify_root_value(
            differentiate(f, z, k),
            base_region,
            max_nodes=max(0, policy.max_cells - tested),
        )
        tested += 1
        if p is not None and p.value.is_zero is False and k == len(zeros):
            return ImplicitMultiplicityProof(
                f, z, base_region, tuple(zeros), order=k, leading_value=p
            )
        if p is not None and p.value == 0:
            zeros.append(p)
        elif k and k == len(zeros):
            for precision in policy.precisions:
                if tested >= policy.max_cells:
                    break
                tested += 1
                coefficients = complex_box_taylor(
                    f,
                    z,
                    base_region.rectangle.bounds(),
                    k,
                    precision=precision,
                    max_series_terms=policy.max_series_terms,
                )
                if coefficients is not None:
                    a, b, c, d = coefficients[k]
                    if a > 0 or c < 0 or b > 0 or d < 0:
                        witness = ImplicitJetWitness(
                            f,
                            z,
                            base_region.rectangle.bounds(),
                            k,
                            coefficients,
                            precision,
                            policy.max_series_terms,
                        )
                        return ImplicitMultiplicityProof(
                            f, z, base_region, tuple(zeros), witness, k
                        )
            break
        else:
            break
        if tested >= policy.max_cells:
            break
    return ImplicitMultiplicityProof(
        f, z, base_region, tuple(zeros), reason="order-or-budget-unresolved"
    )


def certify_common_zero(expressions, base_region, *, max_order=8, policy=None):
    """Return local common-zero evidence; unresolved orders stay explicit."""
    if not isinstance(expressions, (tuple, sp.Tuple)) or not expressions:
        raise ValueError("expressions must be a nonempty tuple")
    policy = EnclosurePolicy() if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_common_zero",
            sp.Tuple(*expressions),
            (base_region,),
            {"max_order": max_order, "policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    values = tuple(map(sp.sympify, expressions))
    share = max(0, policy.max_cells // len(values))
    orders = tuple(
        certify_implicit_multiplicity(
            f, base_region, max_order=max_order, policy=replace(policy, max_cells=share)
        )
        for f in values
    )
    return CommonZeroProof(base_region, values, orders)


def rebase_implicit_proof(proof, base_region):
    """Transfer identities to a checked child base; rebuild its jet enclosure."""
    if type(proof) is ImplicitRootValueProof:
        return replace(
            proof,
            base_region=base_region,
            children=tuple(
                rebase_implicit_proof(p, base_region) for p in proof.children
            ),
        )
    if type(proof) is ImplicitMultiplicityProof:
        witness = proof.taylor
        if witness is not None:
            coefficients = complex_box_taylor(
                proof.expression,
                proof.variable,
                base_region.rectangle.bounds(),
                witness.order,
                precision=witness.precision,
                max_series_terms=witness.max_series_terms,
            )
            if coefficients is None:
                return None
            witness = replace(
                witness, box=base_region.rectangle.bounds(), coefficients=coefficients
            )
        return replace(
            proof,
            base_region=base_region,
            taylor=witness,
            zero_jets=tuple(
                rebase_implicit_proof(p, base_region) for p in proof.zero_jets
            ),
            leading_value=(
                rebase_implicit_proof(proof.leading_value, base_region)
                if proof.leading_value is not None
                else None
            ),
        )
    raise TypeError("unsupported implicit proof type")
