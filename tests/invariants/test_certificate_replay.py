"""Certificates must encode mathematical claims that can be replayed independently."""

import sympy as sp

import funcprops as fp
from funcprops.real_analysis.advanced_convexity import ConvexityCertificate
from funcprops.results import PropertyResult

x = sp.symbols("x", real=True)


def test_strong_convexity_modulus_replays_as_second_derivative_bound():
    expr = 3 * x**2 + 2 * x + 1
    result = fp.function_convexity(expr, x, details=True, all_properties=True)
    assert isinstance(result, PropertyResult)
    cert = next(
        item for item in result.evidence if isinstance(item, ConvexityCertificate)
    )
    assert cert.classification is fp.Convexity.STRONGLY_CONVEX
    residual = sp.diff(expr, x, 2) - cert.modulus
    assert fp.function_sign(residual, x) in {
        fp.Sign.ZERO,
        fp.Sign.NONNEGATIVE,
        fp.Sign.POSITIVE,
    }
