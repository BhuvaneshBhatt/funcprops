"""Krawczyk theorem witnesses, transferred complements and bounded integration."""

import pickle
from dataclasses import replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops import analytic_contours as ac
from funcprops import complex_isolation as ci
from funcprops import complex_newton as cn
from funcprops._checkpoints import capture_checkpoints
from funcprops.complex_interval import complex_box_jet

z = sp.Symbol("z")
R = sp.Rational(1, 10)
RECT = (-R - sp.I * R, R + sp.I * R)


@pytest.fixture(scope="module")
def parent():
    p = fp.certify_analytic_contour(sp.exp(z) - 1, z, *RECT)
    assert p.verify() and p.zero_count == 1
    return p


@pytest.fixture(scope="module")
def refinement(parent):
    c = fp.certify_complex_refinement(parent)
    assert c.verify()
    return c


@pytest.fixture(scope="module")
def isolated():
    q = fp.certify_complex_isolation(
        sp.exp(z) - 1,
        z,
        *RECT,
        max_box_diameter=sp.Rational(1, 10**8),
        policy=fp.EnclosurePolicy(max_depth=32),
    )
    assert q.complete and q.verify() and q.refinements
    return q


@pytest.mark.parametrize(
    "expr",
    [
        z,
        sp.S.One,
        sp.pi,
        sp.I,
        z**4 + z * sp.exp(z),
        sp.sin(z**2 + 1),
        sp.cos(z),
        sp.sinh(sp.I * z),
        sp.cosh(z + sp.I / 5),
        sp.erf(z),
        sp.erfc(z * z + z),
        sp.exp(sp.sin(z)),
        (z + sp.I) ** 3 * sp.exp(z / 3),
    ],
)
def test_structural_derivative_reference(expr):
    p = sp.Rational(1, 10) + sp.I / 20
    box = (sp.re(p), sp.im(p), sp.re(p), sp.im(p))
    result = complex_box_jet(expr, z, box)
    for enclosure, expected in zip(
        result, (expr.subs(z, p), sp.diff(expr, z).subs(z, p)), strict=True
    ):
        real, imag = sp.N(expected, 100).as_real_imag()
        a, b, c, d = enclosure
        assert a <= real <= c and b <= imag <= d


@pytest.mark.parametrize(
    "expr", [sp.sin(z * z + z) * sp.exp(z), sp.erf(z + z * z), sp.erfc(sp.sin(z))]
)
def test_derivative_on_a_box_encloses_interior_and_corner_references(expr):
    result = complex_box_jet(expr, z, (-R, -R, R, R))
    a, b, c, d = result[1]
    derivative = sp.diff(expr, z)
    for x in (-R, sp.S.Zero, R):
        for y in (-R, sp.S.Zero, R):
            real, imag = sp.N(derivative.subs(z, x + sp.I * y), 100).as_real_imag()
            assert a <= real <= c and b <= imag <= d


@pytest.mark.parametrize(
    "expr",
    [
        sp.log(z),
        sp.conjugate(z),
        sp.Abs(z),
        sp.exp(sp.Symbol("a") * z),
        sp.Float(".5") * z,
        sp.Mul(z, sp.Pow(z, -1, evaluate=False), evaluate=False),
    ],
)
def test_derivative_does_not_expand_the_source_grammar(expr):
    assert complex_box_jet(expr, z, (-R, -R, R, R)) is None


def test_strict_contraction_child_and_all_complements(refinement):
    c = refinement
    assert 0 <= c.contraction < 1 and c.root_count == c.multiplicity_count == 1
    assert cn._inside(c.image, c.child_rectangle.bounds())
    assert cn._inside(c.child_rectangle.bounds(), c.rectangle.bounds())
    assert c.image[0] <= 0 <= c.image[2] and c.image[1] <= 0 <= c.image[3]
    assert len(c.zero_regions) == 4
    assert [r.zero_count for r in c.regions] == [1, 0, 0, 0, 0]
    assert all(r.verify() for r in c.regions)
    assert all(
        fp.verify_certificate(r, expr=sp.exp(z) - 1, var=z)
        for r in (*c.regions, c, c.derivative, c.center_derivative)
    )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda c: replace(c, expression=sp.sin(z)),
        lambda c: replace(c, variable=sp.Symbol("w")),
        lambda c: replace(c, source_syntax="changed"),
        lambda c: replace(c, coordinate_assumptions=()),
        lambda c: replace(c, center=sp.S.One),
        lambda c: replace(c, inverse=sp.S.Zero),
        lambda c: replace(c, inverse=c.inverse + 1),
        lambda c: replace(c, residual=(sp.S.Zero,) * 4),
        lambda c: replace(c, image=(sp.S.Zero,) * 4),
        lambda c: replace(c, contraction=sp.S.One),
        lambda c: replace(c, contraction=sp.S.Zero),
        lambda c: replace(c, child_rectangle=c.rectangle),
        lambda c: replace(c, parent=replace(c.parent, zero_count=2)),
        lambda c: replace(c, parent=object()),
        lambda c: replace(c, derivative=replace(c.derivative, bounds=(sp.S.Zero,) * 4)),
        lambda c: replace(
            c, derivative=replace(c.derivative, expression=sp.exp(2 * z))
        ),
        lambda c: replace(c, derivative=replace(c.derivative, box=cn._point(c.center))),
        lambda c: replace(c, derivative=replace(c.derivative, order=2)),
        lambda c: replace(
            c, center_derivative=replace(c.center_derivative, bounds=(sp.S.One,) * 4)
        ),
        lambda c: replace(c, value=replace(c.value, bounds=(sp.S.One,) * 4)),
        lambda c: replace(c, value=replace(c.value, box=c.rectangle.bounds())),
        lambda c: replace(c, tested=True),
    ],
)
def test_false_derivatives_inverses_and_enclosures_rejected(refinement, mutation):
    assert mutation(refinement).check().certified is False


@pytest.mark.parametrize("version", [True, 0, 2])
def test_unsupported_refinement_schemas(refinement, version):
    status = fp.replay_status(replace(refinement, schema_version=version))
    assert status.certified is not True and not status.complete


def test_parent_graph_cannot_be_cyclic(refinement):
    cyclic = replace(refinement)
    object.__setattr__(cyclic, "parent", fp.ComplexNewtonRegion(cyclic, 0))
    assert not cyclic.verify()


def test_self_attesting_nested_witnesses_rejected(refinement):
    class ForgedDerivative(fp.ComplexDerivativeWitness):
        def verify(self):
            return True

    class ForgedRegion(fp.ComplexNewtonRegion):
        def verify(self):
            return True

    fake = ForgedDerivative(**refinement.derivative.__dict__)
    assert not replace(refinement, derivative=fake).verify()
    region = ForgedRegion(refinement, 0)
    assert fp.verify_certificate(region) is False
    assert fp.replay_status(region).certified is False


def test_malformed_regions_decline_instead_of_raising(refinement):
    for r in (
        fp.ComplexNewtonRegion(object(), 0),
        fp.ComplexNewtonRegion(refinement, -1),
        fp.ComplexNewtonRegion(refinement, True),
        fp.ComplexNewtonRegion(refinement, 5),
    ):
        assert r.check().certified is False and not r.verify()


def test_nonvanishing_derivative_alone_does_not_accept_newton():
    p = fp.certify_analytic_contour(sp.exp(z) - 1, z, -1 - sp.I, 1 + sp.I)
    assert p.verify() and p.zero_count == 1
    assert fp.certify_complex_refinement(p) is None


def test_clusters_are_not_contracted_to_single_roots():
    p = fp.certify_analytic_contour(
        (z - sp.Rational(1, 100)) * (z + sp.Rational(1, 100)), z, -1 - sp.I, 1 + sp.I
    )
    assert p.verify() and p.zero_count == 2
    assert fp.certify_complex_refinement(p) is None
    q = fp.certify_complex_isolation(
        (sp.exp(z) - 1) ** 2,
        z,
        *RECT,
        max_box_diameter=R,
        policy=fp.EnclosurePolicy(max_depth=0),
        use_multiple=False,
    )
    assert q.coverage_complete and q.total_count == 2 and not q.isolation_complete
    assert not q.refinements and q.verify()


def test_requested_diameter_and_error_enclosures(isolated):
    q = isolated
    assert q.coverage_complete and q.isolation_complete and q.accuracy_complete
    assert q.root_count == q.total_count == 1
    for box in q.isolating_boxes:
        a, b, c, d = box.bounds()
        assert (c - a) ** 2 + (d - b) ** 2 <= q.proof.max_box_diameter**2
    assert all(c.verify() for c in q.refinements)


@pytest.mark.parametrize("kind", ["omit", "duplicate", "change", "overlap"])
def test_transferred_complements_are_required_for_coverage(isolated, kind):
    p = isolated.proof
    if kind == "omit":
        bad = ci._assembled(p, zeros=p.zero_regions[1:])
    elif kind == "duplicate":
        bad = ci._assembled(p, zeros=(*p.zero_regions, p.zero_regions[0]))
    elif kind == "change":
        bad = ci._assembled(
            p, zeros=(replace(p.zero_regions[0], index=0), *p.zero_regions[1:])
        )
    else:
        bad = ci._assembled(p, roots=(*p.root_regions, p.root_regions[0]))
    assert not bad.verify()


def test_native_replay_never_calls_refinement_proposals(isolated, monkeypatch):
    def disabled(*args, **kwargs):
        raise AssertionError("producer called during replay")

    for module, names in (
        (ci, ("_run", "_propose_refinement", "certify_analytic_contour")),
        (cn, ("_propose_refinement", "certify_complex_refinement")),
        (ac, ("certify_analytic_contour",)),
    ):
        for name in names:
            monkeypatch.setattr(module, name, disabled)
    for record in (isolated, isolated.proof, *isolated.refinements):
        status = fp.replay_status(record, expr=sp.exp(z) - 1, var=z)
        assert (
            record.verify()
            and status.certified
            and status.complete
            and not status.factory_replay
        )
        assert fp.replay_status(record, expr=sp.sin(z), var=z).certified is False


def test_newton_checkpoint_resume_and_wall_preservation():
    checkpoints = []
    with capture_checkpoints(checkpoints.append):
        p = fp.certify_complex_isolation(
            sp.exp(z) - 1,
            z,
            *RECT,
            max_box_diameter=sp.Rational(1, 10**8),
            policy=fp.EnclosurePolicy(max_cells=6, max_depth=32),
        )
    assert p.verify() and p.refinements and not p.complete and p.pending
    assert all(c.verify() for c in checkpoints)
    wall = fp.resume_complex_isolation(p, policy=fp.EnclosurePolicy(seconds=0.001))
    assert wall.verify() and wall.proof.regions == p.proof.regions
    assert wall.proof.max_box_diameter == p.proof.max_box_diameter
    q = fp.resume_complex_isolation(
        pickle.loads(pickle.dumps(wall)), policy=fp.EnclosurePolicy(max_depth=32)
    )
    assert q.verify() and q.complete and q.root_count == 1


@pytest.mark.parametrize("limit", [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 12])
def test_failed_and_successful_refinement_charged_to_one_budget(limit):
    q = fp.certify_complex_isolation(
        sp.exp(z) - 1,
        z,
        *RECT,
        max_box_diameter=sp.Rational(1, 10**8),
        policy=fp.EnclosurePolicy(max_cells=limit, max_depth=32),
    )
    assert q.verify() and q.tested <= limit


def test_direct_refinement_budgets_and_precision(parent, monkeypatch):
    assert (
        fp.certify_complex_refinement(parent, policy=fp.EnclosurePolicy(max_cells=1))
        is None
    )
    assert (
        fp.certify_complex_refinement(parent, policy=fp.EnclosurePolicy(seconds=0.001))
        is None
    )
    original = cn.complex_box_jet
    calls = []

    def limited(*args, **kwargs):
        calls.append(kwargs["precision"])
        return None if kwargs["precision"] == 2 else original(*args, **kwargs)

    monkeypatch.setattr(cn, "complex_box_jet", limited)
    r = fp.certify_complex_refinement(
        parent,
        policy=fp.EnclosurePolicy(precision=2, max_precision=8, max_refinements=2),
    )
    assert r and r.verify() and r.tested == 4 and r.derivative.precision == 4
    assert 2 in calls and 4 in calls


def test_public_integration_exposes_refinement_certificates():
    q = fp.complex_zeros(
        sp.exp(z) - 1,
        z,
        rectangle=RECT,
        return_result=True,
        max_box_diameter=sp.Rational(1, 10**6),
        policy=fp.EnclosurePolicy(max_depth=32),
    )
    assert q.complete and q.verify() and q.refinements
    assert type(q.rectangles[0].certificate) is fp.ComplexNewtonRegion
    assert fp.certify_complex_refinement(q.rectangles[0]).verify()


@pytest.mark.parametrize("public", [False, True])
def test_tiny_wall_seed_preserves_diameter(public):
    options = {"max_box_diameter": R, "policy": fp.EnclosurePolicy(seconds=0.001)}
    q = (
        fp.isolate_complex_roots(sp.exp(z) - 1, z, RECT, **options)
        if public
        else fp.certify_complex_isolation(sp.exp(z) - 1, z, *RECT, **options)
    )
    assert q.verify() and not q.complete and q.state.proof.max_box_diameter == R


@pytest.mark.parametrize("diameter", [True, 0, -1, sp.sqrt(2), 0.1])
def test_invalid_diameter_rejected(diameter):
    with pytest.raises(ValueError, match="exact rational"):
        fp.certify_complex_isolation(sp.exp(z) - 1, z, *RECT, max_box_diameter=diameter)
    with pytest.raises(ValueError, match="exact rational"):
        fp.isolate_complex_roots(
            z * z + 1, z, (-2 - 2 * sp.I, 2 + 2 * sp.I), max_box_diameter=diameter
        )


def test_bisection_mode_meets_accuracy():
    q = fp.certify_complex_isolation(
        sp.exp(z) - 1,
        z,
        *RECT,
        max_box_diameter=sp.Rational(1, 100),
        use_newton=False,
        policy=fp.EnclosurePolicy(max_depth=32),
    )
    assert q.complete and q.verify() and not q.refinements


def test_native_newton_inventory():
    records = {r["type"]: r for r in fp.proof_api_manifest()["records"]}
    for name in (
        "ComplexDerivativeWitness",
        "ComplexNewtonRefinement",
        "ComplexNewtonRegion",
    ):
        r = records["funcprops.complex_newton." + name]
        assert r["replay_supported"] and r["contract"] == "witness-kernel"


@pytest.mark.parametrize(
    "expr,rectangle,count",
    [
        (sp.sin(z), (-4 - sp.I, 4 + sp.I), 3),
        (sp.exp(z) + 1, (-1 - 4 * sp.I, 1 + 4 * sp.I), 2),
        (sp.erf(z), RECT, 1),
        (sp.erfc(z) - 1, RECT, 1),
    ],
)
def test_complete_refinement_for_multiple_boxes_and_entire_primitives(
    expr, rectangle, count
):
    q = fp.certify_complex_isolation(
        expr,
        z,
        *rectangle,
        max_box_diameter=sp.Rational(1, 20),
        policy=fp.EnclosurePolicy(max_depth=40, max_cells=4096),
    )
    assert q.complete and q.verify() and q.root_count == q.total_count == count
    assert q.refinements


def test_nonreal_rational_inverse_and_exact_linear_root():
    for expr, center in ((z * z + 1, sp.I), (z - 1, sp.S.One)):
        p = fp.certify_analytic_contour(
            expr, z, center - R - sp.I * R, center + R + sp.I * R
        )
        c = fp.certify_complex_refinement(p)
        assert c and c.verify()
        assert c.image[0] <= sp.re(center) <= c.image[2]
        assert c.image[1] <= sp.im(center) <= c.image[3]
        if expr == z * z + 1:
            assert c.inverse == -sp.I / 2
        else:
            assert c.contraction == 0
