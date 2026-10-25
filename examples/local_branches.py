"""A selected local logarithmic germ has a source-bound replay contract."""

from dataclasses import replace

import sympy as sp

import funcprops as fp

z = sp.Symbol("z")
chart = fp.LocalBranchContext(-1, ((z, sp.I * sp.pi),))
residue = fp.residue(
    sp.log(z) / (z + 1), z, -1, branch_context=chart, return_certificate=True
)
assert residue is not None and residue.verify() and residue.residue == sp.I * sp.pi
assert not replace(residue, branch_context=None).verify()
assert fp.residue(sp.log(z) / (z + 1), z, -1, return_certificate=True) is None
