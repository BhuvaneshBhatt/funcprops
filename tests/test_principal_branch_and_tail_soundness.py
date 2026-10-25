"""Principal local branches, raw rectangle boundaries and real tail premises."""

from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops.asymptotic_tails import TailSignCertificate, certify_tail_sign
from funcprops.certified_operations import LaurentCertificate, ResidueCertificate
from funcprops.meromorphic_contours import meromorphic_rectangle_count

z = s.Symbol("z")
x = s.Symbol("x", real=True)


@pytest.mark.parametrize(
    "form",
    [
        lambda z: s.log(z),
        lambda z: s.sqrt(z),
        lambda z: s.log(z) / (z + 1),
        lambda z: s.sqrt(z) / (z + 1),
        lambda z: s.Pow(z, s.pi, evaluate=False),
    ],
)
def test_principal_cut_has_no_full_disk_meromorphic_certificate(form):
    e = form(z)
    assert fp.laurent_series(e, z, -1, return_certificate=True) is None
    assert fp.residue(e, z, -1, return_certificate=True) is None
    assert fp.classify_singularity(e, z, -1, return_certificate=True) is None
    assert not LaurentCertificate(e, z, s.Integer(-1), s.S.One, 4).verify()
    assert not ResidueCertificate(e, z, s.Integer(-1), s.S.Zero).verify()


@pytest.mark.parametrize("point", [s.S.One, s.I, -s.I, 1 + s.I])
@pytest.mark.parametrize("form", [lambda z: s.log(z), lambda z: s.sqrt(z)])
def test_principal_germ_away_from_cut_preserved(point, form):
    e = form(z)
    c = fp.laurent_series(e, z, point, order=3, return_certificate=True)
    assert c.verify()
    c = fp.residue(e, z, point, return_certificate=True)
    assert c.residue == 0 and c.verify()


def test_shifted_branch_cut_and_whole_germ_cancellation():
    assert fp.laurent_series(s.log(z - 2), z, 1, return_certificate=True) is None
    e = s.exp(s.log(z, evaluate=False), evaluate=False)
    c = fp.laurent_series(e, z, -1, return_certificate=True)
    assert c.verify()
    e = s.sin(1 / z) ** 2 + s.cos(1 / z) ** 2
    assert fp.laurent_series(e, z, 0, return_certificate=True).verify()


@pytest.mark.parametrize("bounds", [(-1 - s.I, s.I), (-1 - s.I, 1), (0, 1 + s.I)])
def test_rectangle_original_boundary_hole_not_erased(bounds):
    held = s.Mul(z, s.Pow(z, -1, evaluate=False), evaluate=False)
    assert meromorphic_rectangle_count(held, z, *bounds) is None


def test_rectangle_interior_removable_hole_and_replay_binding():
    held = s.Mul(z, s.Pow(z, -1, evaluate=False), evaluate=False)
    c = meromorphic_rectangle_count(held, z, -1 - s.I, 1 + s.I)
    assert c.expression == held and c.verify()
    assert (c.zeros, c.poles, c.winding) == (0, 0, 0)
    assert not replace(c, upper_right=s.I).verify()
    assert not replace(c, winding=1).verify()


@pytest.mark.parametrize("bounds", [(1 + s.I, -1 - s.I), (0, 0), (0, 1), (0, s.I)])
def test_rectangle_geometry_must_have_positive_area_and_order(bounds):
    assert meromorphic_rectangle_count(s.S.One, z, *bounds) is None


@pytest.mark.parametrize("e", [s.exp(x + s.I), s.exp(x + s.I * s.pi, evaluate=False)])
def test_complex_or_negative_exponential_not_positive_real_tail(e):
    assert certify_tail_sign(e, x, threshold=0) is None
    c = TailSignCertificate(e, x, 1, s.S.Zero, 1, "exp-polynomial-dominance")
    assert not c.verify()


def test_tail_source_hole_blocks_proof_until_excluded():
    held = s.Mul(x - 2, s.Pow(x - 2, -1, evaluate=False), evaluate=False)
    assert certify_tail_sign(held, x, threshold=0) is None
    assert certify_tail_sign(held, x, threshold=2) is None
    c = certify_tail_sign(held, x, threshold=3)
    assert c.verify()
    assert not replace(c, threshold=s.S.Zero).verify()


@pytest.mark.parametrize(
    "e,direction,sign",
    [
        (s.exp(x + 1) * (x + 1), 1, 1),
        (-s.exp(-x) * (-x + 1), -1, -1),
        (1 / (x * x + 1), 1, 1),
    ],
)
def test_valid_real_tail_theorems_preserved(e, direction, sign):
    c = certify_tail_sign(e, x, direction=direction, threshold=1)
    assert c.sign == sign and c.verify()


def test_argument_principle_keeps_source_boundary_exclusions():
    t = s.Symbol("t", real=True)
    contour = fp.ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    hole = s.Mul(z - 1, s.Pow(z - 1, -1, evaluate=False), evaluate=False)
    assert fp.argument_principle(hole, z, contour, return_certificate=True) is None
    interior = s.Mul(z, s.Pow(z, -1, evaluate=False), evaluate=False)
    c = fp.argument_principle(interior, z, contour, return_certificate=True)
    assert c.expression == interior and c.zeros_minus_poles == 0 and c.verify()


def test_constant_contour_premises():
    t = s.Symbol("t", real=True)
    open_path = fp.ParametricContour(t, (t, 0, 1))
    assert fp.argument_principle(s.S.One, z, open_path, return_certificate=True) is None
    assert fp.argument_principle(s.S.One, z, object(), return_certificate=True) is None
    a = s.Symbol("a", complex=True)
    circle = fp.ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    assert fp.argument_principle(a * z, z, circle, return_certificate=True) is None
