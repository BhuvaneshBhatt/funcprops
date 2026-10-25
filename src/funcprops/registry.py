from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

import sympy as sp
from sympy import S, Symbol

from .conditions import parse_catalogue_expression
from .exactness import certify_identity_equal


class FunctionSlot(sp.Dummy):
    """A rule-local placeholder for one positional function argument.

    ``FunctionSlot`` behaves like a SymPy expression so registry
    conditions and results can be written naturally, while retaining an
    explicit positional binding.  Every construction is a fresh ``Dummy``; a
    human-readable name never creates a global-symbol dependency.
    """

    def __new__(cls, position: int, name: str | None = None):
        if isinstance(position, bool) or not isinstance(position, int) or position < 0:
            raise ValueError("FunctionSlot position must be a non-negative integer")
        display = name or f"slot{position}"
        obj = sp.Dummy.__new__(cls, display)
        obj._function_slot_position = position
        obj._function_slot_name = name
        return obj

    @property
    def position(self) -> int:
        return self._function_slot_position

    @property
    def display_name(self) -> str | None:
        return self._function_slot_name


def make_function_slots(*names: str) -> tuple[FunctionSlot, ...]:
    """Create fresh, positionally bound registry placeholders.

    Examples
    --------
    ``nu, z = make_function_slots("nu", "z")`` binds ``nu`` to argument slot 0 and
    ``z`` to argument slot 1 of whichever function head owns the rule.
    """

    return tuple(FunctionSlot(i, name) for i, name in enumerate(names))


def _replace_slots(value, substitutions: dict[FunctionSlot, Any]):
    if isinstance(value, sp.Basic):
        return value.xreplace(substitutions)
    if isinstance(value, tuple):
        return tuple(_replace_slots(v, substitutions) for v in value)
    if isinstance(value, list):
        return [_replace_slots(v, substitutions) for v in value]
    if isinstance(value, dict):
        return {
            _replace_slots(k, substitutions): _replace_slots(v, substitutions)
            for k, v in value.items()
        }
    return value


@dataclass(frozen=True)
class InstantiatedPropertyRule:
    """A native registry theorem instantiated for one concrete function call."""

    rule: "PropertyRule"
    expression: sp.Basic
    subject: tuple[Any, ...]
    conditions: Any
    result: Any
    substitutions: tuple[tuple[FunctionSlot, Any], ...]

    @property
    def substitution_map(self) -> dict[FunctionSlot, Any]:
        return dict(self.substitutions)


@dataclass(frozen=True)
class PropertyRule:
    """A localized, typed theorem about positional arguments of a function head.

    This type is responsible only for theorem matching and instantiation.
    Transport through compositions such as ``F(g(x))`` is handled separately
    by the registry transport layer.
    """

    head: Any
    property: str
    subject: tuple[FunctionSlot, ...]
    conditions: Any = S.true
    result: Any = None
    proof_kind: str | None = None
    verifier: Any = None
    source: str | None = None

    def __post_init__(self):
        subjects = (
            (self.subject,)
            if isinstance(self.subject, FunctionSlot)
            else tuple(self.subject)
        )
        if not subjects:
            raise ValueError(
                "PropertyRule subject must contain at least one FunctionSlot"
            )
        if not all(isinstance(slot, FunctionSlot) for slot in subjects):
            raise TypeError(
                "PropertyRule subject entries must be FunctionSlot instances"
            )
        if len(set(subjects)) != len(subjects):
            raise ValueError("PropertyRule subject cannot contain duplicate slots")
        object.__setattr__(self, "subject", subjects)
        object.__setattr__(self, "conditions", sp.sympify(self.conditions))

        used = set(subjects)
        for value in (self.conditions, self.result):
            if isinstance(value, sp.Basic):
                used.update(value.atoms(FunctionSlot))
        if used:
            positions = [slot.position for slot in used]
            if len(set(positions)) != len(positions):
                raise ValueError(
                    "A PropertyRule cannot contain distinct FunctionSlots for the same position"
                )

    @property
    def slots(self) -> tuple[FunctionSlot, ...]:
        used = set(self.subject)
        for value in (self.conditions, self.result):
            if isinstance(value, sp.Basic):
                used.update(value.atoms(FunctionSlot))
        return tuple(sorted(used, key=lambda slot: slot.position))

    def matches(self, expr) -> bool:
        """Check whether the other record binds the same source and domain premises."""

        expr = sp.sympify(expr)
        if getattr(expr, "func", None) != self.head:
            return False
        nargs = len(getattr(expr, "args", ()))
        return all(slot.position < nargs for slot in self.slots)

    def substitutions(self, expr) -> dict[FunctionSlot, Any]:
        expr = sp.sympify(expr)
        if not self.matches(expr):
            raise ValueError(f"Rule for {self.head} does not match {expr}")
        args = expr.args
        return {slot: args[slot.position] for slot in self.slots}

    def instantiate(self, expr) -> InstantiatedPropertyRule:
        """Substitute concrete subjects into the rule while retaining its parameter guards."""

        expr = sp.sympify(expr)
        repl = self.substitutions(expr)
        return InstantiatedPropertyRule(
            rule=self,
            expression=expr,
            subject=tuple(repl[slot] for slot in self.subject),
            conditions=_replace_slots(self.conditions, repl),
            result=_replace_slots(self.result, repl),
            substitutions=tuple((slot, repl[slot]) for slot in self.slots),
        )


@dataclass(frozen=True)
class ArgumentPattern:
    """Match one positional argument using native type, sign or literal premises."""

    name: str | None = None
    kind: str = "any"
    predicates: tuple[str, ...] = ()
    choices: tuple[str, ...] = ()

    def matches(self, actual):
        """Return whether every stored argument premise is proved for actual."""
        if self.kind == "unsupported":
            return False
        if self.kind == "literal":
            return any(
                certify_identity_equal(actual, parse_catalogue_expression(value))
                is True
                for value in self.choices
            )
        if self.kind == "tuple":
            if not isinstance(actual, (sp.Tuple, tuple, list)):
                return False
        elif self.kind != "any":
            attribute = {
                "integer": "is_integer",
                "real": "is_real",
                "complex": "is_complex",
            }.get(self.kind)
            if attribute is None or getattr(actual, attribute, None) is not True:
                return False
        attributes = {
            "even": "is_even",
            "positive": "is_positive",
            "negative": "is_negative",
            "nonnegative": "is_nonnegative",
            "numeric": "is_number",
        }
        return all(
            predicate in attributes
            and getattr(actual, attributes[predicate], None) is True
            for predicate in self.predicates
        )


@dataclass(frozen=True)
class RuleSignature:
    """Bind argument patterns, analysis mode, coordinate ownership and precedence."""

    arguments: tuple[ArgumentPattern, ...] = ()
    mode: str | None = None
    coordinate: str | None = None
    priority: int = 0


@dataclass(frozen=True)
class RuleCase:
    """Pair a sufficient property case with native argument matching and a stable identity."""

    value_source: str
    condition_source: str
    source_property_type: str | None = None
    rule_id: str | None = None
    signature: RuleSignature = RuleSignature()

    @property
    def condition(self):
        return parse_catalogue_expression(self.condition_source or "True")

    @property
    def value(self):
        return parse_catalogue_expression(self.value_source)

    def substitutions(self, expr):
        """Bind named positional subjects to their actual function arguments."""
        return {
            Symbol(pattern.name): actual
            for pattern, actual in zip(
                self.signature.arguments, getattr(expr, "args", ()), strict=False
            )
            if pattern.name is not None
        }

    def instantiate(self, expr):
        """Substitute concrete arguments into a case's value and parameter guard."""
        replacements = self.substitutions(expr)
        value, condition = self.value, self.condition
        if isinstance(value, sp.Basic):
            value = value.xreplace(replacements)
        if isinstance(condition, sp.Basic):
            condition = condition.xreplace(replacements)
        return value, condition

    def matches(self, expr, *, var=None, mode=None):
        """Check arity, argument premises, analysis mode and coordinate ownership."""
        signature = self.signature
        args = getattr(expr, "args", ())
        if signature.arguments and len(signature.arguments) != len(args):
            return False
        if not all(
            pattern.matches(actual)
            for pattern, actual in zip(signature.arguments, args, strict=False)
        ):
            return False
        if mode in ("real", "complex") and signature.mode not in (None, "any", mode):
            return False
        if var is not None and signature.coordinate is not None:
            mapped = self.substitutions(expr).get(Symbol(signature.coordinate))
            if mapped is not None and mapped != var:
                return False
        return True

    def specificity(self, *, mode=None):
        """Return the declared case precedence, with exact-mode cases first."""
        return self.signature.priority + (
            2 if mode in ("real", "complex") and self.signature.mode == mode else 0
        )


def _rule_signature(data):
    # JSON lists become immutable records before rules are exposed to callers.
    arguments = tuple(
        ArgumentPattern(
            name=argument.get("name"),
            kind=argument["kind"],
            predicates=tuple(argument.get("predicates", ())),
            choices=tuple(argument.get("choices", ())),
        )
        for argument in data.get("arguments", ())
    )
    return RuleSignature(
        arguments, data.get("mode"), data.get("coordinate"), data.get("priority", 0)
    )


@dataclass(frozen=True)
class Family:
    """Group property rules for a supported symbolic function family."""

    raw: dict[str, Any]

    @property
    def id(self):
        return self.raw["family_id"]

    @property
    def sympy_names(self):
        return tuple(self.raw.get("sympy_names", ()))

    @property
    def mpmath_names(self):
        return tuple(self.raw.get("mpmath_names", ()))

    def cases(self, prop: str) -> tuple[RuleCase, ...]:
        """Materialize immutable native matching records for one property."""

        p = self.raw.get("properties", {}).get(prop, {})
        return tuple(
            RuleCase(
                **{
                    k: c.get(k)
                    for k in (
                        "value_source",
                        "condition_source",
                        "source_property_type",
                        "rule_id",
                    )
                },
                signature=_rule_signature(c["signature"]),
            )
            for c in p.get("cases", ())
        )


class FunctionRegistry:
    """Load and query guarded function-property declarations."""

    def __init__(
        self,
        records: Iterable[dict[str, Any]],
        *,
        property_rules: Iterable[PropertyRule] = (),
        identity_rules: Iterable[Any] = (),
        derivative_rules: Iterable[Any] = (),
    ):
        self._families = tuple(Family(r) for r in records)
        self._by_name = {}
        for fam in self._families:
            for n in (
                fam.id,
                *fam.sympy_names,
                *fam.mpmath_names,
            ):
                self._by_name.setdefault(n, fam)
        self._property_rules: list[PropertyRule] = []
        self._rules_by_head: dict[Any, list[PropertyRule]] = {}
        for rule in property_rules:
            self.register_property_rule(rule)
        self._identity_rules: list[Any] = []
        self._derivative_rules: list[Any] = []
        for rule in identity_rules:
            self.register_identity_rule(rule)
        for rule in derivative_rules:
            self.register_derivative_rule(rule)

    def __len__(self):
        return len(self._families)

    def __iter__(self):
        return iter(self._families)

    def get(self, name: str) -> Family | None:
        """Return the matching function family, or the supplied default when absent."""

        return self._by_name.get(name)

    def require(self, name: str) -> Family:
        """Return the matching function family or raise KeyError when absent."""

        f = self.get(name)
        if f is None:
            raise KeyError(name)
        return f

    def register_property_rule(self, rule: PropertyRule) -> PropertyRule:
        """Register one native localized property theorem.

        Catalogue-derived ``Family``/``RuleCase`` records remain independent in
        Catalogue entries can be adapted to this native rule API when their
        argument semantics are unambiguous.
        """

        if not isinstance(rule, PropertyRule):
            raise TypeError("rule must be a PropertyRule")
        self._property_rules.append(rule)
        self._rules_by_head.setdefault(rule.head, []).append(rule)
        return rule

    def register_identity_rule(self, rule):
        """Register a guarded symbolic identity with explicit argument subjects."""

        from .registry_derivatives import IdentityRule

        if not isinstance(rule, IdentityRule):
            raise TypeError("rule must be an IdentityRule")
        self._identity_rules.append(rule)
        return rule

    def register_derivative_rule(self, rule):
        """Register a guarded derivative rule for an argument position."""

        from .registry_derivatives import DerivativeRule

        if not isinstance(rule, DerivativeRule):
            raise TypeError("rule must be a DerivativeRule")
        self._derivative_rules.append(rule)
        return rule

    def identity_rules(self, *, head=None):
        """Return identity rules matching the requested function head."""

        rules = tuple(self._identity_rules)
        return tuple(r for r in rules if head is None or r.head == head)

    def derivative_rules(self, *, head=None, position=None):
        """Return derivative rules matching the requested head and argument position."""

        rules = tuple(self._derivative_rules)
        return tuple(
            r
            for r in rules
            if (head is None or r.head == head)
            and (position is None or r.with_respect_to.position == position)
        )

    def match_identity_rules(self, expr):
        """Instantiate matching identity rules against concrete function arguments."""

        expr = sp.sympify(expr)
        return tuple(r for r in self.identity_rules(head=expr.func) if r.matches(expr))

    def match_derivative_rules(self, expr, *, position=None):
        """Instantiate matching derivative rules against concrete function arguments."""

        expr = sp.sympify(expr)
        return tuple(
            r
            for r in self.derivative_rules(head=expr.func, position=position)
            if r.matches(expr)
        )

    def property_rules(
        self, *, head=None, property: str | None = None
    ) -> tuple[PropertyRule, ...]:
        """Return native rules, optionally filtered by head/property name."""

        rules = (
            tuple(self._rules_by_head.get(head, ()))
            if head is not None
            else tuple(self._property_rules)
        )
        if property is not None:
            rules = tuple(rule for rule in rules if rule.property == property)
        return rules

    def match_property_rules(
        self, expr, *, property: str | None = None
    ) -> tuple[PropertyRule, ...]:
        """Return native rules whose function head/slots match ``expr``."""

        expr = sp.sympify(expr)
        return tuple(
            rule
            for rule in self.property_rules(
                head=getattr(expr, "func", None), property=property
            )
            if rule.matches(expr)
        )

    def instantiate_property_rules(
        self, expr, *, property: str | None = None
    ) -> tuple[InstantiatedPropertyRule, ...]:
        """Instantiate all matching native rules for one concrete call."""

        return tuple(
            rule.instantiate(expr)
            for rule in self.match_property_rules(expr, property=property)
        )


@lru_cache(maxsize=1)
def registry() -> FunctionRegistry:
    """Return the cached registry of guarded symbolic function-property rules."""

    p = files("funcprops").joinpath("data/catalogue.json")
    payload = json.loads(p.read_text())
    reg = FunctionRegistry(payload["families"])
    from .native_registry import install_native_rules

    install_native_rules(reg)
    return reg


def adapt_catalogue_rule_case(
    head,
    property_name: str,
    case: RuleCase,
    *,
    source: str | None = None,
) -> PropertyRule | None:
    """Adapt a simple positional catalogue case to a native ``PropertyRule``.

    Only one unrestricted named argument is localized here. Typed, literal and
    structured argument premises require their own transport theorem.
    """

    patterns = case.signature.arguments
    if len(patterns) != 1 or any(
        pattern.kind != "any" or pattern.name is None or pattern.predicates
        for pattern in patterns
    ):
        return None
    names = [pattern.name for pattern in patterns]
    slots = tuple(FunctionSlot(i, name) for i, name in enumerate(names))
    substitutions = {
        Symbol(name): slot for name, slot in zip(names, slots, strict=True)
    }
    value = case.value
    condition = case.condition
    if isinstance(value, sp.Basic):
        value = value.xreplace(substitutions)
    if isinstance(condition, sp.Basic):
        condition = condition.xreplace(substitutions)

    # Unbound catalogue variables would make a localized rule depend on a
    # global placeholder instead of its concrete function argument.
    residual = set()
    for obj in (value, condition):
        if isinstance(obj, sp.Basic):
            residual.update(obj.free_symbols)
    if residual & {Symbol(name) for name in names}:
        return None
    return PropertyRule(
        head,
        property_name,
        slots,
        conditions=condition,
        result=value,
        proof_kind="catalogue-adaptation",
        source=source or case.rule_id or "catalogue",
    )
