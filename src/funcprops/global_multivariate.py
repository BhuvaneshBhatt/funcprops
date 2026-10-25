"""Source-bound affine full-real mapping and dimension-safe composition."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise, product

import sympy as sp

from .results import ConditionalExpression, PropertyResult, TruthValue

_KINDS = {"injective", "surjective", "bijective"}


def _data(expressions, variables, kind):
    from .real_analysis.mapping import _multivariate_mapping_truth

    outs = tuple(map(sp.sympify, expressions))
    vv = tuple(map(sp.sympify, variables))
    if (
        not outs
        or not vv
        or any(not isinstance(v, sp.Symbol) for v in vv)
        or len(set(vv)) != len(vv)
    ):
        raise ValueError("nonempty outputs and distinct Symbol variables are required")
    J = sp.Matrix(outs).jacobian(vv)
    truth = _multivariate_mapping_truth(outs, vv, mode=kind)
    if not isinstance(truth, PropertyResult) and truth not in (
        TruthValue.TRUE,
        TruthValue.FALSE,
    ):
        truth = TruthValue.UNKNOWN
    return outs, vv, J, truth


def _context(assumptions, variables):
    from .assumptions import normalize_assumptions

    context = normalize_assumptions(assumptions)
    if context.free_symbols.intersection(variables):
        raise ValueError(
            "mapping assumptions must concern parameters, not full-real coordinates"
        )
    return context


def _specialize(truth, context):
    from .assumptions import entails
    from .stratification import resolve_result_assumptions

    if context is sp.S.false or entails(sp.S.false, context) is True:
        return TruthValue.UNKNOWN
    if isinstance(truth, PropertyResult):
        result = resolve_result_assumptions(truth, context, preserve_result=True)
        if result.primary in (TruthValue.TRUE, TruthValue.FALSE) and all(
            c.condition is sp.S.true for c in result.cases
        ):
            return result.primary
        return result
    return truth


@dataclass(frozen=True)
class GlobalMapCertificate:
    """Record global affine mapping properties under coefficient and rank premises."""

    classification: TruthValue
    kind: str
    jacobian: sp.Matrix
    source: str
    expressions: tuple | None = None
    variables: tuple | None = None
    cases: tuple = ()
    assumptions: object = sp.S.true

    @property
    def expression(self):
        return sp.Tuple(*self.expressions) if self.expressions is not None else None

    @property
    def variable(self):
        return sp.Tuple(*self.variables) if self.variables is not None else None

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify() and all(
            c.value is not TruthValue.UNKNOWN for c in self.cases
        )

    @property
    def scope(self):
        return "affine-map-between-full-real-spaces-under-parameter-assumptions"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            actual = affine_global_mapping(
                self.expressions,
                self.variables,
                kind=self.kind,
                assumptions=self.assumptions,
            )
            known = self.classification in (TruthValue.TRUE, TruthValue.FALSE) or any(
                c.value in (TruthValue.TRUE, TruthValue.FALSE) for c in self.cases
            )
            return known and self == actual
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


def affine_global_mapping(
    expressions, variables, *, kind="bijective", assumptions=True
):
    """Prove supported global mapping properties of a real affine map."""

    if kind not in _KINDS:
        raise ValueError("kind must be injective, surjective or bijective")
    outs, vv, J, truth = _data(expressions, variables, kind)
    context = _context(assumptions, vv)
    truth = _specialize(truth, context)
    cases = truth.cases if isinstance(truth, PropertyResult) else ()
    classification = TruthValue.UNKNOWN if isinstance(truth, PropertyResult) else truth
    source = (
        "affine-guarded-rank"
        if cases
        else "affine-full-rank"
        if classification is not TruthValue.UNKNOWN
        else "unproved-affine-hypotheses"
    )
    return GlobalMapCertificate(
        classification, kind, J, source, outs, vv, cases, context
    )


@dataclass(frozen=True)
class ComposedMapCertificate:
    """Transport checked global mapping properties through a composition."""

    components: tuple[GlobalMapCertificate, ...]
    kind: str
    classification: TruthValue
    source: str = "composition-of-certified-maps"
    cases: tuple = ()
    assumptions: object = sp.S.true

    @property
    def certified(self):
        return self.verify()

    @property
    def complete(self):
        return self.verify() and all(
            c.value is not TruthValue.UNKNOWN for c in self.cases
        )

    @property
    def scope(self):
        return "composition-between-full-real-spaces-under-parameter-assumptions"

    def verify(self):
        """Return whether the record satisfies its declared replay obligations."""

        try:
            known = self.classification is TruthValue.TRUE or any(
                c.value is TruthValue.TRUE for c in self.cases
            )
            return known and self == compose_global_maps(
                self.components, kind=self.kind, assumptions=self.assumptions
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
            NotImplementedError,
            ArithmeticError,
        ):
            return False


def compose_global_maps(certificates, *, kind="bijective", assumptions=True):
    """Compose compatible global-map certificates in application order."""

    if kind not in _KINDS:
        raise ValueError("kind must be injective, surjective or bijective")
    certs = tuple(certificates)
    if any(not isinstance(c, GlobalMapCertificate) for c in certs):
        raise TypeError("composition requires affine mapping certificates")
    coordinates = set().union(*(set(c.variables or ()) for c in certs))
    context = _context(
        sp.And(sp.sympify(assumptions), *(c.assumptions for c in certs)), coordinates
    )

    def result(value, cases=()):
        return ComposedMapCertificate(
            certs, kind, value, cases=cases, assumptions=context
        )

    if not certs or any(not c.verify() for c in certs):
        return result(TruthValue.UNKNOWN)
    allowed = {
        "bijective": {"bijective"},
        "injective": {"injective", "bijective"},
        "surjective": {"surjective", "bijective"},
    }[kind]
    if any(c.kind not in allowed for c in certs) or any(
        a.jacobian.rows != b.jacobian.cols for a, b in pairwise(certs)
    ):
        return result(TruthValue.UNKNOWN)
    specialized = tuple(
        affine_global_mapping(
            c.expressions, c.variables, kind=c.kind, assumptions=context
        )
        for c in certs
    )
    if all(c.classification is TruthValue.TRUE for c in specialized):
        return result(TruthValue.TRUE)
    cases = _composition_cases(specialized)
    return result(TruthValue.UNKNOWN, cases)


def _composition_cases(certs):
    if not certs or not any(c.cases for c in certs):
        return ()
    choices = [
        c.cases or (ConditionalExpression(c.classification, sp.S.true),) for c in certs
    ]
    size = 1
    for choice in choices:
        size *= len(choice)
    if size > 256:
        return ()
    cases = []
    for row in product(*choices):
        guard = sp.And(*(c.condition for c in row))
        if guard is not sp.S.false:
            value = (
                TruthValue.TRUE
                if all(c.value is TruthValue.TRUE for c in row)
                else TruthValue.UNKNOWN
            )
            cases.append(ConditionalExpression(value, guard))
    return tuple(cases)
