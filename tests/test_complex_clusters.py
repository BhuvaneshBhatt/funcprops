from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

z = sp.Symbol("z")


@pytest.mark.parametrize(
    "f,R,count",
    [
        (sp.exp(z) - 1, sp.Rational(1, 2), 1),
        ((sp.exp(z) - 1) ** 2, sp.Rational(1, 4), 2),
        ((sp.exp(z) - 1) ** 3, sp.Rational(1, 4), 3),
        ((z * z + sp.Rational(1, 100)) ** 2, sp.Rational(1, 2), 4),
        (z - sp.I, sp.Rational(1, 2), 0),
    ],
)
def test_analytic_cluster_count_does_not_infer_real_or_distinct_roots(f, R, count):
    r = fp.certify_complex_cluster(f, z, 0, R)
    assert r.complete and r.zero_count == count and r.multiplicity_count == count
    assert r.verify() and fp.verify_certificate(r)
    assert fp.replay_status(r).outcome == "complete-coverage"
    assert fp.replay_status(r).factory_replay is False
    if count:
        assert r.real_root_count is None and r.distinct_root_count is None
        assert r.individual_multiplicities is None


def test_nonreal_center():
    r = fp.certify_complex_cluster((z - sp.I) ** 2, z, sp.I, sp.Rational(1, 2))
    assert r.verify() and r.zero_count == 2


@pytest.mark.parametrize(
    "f",
    [
        z - sp.Rational(1, 2),
        sp.log(z),
        sp.sqrt(z),
        sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False),
        sp.exp(z * z),
        sp.tan(z),
    ],
)
def test_complex_boundary_obligations(f):
    r = fp.certify_complex_cluster(
        f, z, 0, sp.Rational(1, 2), policy=fp.EnclosurePolicy(max_taylor_order=8)
    )
    assert not r.complete and r.zero_count is None and not r.verify()


def test_source_parameter_and_coordinate_guards():
    a = sp.Symbol("a")
    for f, variable in ((z - a, z), (sp.exp(z) - 1, sp.Symbol("z", real=True))):
        r = fp.certify_complex_cluster(f, variable, 0, sp.Rational(1, 2))
        assert not r.complete and not r.verify()


def test_complex_witness_mutations_and_independent_replay(monkeypatch):
    r = fp.certify_complex_cluster((sp.exp(z) - 1) ** 2, z, 0, sp.Rational(1, 4))
    for altered in (
        replace(r, zero_count=1),
        replace(r, remainder=0),
        replace(r, radius=1),
        replace(r, source_syntax="wrong"),
        replace(r, coefficients=(sp.S.Zero,) * len(r.coefficients)),
        replace(r, coefficient_bounds=r.coefficient_bounds[:-1]),
        replace(r, majorant_bound=replace(r.majorant_bound, lower=0, upper=0)),
    ):
        assert not altered.verify()

    def disabled(*args, **kwargs):
        raise AssertionError("cluster search called during replay")

    monkeypatch.setattr("funcprops.complex_clusters.certify_complex_cluster", disabled)
    assert r.verify()
    assert not fp.verify_certificate(r, expr=sp.exp(z) - 1, var=z)


def test_order_and_cell_budget_can_decline():
    for policy in (
        fp.EnclosurePolicy(max_taylor_order=0),
        fp.EnclosurePolicy(max_cells=0),
    ):
        r = fp.certify_complex_cluster(
            sp.exp(z) - 1, z, 0, sp.Rational(1, 2), policy=policy
        )
        assert not r.complete and r.zero_count is None
