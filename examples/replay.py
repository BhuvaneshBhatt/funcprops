"""Native witnesses replay after the proposing entrypoints are disabled."""

from dataclasses import replace
from unittest.mock import patch

import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)
proof = fp.prove_root_coverage(sp.exp(x) - 2, x, sp.Interval(0, 1))
assert proof.verify() and proof.complete


def forbidden(*args, **kwargs):
    raise AssertionError("replay invoked proposing search")


with patch("funcprops.coverage_search.propose_leaf", forbidden):
    assert fp.verify_certificate(proof)
assert not fp.verify_certificate(replace(proof, root_count=77))
assert not fp.verify_certificate(proof, expr=sp.exp(x) - 3, var=x)
assert fp.replay_status(proof).outcome == "complete-coverage"
assert fp.replay_status(object()).certified is None
