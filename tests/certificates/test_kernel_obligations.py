"""Sentinels used by the isolated checker-mutation runner."""

from dataclasses import replace

import sympy as sp

import funcprops as fp

x = sp.Symbol("x", real=True)


def test_omitted_domain_is_rejected_even_with_recomputed_totals():
    proof = fp.prove_root_coverage(x - 1, x, sp.Interval(-2, 2))
    assert proof.verify() and proof.complete
    forged = replace(proof, leaves=(), root_count=0, multiplicity_count=0)
    assert not forged.verify()


def test_duplicate_domain_is_rejected_even_with_recomputed_totals():
    proof = fp.prove_root_coverage(x - 1, x, sp.Interval(-2, 2))
    assert len(proof.leaves) == 1 and proof.verify()
    forged = replace(proof, leaves=proof.leaves * 2, root_count=2, multiplicity_count=2)
    assert not forged.verify()


def test_changed_source_syntax_cannot_rebind_every_leaf():
    proof = fp.prove_root_coverage(x - 1, x, sp.Interval(-2, 2))
    context = replace(proof.context, source_syntax="forged-source")
    forged = replace(
        proof,
        context=context,
        leaves=tuple(replace(leaf, context=context) for leaf in proof.leaves),
    )
    assert proof.verify() and not forged.verify()
