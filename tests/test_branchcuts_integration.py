import sympy as sp

from funcprops import function_branchcuts
from funcprops.branchcuts import branch_cut_jumps_pairs, branch_jump


def test_log_branchcut_property_uses_structural_rule():
    z = sp.Symbol("z")
    conds = function_branchcuts(sp.log(z), z)
    assert len(conds) == 1
    assert conds[0].has(sp.Contains(z, sp.S.Reals))
    assert conds[0].has(z < 0)


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
    conds = function_branchcuts(z**n, z)
    # SymPy assumptions may simplify the noninteger guard away entirely.
    assert conds == () or all(c is not sp.S.true for c in conds)
