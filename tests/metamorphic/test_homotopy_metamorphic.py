import sympy as sp

import funcprops as fp
from funcprops.certified_operations import _free_reduce


def circle(radius, t, phase=0):
    return fp.ParametricContour(radius * sp.exp(sp.I * (t + phase)), (t, 0, 2 * sp.pi))


def test_word_inverse():
    word = (1, 2, -1, 3, -2)
    inverse = tuple(-x for x in reversed(word))
    assert _free_reduce(word + inverse) == ()


def test_subdivision_neutrality():
    word = (1, 2, -1)
    assert _free_reduce((*word[:1], 3, -3, *word[1:])) == _free_reduce(word)


def test_reparameterization():
    t = sp.symbols("t", real=True)
    standard = circle(3, t)
    shifted = circle(3, t, 2 * sp.pi)
    cert = fp.homotopic(standard, shifted, punctures=(-1, 1), return_certificate=True)
    assert cert.verify()
    assert cert.first_word == cert.second_word
    assert cert.reduced_word == cert.first_word


def test_orientation_reversal():
    t = sp.symbols("t", real=True)
    contour = circle(3, t)
    assert fp.homotopic(contour, contour.reversed(), punctures=(-1, 1)) is False
