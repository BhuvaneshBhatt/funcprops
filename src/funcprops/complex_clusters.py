"""Selected analytic cluster counts using Cauchy tails and Rouché's theorem.

The count includes multiplicity. It does not assert distinctness, individual
multiplicities, or reality. Only an explicit entire grammar is supported.
"""

from dataclasses import dataclass, replace

import sympy as sp

from .coverage_contract import CheckOutcome, CheckResult, EnclosureWitness
from .enclosure_policy import EnclosurePolicy
from .enclosures import enclosure_witness
from .source_syntax import differentiate, normalize_arithmetic

_AUX = sp.Symbol("_cluster_enclosure", real=True)


def _gaussian(value):
    return isinstance(sp.re(value), sp.Rational) and isinstance(
        sp.im(value), sp.Rational
    )


def _size(value):
    return abs(sp.re(value)) + abs(sp.im(value))


def _majorant(f, z, center, radius):
    """Upper bound on |f| on the larger complex circle, preserving raw syntax.

    Gaussian constants, coordinate, sums/products, nonnegative integral powers,
    and exponentials of affine Gaussian polynomials form the declared grammar.
    Negative powers are rejected even when cancellation would remove a hole.
    """
    if f == z:
        return _size(center) + radius
    if not f.has(z):
        return _size(f) if _gaussian(f) else None
    if f.is_Add or f.is_Mul:
        values = [_majorant(a, z, center, radius) for a in f.args]
        if any(a is None for a in values):
            return None
        return sp.Add(*values) if f.is_Add else sp.Mul(*values)
    if f.is_Pow and f.exp.is_Integer and f.exp >= 0:
        base = _majorant(f.base, z, center, radius)
        return None if base is None else base**f.exp
    if f.func in (sp.erf, sp.erfc, sp.sin, sp.cos, sp.sinh, sp.cosh):
        r = _majorant(f.args[0], z, center, radius)
        if r is None:
            return None
        if f.func in (sp.erf, sp.erfc):
            bound = 2 * r * sp.exp(r**2) / sp.sqrt(sp.pi)
            return bound if f.func is sp.erf else 1 + bound
        return sp.exp(r)
    if f.func is sp.exp:
        # Validate the argument's raw grammar before polynomial normalization.
        if _majorant(f.args[0], z, center, radius) is None:
            return None
        try:
            p = sp.Poly(normalize_arithmetic(f.args[0]), z, domain=sp.QQ_I)
            if p.degree() > 1:
                return None
            a, b = p.nth(1), p.nth(0)
            return sp.exp(sp.re(a * center + b) + _size(a) * radius)
        except (ValueError, TypeError, sp.PolynomialError):
            return None
    return None


def _magnitude(value):
    return sp.sqrt(
        sp.expand_complex(value).as_real_imag()[0] ** 2
        + sp.expand_complex(value).as_real_imag()[1] ** 2
    )


@dataclass(frozen=True)
class ComplexClusterCertificate:
    """Count zeros with multiplicity in a supported analytic disk."""

    expression: sp.Expr
    variable: sp.Symbol
    center: sp.Expr
    radius: sp.Rational
    outer_radius: sp.Rational
    order: int
    source_syntax: str
    coordinate_assumptions: tuple
    coefficients: tuple = ()
    coefficient_bounds: tuple = ()
    majorant_bound: EnclosureWitness | None = None
    remainder: sp.Rational | None = None
    zero_count: int | None = None
    obligations: tuple = ()
    schema_version: int = 1

    @property
    def complete(self):
        return self.zero_count is not None and not self.obligations

    @property
    def multiplicity_count(self):
        return self.zero_count

    @property
    def distinct_root_count(self):
        return 0 if self.zero_count == 0 else None

    @property
    def real_root_count(self):
        return 0 if self.zero_count == 0 else None

    @property
    def individual_multiplicities(self):
        return () if self.zero_count == 0 else None

    @property
    def scope(self):
        return "analytic-complex-disk-count-with-multiplicity"

    def check(self):
        """Replay the bound evidence and return the detailed check outcome."""

        return check_complex_cluster(self)

    @property
    def certified(self):
        return self.verify()

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        return self.check().certified is True


def check_complex_cluster(cert):
    """Replay explicit Cauchy and Rouché inequalities without running search."""
    from .coverage_checker import _bound_matches

    reject = CheckResult(CheckOutcome.REJECTED, False, False, "false-cluster-premise")
    try:
        if (
            not isinstance(cert, ComplexClusterCertificate)
            or type(cert.schema_version) is not int
            or cert.schema_version != 1
        ):
            return CheckResult(
                CheckOutcome.UNSUPPORTED, None, False, "unsupported-cluster-version"
            )
        f, z, R, S, n = (
            cert.expression,
            cert.variable,
            cert.radius,
            cert.outer_radius,
            cert.order,
        )
        if (
            not isinstance(z, sp.Symbol)
            or z.assumptions0 != {"commutative": True}
            or cert.coordinate_assumptions != tuple(sorted(z.assumptions0.items()))
            or cert.source_syntax != sp.srepr(f)
            or f.free_symbols - {z}
            or f.has(sp.Float)
            or not _gaussian(cert.center)
            or not isinstance(R, sp.Rational)
            or not isinstance(S, sp.Rational)
            or not 0 < R < S
            or type(n) is not int
            or n < 0
        ):
            return reject
        majorant = _majorant(f, z, cert.center, S)
        if cert.obligations and cert.zero_count is None:
            return CheckResult(
                CheckOutcome.UNSUPPORTED, None, False, "; ".join(cert.obligations)
            )
        if (
            majorant is None
            or cert.obligations
            or type(cert.zero_count) is not int
            or not 0 <= cert.zero_count <= n
            or len(cert.coefficients) != n + 1
            or len(cert.coefficient_bounds) != n + 1
        ):
            return reject
        if (
            not isinstance(cert.coefficients, tuple)
            or not isinstance(cert.coefficient_bounds, tuple)
            or not isinstance(cert.obligations, tuple)
        ):
            return reject
        expected = tuple(
            differentiate(normalize_arithmetic(f), z, k).subs(z, cert.center)
            / sp.factorial(k)
            for k in range(n + 1)
        )
        if cert.coefficients != expected:
            return reject
        for coefficient, bound in zip(expected, cert.coefficient_bounds, strict=True):
            if (
                not _bound_matches(
                    bound, _magnitude(coefficient), _AUX, sp.FiniteSet(0)
                )
                or bound.lower < 0
            ):
                return reject
        if (
            not _bound_matches(cert.majorant_bound, majorant, _AUX, sp.FiniteSet(0))
            or cert.majorant_bound.lower < 0
        ):
            return reject
        q = R / S
        tail = cert.majorant_bound.upper * q ** (n + 1) / (1 - q)
        if cert.remainder != tail:
            return reject
        m = cert.zero_count
        dominant = cert.coefficient_bounds[m].lower * R**m
        others = sum(
            b.upper * R**k for k, b in enumerate(cert.coefficient_bounds) if k != m
        )
        if dominant <= others + tail:
            return reject
        return CheckResult(CheckOutcome.COMPLETE, True, True)
    except (
        AttributeError,
        TypeError,
        ValueError,
        ArithmeticError,
        NotImplementedError,
        sp.PolynomialError,
    ):
        return reject


def certify_complex_cluster(expr, var, center, radius, *, policy=None):
    """Count a selected entire cluster, or report an unresolved analytic premise.

    Cauchy's estimate on the outer circle bounds the omitted Taylor series;
    strict dominance of one monomial then gives a multiplicity-inclusive count.
    """
    policy = EnclosurePolicy(max_taylor_order=16) if policy is None else policy
    if policy.seconds is not None:
        from .work_budget import bounded_query

        return bounded_query(
            "certify_complex_cluster",
            expr,
            (var, center, radius),
            {"policy": replace(policy, seconds=None)},
            policy.seconds,
        )
    f, z, c, R = map(sp.sympify, (expr, var, center, radius))
    cert = ComplexClusterCertificate(
        f,
        z,
        c,
        R,
        2 * R,
        0,
        sp.srepr(f),
        tuple(sorted(z.assumptions0.items())) if isinstance(z, sp.Symbol) else (),
    )
    if (
        not isinstance(z, sp.Symbol)
        or z.assumptions0 != {"commutative": True}
        or not isinstance(R, sp.Rational)
        or R <= 0
        or not _gaussian(c)
        or f.free_symbols - {z}
        or f.has(sp.Float)
    ):
        return replace(
            cert, obligations=("exact-complex-coordinate-and-geometry-required",)
        )
    majorant = _majorant(f, z, c, 2 * R)
    if majorant is None:
        return replace(cert, obligations=("unsupported-entire-source-grammar",))
    # One Taylor order consumes one cell of the declared work budget.
    tested = 0
    for precision in policy.precisions:
        M = enclosure_witness(
            majorant, _AUX, sp.FiniteSet(0), precision, policy.max_series_terms
        )
        if M is None:
            continue
        coefficients, bounds = [], []
        for n in range(policy.max_taylor_order + 1):
            if tested >= policy.max_cells:
                break
            tested += 1
            coefficient = differentiate(normalize_arithmetic(f), z, n).subs(
                z, c
            ) / sp.factorial(n)
            bound = enclosure_witness(
                _magnitude(coefficient),
                _AUX,
                sp.FiniteSet(0),
                precision,
                policy.max_series_terms,
            )
            if bound is None:
                break
            coefficients.append(coefficient)
            bounds.append(bound)
            tail = M.upper * sp.Rational(1, 2) ** n
            for m in range(n + 1):
                if (
                    bounds[m].lower * R**m
                    > sum(b.upper * R**k for k, b in enumerate(bounds) if k != m) + tail
                ):
                    candidate = replace(
                        cert,
                        order=n,
                        coefficients=tuple(coefficients),
                        coefficient_bounds=tuple(bounds),
                        majorant_bound=M,
                        remainder=tail,
                        zero_count=m,
                    )
                    if candidate.verify():
                        return candidate
    return replace(cert, obligations=("unresolved-cluster-or-order-precision-budget",))
