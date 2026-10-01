import sympy as sp

from funcprops import branch_cuts
from funcprops.branchcuts import branch_cut_jumps_pairs, branch_jump


def test_log_branchcut_property_uses_structural_rule():
    z = sp.Symbol("z")
    conds = branch_cuts(sp.log(z), z)
    assert len(conds) == 1
    assert conds == (z < 0,)


def test_sqrt_branch_jump_preserved():
    z = sp.Symbol("z")
    jump = branch_jump(sp.sqrt(z), z)
    assert jump.has(2 * sp.I * sp.sqrt(-z))


def test_composite_branchcut_engine_is_available():
    z = sp.Symbol("z")
    assoc = branch_cut_jumps_pairs(sp.log(z) + sp.sqrt(z), z)
    assert any(expr != 0 for expr, cond in assoc["Jump"])


def test_power_integer_exponent_cut_is_guarded():
    z = sp.Symbol("z")
    n = sp.Symbol("n", integer=True)
    conds = branch_cuts(z**n, z)
    # SymPy assumptions may simplify the noninteger guard away entirely.
    assert conds == () or all(c is not sp.S.true for c in conds)


def test_log_affine_pullback_uses_clear_real_ray_relation():
    z = sp.Symbol("z")
    assert branch_cuts(sp.log(1 - z), z) == (z > 1,)


def test_log_nonreal_affine_pullback_retains_realness_geometry():
    z = sp.Symbol("z")
    conds = branch_cuts(sp.log(sp.I * z), z)
    assert len(conds) == 1
    assert conds[0].has(sp.Contains(sp.I * z, sp.S.Reals))


def test_log_oblique_affine_pullback_retains_realness_geometry():
    z = sp.Symbol("z")
    conds = branch_cuts(sp.log((1 + sp.I) * z + 2), z)
    assert len(conds) == 1
    assert any(
        isinstance(atom, sp.Contains) and atom.args[1] == sp.S.Reals
        for atom in sp.And.make_args(conds[0])
    )
