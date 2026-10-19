"""The new oracle retains pointwise and domain transfer boundaries."""

from unittest.mock import patch

import sympy as sp
from exprtools import zerotest

import funcprops.exactness as boundary


def test_exprtools_preserves_symbolic_nonidentity_vs_pointwise_zero():
    assert boundary.zerotest is zerotest
    x = sp.Symbol("x", real=True)
    assert boundary.certify_identity_zero(x) is False
    assert boundary.certify_zero(x) is None
    assert boundary.certify_zero(x, sp.Q.positive(x)) is False


def test_unknown_and_certified_confidence_are_preserved():
    x = sp.Symbol("x")
    with patch.object(boundary, "zerotest", return_value=None) as oracle:
        assert boundary.certify_zero(sp.sin(x)) is None
    oracle.assert_called_once_with(sp.sin(x), assumptions=True, confidence="certified")


def test_formula_cancellation_does_not_transfer_across_a_domain_hole():
    x = sp.Symbol("x", real=True)
    assert (
        boundary.certify_identity_equal_on_domain((x * x - 1) / (x - 1), x + 1, x)
        is not True
    )
