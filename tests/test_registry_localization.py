import pytest
import sympy as sp

from funcprops import FunctionSlot, PropertyRule
from funcprops.registry import make_function_slots


def test_function_slot_is_local_sympy_placeholder():
    left = FunctionSlot(0, "nu")
    right = FunctionSlot(0, "nu")

    assert left != right
    assert left.position == right.position == 0
    assert str(left) == "_nu"
    assert (left > -1).has(left)


def test_make_function_slots_assign_positions_in_order():
    nu, z = make_function_slots("nu", "z")

    assert nu.position == 0
    assert z.position == 1
    assert nu != z


def test_property_rule_instantiates_conditions_result_and_subject():
    nu, z = make_function_slots("nu", "z")
    rule = PropertyRule(
        head=sp.besselj,
        property="real_zeros",
        subject=(z,),
        conditions=(nu > -1) & (z > 0),
        result=sp.Tuple(nu, z),
        proof_kind="fixture",
    )
    a, x = sp.symbols("a x", real=True)

    instantiated = rule.instantiate(sp.besselj(a + 1, x**2))

    assert instantiated.subject == (x**2,)
    assert instantiated.conditions == ((a + 1 > -1) & (x**2 > 0))
    assert instantiated.result == sp.Tuple(a + 1, x**2)
    assert instantiated.substitution_map[nu] == a + 1
    assert instantiated.substitution_map[z] == x**2


def test_property_rule_does_not_capture_same_named_user_symbols():
    user_nu = sp.Symbol("nu")
    user_z = sp.Symbol("z")
    nu, z = make_function_slots("nu", "z")
    rule = PropertyRule(
        head=sp.besselj,
        property="sign",
        subject=z,
        conditions=nu > -1,
        result=z + nu,
    )

    instantiated = rule.instantiate(sp.besselj(user_z, user_nu))

    assert instantiated.subject == (user_nu,)
    assert instantiated.conditions == (user_z > -1)
    assert instantiated.result == user_nu + user_z
    assert instantiated.conditions.has(user_z)
    assert not instantiated.conditions.has(nu)


def test_property_rule_handles_same_actual_symbol_in_multiple_slots():
    a, b = make_function_slots("a", "b")
    x = sp.Symbol("x")
    rule = PropertyRule(
        head=sp.beta,
        property="fixture",
        subject=(a, b),
        conditions=a + b > 0,
        result=a - b,
    )

    instantiated = rule.instantiate(sp.beta(x, x))

    assert instantiated.subject == (x, x)
    assert instantiated.conditions == (2 * x > 0)
    assert instantiated.result == 0


def test_property_rule_matching_is_by_function_head_and_slot_arity():
    nu, z = make_function_slots("nu", "z")
    rule = PropertyRule(
        head=sp.besselj,
        property="fixture",
        subject=z,
        conditions=nu > -1,
    )

    assert rule.matches(sp.besselj(0, 1))
    assert not rule.matches(sp.bessely(0, 1))


def test_duplicate_argument_positions():
    first = FunctionSlot(0, "first")
    second = FunctionSlot(0, "second")

    with pytest.raises(ValueError, match="same position"):
        PropertyRule(
            head=sp.besselj,
            property="fixture",
            subject=first,
            conditions=second > 0,
        )


def test_function_slot_rejects_invalid_position():
    with pytest.raises(ValueError):
        FunctionSlot(-1, "bad")


def test_registry_native_rule_lifecycle():
    from funcprops import FunctionRegistry

    nu, z = make_function_slots("nu", "z")
    zeros_rule = PropertyRule(
        head=sp.besselj,
        property="real_zeros",
        subject=z,
        conditions=(nu > -1) & (z > 0),
        result=sp.Tuple(nu, z),
    )
    sign_rule = PropertyRule(
        head=sp.besselj,
        property="sign",
        subject=z,
        conditions=z > 0,
        result=sp.S.One,
    )
    native = FunctionRegistry([], property_rules=(zeros_rule, sign_rule))
    a, x = sp.symbols("a x", real=True)
    expr = sp.besselj(a, x)

    assert native.property_rules(head=sp.besselj, property="real_zeros") == (
        zeros_rule,
    )
    assert native.match_property_rules(expr, property="real_zeros") == (zeros_rule,)
    instantiated = native.instantiate_property_rules(expr, property="real_zeros")
    assert len(instantiated) == 1
    assert instantiated[0].conditions == ((a > -1) & (x > 0))
    assert native.match_property_rules(sp.bessely(a, x)) == ()


def test_function_registry_rejects_non_property_rule_registration():
    from funcprops import FunctionRegistry

    native = FunctionRegistry([])
    with pytest.raises(TypeError, match="PropertyRule"):
        native.register_property_rule(object())
