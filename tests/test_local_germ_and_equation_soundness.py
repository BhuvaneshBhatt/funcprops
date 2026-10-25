"""Complex local theorem preconditions and first-match equation domains."""

from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops.certified_operations import LaurentCertificate, ResidueCertificate


@pytest.mark.parametrize("assumptions", [{}, {"real": True}, {"positive": True}])
@pytest.mark.parametrize(
    "form",
    [
        lambda z: s.Abs(z) / z,
        lambda z: s.conjugate(z) / z**2,
        lambda z: s.sqrt(z),
        lambda z: s.log(z),
    ],
)
def test_nonmeromorphic_local_proofs_decline(assumptions, form):
    z = s.Symbol("z", **assumptions)
    # Hold nonholomorphic nodes before variable assumptions can simplify them.
    raw = s.Symbol("raw")
    e = (
        form(raw).subs(raw, z, simultaneous=True)
        if not assumptions
        else form(raw).xreplace({raw: z})
    )
    if e == 1 / z and assumptions:
        # conjugate(real z) has already lost its source; use an unevaluated node.
        e = s.Mul(s.conjugate(z, evaluate=False), z**-2, evaluate=False)
    if e == 1 and assumptions:
        e = s.Mul(s.Abs(z, evaluate=False), z**-1, evaluate=False)
    if e == z and assumptions and form(raw) == s.Abs(raw) / raw:
        e = s.Mul(s.Abs(z, evaluate=False), z**-1, evaluate=False)
    assert fp.laurent_series(e, z, 0, return_certificate=True) is None
    assert fp.residue(e, z, 0, return_certificate=True) is None
    assert not LaurentCertificate(e, z, s.S.Zero, s.S.One, 4).verify()
    assert not ResidueCertificate(e, z, s.S.Zero, s.S.Zero).verify()


@pytest.mark.parametrize(
    "form", [lambda z: s.exp(z) / z**2, lambda z: s.log(1 + z), lambda z: s.sqrt(1 + z)]
)
def test_meromorphic_and_local_analytic_germs_preserved(form):
    z = s.Symbol("z", real=True)
    e = form(z)
    c = fp.laurent_series(e, z, 0, order=4, return_certificate=True)
    assert c.certified and c.complete
    assert not replace(c, series=c.series + 1).verify()
    r = fp.residue(e, z, 0, return_certificate=True)
    assert r.certified and r.residue == s.residue(e, z, 0)


@pytest.mark.parametrize(
    "condition", [lambda x: x < 0, lambda x: x > 0, lambda x: s.Ne(x, 0)]
)
def test_inactive_branch_pole_does_not_remove_root(condition):
    x = s.Symbol("x", real=True)
    e = s.Piecewise((1 / x, condition(x)), (x, True))
    c = fp.solve(e, x, domain=s.S.Reals, return_certificate=True)
    assert c.solutions == s.FiniteSet(0) and c.complete and c.verify()
    assert c.effective_domain == s.S.Reals
    assert not replace(c, solutions=s.S.EmptySet).verify()


def test_active_branch_pole_stays_excluded():
    x = s.Symbol("x", real=True)
    e = s.Piecewise((1 / x, x <= 0), (x - 1, True))
    c = fp.solve(e, x, domain=s.S.Reals, return_certificate=True)
    assert c.solutions == s.FiniteSet(1) and c.complete and c.verify()
    assert c.effective_domain == s.Complement(s.S.Reals, s.FiniteSet(0))


def test_unresolved_domains_do_not_get_exhaustive_equation_claims():
    x = s.Symbol("x", real=True)
    e = s.Mul(s.S.Zero, s.gamma(x), evaluate=False)
    c = fp.solve(e, x, domain=s.S.Reals, return_certificate=True)
    assert not c.complete and c.verify()
    z = s.Symbol("z")
    e = s.Piecewise((1 / z, s.re(z) > 0), (z, True))
    c = fp.solve(e, z, return_certificate=True)
    assert not c.complete and c.verify()


def test_unsupported_essential_germs():
    z = s.Symbol("z")
    assert fp.laurent_series(s.exp(s.exp(1 / z)), z, 0, return_certificate=True) is None
    assert fp.residue(s.exp(s.exp(1 / z)), z, 0, return_certificate=True) is None


def test_inverse_replay_preserves_inverse_source_domain():
    x = s.Symbol("x", real=True)
    c = fp.inverse(x, x, return_certificate=True)
    y = c.value
    held_hole = s.Mul(y, y, s.Pow(y, -1, evaluate=False), evaluate=False)
    assert c.verify()
    assert not replace(c, inverse=held_hole).verify()


def test_piecewise_implicit_undefined_region_not_a_root():
    x = s.Symbol("x", real=True)
    e = s.Piecewise((x - 1, x > 0))
    c = fp.solve(e, x, domain=s.S.Reals, return_certificate=True)
    assert c.complete and c.verify() and c.solutions == s.FiniteSet(1)
    assert c.effective_domain == s.Interval.open(0, s.oo)


@pytest.mark.parametrize("value", [s.oo, -s.oo, s.zoo, s.nan])
def test_nonfinite_local_source_is_not_a_complex_germ(value):
    z = s.Symbol("z")
    assert fp.laurent_series(value, z, return_certificate=True) is None
    assert fp.residue(value, z, 0, return_certificate=True) is None
