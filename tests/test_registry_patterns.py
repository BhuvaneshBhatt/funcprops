import json
from importlib.resources import files

import pytest
import sympy as sp

from funcprops import ArgumentPattern, RuleCase, RuleSignature
from funcprops.conditions import parse_catalogue_expression
from funcprops.engine import ConditionTruth, truth_value


@pytest.mark.parametrize(
    "pattern, accepted, rejected",
    [
        (ArgumentPattern("n", "integer"), sp.Integer(2), sp.Rational(3, 2)),
        (ArgumentPattern("n", "integer", ("positive",)), sp.Integer(2), -sp.S.One),
        (ArgumentPattern("n", "integer", ("even",)), sp.Integer(4), sp.Integer(3)),
        (ArgumentPattern("n", "any", ("numeric",)), sp.pi, sp.Symbol("x")),
        (ArgumentPattern("a", "tuple"), sp.Tuple(1, 2), sp.Integer(1)),
        (
            ArgumentPattern(kind="literal", choices=("Integer(2)", "Integer(3)")),
            sp.Integer(2),
            sp.Integer(4),
        ),
    ],
)
def test_argument_premises(pattern, accepted, rejected):
    assert pattern.matches(accepted) is True
    assert pattern.matches(rejected) is False


def test_unproved_argument_premises():
    n = sp.Symbol("n", integer=True)
    assert ArgumentPattern("n", "integer").matches(n) is True
    assert ArgumentPattern("n", "integer", ("even",)).matches(n) is False
    assert ArgumentPattern(kind="literal", choices=("Integer(2)",)).matches(n) is False
    assert ArgumentPattern(kind="unsupported").matches(n) is False


def test_rule_signature_binding():
    x, y = sp.symbols("x y", real=True)
    signature = RuleSignature((ArgumentPattern("x"),), "real", "x", 2)
    case = RuleCase(
        "Pow(Symbol('x'), Integer(2))", "true", rule_id="square:0", signature=signature
    )
    function = sp.Function("F")
    assert case.matches(function(x), var=x, mode="real")
    assert not case.matches(function(x), var=y, mode="real")
    assert not case.matches(function(x), var=x, mode="complex")
    assert not case.matches(function(x, y), mode="real")
    assert case.instantiate(function(x + 1)) == ((x + 1) ** 2, sp.S.true)
    assert case.specificity(mode="real") == 4


def test_opaque_values_stay_unknown():
    value = parse_catalogue_expression(
        "Function('CatalogueCondition')(Symbol('unresolved_value'))"
    )
    assert truth_value(value) is ConditionTruth.UNKNOWN


def test_catalogue_rule_schema():
    data = json.loads(files("funcprops").joinpath("data/catalogue.json").read_text())
    assert data["schema"] == "function-property-catalogue"
    for family in data["families"]:
        for name, prop in family["properties"].items():
            for index, case in enumerate(prop["cases"]):
                assert case["rule_id"] == f"{family['family_id']}:{name}:{index}"
                assert set(case["signature"]) == {
                    "arguments",
                    "mode",
                    "coordinate",
                    "priority",
                }
