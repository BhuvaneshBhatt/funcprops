import pytest
from sympy import Basic

from funcprops.registry import registry

REG = registry()
FAMILIES = list(REG)


def test_catalogue_has_233_families():
    assert len(REG) == 233


@pytest.mark.parametrize("family", FAMILIES, ids=lambda f: f.id)
def test_family_has_canonical_identity(family):
    assert family.id
    assert family.sympy_names or family.mpmath_names or family.catalogue_names


CASES = [
    (f.id, p, c)
    for f in FAMILIES
    for p in f.raw.get("properties", {})
    for c in f.cases(p)
]


@pytest.mark.parametrize(
    "family_id,prop,case",
    CASES,
    ids=lambda x: getattr(x, "source_lhs", None) or str(x)[:80],
)
def test_every_rule_condition_normalizes_to_sympy(family_id, prop, case):
    out = case.condition
    assert isinstance(out, Basic), (family_id, prop, case.condition_source, out)


BOOLEAN_PROPS = {
    "RealDomain",
    "ComplexDomain",
    "Integer",
    "Rational",
    "Real",
    "RealIfDefined",
    "Positive",
    "Negative",
    "NonPositive",
    "NonNegative",
    "Injective",
    "LocallyAnalytic",
}
BOOL_CASES = [(f.id, p, c) for f in FAMILIES for p in BOOLEAN_PROPS for c in f.cases(p)]


@pytest.mark.parametrize("family_id,prop,case", BOOL_CASES)
def test_boolean_property_values_normalize(family_id, prop, case):
    out = case.value
    assert isinstance(out, Basic), (family_id, prop, case.value_source)
