import sympy as sp

import funcprops as fp


def test_multivariate_rational_pole_is_hypersurface():
    x, y = sp.symbols("x y")
    result = fp.function_singularities(1 / (x + y), (x, y), return_result=True)
    expected = sp.Eq(sp.re(x) + sp.re(y), 0) & sp.Eq(sp.im(x) + sp.im(y), 0)
    assert result.singularities == expected
    assert result.poles == expected


def test_multivariate_log_cut_is_preimage_of_nonpositive_real_axis():
    x, y = sp.symbols("x y")
    result = fp.function_singularities(sp.log(x + y), (x, y), return_result=True)
    point = sp.Eq(sp.re(x) + sp.re(y), 0) & sp.Eq(sp.im(x) + sp.im(y), 0)
    cut = sp.Eq(sp.im(x) + sp.im(y), 0) & (sp.re(x) + sp.re(y) < 0)
    assert result.branch_points == point
    assert result.branch_cuts == cut
    assert result.singularities == (
        sp.Eq(sp.im(x) + sp.im(y), 0) & (sp.re(x) + sp.re(y) <= 0)
    )


def test_open_support_excludes_hypersurface_but_retains_boundary_classification():
    x, y = sp.symbols("x y", real=True)
    expr = fp.ConditionalExpression(1 / (x + y), (x > 0) & (y > 0))
    result = fp.function_singularities(expr, (x, y), sp.S.Reals, return_result=True)
    assert result.singularities is sp.S.false
    assert result.interior_singularities is sp.S.false
    assert result.boundary_singularities is not sp.S.false
    assert result.exterior_singularities is not sp.S.false


def test_closed_support_keeps_boundary_singularity():
    x, y = sp.symbols("x y", real=True)
    expr = fp.ConditionalExpression(1 / (x + y), (x >= 0) & (y >= 0))
    result = fp.function_singularities(expr, (x, y), sp.S.Reals, return_result=True)
    assert result.singularities is not sp.S.false
    assert result.interior_singularities is sp.S.false
    assert result.boundary_singularities is not sp.S.false


def test_unrestricted_domain_has_only_interior_singularities():
    x, y = sp.symbols("x y", real=True)
    result = fp.function_singularities(
        1 / (x + y), (x, y), sp.S.Reals, return_result=True
    )
    assert result.interior_singularities == result.unrestricted_singularities
    assert result.boundary_singularities is sp.S.false
    assert result.exterior_singularities is sp.S.false


def test_multivariate_classification_coverage_is_complete():
    x, y = sp.symbols("x y")
    u = x + y

    pole = fp.function_singularities(1 / u, (x, y), return_result=True)
    removable = fp.function_singularities(sp.sin(u) / u, (x, y), return_result=True)
    essential = fp.function_singularities(sp.exp(1 / u), (x, y), return_result=True)
    branch = fp.function_singularities(sp.log(u), (x, y), return_result=True)

    xr, yr = sp.symbols("xr yr", real=True)
    sign = fp.function_singularities(
        sp.sign(xr + yr), (xr, yr), sp.S.Reals, return_result=True
    )

    cases = (
        (pole, "poles", fp.SingularityKind.POLE),
        (removable, "removable", fp.SingularityKind.REMOVABLE),
        (essential, "essential", fp.SingularityKind.ESSENTIAL),
        (branch, "branch_points", fp.SingularityKind.BRANCH_POINT),
        (branch, "branch_cuts", fp.SingularityKind.BRANCH_CUT),
        (sign, "definition_cuts", fp.SingularityKind.DEFINITION_CUT),
        (sign, "discontinuities", fp.SingularityKind.DISCONTINUITY),
    )
    for result, field, kind in cases:
        assert getattr(result, field) is not sp.S.false
        assert any(record.kind is kind for record in result.records)
        assert result.singularities is not sp.S.false

    field_for_kind = {
        fp.SingularityKind.POLE: "poles",
        fp.SingularityKind.REMOVABLE: "removable",
        fp.SingularityKind.ESSENTIAL: "essential",
        fp.SingularityKind.BRANCH_POINT: "branch_points",
        fp.SingularityKind.BRANCH_CUT: "branch_cuts",
        fp.SingularityKind.DEFINITION_CUT: "definition_cuts",
        fp.SingularityKind.DISCONTINUITY: "discontinuities",
    }
    for result in (pole, removable, essential, branch, sign):
        for record in result.records:
            assert getattr(result, field_for_kind[record.kind]) is not sp.S.false


def test_multivariate_classification_is_symmetric_under_variable_exchange():
    x, y = sp.symbols("x y")
    expressions = (
        sp.sin(x + 2 * y) / (x + 2 * y),
        sp.log(x + 2 * y),
    )
    fields = (
        "poles",
        "removable",
        "essential",
        "branch_points",
        "branch_cuts",
        "definition_cuts",
        "discontinuities",
        "singularities",
    )
    exchange = {x: y, y: x}
    for expr in expressions:
        original = fp.function_singularities(expr, (x, y), return_result=True)
        swapped = fp.function_singularities(
            expr.xreplace(exchange), (y, x), return_result=True
        )
        for field in fields:
            expected = getattr(original, field).xreplace(exchange)
            assert getattr(swapped, field) == expected


def test_multivariate_registry_pullback_preserves_special_function_classification():
    x, y = sp.symbols("x y")
    result = fp.function_singularities(
        sp.besselj(sp.Rational(1, 2), x + y), (x, y), return_result=True
    )
    assert result.branch_points is not sp.S.false
    assert result.branch_cuts is not sp.S.false
    assert any(
        record.kind is fp.SingularityKind.BRANCH_POINT
        and record.source.startswith("multivariate-pullback")
        for record in result.records
    )


def test_joint_registry_transport_preserves_two_argument_geometry():
    x, y = sp.symbols("x y")
    result = fp.function_singularities(sp.elliptic_e(x, y), (x, y), return_result=True)

    branch_point_conditions = {
        record.condition
        for record in result.records
        if record.kind is fp.SingularityKind.BRANCH_POINT
        and record.source == "registry"
    }
    assert sp.Eq(y * sp.sin(x) ** 2, 1) in branch_point_conditions
    assert sp.Eq(sp.cos(x), 0) in branch_point_conditions
    assert result.branch_points is not sp.S.false
    assert result.branch_cuts is not sp.S.false

    dummy_names = {
        symbol.name
        for record in result.records
        for symbol in (record.condition.free_symbols | record.guard.free_symbols)
        if symbol.name.startswith("_funcprops_")
    }
    assert dummy_names == set()


def test_joint_registry_transport_preserves_real_definition_cut_guards():
    x, y = sp.symbols("x y", real=True)
    result = fp.function_singularities(
        sp.elliptic_e(x, y), (x, y), sp.S.Reals, return_result=True
    )

    definition_records = [
        record
        for record in result.records
        if record.kind is fp.SingularityKind.DEFINITION_CUT
        and record.source == "registry"
    ]
    assert any(
        record.condition == sp.Eq(y, 1) and record.guard is sp.S.true
        for record in definition_records
    )
    assert any(
        record.condition == ((y > 1) & sp.Eq(x, sp.pi / 2))
        and record.guard is sp.S.true
        for record in definition_records
    )
    assert result.definition_cuts is not sp.S.false


def test_joint_registry_transport_is_invariant_under_alpha_renaming():
    x, y, u, v = sp.symbols("x y u v")
    first = fp.function_singularities(sp.elliptic_e(x, y), (x, y), return_result=True)
    second = fp.function_singularities(sp.elliptic_e(u, v), (u, v), return_result=True)
    rename = {x: u, y: v}

    def registry_signature(result):
        return {
            (
                record.kind,
                record.condition,
                record.guard,
                record.multiplicity,
            )
            for record in result.records
            if record.source == "registry"
        }

    expected = {
        (kind, condition.xreplace(rename), guard.xreplace(rename), multiplicity)
        for kind, condition, guard, multiplicity in registry_signature(first)
    }
    assert registry_signature(second) == expected
