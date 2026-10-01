import sympy as sp

import funcprops as fp
from funcprops.certified_operations import _cut_crossing_word, _cut_system_valid


def test_basepoint_on_cut_rejected():
    assert not _cut_system_valid((-1, 1), 3, 1)


def test_parallel_punctures_rejected():
    assert not _cut_system_valid((0, 2), 3 * sp.I, 1)


def test_contour_through_puncture_unknown():
    t = sp.symbols("t", real=True)
    contour = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    assert _cut_crossing_word(contour, (-1, 1), sp.I) is None


def test_open_path_unknown():
    t = sp.symbols("t", real=True)
    first = fp.ParametricContour(t, (t, 0, 1))
    second = fp.ParametricContour(t**2, (t, 0, 1))
    assert fp.homotopic(first, second, punctures=(2, 3)) is None
