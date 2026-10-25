"""Whole-source and whole-germ adversarial certificate regressions."""

from dataclasses import replace

import pytest
import sympy as s

from funcprops.certified_operations import (
    EquationSolutionCertificate,
    InverseCertificate,
    SingularityClassificationCertificate,
    WindingCertificate,
    classify_singularity,
    inverse,
    solve,
    winding_number,
)
from funcprops.integration import ParametricContour

z = s.Symbol("z")
x = s.Symbol("x", real=True)
t = s.Symbol("t", real=True)


def test_complex_phase_is_not_a_fixed_radius_circle():
    a = s.Symbol("a", imaginary=True)
    contour = ParametricContour(s.exp(s.I * (t + a * s.sin(t))), (t, 0, 2 * s.pi))
    assert contour.closed
    assert winding_number(contour, s.I / 2) is None
    bad = WindingCertificate(contour, s.I / 2, 1, 2 * s.pi * s.I)
    assert not bad.verify()
    # At a=4*I the radial graph has radius exp(-4) at angle pi/2;
    # i/2 is outside that simple closed curve, unlike the unit-circle model.
    assert s.exp(-4) < s.Rational(1, 2)
    specialized = ParametricContour(contour.gamma.subs(a, 4 * s.I), (t, 0, 2 * s.pi))
    assert winding_number(specialized, s.I / 2) is None


@pytest.mark.parametrize("direction", [1, -1, 2])
def test_valid_circle_phase_and_orientation(direction):
    contour = ParametricContour(
        2 + 3 * s.exp(s.I * (direction * t + 3 * s.sin(t))), (t, 0, 2 * s.pi)
    )
    certificate = winding_number(contour, 2, return_certificate=True)
    assert certificate.winding == direction and certificate.verify()
    assert winding_number(contour, 10) == 0
    assert winding_number(contour.reversed(), 2) == -direction


def test_circle_phase_source_holes_cannot_cancel():
    ratio = s.Mul(t - s.pi, s.Pow(t - s.pi, -1, evaluate=False), evaluate=False)
    phase = s.Add(t, s.Mul(ratio, s.sin(t), evaluate=False), evaluate=False)
    gamma = s.exp(s.Mul(s.I, phase, evaluate=False), evaluate=False)
    contour = ParametricContour(gamma, (t, 0, 2 * s.pi))
    assert contour.closed
    assert winding_number(contour, 0) is None


@pytest.mark.parametrize(
    "expression,expected",
    [
        (s.exp(s.log(z, evaluate=False), evaluate=False), "zero"),
        (s.sin(1 / z) ** 2 + s.cos(1 / z) ** 2, "regular"),
        (s.log(z), "branch_point"),
        (s.log(1 / z), "branch_point"),
        (z * s.log(z) + 1 / z, "branch_point"),
        (1 + s.sqrt(z), "branch_point"),
        (s.exp(1 / z), "essential"),
        (s.exp(1 / z) + s.exp(-1 / z), "essential"),
        (z * s.exp(1 / z) + 1 / z, "essential"),
        (1 / z**3, "pole"),
        (s.sin(z), "zero"),
    ],
)
def test_whole_germ_classification(expression, expected):
    c = classify_singularity(expression, z, 0, return_certificate=True)
    assert c.kind == expected and c.verify()
    assert not replace(c, kind="incorrect").verify()


@pytest.mark.parametrize(
    "expression",
    [
        s.log(z * z) - 2 * s.log(z),
        s.Abs(z),
        s.conjugate(z),
        s.re(z),
        1 / (1 + s.exp(1 / z)),
    ],
)
def test_unsupported_or_nonisolated_germs_do_not_gain_certificates(expression):
    assert classify_singularity(expression, z, 0) is None
    assert not SingularityClassificationCertificate(
        expression, z, 0, "essential", None
    ).verify()
    assert not SingularityClassificationCertificate(
        expression, z, 0, "branch_point", None
    ).verify()


def test_identically_zero_punctured_germ():
    source = s.Add(s.log(z), -s.log(z), evaluate=False)
    proof = classify_singularity(source, z, 0, return_certificate=True)
    assert proof.kind == "identically_zero" and proof.order is s.oo
    assert proof.verify()
    assert not replace(proof, kind="zero").verify()


@pytest.mark.parametrize("domain", [s.S.Reals, s.S.Complexes])
def test_equation_source_pole_is_not_a_root(domain):
    held = s.Mul(x, x, s.Pow(x, -1, evaluate=False), evaluate=False)
    c = solve(held, x, domain=domain, return_certificate=True)
    assert c.complete and c.verify() and c.solutions is s.S.EmptySet
    assert not replace(c, solutions=s.FiniteSet(0)).verify()
    factory_replay = EquationSolutionCertificate(held, x, domain, s.FiniteSet(0), True)
    assert not factory_replay.verify()


def test_equation_identically_zero_only_on_source_domain():
    held = s.Add(
        s.Mul(x, s.Pow(x, -1, evaluate=False), evaluate=False), -1, evaluate=False
    )
    c = solve(held, x, domain=s.S.Reals, return_certificate=True)
    assert c.verify() and c.complete and c.solutions == s.S.Reals - s.FiniteSet(0)
    assert not replace(c, effective_domain=s.S.Reals).verify()


def test_log_source_exclusion_survives_equation_normalization():
    held = s.exp(s.log(x, evaluate=False), evaluate=False)
    c = solve(held, x, return_certificate=True)
    assert c.complete and c.solutions is s.S.EmptySet and c.verify()


def test_unresolved_source_exclusion_keeps_equation_incomplete():
    base = s.sin(x) - x
    held = s.Add(
        s.Mul(base, s.Pow(base, -1, evaluate=False), evaluate=False), -1, evaluate=False
    )
    c = solve(held, x, domain=s.S.Reals, return_certificate=True)
    assert not c.complete and c.solutions.has(s.ConditionSet) and c.verify()


def test_inverse_source_domain_cannot_include_holes():
    y = s.Symbol("y", real=True)
    held = s.Mul(x, x, s.Pow(x, -1, evaluate=False), evaluate=False)
    image = s.S.Reals - s.FiniteSet(0)
    bad = InverseCertificate(held, x, y, y, s.S.Reals, image)
    assert not bad.verify() and inverse(held, x, return_certificate=True) is None
    good = replace(bad, domain=image)
    assert good.verify()


def test_inverse_value_coordinate_assumptions_bind_the_image():
    positive = s.Symbol("positive", positive=True)
    negative_domain = s.Interval(-2, -1)
    bad = InverseCertificate(x, x, positive, positive, negative_domain, negative_domain)
    assert not bad.verify()


@pytest.mark.parametrize(
    "expression",
    [
        s.Abs(z),
        s.conjugate(z),
        s.re(z),
        z ** s.Symbol("unknown_exponent"),
        z**z,
        s.gamma(z),
    ],
)
def test_unsupported_continuation_is_not_certified_unchanged(expression):
    from funcprops.certified_operations import analytic_continue

    contour = ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    assert analytic_continue(expression, z, contour, return_certificate=True) is None


def test_continuation_requires_source_defined_on_path():
    from funcprops.certified_operations import analytic_continue

    contour = ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    assert analytic_continue(1 / (z - 1), z, contour) is None
    assert analytic_continue(s.exp(z), z, contour) == s.exp(z)
    valid = analytic_continue(s.log(z), z, contour, return_certificate=True)
    assert valid.verify() and s.simplify(valid.continued - s.log(z)) == 2 * s.pi * s.I


def test_unsupported_none_values_do_not_replay_as_certificates():
    from funcprops.certified_operations import (
        ArgumentPrincipleResult,
        ContinuationCertificate,
    )

    contour = ParametricContour(s.exp(s.I * t), (t, 0, 2 * s.pi))
    assert not ArgumentPrincipleResult(s.exp(z), z, contour, None, True).verify()
    assert not ContinuationCertificate(s.log(s.log(z)), z, contour, None, ()).verify()


def test_continuation_cannot_cancel_contour_source_holes():
    from funcprops.certified_operations import analytic_continue

    ratio = s.Mul(t - s.pi, s.Pow(t - s.pi, -1, evaluate=False), evaluate=False)
    gamma = s.Mul(ratio, s.exp(s.I * t), evaluate=False)
    contour = ParametricContour(gamma, (t, 0, 2 * s.pi))
    assert contour.closed
    assert analytic_continue(z, z, contour, return_certificate=True) is None


def test_winding_path_continuity():
    loop = s.cos(t) + s.I * s.sin(t)
    gamma = s.Piecewise((loop, t < 2 * s.pi), (loop + 3, t < 4 * s.pi), (loop, True))
    contour = ParametricContour(gamma, (t, 0, 6 * s.pi))
    assert contour.closed
    assert winding_number(contour, 0) is None


def test_generic_trigonometric_circle_remains_supported():
    contour = ParametricContour(s.cos(t) + s.I * s.sin(t), (t, 0, 2 * s.pi))
    c = winding_number(contour, 0, return_certificate=True)
    assert c.winding == 1 and c.verify()


def test_generic_winding_rejects_point_on_path_and_infinite_point():
    contour = ParametricContour(s.cos(t) + s.I * s.sin(t), (t, 0, 2 * s.pi))
    assert winding_number(contour, 1) is None
    assert winding_number(contour, s.oo) is None
