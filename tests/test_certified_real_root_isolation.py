import sympy as sp

from funcprops.transcendental.roots import _certified_real_interval_isolation

x = sp.symbols("x", real=True)


def test_partition_isolator_certifies_exact_critical_root_multiplicity():
    result = _certified_real_interval_isolation(x**2, x, sp.Interval(-1, 1))
    assert result is not None and result.complete
    assert result.roots == (sp.Integer(0),)
    root_certificates = [c for c in result.certificates if c.root_count == 1]
    assert any(c.multiplicity == 2 for c in root_certificates)


def test_partition_isolator_does_not_claim_completeness_without_finite_partition():
    result = _certified_real_interval_isolation(sp.sin(x), x, sp.S.Reals)
    assert result is None
