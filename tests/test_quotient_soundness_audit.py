"""Reject empty-source poles and self-attesting nested count/domain records."""

from dataclasses import replace

import pytest
import sympy as s

import funcprops as fp
from funcprops import analytic_contours as ac
from funcprops import quotient_isolation as qi
from funcprops.complex_coverage import ComplexRootCoverage, ComplexRootRegionProof
from funcprops.verification import _certificate_verifiers

z = s.Symbol("z")
RECT = (-1 - s.I, 1 + s.I)


@pytest.mark.parametrize(
    "g", [s.sin(z) ** 2 + s.cos(z) ** 2 - 1, s.cosh(z) ** 2 - s.sinh(z) ** 2 - 1]
)
@pytest.mark.parametrize("d", [z, s.exp(z) - 1])
def test_local_pole_needs_nonempty_source_germs(g, d):
    # The original source is nowhere defined, despite its formal pair 1/d.
    assert s.trigsimp(g) == 0
    f = s.Mul(g, s.Pow(g * d, -1, evaluate=False), evaluate=False)
    source = qi._source(f, z)
    assert source.verify() and source.numerator == 1 and source.denominator == d
    n = fp.certify_analytic_contour(source.numerator, z, *RECT)
    den = fp.certify_analytic_contour(source.denominator, z, *RECT)
    assert n.verify() and den.verify() and den.zero_count == 1
    claim = fp.QuotientRegionProof(source, fp.QuotientCellProof(n, den), "pole")
    assert claim.multiplicity_count == 1
    assert not claim.verify() and not fp.verify_certificate(claim)
    assert fp.replay_status(claim).certified is False
    whole = fp.certify_quotient_isolation(
        f, z, *RECT, policy=fp.EnclosurePolicy(max_cells=64)
    )
    assert whole.verify() and not whole.complete and whole.total_count is None


@pytest.fixture(scope="module")
def quotient():
    return fp.certify_quotient_isolation((s.exp(z) - 2) / (s.exp(z) - 1), z, *RECT)


def test_public_pole_records_carry_replayable_source_domain_evidence(quotient):
    assert quotient.complete and quotient.verify()
    p = quotient.proof.pole_regions[0]
    assert p.guard_contours == quotient.proof.outer[2:]
    assert p.verify() and fp.verify_certificate(p)
    assert not replace(p, guard_contours=()).verify()
    # Positive root records prove actual source definition through exclusions.
    root = quotient.proof.root_regions[0]
    assert root.verify() and root.exclusions


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: replace(p, guard_contours=(None,)),
        lambda p: replace(p, guard_contours=p.guard_contours * 2),
        lambda p: replace(p, guard_contours=list(p.guard_contours)),
        lambda p: replace(
            p, guard_contours=(replace(p.guard_contours[0], expression=z + 3),)
        ),
        lambda p: replace(
            p, guard_contours=(replace(p.guard_contours[0], zero_count=False),)
        ),
        lambda p: replace(
            p,
            guard_contours=(
                replace(
                    p.guard_contours[0],
                    rectangle=fp.CoverageRectangle(2 - s.I, 3 + s.I),
                ),
            ),
        ),
    ],
)
def test_local_pole_domain_premise_is_bound_and_checked(quotient, mutate):
    record = mutate(quotient.proof.pole_regions[0])
    assert not record.verify()
    assert not fp.verify_certificate(record)


def test_nonvanishing_on_the_pole_is_not_required():
    q = fp.certify_quotient_isolation(1 / (s.exp(z) - 1) ** 2, z, *RECT)
    assert q.complete and q.verify() and q.pole_multiplicity_count == 2
    p = q.proof.pole_regions[0]
    assert p.verify() and p.guard_contours[0].zero_count == 1
    assert p.cell.denominator.zero_count == 2


def test_domain_guard_may_have_separate_removable_holes():
    f = s.Mul(z, s.Pow(z, -1, evaluate=False), 1 / (s.exp(z) - 2), evaluate=False)
    q = fp.certify_quotient_isolation(f, z, *RECT)
    assert q.complete and q.verify() and q.distinct_pole_count == 1
    assert len(q.proof.source.guards) == 2
    p = q.proof.pole_regions[0]
    assert len(p.guard_contours) == 2 and p.verify()
    assert not replace(p, guard_contours=p.guard_contours[:1]).verify()


def test_pole_domain_replay_never_searches(monkeypatch, quotient):
    record = quotient.proof.pole_regions[0]

    def forbidden(*args, **kwargs):
        raise AssertionError("domain replay invoked search")

    monkeypatch.setattr(qi, "certify_analytic_contour", forbidden)
    monkeypatch.setattr(ac, "certify_analytic_contour", forbidden)
    monkeypatch.setattr(qi, "_source", forbidden)
    monkeypatch.setattr(qi, "_run", forbidden)
    assert record.verify() and fp.verify_certificate(record)
    assert quotient.verify()


@pytest.fixture(scope="module")
def polynomial():
    q = fp.complex_root_coverage(z**2 + 1, z, -2 - 2 * s.I, 2 + 2 * s.I)
    assert q.verify() and q.root_count == 2
    return q


def test_polynomial_assembly_rejects_self_attesting_regions(polynomial):
    class LyingRegion(ComplexRootRegionProof):
        def verify(self):
            return True

    p = polynomial.regions[0]
    forged = LyingRegion(p.expression, p.variable, p.rectangle, 77, 77)
    q = replace(polynomial, regions=(forged,), root_count=77, multiplicity_count=77)
    assert not q.verify() and not fp.verify_certificate(q)
    assert fp.replay_status(q).certified is False
    assert not fp.verify_certificate(forged)


def test_direct_base_region_check_does_not_accept_a_subclass(polynomial):
    class OtherRegion(ComplexRootRegionProof):
        pass

    r = polynomial.regions[0]
    q = OtherRegion(**r.__dict__)
    assert not q.verify() and not fp.verify_certificate(q)


def test_polynomial_assembly_subclasses(polynomial):
    class LyingCover(ComplexRootCoverage):
        def verify(self):
            return True

    q = LyingCover(**replace(polynomial, root_count=77, multiplicity_count=77).__dict__)
    assert not fp.verify_certificate(q)
    assert fp.replay_status(q).certified is False


@pytest.mark.parametrize(
    "name", ["rectangle", "unresolved_rectangle", "region_rectangle"]
)
def test_polynomial_cover_does_not_trust_rectangle_subclasses(polynomial, name):
    class LyingRectangle(fp.CoverageRectangle):
        def valid(self):
            return True

    r = polynomial.rectangle
    bad = LyingRectangle(r.lower_left, r.upper_right)
    if name == "rectangle":
        p = replace(polynomial, rectangle=bad)
    elif name == "region_rectangle":
        p = replace(
            polynomial, regions=(replace(polynomial.regions[0], rectangle=bad),)
        )
    else:
        p = replace(
            polynomial,
            regions=(),
            unresolved=(bad,),
            complete=False,
            root_count=None,
            multiplicity_count=None,
        )
    assert not p.verify() and not fp.verify_certificate(p)


@pytest.mark.parametrize("field", ["regions", "unresolved"])
def test_polynomial_assembly_requires_immutable_region_lists(polynomial, field):
    assert not replace(polynomial, **{field: list(getattr(polynomial, field))}).verify()


def test_polynomial_count_replay(monkeypatch, polynomial):
    import funcprops.complex_coverage as cc

    def forbidden(*args, **kwargs):
        raise AssertionError("replay invoked coverage proposer")

    monkeypatch.setattr(cc, "complex_root_coverage", forbidden)
    assert polynomial.verify() and fp.verify_certificate(polynomial)


@pytest.mark.parametrize(
    "base",
    [t for t, _ in _certificate_verifiers()],
    ids=lambda t: t.__module__ + "." + t.__name__,
)
def test_unregistered_record_dispatch(base):
    forged_type = type(
        "Unregistered" + base.__name__, (base,), {"verify": lambda self: True}
    )
    forged = object.__new__(forged_type)
    assert fp.verify_certificate(forged) is False
    status = fp.replay_status(forged)
    assert status.certified is False and status.complete is False
    assert status.outcome == "rejected-evidence"


def test_registered_derived_record_selects_its_own_checker(monkeypatch):
    import funcprops.verification as verification

    class Base:
        pass

    class Derived(Base):
        pass

    monkeypatch.setattr(
        verification,
        "_certificate_verifiers",
        lambda: (
            (Base, lambda cert, expr, var: False),
            (Derived, lambda cert, expr, var: True),
        ),
    )
    assert verification.verify_certificate(Derived()) is True
    assert verification.verify_certificate(Base()) is False

    class Unregistered(Derived):
        pass

    assert verification.verify_certificate(Unregistered()) is False


def test_factory_real_coverage_rejects_self_attesting_count_leaf():
    from funcprops.root_coverage import RootRegionProof

    x = s.Symbol("x", real=True)
    good = fp.root_coverage(x**2 + 1, x, s.Interval(-1, 1))
    assert good.verify() and good.root_count == 0

    class LyingRegion(RootRegionProof):
        def verify(self):
            return True

    leaf = LyingRegion(
        **replace(good.regions[0], root_count=77, multiplicity_count=77).__dict__
    )
    bad = replace(good, regions=(leaf,), root_count=77, multiplicity_count=77)
    assert not bad.verify() and not fp.verify_certificate(bad)


@pytest.mark.parametrize("native", [False, True])
def test_root_coverage_cannot_shrink_its_domain_through_a_callback(native):
    from funcprops.domain_tracking import DomainRecord
    from funcprops.root_coverage import RootCoverageCertificate

    x = s.Symbol("x", real=True)
    good = fp.prove_root_coverage(x, x, s.Interval(-1, 1))
    assert good.verify() and good.root_count == 1

    class LyingDomain(DomainRecord):
        def verify(self):
            return True

        def matches(self, other):
            return True

    domain = LyingDomain(
        **replace(good.context.domain_record, effective=s.S.EmptySet).__dict__
    )
    if native:
        bad = replace(
            good,
            context=replace(good.context, domain_record=domain, effective=s.S.EmptySet),
            leaves=(),
            unresolved=s.S.EmptySet,
            complete=True,
            root_count=0,
            multiplicity_count=0,
            exhaustion=None,
        )
    else:
        bad = RootCoverageCertificate(
            x, x, domain, complete=True, root_count=0, multiplicity_count=0
        )
    assert not bad.verify() and not fp.verify_certificate(bad)


def test_specialized_coverage_children():
    from funcprops.root_coverage import RootCoverageCertificate

    x, a = s.symbols("x a", real=True)
    good = fp.specialize_root_coverage(x - a, x, {a: 0}, s.Interval(-1, 1))
    assert good.verify() and good.coverage.root_count == 1

    class LyingCover(RootCoverageCertificate):
        def verify(self):
            return True

    child = LyingCover(
        **replace(good.coverage, root_count=77, multiplicity_count=77).__dict__
    )
    assert not replace(good, coverage=child).verify()


@pytest.fixture(scope="module")
def uniform_box():
    x, a = s.symbols("x a", real=True)
    good = fp.certify_parameter_box(x - a, x, {a: s.Interval(0, 1)}, s.Interval(-2, 2))
    assert good.verify() and good.root_count == 1
    return good


@pytest.mark.parametrize("route", ["cover", "zero-subset", "parameter-cell"])
def test_parameter_assembly_children(uniform_box, route):
    from funcprops.parameter_contract import (
        ParameterCoverageProof,
        ParameterRootCell,
        UniformParameterCertificate,
        UniformParameterCover,
        UniformZeroSubsetWitness,
    )

    q = uniform_box

    class LyingUniform(UniformParameterCertificate):
        def verify(self):
            return True

    count = 0 if route == "zero-subset" else 77
    forged = LyingUniform(
        **replace(q, root_count=count, multiplicity_count=count).__dict__
    )
    if route == "zero-subset":
        bad = replace(
            q,
            root_count=0,
            multiplicity_count=0,
            witness=UniformZeroSubsetWitness(forged),
        )
    elif route == "cover":
        bad = UniformParameterCover(
            q.expression,
            q.variable,
            q.domain,
            q.parameter_domains,
            q.source_syntax,
            q.coordinate_assumptions,
            (forged,),
            s.S.EmptySet,
            True,
            77,
            77,
        )
    else:
        a, P = q.parameter_domains[0]
        cell = ParameterRootCell(P, "uniform-parameter-box", 77, 77, forged)
        bad = ParameterCoverageProof(
            q.expression,
            q.variable,
            a,
            q.domain,
            P,
            q.source_syntax,
            q.coordinate_assumptions,
            (cell,),
            s.S.EmptySet,
            True,
        )
    assert not bad.verify() and not fp.verify_certificate(bad)


def test_parameter_parent_replay():
    from funcprops.coverage_contract import CheckOutcome, CheckResult
    from funcprops.parameter_contract import (
        ParameterCoverageProof,
        SpecializedParameterProof,
    )

    x, a = s.symbols("x a", real=True)
    good = fp.parameter_root_coverage(x - a, x, a)
    assert good.verify()

    class LyingParent(ParameterCoverageProof):
        def check(self):
            return CheckResult(CheckOutcome.COMPLETE, True, True)

    cells = tuple(replace(c, root_count=77, multiplicity_count=77) for c in good.cells)
    forged = LyingParent(**replace(good, cells=cells).__dict__)
    bad = SpecializedParameterProof(forged, s.S.Zero)
    assert bad.root_count == 77
    assert not bad.verify() and not fp.verify_certificate(bad)


def test_adaptive_result_does_not_trust_a_state_check_override():
    from funcprops.adaptive_roots import AdaptiveRootResult, CoverageState
    from funcprops.coverage_contract import CheckOutcome, CheckResult

    x = s.Symbol("x", real=True)
    good = fp.adaptive_root_coverage(x, x, s.Interval(-1, 1))
    assert good.verify()

    class LyingState(CoverageState):
        def check(self):
            return CheckResult(CheckOutcome.COMPLETE, True, True)

    bad = AdaptiveRootResult(LyingState(**good.state.__dict__))
    assert not bad.verify() and not fp.verify_certificate(bad)
    with pytest.raises(TypeError):
        fp.resume_root_coverage(bad.state)


def test_real_tail_leaf_does_not_trust_a_tail_verifier_override():
    from funcprops.asymptotic_tails import TailSignCertificate
    from funcprops.root_coverage import RootRegionProof

    x = s.Symbol("x", real=True)
    good = fp.certify_tail_sign(x**2 - 2, x, threshold=2)
    assert good.verify()

    class LyingTail(TailSignCertificate):
        def verify(self):
            return True

    false_tail = LyingTail(**replace(good, threshold=s.S.Zero).__dict__)
    leaf = RootRegionProof(
        x**2 - 2, x, s.Interval(0, s.oo), "tail", 0, 0, (), false_tail
    )
    assert not leaf.verify() and not fp.verify_certificate(leaf)


def test_periodic_leaf_does_not_trust_a_family_verifier_override():
    from funcprops.root_coverage import RootRegionProof
    from funcprops.transcendental.periodic import PeriodicSet
    from funcprops.transcendental.roots import RootIsolationResult

    x = s.Symbol("x", real=True)

    class LyingFamily(RootIsolationResult):
        def verify(self):
            return True

    family = LyingFamily(
        expression=s.S.One,
        variable=x,
        periodic=PeriodicSet(s.FiniteSet(0), s.pi),
        complete=True,
    )
    leaf = RootRegionProof(
        s.S.One, x, s.S.Reals, "periodic-family", s.oo, s.oo, (), family
    )
    assert not leaf.verify() and not fp.verify_certificate(leaf)
