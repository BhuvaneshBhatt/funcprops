import sympy as sp

import funcprops as fp


def test_argument_principle_certifies_one_exp_root():
    z = sp.symbols("z")
    cert = fp.argument_principle_count(
        sp.exp(z) - 1,
        z,
        (-1 - sp.I, 1 + sp.I),
        precision=50,
    )
    assert cert.certified
    assert cert.winding_number == 1
    assert cert.zero_count == 1
    assert cert.pole_count == 0
    assert cert.method == "validated_interval_argument_principle"
    assert cert.boundary_segments >= 4


def test_argument_principle_refuses_boundary_zero():
    z = sp.symbols("z")
    cert = fp.argument_principle_count(
        sp.exp(z) - 1,
        z,
        (0 - sp.I, 1 + sp.I),
        precision=40,
        max_boundary_depth=8,
    )
    assert not cert.certified
    assert cert.zero_count is None


def test_complex_isolation_separates_three_sine_roots():
    z = sp.symbols("z")
    result = fp.complex_zeros(
        sp.sin(z),
        z,
        rectangle=(-4 - sp.I, 4 + sp.I),
        return_result=True,
        precision=50,
        max_isolation_depth=6,
    )
    assert result.complete
    assert result.total_count == 3
    assert len(result.rectangles) == 3
    assert all(item.root_count == 1 for item in result.rectangles)
    assert sum(item.root_count for item in result.rectangles) == result.total_count
    assert all(item.certificate.certified for item in result.rectangles)


def test_exact_complex_roots_are_returned_as_mathematical_set():
    z = sp.symbols("z")
    roots = fp.complex_zeros(
        z**3 - 1,
        z,
        rectangle=(-2 - 2 * sp.I, 2 + 2 * sp.I),
    )
    assert isinstance(roots, sp.FiniteSet)
    assert len(roots) == 3
    assert sp.Integer(1) in roots


def test_unresolved_branch_geometry_is_not_certified():
    z = sp.symbols("z")
    cert = fp.argument_principle_count(
        sp.log(z) - 1,
        z,
        (-2 - sp.I, 2 + sp.I),
        precision=40,
    )
    assert not cert.certified
    assert cert.zero_count is None
    assert cert.analytic_certificate.holomorphic is not True
