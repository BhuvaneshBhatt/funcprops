"""Coherent malformed proofs must not manufacture image or parameter claims."""

from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.parameter_contract import ParameterRootCell
from funcprops.real_images.critical_values import ImageSite, site_value

x, y, a, b = sp.symbols("x y a b", real=True)


@pytest.fixture(scope="module")
def convex_cover():
    return fp.parameter_root_coverage(sp.exp(x) - 1 - x - a, x, a, sp.Interval(-1, 1))


def test_compound_minimum_cell(convex_cover):
    witness = next(c.witness for c in convex_cover.cells if c.region == sp.FiniteSet(0))
    domain = sp.FiniteSet(0, 2)
    bad = replace(
        convex_cover,
        parameter_domain=domain,
        cells=(ParameterRootCell(domain, "convex-level", 0, 0, witness),),
    )
    assert not bad.verify() and not fp.verify_certificate(bad)
    good = replace(
        convex_cover,
        parameter_domain=domain,
        cells=(
            ParameterRootCell(sp.FiniteSet(0), "convex-level", 1, 2, witness),
            ParameterRootCell(sp.FiniteSet(2), "convex-level", 0, 0, witness),
        ),
    )
    assert good.verify()
    p = fp.specialize_parameter_coverage(good, 0)
    assert p.verify() and (p.root_count, p.multiplicity_count) == (1, 2)


@pytest.mark.parametrize("guard", [x > 0, y > 0, b > 0, sp.Integer(1)])
def test_parameter_guard_scope(guard):
    r = fp.analyze_parameter_range(x * x + a * x, x, (a,), sp.Interval(-1, 1), value=y)
    # Change the premise and formula together to test their source binding.
    condition = (
        sp.And(guard, r.condition)
        if isinstance(guard, sp.logic.boolalg.Boolean)
        else r.condition
    )
    assert not replace(r, parameter_domain=guard, condition=condition).verify()
    with pytest.raises(ValueError):
        fp.analyze_parameter_range(
            x * x + a * x, x, (a,), sp.Interval(-1, 1), value=y, parameter_domain=guard
        )


@pytest.mark.parametrize(
    "expression,domain",
    [
        (1 / x, sp.FiniteSet(0)),
        (sp.I * x, sp.FiniteSet(sp.I)),
        (sp.I, sp.FiniteSet(1)),
        (sp.Float(1) * x, sp.FiniteSet(1)),
    ],
)
def test_invalid_finite_sites(expression, domain):
    sites = tuple(
        ImageSite(p, site_value(expression, x, p), True, "point") for p in domain
    )
    cover = fp.CriticalValueCover(expression, x, domain, sites=sites)
    assert not cover.verify() and not fp.verify_certificate(cover)


def test_finite_complex_intermediates():
    domain = sp.FiniteSet(0)
    expression = (x + sp.I) ** 2
    cover = fp.CriticalValueCover(
        expression, x, domain, sites=(ImageSite(sp.S.Zero, -sp.S.One, True, "point"),)
    )
    assert cover.verify() and fp.verify_certificate(cover)


def test_intrinsic_parameter_scope():
    p = sp.Symbol("positive_parameter", positive=True)
    f = sp.exp(x) - 1 - x - p
    with pytest.raises(ValueError, match="parameter_domain"):
        fp.parameter_root_coverage(f, x, p, sp.Interval(-1, 1))
    r = fp.parameter_root_coverage(
        f, x, p, sp.Interval(-1, 1), parameter_domain=sp.Interval.open(0, sp.oo)
    )
    assert r.complete and r.verify()
    value = fp.specialize_parameter_coverage(r, sp.Rational(1, 10))
    assert value.verify() and value.root_count == 2
    assert not fp.specialize_parameter_coverage(r, -1).verify()
