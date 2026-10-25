# Common proof routes: premises, coverage and scope

This guide states sufficient hypotheses for inequality, affine-map and root-box certificates.

## Inequality results

certify_inequality retains a source expression before simplifying lhs-rhs. The stored source DomainRecord must establish definition on the whole requested interval. Cancellation cannot turn a punctured expression into a proof on the missing point. UNKNOWN is a result, not a certificate of FALSE. This producer does not yet issue verified counterexample certificates, so FALSE payloads do not pass its verifier.

An outward-interval proof binds its expression, variable and domain to its real ball witness. A subdivision proof checks both children, their source/relation, and exact coverage of the parent interval. It can replay even if one whole-cell interval enclosure was inconclusive. Closed subdivision seams may overlap in an inequality proof; unlike additive root counts, this does not double-count a quantity. Original open outer endpoints are preserved.

No unused Taylor model is advertised as evidence for an inequality. A negative whole-cell enclosure stops futile subdivision but still returns UNKNOWN until there is a dedicated FALSE/counterexample proof route.

## Derivative induction

DerivativeChainCertificate binds the base proof to the claimed derivative, variable, domain and strict-positive relation. Its induction endpoint must be the finite left endpoint. The original function must have the required smooth real extension through that endpoint.

The result proves nonnegativity on domain and positivity on strict_domain. If f(left)=0 at an included endpoint, relation is >= and strict_domain omits that endpoint. For example exp(x)-1-x on [0,1] has a valid induction certificate, but the strict-positive claim applies to (0,1]. This preserves the intended earlier boundary behavior without labeling the zero endpoint strictly positive.

## Core plus tails

GlobalInequalityCertificate binds the positive core and every tail to the same source, coordinate and relation. Both strict tail bounds must reach the core; individually valid distant tails cannot cover a negative gap. A complete claim also establishes whole-real source definition. An inconclusive core is not a positive proof, regardless of how its tail records are labeled.

## Global affine maps and composition

The helper uses the guarded affine proof used by the main mapping API. A constant derivative alone is insufficient: Piecewise jumps can disappear under differentiation. Source definition, affine remainder, real coefficients, real offsets and non-generic rank must be established. Source expressions and variables are retained for replay. Unresolved parameter strata return UNKNOWN in the compact helper; the main mapping API retains guarded parameter cases.

Compositions are applied in listed order. Each output dimension must match the next input dimension. Only applicable TRUE component theorems prove a TRUE composite. Failure of sufficient hypotheses does not prove a FALSE composite; a noninjective outer map can still be injective on the preceding image.

Float coefficients are declined by the exact multivariate affine-rank and inverse-function determinant routes. A rounded determinant can be zero when the determinant of the stored dyadic coefficients is nonzero. Use Rational for exact decimal intent; explicitly converting a Float to Rational instead means its actual stored dyadic value. No tolerance is guessed, and numerical uncertainty is not converted into exact rank knowledge.

## Krawczyk root boxes

The interval arithmetic route establishes real polynomial smoothness, finite closed boxes, exact non-Float data, and a provably nonsingular center Jacobian before matrix inversion. A generic symbolic inverse is not a proof that a parameterized Jacobian is nonzero. Original coordinate holes and jumps cannot disappear during differentiation. Supported nonlinear polynomial boxes continue to certify; other families decline.

The factory-based affine record additionally checks the actual zero residual and unique affine rank. Its candidate being inside the box is insufficient. The interval route binds both its iteration center and recorded enclosure. The root field stores the iteration center in the interval route; the enclosure, not that field, describes where its certified zero lies. This naming issue remains on the smaller-issue list.

## Equation solution coverage

ConditionSet anywhere inside a returned solution set keeps complete=False. For x*(cos(x)-x)=0 on the real line, Union({0}, ConditionSet(...)) is not a complete explicit solution merely because the outer constructor is Union. Unresolved sets may still be represented and replayed accurately as partial results.

These changes are scoped soundness safeguards, not a package-wide independent formal proof system. Other factory-based records and domain/precision interfaces still need staged migration.
