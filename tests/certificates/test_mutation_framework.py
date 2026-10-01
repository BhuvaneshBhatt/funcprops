from dataclasses import fields, replace

import sympy as sp

import funcprops as fp


def mutations(certificate, replacements):
    names = {field.name for field in fields(certificate)}
    for name, value in replacements.items():
        if name in names:
            yield replace(certificate, **{name: value})


def test_homotopy_mutations_fail():
    t = sp.symbols("t", real=True)
    first = fp.ParametricContour(3 * sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    second = fp.ParametricContour(3 * (sp.cos(t) + sp.I * sp.sin(t)), (t, 0, 2 * sp.pi))
    cert = fp.homotopic(first, second, punctures=(-1, 1), return_certificate=True)
    assert cert.verify()
    changed = {
        "punctures": (-1, -1),
        "first_word": (*cert.first_word, 1),
        "second_word": (*cert.second_word, -1),
        "reduced_word": (),
        "cut_direction": 0,
    }
    assert all(not mutant.verify() for mutant in mutations(cert, changed))


def test_winding_mutations_fail():
    t = sp.symbols("t", real=True)
    contour = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    cert = fp.winding_number(contour, 0, return_certificate=True)
    assert cert.verify()
    assert all(
        not mutant.verify() for mutant in mutations(cert, {"winding": 2, "integral": 0})
    )
