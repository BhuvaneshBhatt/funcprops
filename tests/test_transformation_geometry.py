import sympy as sp

from funcprops import (
    Sign,
    TruthValue,
    change_of_variables,
    determinant_nonvanishing,
    jacobian,
    local_invertibility,
    transformation_geometry,
    verify_certificate,
)


def test_exact_jacobian_and_affine_local_invertibility():
    x, y = sp.symbols("x y", real=True)
    exprs = (2 * x + y, x - y)
    jac = jacobian(exprs, (x, y))
    assert jac == sp.ImmutableMatrix([[2, 1], [1, -1]])
    jac_cert = jacobian(exprs, (x, y), return_result=True)
    assert jac_cert.verify()
    assert determinant_nonvanishing(exprs, (x, y)) is TruthValue.TRUE
    nonzero = determinant_nonvanishing(exprs, (x, y), return_result=True)
    assert nonzero.determinant == -3
    assert nonzero.classification is TruthValue.TRUE
    assert verify_certificate(nonzero)
    assert local_invertibility(exprs, (x, y)) is TruthValue.TRUE
    local = local_invertibility(exprs, (x, y), return_result=True)
    assert local.classification is TruthValue.TRUE
    assert verify_certificate(local)


def test_singular_jacobian_is_not_nonvanishing_on_whole_domain():
    x, y = sp.symbols("x y", real=True)
    exprs = (x**2, y)
    assert determinant_nonvanishing(exprs, (x, y)) is TruthValue.FALSE
    nonzero = determinant_nonvanishing(exprs, (x, y), return_result=True)
    assert nonzero.determinant == 2 * x
    assert nonzero.classification is TruthValue.FALSE
    assert nonzero.source == "semialgebraic-zero-witness"
    assert local_invertibility(exprs, (x, y)) is TruthValue.FALSE


def test_domain_restriction_certifies_polar_map_away_from_origin():
    r, theta = sp.symbols("r theta", real=True)
    exprs = (r * sp.cos(theta), r * sp.sin(theta))
    cert = determinant_nonvanishing(exprs, (r, theta), domain=r > 0, return_result=True)
    assert sp.simplify(cert.determinant - r) == 0
    assert cert.classification is TruthValue.TRUE
    assert cert.verify()


def test_parameter_assumption_certifies_linear_scaling():
    a = sp.symbols("a", nonzero=True, real=True)
    x, y = sp.symbols("x y", real=True)
    cert = determinant_nonvanishing((a * x, y), (x, y), return_result=True)
    assert cert.determinant == a
    assert cert.classification is TruthValue.TRUE
    assert cert.verify()


def test_substitution_orientation():
    x, y = sp.symbols("x y", real=True)
    cert = change_of_variables((2 * x + y, x - y), (x, y))
    assert cert.classification is TruthValue.TRUE
    assert cert.volume_factor == 3
    assert cert.orientation is Sign.NEGATIVE
    assert cert.verify()
    assert verify_certificate(cert)


def test_nonsquare_map_stays_unknown_for_inverse_function_theorem():
    x, y = sp.symbols("x y", real=True)
    local = local_invertibility((x + y,), (x, y), return_result=True)
    assert local.classification is TruthValue.UNKNOWN
    assert local.source == "nonsquare-map"
    cov = change_of_variables((x + y,), (x, y))
    assert cov.classification is TruthValue.UNKNOWN


def test_transformation_geometry():
    x, y = sp.symbols("x y", real=True)
    result = transformation_geometry((x + y, x - y), (x, y))
    assert result.jacobian.verify()
    assert result.determinant == -2
    assert result.determinant_nonvanishing.classification is TruthValue.TRUE
    assert result.local_invertibility.classification is TruthValue.TRUE
    assert result.change_of_variables.classification is TruthValue.TRUE
    assert result.change_of_variables.absolute_determinant == 2


def test_nonlinear_jacobian_is_exact_before_invertibility_analysis():
    x, y = sp.symbols("x y", real=True)
    jac = jacobian((x**2 + y, sp.sin(x) + y**2), (x, y))
    assert jac == sp.ImmutableMatrix([[2 * x, 1], [sp.cos(x), 2 * y]])
    assert jacobian((x**2 + y, sp.sin(x) + y**2), (x, y), return_result=True).verify()


def test_transformation_geometry_preserves_unknown_for_nonsquare_map():
    x, y = sp.symbols("x y", real=True)
    result = transformation_geometry((x + y,), (x, y))
    assert result.determinant is sp.S.NaN
    assert result.local_invertibility.classification is TruthValue.UNKNOWN
    assert result.change_of_variables.classification is TruthValue.UNKNOWN


def test_singular_change_of_variables_replays_negative_certificate():
    x, y = sp.symbols("x y", real=True)
    cert = change_of_variables((x, 0), (x, y))
    assert cert.classification is TruthValue.FALSE
    assert cert.local_invertibility.classification is TruthValue.FALSE
    assert cert.verify()
    assert verify_certificate(cert)


def test_transformation_rejects_invalid_coordinates():
    x = sp.symbols("x")
    for variables in ((), (x, x)):
        try:
            jacobian((x,), variables)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected invalid variables to fail: {variables!r}")
    try:
        jacobian((x,), 1)
    except TypeError:
        pass
    else:
        raise AssertionError("numeric coordinate should fail")
