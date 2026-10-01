import sympy as sp

import funcprops as fp
from funcprops.results import Monotonicity, TruthValue
from funcprops.theorem_closure import TheoremFact, close_theorems


def test_registry_is_authoritative_and_valid():
    assert fp.validate_registry()
    out = close_theorems(
        [TheoremFact("monotonicity", Monotonicity.STRICTLY_INCREASING)]
    )
    assert any(
        f.property == "injective" and f.value is TruthValue.TRUE and f.theorem_id
        for f in out
    )
    assert fp.generated_adversarial_cases()


def test_ball_taylor_inequality_and_real_root():
    x = sp.symbols("x", real=True)
    interval = sp.Interval(0, 1)
    b = fp.certified_real_ball(sp.exp(x), x, interval)
    assert b and b.excludes_zero and b.verify()
    tm = fp.taylor_model(sp.exp(x), x, interval, order=2)
    assert tm and tm.verify()
    q = fp.certify_inequality(sp.exp(x), 0, x, interval)
    assert q.classification is TruthValue.TRUE and q.verify()
    r = fp.verify_real_root_interval(sp.exp(x) - 2, x, sp.Interval(0, 2))
    assert r.root_count == 1 and r.verify()


def test_composed_affine_global_maps():
    x, y = sp.symbols("x y")
    a = fp.affine_global_mapping((x + y, x - y), (x, y), kind="bijective")
    b = fp.affine_global_mapping((2 * x, 3 * y), (x, y), kind="bijective")
    c = fp.compose_global_maps((a, b))
    assert c.classification is TruthValue.TRUE and c.verify()


def test_parameter_family_strata():
    x, a = sp.symbols("x a", real=True)
    r = fp.exponential_affine_transition_cells(sp.exp(x) + a, x, a)
    assert r and len(r.cases) == 2
    q = fp.quadratic_discriminant_cells(x**2 + a * x + 1, x, a)
    assert q and len(q.cases) == 3


def test_rouche_replay_binds_g():
    z = sp.symbols("z")
    c = fp.rouche_polynomial_circle(
        z**3 + sp.Rational(1, 10) * z + sp.Rational(1, 10), z
    )
    assert c and c.verify()
    forged = fp.RoucheCertificate(c.f, z**2, z, c.center, c.radius, c.count)
    assert not forged.verify()
