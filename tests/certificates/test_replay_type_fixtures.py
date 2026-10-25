"""Direct valid/invalid fixtures for the leaf/factory_replay replay observation gaps."""

from dataclasses import fields, is_dataclass, replace

import pytest
import sympy as sp

import funcprops as fp
from funcprops.analytic_contours import ComplexBoxWitness
from funcprops.complex_multiplicity import ComplexPowerRootRegion
from funcprops.coverage_contract import EnclosureWitness
from funcprops.parameter_contract import BoxEnclosureWitness

x, a, b = sp.symbols("x a b", real=True)
z = sp.Symbol("z")
RECT = (-1 - sp.I, 1 + sp.I)


def first_record(value, record_type):
    visited = set()

    def find(item):
        if id(item) in visited:
            return None
        visited.add(id(item))
        if type(item) is record_type:
            return item
        children = ()
        if is_dataclass(item):
            children = (getattr(item, field.name) for field in fields(item))
        elif isinstance(item, (tuple, list)):
            children = item
        for child in children:
            found = find(child)
            if found is not None:
                return found
        return None

    result = find(value)
    assert type(result) is record_type
    return result


@pytest.fixture(scope="module")
def cases():
    contour = fp.certify_analytic_contour(sp.exp(z) - 1, z, *RECT)
    complex_box = first_record(contour, ComplexBoxWitness)
    parameter = fp.certify_parameter_box(
        sp.exp(x) + a * x - b,
        x,
        {
            a: sp.Interval(-sp.Rational(1, 4), sp.Rational(1, 4)),
            b: sp.Interval(sp.Rational(3, 2), 2),
        },
        sp.Interval(0, 1),
    )
    box = first_record(parameter, BoxEnclosureWitness)
    enclosure = first_record(
        fp.enclose_expression(sp.exp(x), x, sp.Interval(0, 1)), EnclosureWitness
    )
    power = first_record(
        fp.certify_complex_isolation((sp.exp(z) - 2) ** 3, z, *RECT),
        ComplexPowerRootRegion,
    )
    t = sp.Symbol("t", real=True)
    loop = fp.ParametricContour(sp.exp(sp.I * t), (t, 0, 2 * sp.pi))
    deformation = fp.deform_contour(1 / z, z, loop, loop, return_certificate=True)
    integral = fp.integrate(x * x, (x, 0, 1), return_result=True)
    monotone = fp.complete_monotonicity(
        sp.exp(-x), x, domain=sp.Interval(0, sp.oo), return_result=True
    )
    determinant = fp.determinant_nonvanishing((2 * x,), x, return_result=True)
    return {
        "complex-box": (complex_box, replace(complex_box, bounds=(sp.S.Zero,) * 4)),
        "parameter-box": (box, replace(box, lower=box.upper + 1)),
        "real-enclosure": (enclosure, replace(enclosure, lower=enclosure.upper + 1)),
        "power-region": (
            power,
            replace(power, factorization=replace(power.factorization, multiplicity=4)),
        ),
        "contour-deformation": (
            deformation,
            replace(deformation, second=loop.reversed()),
        ),
        "integral": (integral, replace(integral, value=sp.Integer(77))),
        "complete-monotonicity": (
            monotone,
            replace(monotone, classification=fp.TruthValue.FALSE),
        ),
        "determinant": (determinant, replace(determinant, determinant=sp.S.Zero)),
    }


@pytest.mark.parametrize(
    "name",
    [
        "complex-box",
        "parameter-box",
        "real-enclosure",
        "power-region",
        "contour-deformation",
        "integral",
        "complete-monotonicity",
        "determinant",
    ],
)
def test_registered_record_replay(cases, name):
    good, bad = cases[name]
    assert fp.verify_certificate(good) is True
    assert fp.verify_certificate(bad) is False
    status = fp.replay_status(good)
    assert status.certified is True
    declared = getattr(good, "complete", None)
    if declared is True or declared is sp.S.true:
        assert status.complete is True
    elif declared is False or declared is sp.S.false:
        assert status.complete is False
    assert fp.replay_status(bad).certified is False
