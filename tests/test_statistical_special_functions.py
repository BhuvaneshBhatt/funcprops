import sympy as sp

import funcprops as fp


def test_statistical_heads_exact_rules():
    h, a, x, alpha = sp.symbols("h a x alpha", real=True)
    assert fp.OwenT(h, 0) == 0
    assert fp.OwenT(0, a) == sp.atan(a) / (2 * sp.pi)
    assert sp.diff(fp.OwenT(h, a), a) == sp.exp(-(h**2) * (1 + a**2) / 2) / (
        2 * sp.pi * (1 + a**2)
    )
    assert (
        sp.diff(fp.MittagLefflerE(alpha, x), x)
        == fp.MittagLefflerE(alpha, alpha, x) / alpha
    )
    assert fp.MittagLefflerE(1, x) == sp.exp(x)


def test_regularized_gamma_heads_rewrite_and_differentiate():
    a = sp.symbols("a", positive=True)
    x = sp.symbols("x", positive=True)
    p = fp.RegularizedGammaP(a, x)
    q = fp.RegularizedGammaQ(a, x)
    density = x ** (a - 1) * sp.exp(-x) / sp.gamma(a)
    assert sp.diff(p, x) == density
    assert sp.diff(q, x) == -density
    assert p.rewrite(sp.lowergamma) == sp.lowergamma(a, x) / sp.gamma(a)
    assert q.rewrite(sp.uppergamma) == sp.uppergamma(a, x) / sp.gamma(a)


def test_loggamma_and_digamma_geometry_on_positive_axis():
    x = sp.symbols("x", positive=True)
    assert fp.convexity(sp.loggamma(x), x, domain=x > 0) is fp.Convexity.STRICTLY_CONVEX
    assert (
        fp.monotonicity(sp.digamma(x), x, domain=x > 0)
        is fp.Monotonicity.STRICTLY_INCREASING
    )
    assert fp.convexity(sp.digamma(x), x, domain=x > 0) is fp.Convexity.STRICTLY_CONCAVE


def test_polygamma_sign_and_monotonicity_parity_strata():
    x = sp.symbols("x", positive=True)
    assert fp.sign(sp.polygamma(1, x), x, domain=x > 0) is fp.Sign.POSITIVE
    assert fp.sign(sp.polygamma(2, x), x, domain=x > 0) is fp.Sign.NEGATIVE
    assert (
        fp.monotonicity(sp.polygamma(1, x), x, domain=x > 0)
        is fp.Monotonicity.STRICTLY_DECREASING
    )
    assert (
        fp.monotonicity(sp.polygamma(2, x), x, domain=x > 0)
        is fp.Monotonicity.STRICTLY_INCREASING
    )


def test_regularized_gamma_monotonicity_and_range():
    a = sp.symbols("a", positive=True)
    x, y = sp.symbols("x y", real=True)
    p = fp.RegularizedGammaP(a, x)
    q = fp.RegularizedGammaQ(a, x)
    assert fp.monotonicity(p, x, domain=x > 0) is fp.Monotonicity.STRICTLY_INCREASING
    assert fp.monotonicity(q, x, domain=x > 0) is fp.Monotonicity.STRICTLY_DECREASING
    assert (
        sp.simplify_logic(fp.range(p, x, y, constraints=x > 0) ^ sp.And(y > 0, y < 1))
        is sp.false
    )
    assert (
        sp.simplify_logic(fp.range(q, x, y, constraints=x > 0) ^ sp.And(y > 0, y < 1))
        is sp.false
    )


def test_regularized_beta_is_increasing_on_probability_support():
    a, b = sp.symbols("a b", positive=True)
    x, y = sp.symbols("x y", real=True)
    expr = sp.betainc_regularized(a, b, 0, x)
    support = sp.And(x > 0, x < 1)
    assert (
        fp.monotonicity(expr, x, domain=support) is fp.Monotonicity.STRICTLY_INCREASING
    )
    assert (
        sp.simplify_logic(
            fp.range(expr, x, y, constraints=support) ^ sp.And(y > 0, y < 1)
        )
        is sp.false
    )


def test_owen_t_is_positive_and_increasing_in_second_argument():
    h = sp.symbols("h", real=True)
    a = sp.symbols("a", positive=True)
    expr = fp.OwenT(h, a)
    assert fp.sign(expr, a, domain=a > 0) is fp.Sign.POSITIVE
    assert fp.monotonicity(expr, a, domain=a > 0) is fp.Monotonicity.STRICTLY_INCREASING


def test_marcum_q_threshold_and_noncentrality_monotonicity():
    m = sp.symbols("m", positive=True)
    a, b = sp.symbols("a b", positive=True)
    assert (
        fp.monotonicity(sp.marcumq(m, a, b), b, domain=b > 0)
        is fp.Monotonicity.STRICTLY_DECREASING
    )
    assert (
        fp.monotonicity(sp.marcumq(m, a, b), a, domain=a > 0)
        is fp.Monotonicity.STRICTLY_INCREASING
    )


def test_marcum_q_probability_range_on_positive_threshold():
    m, a = sp.symbols("m a", positive=True)
    b, y = sp.symbols("b y", real=True)
    result = fp.range(sp.marcumq(m, a, b), b, y, constraints=b > 0)
    assert sp.simplify_logic(result ^ sp.And(y > 0, y < 1)) is sp.false


def test_mittag_leffler_parameter_guard():
    alpha = sp.symbols("alpha", real=True)
    x = sp.symbols("x", nonnegative=True)
    expr = fp.MittagLefflerE(alpha, -x)
    unresolved = fp.complete_monotonicity(expr, x, domain=x >= 0)
    assert isinstance(unresolved, sp.Piecewise)
    assert unresolved.subs(alpha, sp.Rational(1, 2)) is sp.S.true
    assert str(unresolved.subs(alpha, 2)) == "unknown"
    assert (
        fp.complete_monotonicity(
            expr,
            x,
            domain=x >= 0,
            assumptions=sp.And(alpha > 0, alpha <= 1),
        )
        is fp.TruthValue.TRUE
    )


def test_mittag_leffler_geometry_follows_complete_monotonicity():
    alpha = sp.symbols("alpha", positive=True)
    x = sp.symbols("x", positive=True)
    expr = fp.MittagLefflerE(alpha, -x)
    mono = fp.monotonicity(expr, x, domain=x > 0, return_result=True)
    convex = fp.convexity(expr, x, domain=x > 0, return_result=True)
    sign = fp.sign(expr, x, domain=x > 0, return_result=True)
    assert isinstance(mono, fp.PropertyResult)
    assert mono.cases[0].value is fp.Monotonicity.NONINCREASING
    assert isinstance(convex, fp.PropertyResult)
    assert convex.cases[0].value is fp.Convexity.CONVEX
    assert isinstance(sign, fp.PropertyResult)
    assert sign.cases[0].value is fp.Sign.POSITIVE


def test_besselk_complete_monotonicity_requires_open_positive_axis():
    nu = sp.symbols("nu", real=True)
    x = sp.symbols("x", real=True)
    assert (
        fp.complete_monotonicity(
            sp.besselk(nu, x), x, domain=x > 0, assumptions=sp.Contains(nu, sp.S.Reals)
        )
        is fp.TruthValue.TRUE
    )
    assert (
        fp.complete_monotonicity(
            sp.besselk(nu, x), x, domain=x >= 0, assumptions=sp.Contains(nu, sp.S.Reals)
        )
        is fp.TruthValue.UNKNOWN
    )


def test_complete_monotonicity_certificate_replays_generically():
    alpha = sp.symbols("alpha", positive=True)
    x = sp.symbols("x", nonnegative=True)
    cert = fp.complete_monotonicity(
        fp.MittagLefflerE(alpha, -x),
        x,
        domain=x >= 0,
        assumptions=alpha <= 1,
        return_result=True,
    )
    assert cert.classification is fp.TruthValue.TRUE
    assert cert.verify()
    assert fp.verify_certificate(cert)


def test_modified_bessel_statistical_ratio_geometry():
    nu = sp.symbols("nu", real=True)
    x, y = sp.symbols("x y", real=True)
    ratio = sp.besseli(nu + 1, x) / sp.besseli(nu, x)
    domain = x > 0

    mono = fp.monotonicity(ratio, x, domain=domain, return_result=True)
    sign = fp.sign(ratio, x, domain=domain, return_result=True)
    convex = fp.convexity(ratio, x, domain=domain, return_result=True)
    rg = fp.range(ratio, x, y, constraints=domain, return_result=True)

    for result, expected in (
        (mono, fp.Monotonicity.STRICTLY_INCREASING),
        (sign, fp.Sign.POSITIVE),
        (convex, fp.Convexity.CONCAVE),
    ):
        assert isinstance(result, fp.PropertyResult)
        assert result.cases[0].value is expected
        assert (
            sp.simplify_logic(result.cases[0].condition ^ (nu >= -sp.Rational(1, 2)))
            is sp.false
        )

    assert isinstance(rg, fp.PropertyResult)
    assert sp.simplify_logic(rg.cases[0].value ^ sp.And(y > 0, y < 1)) is sp.false
    assert (
        sp.simplify_logic(rg.cases[0].condition ^ (nu >= -sp.Rational(1, 2)))
        is sp.false
    )
