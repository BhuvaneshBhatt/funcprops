"""Checked isolating evidence is reused without root discovery."""

import pickle
import sys
from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)


def test_nonrational_bracket():
    p = fp.adaptive_root_coverage(
        2 * x + sp.cos(x), x, sp.Interval.open(-sp.pi / 4, 0)
    ).proof
    assert p.complete and p.root_count == 1
    called = []

    def observe(frame, event, arg):
        if event == "call" and frame.f_code is fp.adaptive_root_coverage.__code__:
            called.append(frame.f_code.co_name)

    before = sys.getprofile()
    sys.setprofile(observe)
    try:
        root = fp.ImplicitRealRoot.from_cover(p)
        assert root.verify() and fp.verify_certificate(
            root, expr=2 * x + sp.cos(x), var=x
        )
        assert root.enclosure(14).measure < sp.Rational(1, 10**13)
        assert pickle.loads(pickle.dumps(root)).verify()
    finally:
        sys.setprofile(before)
    assert called == []
    with pytest.raises(ValueError):
        fp.ImplicitRealRoot.from_cover(replace(p, root_count=2))


def test_reflected_values():
    positive = fp.implicit_real_root(
        x - sp.cos(x), x, sp.Interval(sp.Rational(1, 2), 1)
    )
    negative = fp.implicit_real_root(
        x + sp.cos(x), x, sp.Interval(-1, -sp.Rational(1, 2))
    )
    left = fp.critical_value(x * x, x, positive)
    right = fp.critical_value(x * x, x, negative)
    assert fp.critical_values_equal(left, right) is True
    assert (
        fp.critical_values_equal(left, fp.critical_value(x * x + 1, x, negative))
        is None
    )
    p = fp.adaptive_root_coverage(x - sp.cos(x), x, sp.Interval(0, 1)).proof
    assert positive.same_root(fp.ImplicitRealRoot.from_cover(p)) is True


def test_false_exact_root_metadata():
    p = fp.adaptive_root_coverage((sp.exp(x) - 2) ** 3, x, sp.Interval(0, 1)).proof
    assert p.complete and p.verify()
    index = next(i for i, candidate in enumerate(p.leaves) if candidate.root_count == 1)
    leaf = p.leaves[index]
    bad = replace(leaf, roots=((sp.Rational(1, 2), leaf.multiplicity_count),))
    assert not bad.verify()


def test_bound_coordinates_are_constant():
    p = fp.adaptive_root_coverage(
        2 * x + sp.cos(x), x, sp.Interval.open(-sp.pi / 4, 0)
    ).proof
    root = fp.ImplicitRealRoot.from_cover(p)
    value = fp.critical_value(x * x + sp.sin(x), x, root)
    z = sp.Symbol("z", real=True)
    assert root.subs(x, z) == root and root.xreplace({x: z}) == root
    assert value.subs(x, z) == value and value.xreplace({x: z}) == value


def test_normalization_keeps_root_evidence():
    held = sp.Add(
        x - sp.cos(x),
        sp.Mul(0, sp.Pow(x - 100, -1, evaluate=False), evaluate=False),
        evaluate=False,
    )
    p = fp.adaptive_root_coverage(held, x, sp.Interval(0, sp.pi / 2)).proof
    assert p.complete and p.root_count == 1
    root = fp.ImplicitRealRoot.from_cover(p)
    assert fp.normalize_real_expression(root) is root
    assert root.verify()
