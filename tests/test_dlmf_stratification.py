import sympy as sp
from sympy import S

from funcprops import (
    Boundedness,
    PropertyResult,
    dlmf_audit_report,
    function_boundedness,
    function_domain,
    function_poles,
    function_range,
)

x, y = sp.symbols("x y", real=True)
a, b, nu = sp.symbols("a b nu", real=True)


def _case(result, predicate):
    assert isinstance(result, PropertyResult)
    return [c for c in result.cases if predicate(c)]


def test_besseli_parameter_domain_stratification_from_catalogue():
    r = function_domain(sp.besseli(nu, x), x, stratified=True)
    assert isinstance(r, PropertyResult)
    assert any(
        c.value is S.true and c.condition.has(sp.Contains(nu, S.Integers))
        for c in r.cases
    )
    assert any(
        sp.simplify(c.value - (x >= 0)) is S.true if False else c.value == (x >= 0)
        for c in r.cases
    )


def test_besseli_parameter_dependent_range_endpoint_open_and_closed():
    ro = function_range(sp.besseli(nu, x), x, y, constraints=x > 0)
    rc = function_range(sp.besseli(nu, x), x, y, constraints=x >= 0)
    assert any(c.value == (y > 1) and c.condition == sp.Eq(nu, 0) for c in ro.cases)
    assert any(c.value == (y >= 1) and c.condition == sp.Eq(nu, 0) for c in rc.cases)
    assert any(
        c.value == (y > 0) and c.condition == sp.StrictGreaterThan(nu, 0)
        for c in ro.cases
    )
    assert any(
        c.value == (y >= 0) and c.condition == sp.StrictGreaterThan(nu, 0)
        for c in rc.cases
    )


def test_incomplete_gamma_parameter_endpoint_and_boundedness():
    lo = function_range(sp.lowergamma(a, x), x, y, constraints=x >= 0)
    up = function_range(sp.uppergamma(a, x), x, y, constraints=x >= 0)
    assert lo.cases[0].value == sp.And(y >= 0, y < sp.gamma(a))
    assert up.cases[0].value == sp.And(y > 0, y <= sp.gamma(a))
    bl = function_boundedness(sp.lowergamma(a, x), x, domain=x >= 0)
    assert bl.cases[0].value is Boundedness.BOUNDED
    assert bl.cases[0].condition == (a > 0)


def test_incomplete_beta_parameter_dependent_endpoint():
    expr = sp.betainc(a, b, 0, x)
    r = function_range(expr, x, y, constraints=sp.And(x >= 0, x <= 1))
    assert r.cases[0].value == sp.And(y >= 0, y <= sp.beta(a, b))
    assert (
        sp.simplify_logic(sp.Equivalent(r.cases[0].condition, sp.And(a > 0, b > 0)))
        is S.true
    )
    rr = function_range(
        sp.betainc_regularized(a, b, 0, x), x, y, constraints=sp.And(x >= 0, x <= 1)
    )
    assert rr.cases[0].value == sp.And(y >= 0, y <= 1)


def test_zeta_registry_pole_not_erased_by_failed_local_series():
    s = sp.symbols("s")
    poles = function_poles(sp.zeta(s), s)
    assert any(p.condition == sp.Eq(s, 1) for p in poles)


def test_dlmf_audit_manifest_covers_catalogue_and_is_structurally_clean():
    report = dlmf_audit_report()
    assert report["summary"]["catalogue_families"] == 233
    assert report["summary"]["dlmf_scoped"] >= 130
    assert report["summary"]["hand_audited"] >= 30
    assert report["summary"]["structural_issue_count"] == 0
    assert dlmf_audit_report("besseli")["status"] == "hand-audited-core"
