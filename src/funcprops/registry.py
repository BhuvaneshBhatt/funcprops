from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from typing import Any

import sympy as sp
from sympy import Symbol

from .conditions import parse_catalogue_expression


def _balanced_content(text: str, start: int, open_char="[", close_char="]"):
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return text[start + 1 : i]
    return None


def _split_top_level(text: str):
    out = []
    start = 0
    depth = 0
    pairs = {"[": "]", "(": ")", "{": "}"}
    closes = set(pairs.values())
    stack = []
    for i, ch in enumerate(text):
        if ch in pairs:
            stack.append(pairs[ch])
            depth += 1
        elif ch in closes and stack and ch == stack[-1]:
            stack.pop()
            depth -= 1
        elif ch == "," and depth == 0:
            out.append(text[start:i].strip())
            start = i + 1
    out.append(text[start:].strip())
    return out


def _source_signature(lhs: str | None):
    """Extract the represented function pattern and property mode/variable."""
    if not lhs:
        return None, (), None, None
    lhs = lhs.split("/;", 1)[0].strip()
    first = lhs.find("[")
    if first < 0:
        return None, (), None, None
    outer = _balanced_content(lhs, first)
    if outer is None:
        return None, (), None, None
    outer_args = _split_top_level(outer)
    if not outer_args:
        return None, (), None, None
    fpat = outer_args[0].strip()
    if fpat.startswith("HoldPattern["):
        i = fpat.find("[")
        inner = _balanced_content(fpat, i)
        if inner is not None:
            fpat = inner.strip()
    hidx = fpat.find("[")
    if hidx < 0:
        return fpat, (), None, outer_args[1] if len(outer_args) > 1 else None
    head = fpat[:hidx].strip()
    inner = _balanced_content(fpat, hidx)
    args = tuple(_split_top_level(inner or "")) if inner is not None else ()
    prop_head = lhs[:first].strip()
    mode = None
    var_token = None
    if "SingularityProperties" in prop_head and len(outer_args) > 1:
        token = outer_args[1].strip()
        if token == "True":
            mode = "real"
        elif token == "False":
            mode = "complex"
        else:
            mode = "any"
    if "RealUnivariateProperties" in prop_head and len(outer_args) > 1:
        var_token = outer_args[1].strip()
    return head, args, mode, var_token


def _pattern_name(token: str):
    token = token.strip()
    m = re.match(r"([A-Za-z$][A-Za-z0-9$]*)_", token)
    if m:
        return m.group(1)
    m = re.match(r"([A-Za-z$][A-Za-z0-9$]*):", token)
    if m:
        return m.group(1)
    return None


def _literal_pattern_matches(token: str, actual) -> bool:
    token = token.strip()
    # Ordinary named patterns are handled by guards/assumptions.
    if "_" in token and re.match(r"^[A-Za-z$][A-Za-z0-9$]*_", token):
        return True
    # a:(2|3), a:3 style restricted alternatives/defaults.
    if ":" in token and re.match(r"^[A-Za-z$][A-Za-z0-9$]*:", token):
        rhs = token.split(":", 1)[1].strip()
        if rhs.startswith("(") and rhs.endswith(")") and "|" in rhs:
            vals = rhs[1:-1].split("|")
            return any(_literal_pattern_matches(v, actual) for v in vals)
        if rhs.startswith("_"):
            return True
        return _literal_pattern_matches(rhs, actual)
    # List/vector patterns and Blank/Repeated constructs are too rich to match
    # syntactically here; leave them to their explicit registry guard.
    if any(x in token for x in ("_", "Repeated[", "Vectors[", "Matrices[")):
        return True
    try:
        literal = parse_catalogue_expression(token)
        if isinstance(actual, sp.Basic) and isinstance(literal, sp.Basic):
            return sp.simplify(actual - literal) == 0
        return actual == literal
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class RuleCase:
    value_source: str
    condition_source: str
    source_property_type: str | None = None
    source_lhs: str | None = None

    @property
    def condition(self):
        return parse_catalogue_expression(self.condition_source or "True")

    @property
    def value(self):
        return parse_catalogue_expression(self.value_source)

    @property
    def signature(self):
        return _source_signature(self.source_lhs)

    def substitutions(self, expr):
        _, patterns, _, _ = self.signature
        repl = {}
        for token, actual in zip(patterns, getattr(expr, "args", ()), strict=False):
            name = _pattern_name(token)
            if name:
                repl[Symbol(name)] = actual
        return repl

    def instantiate(self, expr):
        repl = self.substitutions(expr)
        value = self.value
        condition = self.condition
        if isinstance(value, sp.Basic):
            value = value.xreplace(repl)
        if isinstance(condition, sp.Basic):
            condition = condition.xreplace(repl)
        return value, condition

    def matches(self, expr, *, var=None, mode=None) -> bool:
        _, patterns, case_mode, var_token = self.signature
        args = getattr(expr, "args", ())
        if patterns and len(patterns) != len(args):
            return False
        for token, actual in zip(patterns, args, strict=False):
            if not _literal_pattern_matches(token, actual):
                return False
        if mode in ("real", "complex") and case_mode not in (None, "any", mode):
            return False
        if var is not None and var_token is not None:
            name = _pattern_name(var_token)
            if name:
                mapped = self.substitutions(expr).get(Symbol(name))
                if mapped is not None and mapped != var:
                    return False
        return True

    def specificity(self, *, mode=None) -> int:
        _, patterns, case_mode, _ = self.signature
        score = 0
        for token in patterns:
            t = token.strip()
            if ":" in t:
                score += 3
            elif re.search(r"_(Integer|Real|Complex|Positive|NonNegative)", t):
                score += 2
            elif "_" not in t:
                score += 4
        if mode in ("real", "complex") and case_mode == mode:
            score += 2
        return score


@dataclass(frozen=True)
class Family:
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

    @property
    def catalogue_names(self):
        return tuple(self.raw.get("catalogue_names", ()))

    def cases(self, prop: str) -> tuple[RuleCase, ...]:
        p = self.raw.get("properties", {}).get(prop, {})
        return tuple(
            RuleCase(
                **{
                    k: c.get(k)
                    for k in (
                        "value_source",
                        "condition_source",
                        "source_property_type",
                        "source_lhs",
                    )
                }
            )
            for c in p.get("cases", ())
        )


class FunctionRegistry:
    def __init__(self, records: Iterable[dict[str, Any]]):
        self._families = tuple(Family(r) for r in records)
        self._by_name = {}
        for fam in self._families:
            for n in (
                fam.id,
                *fam.sympy_names,
                *fam.mpmath_names,
                *fam.catalogue_names,
            ):
                self._by_name.setdefault(n, fam)

    def __len__(self):
        return len(self._families)

    def __iter__(self):
        return iter(self._families)

    def get(self, name: str) -> Family | None:
        return self._by_name.get(name)

    def require(self, name: str) -> Family:
        f = self.get(name)
        if f is None:
            raise KeyError(name)
        return f


@lru_cache(maxsize=1)
def registry() -> FunctionRegistry:
    p = files("funcprops").joinpath("data/catalogue.json")
    payload = json.loads(p.read_text())
    return FunctionRegistry(payload["families"])
