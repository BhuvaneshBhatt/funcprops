# Public helper reference

Signatures and implementation docstrings are generated from exported functions. The [helper and proof contracts](helper-contracts.md) describe accepted inputs, return records, completion and replay boundaries. Read the [result contracts](result-contracts.md) before consuming a proof.

## adaptive_complex_isolation

```text
adaptive_complex_isolation(expr, var, lower_left, upper_right, *, stages=1, policy=None, max_box_width=None, max_box_diameter=None, max_boundary_depth=14, use_newton=True, use_multiple=True)
```

Run finitely many cofinal stages; unresolved work always stays incomplete.

## adaptive_quotient_isolation

```text
adaptive_quotient_isolation(expr, var, lower_left, upper_right, *, stages=1, policy=None, max_box_width=None, max_box_diameter=None, max_boundary_depth=14, use_newton=True, use_multiple=True)
```

Run finitely many cofinal stages; unresolved work always stays incomplete.

## adaptive_root_coverage

```text
adaptive_root_coverage(expr, var, domain, *, policy=None, substitutions=())
```

Certify a finite cover or return a resumable exact unresolved frontier.

## affine_global_mapping

```text
affine_global_mapping(expressions, variables, *, kind='bijective', assumptions=True)
```

Prove supported global mapping properties of a real affine map.

## affine_sine_root_family

```text
affine_sine_root_family(expr, var)
```

Construct a guarded indexed zero family for an affine sine argument.

## affine_trig_root_family

```text
affine_trig_root_family(expr, var)
```

Construct an exhaustive affine sine, cosine or tangent zero family.

## algebraize

```text
algebraize(expr, var, *, domain=None, allow_trig=False)
```

Transform supported transcendental expressions while retaining exact domain constraints.

## analytic_complex_coverage

```text
analytic_complex_coverage(expr, var, lower_left, upper_right, *, policy=None)
```

Subdivide rectangles with unproved contours; every counted seam is clear.

## analytic_continue

```text
analytic_continue(expr, var, contour, *, return_certificate=False, work_budget=None)
```

Continue supported holomorphic operations and constant finite powers.

## analytic_neighborhood

```text
analytic_neighborhood(expr, var, interval, radius=None)
```

Certify a complex rectangular neighborhood of a finite real interval.

## analyze_transcendental_real

```text
analyze_transcendental_real(expr, var, domain=Reals)
```

Collect supported real domain, zero geometry, sign and image information.

## argument_principle

```text
argument_principle(expr, var, contour, *, return_certificate=False, guarded=False, assumptions=True, work_budget=None)
```

Return supported contour zero/pole counts with their analytic premises.

## argument_principle_count

```text
argument_principle_count(expr, var, rectangle, *, precision=60, max_boundary_depth=14)
```

Count zeros in a rectangle by a validated argument-principle contour.

Positive counts use the native exact boundary-homotopy checker. Rounded point evaluations and floating argument sums are diagnostic evidence only. Unsupported grammar or geometry remains uncertified.

## argument_principle_rectangle

```text
argument_principle_rectangle(expr, var, lower_left, upper_right)
```

Exact polynomial zero count in a complex rectangle.

SymPy's exact polynomial root counter is an argument-principle/Cauchy-index computation; the returned certificate independently replays the count.

## as_detailed_result

```text
as_detailed_result(value, *, domain=None, source=None, complete=None, domain_record=None)
```

Return a uniform detailed view without changing compact public APIs.

## cache_info

```text
cache_info()
```

Return ``functools`` cache statistics for every registered package cache.

## certified_monotonic_inverse

```text
certified_monotonic_inverse(expr, var, value, *, domain=True, partition=None)
```

Solve ``expr == value`` using a shared monotonic partition certificate.

Finite cells are solved independently, with uniqueness guaranteed on each strict cell.  Indexed partitions remain exact ``ConditionSet`` objects; this routine never numerically truncates an infinite family.

## certified_real_ball

```text
certified_real_ball(expr, var, domain, *, precision=None, max_precision=None, max_refinements=3, relation=None)
```

Enclose once, or refine a sign goal within explicit precision/work caps.

## certify_algebraic_complex_roots

```text
certify_algebraic_complex_roots(expr, var, rectangle, *, domain=Complexes, condition=True, max_auxiliary_variables=8, max_quotient_dimension=256)
```

Adapt exact algroots enumeration, source filtering and local certificates.

Rational powers retain principal-branch semantics. Multiplicity transfers only for rational sources; augmented-system orders are otherwise separate.

## certify_analytic_contour

```text
certify_analytic_contour(expr, var, lower_left, upper_right, *, policy=None)
```

Certify an entire function's zero count inside a rational rectangle.

## certify_branch_chart

```text
certify_branch_chart(relation, variable, value_symbol, rectangle, formula, *, logarithms=(), units=(), work_budget=None)
```

Check a local explicit recipe as a branch of an entire implicit relation.

## certify_common_zero

```text
certify_common_zero(expressions, base_region, *, max_order=8, policy=None)
```

Return local common-zero evidence; unresolved orders stay explicit.

## certify_complex_cluster

```text
certify_complex_cluster(expr, var, center, radius, *, policy=None)
```

Count a selected entire cluster, or report an unresolved analytic premise.

Cauchy's estimate on the outer circle bounds the omitted Taylor series; strict dominance of one monomial then gives a multiplicity-inclusive count.

## certify_complex_isolation

```text
certify_complex_isolation(expr, var, lower_left, upper_right, *, max_box_width=None, max_box_diameter=None, policy=None, max_boundary_depth=14, use_newton=True, use_multiple=True)
```

Isolate supported entire/quotient zeros with exact coverage and bounded work.

## certify_complex_multiple_root

```text
certify_complex_multiple_root(parent, *, center=None, policy=None)
```

Prove one selected multiple zero, or return None with no guessed order.

## certify_complex_refinement

```text
certify_complex_refinement(parent, *, policy=None)
```

Contract a known count-one rectangle, or return None without new claims.

Accepts a native count certificate or a public CertifiedComplexRootRectangle. A failed Newton proposal leaves the existing parent proof untouched.

## certify_extrema_bounds

```text
certify_extrema_bounds(expr, var, domain, *, tolerance=None, policy=None, critical_covers=())
```

Bound infimum/supremum without requiring explicit stationary coordinates.

Coverage may use enclosures of unresolved stationary regions. Accuracy is a separate, checked goal. Open endpoints contribute limits of C1 extensions, never a claim that the bounds or extrema are attained.

## certify_finite_lipschitz

```text
certify_finite_lipschitz(expression, variable, requested, *, work_budget=None)
```

Return an optimal finite-domain proof, or None if exact data is unresolved.

## certify_global_minimum

```text
certify_global_minimum(expr, var, domain=Reals, *, work_budget=None)
```

Certify an attained minimum by interval curvature or exact components.

## certify_global_positive

```text
certify_global_positive(expr, var, *, core_radius=8)
```

Combine a compact positivity proof with rigorous tail exclusions.

## certify_implicit_multiplicity

```text
certify_implicit_multiplicity(expression, base_region, *, max_order=8, policy=None)
```

Prove zero jets and a first nonzero jet on the isolating rectangle.

## certify_inequality

```text
certify_inequality(lhs, rhs, var, domain, *, relation='>', max_depth=8, precision=30, max_precision=240, max_refinements=3, work_budget=None)
```

Prove a supported real inequality on its effective source domain.

## certify_jump_variation

```text
certify_jump_variation(expression, variable, domain, *, work_budget=None)
```

Construct a finite variation proof using branch monotonic partitions.

## certify_log_atlas

```text
certify_log_atlas(expr, var, rectangles, *, policy=None)
```

Boundedly subdivide requested rectangles until half-plane charts are proved.

## certify_parameter_box

```text
certify_parameter_box(expr, var, parameter_domains, domain, *, policy=None)
```

Certify a full variable cover uniformly on a finite parameter box.

Simple whole-box counts use one leaf. Otherwise disjoint owned variable cells and inflated root windows are assembled without losing complements.

## certify_parameter_geometry

```text
certify_parameter_geometry(expression, variable, parameters, *, domain=Reals, parameter_domain=True, max_cells=256, work_budget=None)
```

Boundedly partition polynomial parameter space by certified root counts.

Up to four real parameters, degree at most four in the root coordinate and rational interval endpoints are supported. Counts are distinct-root counts; the unresolved frontier retains every region not discharged within the cap.

## certify_piecewise_boundaries

```text
certify_piecewise_boundaries(decomposition, *, max_order=1)
```

Certify seam values and one-sided derivatives through ``max_order``.

Limits are always taken on the selected branch expression, never on the enclosing Piecewise object.  ``differentiability_order`` is the highest derivative order whose two one-sided limits agree at the seam (0 means continuity only).

## certify_piecewise_regular

```text
certify_piecewise_regular(expression, variable, domain)
```

Prove continuous finite piecewise C1 structure; corners are allowed.

## certify_property_coverage

```text
certify_property_coverage(expr, var, domain=Reals, *, policy=None, critical_covers=(), zero_covers=())
```

Assemble exact property claims only from exhaustive checked geometry.

Optional covers are keyed by source-cell order and must bind the exact branch derivative/source on its open interior. Unknown locations or ordering leave the affected property incomplete. Monotonicity returns a full partition of open monotone cells plus singleton seams, instead of a global ordering claim.

## certify_quotient_isolation

```text
certify_quotient_isolation(expr, var, lower_left, upper_right, *, max_box_width=None, max_box_diameter=None, policy=None, max_boundary_depth=14, use_multiple=True, use_newton=True)
```

Certify quotient zeros and poles, retaining every raw inverse-base hole.

## certify_quotient_refinement

```text
certify_quotient_refinement(parent, *, cell_index=0, policy=None)
```

Refine a checked joint cell, retaining both divisor counts and its holes.

## certify_root_value

```text
certify_root_value(expression, base_region, *, max_nodes=128, max_power=4, work_budget=None)
```

Bounded congruence/polynomial-identity discovery; None means unresolved.

## certify_tail_sign

```text
certify_tail_sign(expr, var, *, direction=1, threshold=None)
```

Prove a supported tail sign using exact exponential dominance bounds.

## check_algebraic_complex_roots

```text
check_algebraic_complex_roots(proof)
```

Check the stored algebraic complex roots premises and report their replay outcome.

## check_analytic_contour

```text
check_analytic_contour(c)
```

Check the stored analytic contour premises and report their replay outcome.

## check_complex_cluster

```text
check_complex_cluster(cert)
```

Replay explicit Cauchy and Rouché inequalities without running search.

## check_complex_isolation

```text
check_complex_isolation(proof)
```

Check the stored complex isolation premises and report their replay outcome.

## check_complex_refinement

```text
check_complex_refinement(c)
```

Replay strict Krawczyk contraction and count transfer without search.

## check_coverage

```text
check_coverage(proof)
```

Check the stored coverage premises and report their replay outcome.

## check_enclosure

```text
check_enclosure(witness)
```

Replay raw syntax with primitive evaluators; never consult the leaf cache.

## check_leaf

```text
check_leaf(leaf)
```

Check both context and theorem premises for one proposed leaf.

## check_quotient_isolation

```text
check_quotient_isolation(p)
```

Check the stored quotient isolation premises and report their replay outcome.

## classify_singularity

```text
classify_singularity(expr, var, point, *, return_certificate=False, branch_context=None, work_budget=None)
```

Classify an isolated point using exact local order and branch structure.

## clear_caches

```text
clear_caches()
```

Clear all bounded package caches registered for explicit lifecycle control.

## clear_entailment_cache

```text
clear_entailment_cache() -> 'None'
```

Clear memoized assumption-entailment decisions.

## clear_monotonic_partition_cache

```text
clear_monotonic_partition_cache()
```

Clear shared derivative and monotonic-partition computations.

## close_assumptions

```text
close_assumptions(assumptions=True, *, max_rounds=3)
```

Derive supported property implications from normalized assumptions.

## close_theorems

```text
close_theorems(facts)
```

Close guarded theorem facts under supported implication rules.

## complex_isolation_policy_stage

```text
complex_isolation_policy_stage(stage, *, base=None)
```

Grow all caps while retaining every earlier precision in the portfolio.

## complex_root_coverage

```text
complex_root_coverage(expr, var, lower_left, upper_right)
```

Certify polynomial rectangle counts; boundary roots remain unresolved.

## compose_global_maps

```text
compose_global_maps(certificates, *, kind='bijective', assumptions=True)
```

Compose compatible global-map certificates in application order.

## compose_property

```text
compose_property(prop, outer_value, inner_value, *, outer_increasing=True, outer_domain=None, inner_image=None, outer_complete=True, inner_complete=True, outer_bound=None, inner_bound=None)
```

Compose certified facts, refusing unresolved map-interface obligations.

## coverage_policy_stage

```text
coverage_policy_stage(stage, *, base=None)
```

A cofinal sequence of finite effort caps, not an unconditional solver.

## decide

```text
decide(predicate, assumptions: 'sp.Expr | bool' = True, *, knowledge=<PropertyKnowledge.EXACT: 'exact'>, provenance: 'tuple[PropertyProvenance, ...]' = (), reasons: 'tuple[str, ...]' = ()) -> 'PropertyDecision'
```

Decide a property predicate from assumptions and retained theorem provenance.

## deflate_real_root

```text
deflate_real_root(expr, var, domain, center, order, *, policy=None)
```

Prove a finite-order zero by exact jets and a nonzero Taylor unit.

Return a checked local leaf, or None when any premise remains unproved. A small derivative or a numerical zero is never an exact jet witness.

## deform_contour

```text
deform_contour(expr, var, first, second, *, punctures=None, return_certificate=False, work_budget=None)
```

Certify contour deformation for rational meromorphic integrands.

## derivative_cell_root_count

```text
derivative_cell_root_count(expr, var, domain)
```

Count roots from a supported derivative-cell partition and owned endpoints.

## derivative_chain_positive

```text
derivative_chain_positive(expr, var, domain, *, max_depth=6)
```

Prove nonnegativity on domain and strict positivity on strict_domain.

A zero at an included left endpoint is retained in the nonnegative claim; it is explicitly excluded from strict_domain. No strict endpoint claim is inferred merely from positive higher derivatives.

## dlmf_audit_report

```text
dlmf_audit_report(family: 'str | None' = None)
```

Return the generated DLMF audit summary or one family's audit row.

## dlmf_facts

```text
dlmf_facts(family: 'str | None' = None)
```

Return executable and formula-audit DLMF facts.

The generated audit contributes one provenance record per exact formula or narrowly scoped DLMF section.  Helper/wrapper families are marked ``derived``.

## enclose_derivative

```text
enclose_derivative(expr, var, domain, *, order=1, policy=None)
```

Return an enclosure bound to the source and its full-cell regularity.

## enclose_expression

```text
enclose_expression(expr, var, domain, *, policy=None)
```

Intersect valid precision leaves; failed refinement retains earlier proof.

Complete here means a value enclosure on this cell, not root completeness. Refinement intersections are nested by construction, and replay checks every constituent outward enclosure independently of this scheduler/cache.

## encode_algebraic_coefficients

```text
encode_algebraic_coefficients(inputs, variables, *, work_budget=None)
```

Encode up to four real algebraic constants in one field of degree at most four.

All remaining symbols must be declared query coordinates. Inexact, nonreal, transcendental and larger fields decline before a rational backend is loaded.

## entails

```text
entails(condition: 'sp.Expr', assumptions: 'sp.Expr | bool' = True) -> 'bool | None'
```

Return whether normalized assumptions entail ``condition``.

The implementation is bounded: structural and affine Eq/Ne reasoning precede SymPy's assumptions engine; unresolved predicates remain unresolved.

## executable_special_theorems

```text
executable_special_theorems(expr, var)
```

List supported special-function theorems and their parameter guards.

## exp_linear_discriminant

```text
exp_linear_discriminant(expr, var, a, b)
```

Compute the supported exponential-linear root transition locus.

## exp_linear_root_strata

```text
exp_linear_root_strata(expr, var, a, b)
```

Partition a supported exponential-linear family by its real root counts.

## explain

```text
explain(value)
```

Present a property's value, guarded cases and evidence in a common view.

## explain_proof

```text
explain_proof(value, *, completeness=None)
```

Present a proof's replay status, scope and unresolved obligations.

## explain_result

```text
explain_result(value)
```

Return a concise explanation of a property result or certificate.

## exponential_affine_transition_cells

```text
exponential_affine_transition_cells(expr, variable, parameter)
```

Certified simple parameter strata for ``exp(x) + a``-type translations.

This recognizes only a family whose transition is exact: exp(x)+a has one real root for a<0 and none for a>=0 (with a=0 approached only at -oo).

## exponential_fourier_count

```text
exponential_fourier_count(expr, var, domain)
```

Certify the number of distinct real zeros of a restricted exp polynomial.

The proof is recursive.  Multiplication by the positive factor exp(-a0*x) preserves zeros; differentiating the normalized expression removes its lowest exponential term.  Exact derivative roots partition the interval into cells on which the normalized expression is strictly monotone.  Endpoint/critical-point signs then count exactly one or zero roots per cell.  The method declines to certify whenever a derivative root or sign cannot be established exactly.

## exponential_polynomial_terms

```text
exponential_polynomial_terms(expr, var)
```

Parse a restricted real exponential polynomial.

Supported inputs are finite sums of ``c*exp(a*x+b)`` and constants, with exact real coefficients/rates. Equal rates are combined.  This excludes polynomial prefactors and nested exponentials.

## export_coverage_proof

```text
export_coverage_proof(certificate, *, policy=None)
```

Construct independent coverage witnesses from supported finite root records.

Each region is re-proved and checked. Tails or families without a matching witness theorem remain unresolved; a provider status flag is insufficient.

## extremum_geometry

```text
extremum_geometry(expr, var, *, domain=Reals, partition=None)
```

Build indexed extremum evidence bound to its source expression.

## extremum_ordering_theorems

```text
extremum_ordering_theorems(expr, var)
```

Return exact ordering theorems for indexed extremum families.

The Airy proof is derived from ``E=y'^2-x*y^2``: ``E'=-y^2`` and ``(E/(-x))'=y'^2/x^2>0`` for ``x<0``.  At a critical point this ratio is ``y^2``, hence amplitudes decrease as the Airy zero index increases away from zero.

For Bessel J, with ``E=x^2*y'^2+(x^2-nu^2)*y^2``, Bessel's equation gives ``E'=2*x*y^2`` and ``(E/(x^2-nu^2))'=-2*x^3*y'^2/(x^2-nu^2)^2 < 0`` for ``x>nu``.  At critical points the ratio is ``y^2``.  DLMF 10.21.E3 places the positive J_nu derivative zeros at or beyond nu (strictly beyond for the nonzero critical points), yielding decreasing successive extremum magnitudes.

## finite_component_minimum

```text
finite_component_minimum(expr, var, domain=Reals)
```

Find a rational function's infimum, distinguishing unattained limits.

All derivative roots must be solved exactly; unresolved comparisons or root coverage return an incomplete result, without claiming an optimum.

## generated_adversarial_cases

```text
generated_adversarial_cases()
```

Metadata-driven near misses used by architecture/adversarial tests.

## glue_branch_charts

```text
glue_branch_charts(charts, *, requested=None, unresolved=(), work_budget=None)
```

Glue arbitrary supported local branch recipes using certified overlaps.

This assembles given charts; it does not discover arbitrary inverse branches or invent identities. Undecided overlaps and uncovered rectangles remain partial.

## glue_log_charts

```text
glue_log_charts(charts, *, requested=None, normalize_sheets=True, unresolved=(), tested=0, exhaustion=None)
```

Check every shared boundary/overlap, retaining nontrivial transition cycles.

## grammar_obligations

```text
grammar_obligations(expr, var)
```

Syntax obligations only; branch and regularity premises are additional.

## holomorphic_on_rectangle

```text
holomorphic_on_rectangle(expr, var, rectangle)
```

Certify supported principal-branch holomorphy on a closed rectangle.

Returns ``holomorphic=None`` when the current symbolic tests cannot certify either outcome.  No floating sampling is used for a positive certificate.

## homotopic

```text
homotopic(contour1, contour2, *, punctures=(), return_certificate=False, work_budget=None)
```

Certify based-loop homotopy in ``C`` minus finitely many punctures.

The implementation uses a certified cut system and the standard free-group normal form of ``pi_1(C \ P)``.  Thus generator order is retained and the result is genuinely nonabelian for two or more punctures.  ``None`` means that exact crossing geometry could not be certified for the supplied symbolic parameterizations; it is not a negative homotopy result.

## indexed_tail_integer_bracket

```text
indexed_tail_integer_bracket(zero_template, cutoff, *, direction='right', inclusive=True)
```

Certify an integer bracket for the first included indexed zero.

Currently formula-level rigorous for positive Bessel-J function and first derivative zero families with nonnegative real order.  Unsupported families return ``None``.

## indexed_tail_inversion

```text
indexed_tail_inversion(zero_template, cutoff, *, direction='right', inclusive=True)
```

Invert an indexed monotone zero family exactly at a cutoff.

The routine first applies exact same-family/interlacing identities.  For a general cutoff it returns an ``IndexedTailIndex`` whose semantics are the certified least included index; no floating root finder is used.

## infinite_root_coverage

```text
infinite_root_coverage(expr, var, domain=Reals, *, policy=None, substitutions=())
```

Adaptive core/tail or exhaustive periodic coverage for supported classes.

## injectivity_from_partition

```text
injectivity_from_partition(partition)
```

Three-valued injectivity conclusion from a compact or rich partition.

## integrate

```text
integrate(expr, limits, *, return_result=False, tolerance=None, _replay=False)
```

Integrate with source and error-bound certification.

``integrate(expr, (x,a,b))`` integrates over a finite interval/straight complex segment. ``integrate(expr, (z, contour))`` accepts a :class:`ParametricContour` or a sequence of polygon vertices.

## inverse

```text
inverse(expr, var, *, value=None, domain=Reals, return_certificate=False, work_budget=None)
```

Return a symbolic inverse after checking supported domain and identity premises.

## isolate_complex_roots

```text
isolate_complex_roots(expr, var, rectangle, *, precision=60, max_boundary_depth=14, max_isolation_depth=10, domain=Complexes, condition=True, policy=None, max_box_width=None, max_box_diameter=None, use_newton=True, use_multiple=True)
```

Return certified complex root rectangles inside ``rectangle``.

Rectangles with count one isolate a unique simple zero.  A terminal rectangle with count greater than one is a certified cluster counted with multiplicity. Native ``complete`` requires coverage, individual isolation and requested accuracy; ``coverage_complete`` also permits counted clusters. ``total_count`` includes multiplicity on both exact and contour routes; exact locations have a separate ``distinct_root_count``. An unavailable multiplicity stays None.

## krawczyk_box

```text
krawczyk_box(expressions, variables, box)
```

Prove a unique multivariate polynomial root in a supported real box.

## laurent_series

```text
laurent_series(expr, var, point=0, *, order=6, return_certificate=False, branch_context=None, work_budget=None)
```

Return a checked Laurent expansion at an exact point and chosen local branch.

## meromorphic_rectangle_count

```text
meromorphic_rectangle_count(expr, var, lower_left, upper_right, *, policy=None)
```

Count extension zeros/poles, retaining original source exclusions.

Rational sources use the existing exact divisor backend. Supported entire quotients use a replayable quotient ledger; unknown collisions decline.

## minimize_strata

```text
minimize_strata(result)
```

Merge equivalent parameter cases while retaining their guards.

## monodromy

```text
monodromy(expr, var, contour, *, return_certificate=False, work_budget=None)
```

Return the branch change from continuation around a supported closed path.

## monotonic_decomposition

```text
monotonic_decomposition(expr, var, *, strict=True, continuous=True, return_result=False)
```

Find ``expr = F(inner)`` with a certified monotone outer ``F``.

The ordinary result is the mathematical quadruple ``(inner, outer, direction, condition)``.  ``direction`` is ``1`` for an increasing outer map and ``-1`` for a decreasing one.  Use ``return_result=True`` for inverse information, provenance, and replayable certification metadata.

## monotonic_partition

```text
monotonic_partition(expr, var, *, domain=True, return_result=False)
```

Partition a real domain into intervals of certified monotonicity.

Complete finite partitions are returned by default as ordered ``(interval, direction)`` pairs.  If the result is incomplete or uses an indexed infinite description, the structured :class:`MonotonicPartition` is retained so completeness information is not lost.  Set ``return_result=True`` to always receive the structured result.

## normalize_assumptions

```text
normalize_assumptions(value)
```

Canonicalize Boolean syntax without expensive logical reasoning.

## parameter_root_coverage

```text
parameter_root_coverage(expr, var, parameter, domain=Reals, *, parameter_domain=Reals, policy=None)
```

Cover exact one-parameter strata, retaining all exceptional/unproved cells.

Full-space degree <=2 polynomials over QQ[parameter] and compact monotone translations have exact finite strata. Other finite parameter intervals use bounded uniform-box subdivision; collisions need not admit a finite proof.

## piecewise_decomposition

```text
piecewise_decomposition(expr, var, domain=True)
```

Build the certified effective-branch decomposition for a real query.

## polynomial_transition_locus

```text
polynomial_transition_locus(expr, var, parameters=None)
```

Compute parameter loci where a polynomial's degree or multiplicities can change.

## proof_api_manifest

```text
proof_api_manifest()
```

Return proof-type and API metadata, including each declared replay contract.

Entry-point discovery follows the static call graph conservatively: an API listed here can reach a proof-record constructor, but may also return an ordinary result or decline. The inventory is not a mathematical capability claim. Unsupported record types remain listed with replay_supported=False.

## properties

```text
properties(*, category=None)
```

List discoverable root-level mathematical properties.

Pass ``category=...`` to filter the catalog.  The return value is a tuple of ``(name, category, summary)`` triples so it is useful in terminals, notebooks, and documentation tooling without introducing another public result type.

## property_interval_decomposition

```text
property_interval_decomposition(expr, var, *, derivative_order=1, domain=Reals, positive_value=None, negative_value=None, derivative=None)
```

Build an exact interval-pattern certificate from derivative zero geometry.

Infinite indexed boundaries are represented by ``boundary_geometry`` and an alternating flag.

## prove_root_coverage

```text
prove_root_coverage(expr, var, domain=Reals, *, policy=None, substitutions=())
```

Build coverage evidence, preserving exact unresolved regions at every cap.

Infinite nonrational regions, arbitrary parameter strata, selected complex sheets and unsupported primitives remain explicit obligations.

## quadratic_discriminant_cells

```text
quadratic_discriminant_cells(expr, variable, parameter)
```

Exact parameter root-count strata for univariate quadratics in x.

## range_from_monotonic_partition

```text
range_from_monotonic_partition(expr, var, partition=None, *, domain=True)
```

Exact image set when a finite monotonic partition is complete.

## reduce_univariate_condition

```text
reduce_univariate_condition(condition, var, domain=Reals, *, allow_numerical=False)
```

Certified real-univariate reduction using exact real-univariate reduction.

Every relational boundary and discontinuity supplied by the caller should be represented as a relation in ``condition``.  The reducer isolates all roots, partitions the domain, samples each open cell and each boundary point, then reconstructs the exact solution.  It refuses certification if any root set is incomplete.

## refine_parameter_cells

```text
refine_parameter_cells(result, parameters=None, *, split_zero=True, split_sign=False, max_cells=32)
```

Refine unresolved parameter cells by exact zero/sign partitions.

This is bounded and purely symbolic.  It never samples parameter values and never labels a cell with a new conclusion; it only refines guards so existing conditional conclusions can specialize cleanly downstream.

## registry_chain_rule

```text
registry_chain_rule(expr, variables, *, registry=None, second_order=False) -> 'MultivariateChainRuleCertificate'
```

Transport registered derivatives through a multivariate inner map.

The result records formal identities and registered outer-rule conditions. Use source-domain and regularity proofs before applying them on a query set. Custom declarations require ``proof.verify(registry=trusted_registry)``.

## registry_derivative

```text
registry_derivative(expr, var, *, registry=None) -> 'ChainRuleCertificate'
```

Differentiate a function application via a registered outer gradient.

For a path ``x -> F(g1(x), ..., gn(x))`` this certifies the scalar derivative as the dot product of the registered gradient of ``F`` with the path tangent.

## registry_gradient

```text
registry_gradient(expr, *, registry=None, positions=None) -> 'GradientCertificate'
```

Build a certified gradient/partial vector from registered rules.

Conditional strata remain explicit: each requested argument position must have exactly one matching derivative theorem. Ambiguous or missing partials make the certificate incomplete.

## registry_hessian

```text
registry_hessian(expr, *, registry=None, positions=None) -> 'HessianCertificate'
```

Derive an outer Hessian from exact registered first-partial formulas.

This is stricter than numerical differentiation: every requested first partial must come from one unambiguous DerivativeRule, and its formula is differentiated with respect to the rule-local FunctionSlots before concrete arguments are substituted.

## registry_jacobian

```text
registry_jacobian(expressions, variables) -> 'JacobianCertificate'
```

Build the exact Jacobian of an explicit inner map.

## replay_status

```text
replay_status(record, *, expr=None, var=None, work_budget=None)
```

Report unknown for unsupported replay and false for failed replay.

Coverage is exposed only following successful replay. This does not turn a pointer or an unverified provider status flag into a verified proof.

## require_decision

```text
require_decision(decision: 'PropertyDecision', *, operation: 'str | None' = None, allow_unknown: 'bool' = False) -> 'PropertyDecision'
```

Return a proved property decision or raise PropertyEnforcementError.

## residue

```text
residue(expr, var, point, *, return_certificate=False, branch_context=None, work_budget=None)
```

Return a residue from supported exact local-order or Laurent data.

## resume_adaptive_complex_isolation

```text
resume_adaptive_complex_isolation(run, *, stages=1, seconds=None)
```

Continue a validated cofinal run with persistent geometry and effort state.

## resume_adaptive_quotient_isolation

```text
resume_adaptive_quotient_isolation(run, *, stages=1, seconds=None)
```

Continue a validated cofinal run with persistent geometry and effort state.

## resume_complex_isolation

```text
resume_complex_isolation(state, *, policy=None, max_boundary_depth=14, use_newton=True, use_multiple=True)
```

Validate a source-bound checkpoint before continuing its exact frontier.

## resume_parameter_geometry

```text
resume_parameter_geometry(proof, *, max_cells=256, work_budget=None)
```

Refine a checked unresolved parameter frontier with an additional cell budget.

## resume_quotient_isolation

```text
resume_quotient_isolation(state, *, policy=None, max_boundary_depth=14, use_multiple=True, use_newton=True)
```

Validate a joint zero/pole checkpoint and continue its pending frontier.

## resume_root_coverage

```text
resume_root_coverage(state, *, policy=None)
```

Resume the same partition; already certified leaves are retained.

## rewrite_with_registry

```text
rewrite_with_registry(expr, *, registry=None)
```

Instantiate an unambiguous native identity for ``expr`` if available.

## robust_real_sign

```text
robust_real_sign(expr, *, interval_fallback=True)
```

Return a certified sign for a real numeric expression when possible.

The exact symbolic route is tried first.  For unresolved numeric expressions in an audited exp/log vocabulary, interval arithmetic is used so very large or very small exponentials can be compared without overflow/underflow.  A numerical interval containing zero is *not* converted into a sign.

## root_coverage

```text
root_coverage(expr, var, domain=Reals, *, max_depth=10, max_cells=1024, use_families=True, use_tails=True)
```

Propose a verified partition; budget exhaustion keeps unresolved cells.

Multiple roots are supported by exact rational enumeration. Other tangencies remain unresolved. Infinite periodic coverage requires an exhaustive existing family theorem; strict tail bounds never stand in for the remaining core.

## rouche_polynomial_circle

```text
rouche_polynomial_circle(expr, var, *, center=0, radius=1)
```

Certify a polynomial disk count using a strict boundary dominance inequality.

## rouche_polynomial_rectangle

```text
rouche_polynomial_rectangle(expr, var, lower_left, upper_right)
```

Rouché count using a centered dominant monomial on a rectangle boundary.

## route_proofs

```text
route_proofs(expr, routes, *, budget=None)
```

Try eligible proof routes within the requested symbolic effort budget.

## simplify_extremum_range

```text
simplify_extremum_range(expr, var, result)
```

Simplify an ``ExtremumRange`` using exact indexed-extremum theorems.

## smooth

```text
smooth(expr, variable, *, domain=True, max_order=6, work_budget=None, assumptions=True, return_result=False)
```

Return whether ``expr`` is certified C-infinity on ``domain``.

This is the predicate companion to :func:`smoothness`, whose mathematical default is the certified differentiability order.

## solve

```text
solve(expr, var, *, domain=Complexes, return_certificate=False, guarded=False, assumptions=True, work_budget=None)
```

Return a supported equation's solution set, with detailed evidence on request.

## specialize_cells

```text
specialize_cells(result, substitutions)
```

Specialize guards and symbolic conclusions simultaneously.

Source-bound proof records are not rewritten by symbolic substitution. The returned mathematical cases have no inherited certification status; use the typed parameter-proof adapters when a replayable proof is required.

## specialize_parameter_coverage

```text
specialize_parameter_coverage(proof, value)
```

Bind an exact value to a checked stratum; no fresh numerical search.

## specialize_root_coverage

```text
specialize_root_coverage(expr, var, substitutions, domain=Reals, **kwargs)
```

Restrict a guarded root cover to exact parameter substitutions.

## structured_zero_geometry

```text
structured_zero_geometry(expr, var)
```

Return supported indexed zero geometry for a structured expression.

## symbolic_extremum_range

```text
symbolic_extremum_range(expr, var, domain=Reals, *, partition=None)
```

Compute a symbolic image with replayable source information.

## taylor_model

```text
taylor_model(expr, var, domain, *, order=2, center=None)
```

Construct a Taylor polynomial with a certified derivative remainder bound.

## track_domain

```text
track_domain(expr, var, domain=Reals, *, work_budget=None)
```

Certify exact natural domains or coverage of a requested Piecewise set.

Local records have natural=None and natural_complete=False: they do not purport to describe points outside the requested set, or continuity.

## transcendental_roots

```text
transcendental_roots(expr, var, domain=Reals, *, allow_numerical=True)
```

Isolate roots and bind emitted evidence to the analyzed expression.

## transport_instantiated_rule

```text
transport_instantiated_rule(instantiated: 'InstantiatedPropertyRule', analysis_var, *, domain=True, registry=None) -> 'TransportedPropertyRule'
```

Transport a native theorem to one or more analysis variables.

A single symbol uses scalar-path transport. A tuple/list of symbols invokes genuinely multivariate transport.

## validate_registry

```text
validate_registry()
```

Check theorem identifiers, premise declarations and adversarial case definitions.

## verify_certificate

```text
verify_certificate(cert, *, expr=None, var=None, work_budget=None)
```

Replay any certificate supported by the package verifier registry.

## verify_convexity_certificate

```text
verify_convexity_certificate(expr, var, cert)
```

Check the stored convexity certificate premises and report their replay outcome.

## verify_extremum_family

```text
verify_extremum_family(cert)
```

Check the stored extremum family premises and report their replay outcome.

## verify_extremum_ordering

```text
verify_extremum_ordering(cert)
```

Check the stored extremum ordering premises and report their replay outcome.

## verify_extremum_range

```text
verify_extremum_range(cert)
```

Check the stored extremum range premises and report their replay outcome.

## verify_indexed_tail_inversion

```text
verify_indexed_tail_inversion(cert)
```

Check the stored indexed tail inversion premises and report their replay outcome.

## verify_integer_bracket

```text
verify_integer_bracket(cert)
```

Check the stored integer bracket premises and report their replay outcome.

## verify_monotonic_decomposition

```text
verify_monotonic_decomposition(cert)
```

Check the stored monotonic decomposition premises and report their replay outcome.

## verify_monotonic_partition

```text
verify_monotonic_partition(expr, var, cert)
```

Check the stored monotonic partition premises and report their replay outcome.

## verify_real_root_interval

```text
verify_real_root_interval(expr, var, interval)
```

Check the stored real root interval premises and report their replay outcome.

## verify_root_certificate

```text
verify_root_certificate(cert)
```

Check the stored root certificate premises and report their replay outcome.

## verify_zero_geometry

```text
verify_zero_geometry(cert, *, expr=None, var=None)
```

Check the stored zero geometry premises and report their replay outcome.

## winding_number

```text
winding_number(contour, point=0, *, return_certificate=False, work_budget=None)
```

Return a checked integer winding for a supported closed nonvanishing path.

## zero_geometry

```text
zero_geometry(expr, var, *, derivative_order=0, domain=Reals)
```

Cached exact zero-geometry proof primitive.

## zero_ordering_bounds

```text
zero_ordering_bounds(zero)
```

Return exact symbolic neighbor inequalities known for an ``IndexedZero``.
