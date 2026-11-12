# Real image methods and proof obligations

The range assembler handles supported elementary images, compact critical covers, exact implicit values, partial enclosures, common periods, monotone tails and rational polynomial parameter families through degree three. This page describes the image contracts and supported proof methods. See the [range tutorial](../ranges.md) for implemented interfaces and their limits.

Image assembly combines exact source facts, critical geometry, endpoint ownership and tail coverage. A complete critical-point cover should remain useful when an interval endpoint has no closed form or two candidate values cannot yet be ordered.

## Methods and limits

| Mechanism | Implemented scope | Remaining work |
| --- | --- | --- |
| Exact image conditions | Complete critical covers yield Boolean membership without total value ordering | More compact canonical forms for unrelated implicit endpoints |
| Root-evidence reuse | Checked unique-root covers/leaves, exact nonrational brackets, selected common/reflected identities | General analytic root/value identities |
| One-sided cells | Supported C1 interiors, exact endpoint limits, finite Piecewise/Abs/Min/Max partitions | Broader branch and symbolic continuity/root coverage |
| Tail facts | Monotone tails or polynomial trends with bounded oscillatory remainders; caller-side asymptotic adapter | Arbitrary uniform-remainder and parameter-dependent tail facts |
| Flat roots | Independent exact-jet order cap and cached first nonzero jets | More general root clusters and analytic factor discovery |
| Incommensurate periodic images | Two algebraic irrational-ratio frequencies with rational pi phase offsets, including endpoint ownership | Higher-rank relations and general phases |
| Analytic parameter families | Rational cubic families, supported invertible heads and selected strongly convex root-level families | General analytic event discovery and tail transitions |

## Exact formulas before canonical interval presentation

Suppose a connected source cell is continuous and has a finite, exhaustive list of endpoint limits and stationary values. For each possible extremal value `v_i`, retain whether it is attained. Membership in the image can be written as the conjunction of two finite disjunctions: some site lies below the output, and some site lies above it. Use a non-strict comparison at an attained site and a strict comparison at an unattained endpoint limit. A constant cell needs an owned interior representative.

This construction yields an exact Boolean image condition without selecting the least and greatest site or deciding whether unrelated implicit values coincide. `RangeAnalysis.as_condition(y)` exposes that condition when the geometry is complete. Canonical intervals and value ordering can then improve presentation. Source components must be combined by union, and unresolved critical geometry must prevent an exhaustive condition claim.

Symmetry gives useful subsequent comparison rules. If `f(-x) = f(x)` is proved and two unique critical-root intervals correspond under reflection, their values agree. Overlapping brackets also need a checked common-root identity; bracket overlap alone does not prove that two roots are equal. No general analytic identity oracle is assumed.

`root_locations` reuses checked unique-root leaves through `ImplicitRealRoot.from_cover`. Exact nonrational brackets retain their existing evidence. Refinement uses checked subset witnesses, and transport preserves the proof. Source definedness and uniqueness remain bound to the root description.

## Endpoint and nonsmooth geometry

The general bounded-cell route can use native closure regularity or checked differentiability on each open interior, with one-sided endpoint limits and separate owned endpoint/seam values. Infinite limits do not belong to the image. A finite limit belongs only when another owned source point attains it.

Representative source and ownership cases include:

- `x*log(x)` on `(0,1]`, whose image is `[-1/E,0]`. Zero is attained at 1 even though the other endpoint is excluded.
- `sqrt(x) + exp(x)` on `[0,1]`, whose image is `[1,1+E]` despite an unbounded derivative at zero.
- `log(x) + 1/x` on `(0,1)`, whose image is `(1,infinity)`, with an unattained finite infimum.
- A held removable hole at a unique extremum, and a Piecewise seam whose value is outside both neighboring open-cell images.

The executable examples cover endpoint, cusp and owned-seam behavior. Unsupported symbolic backends and domain geometry still decline.

## Asymptotic facts without a dependency cycle

The asymptotic package requires `funcprops`. A required dependency in the reverse direction would create a cycle. `asymptotic.range_facts.range_tail_facts` translates supported limit proposals into `funcprops`-owned whole-tail facts. `bound_range_tail` checks a polynomial trend plus bounded oscillatory remainder; arbitrary remainder evidence needs further adapters. The raw expression, coordinate, direction, source domain, parameter assumptions, finite cutoff and bound evidence must remain attached.

A qualitative asymptotic equivalence can suggest a sign but does not provide the finite cutoff needed to join a compact core. For a derivative decomposition `f' = L + R`, a useful fact is an explicit whole-tail bound `|R| <= q*|L|` with `q < 1` and a known sign for `L`. A certified query must replay those premises, not trust a flag on a provider result.

Tail monotonocity is only one sufficient mechanism. For `f(x) = x**2 + sin(x**3)`, the bound `f(x) >= x**2 - 1` and the limit at both infinities can rule out distant tails from improving a known compact candidate, even though the derivative has infinitely many zeros. Continuity and unbounded output can then establish the remaining intermediate values. Complete analysis of the compact core is still needed for exclusion-based tails. Exact oscillatory phase sequences can instead establish surjectivity directly, as for x*sin(x). Rationally damped bounded oscillators also admit finite-limit tail enclosures.

## Periods and parameter events

For incommensurate frequencies, density describes closure and extremal bounds. Exact endpoint membership needs a separate argument. The continuous image of the real line under `sin(x) + sin(sqrt(2)*x)` is `(-2,2)`: density gives closure `[-2,2]`, while simultaneous endpoint phases are impossible. For `sin(x)**2 + sin(sqrt(2)*x)**2`, zero is attained at zero and the upper endpoint 2 is not attained. Source holes can change that endpoint ownership. An optimizer's certified bound with unknown attainment must not be promoted to a closed exact image.

Beyond the supported polynomial image and convex level families, an analytic continuation strategy needs event conditions for `f_x = f_xx = 0`, stationary points crossing endpoints or poles, and equal critical values at distinct source points. Parameter-dependent endpoint and tail transitions are also relevant. A sampled parameter grid cannot establish a complete event partition.

## Correctness and performance

The tests include source-hole and endpoint ownership cases, exact mathematical expected images, incomplete-budget answers, replay with discovery disabled, and mutations of each theorem premise. Retain separate flags for valid evidence, exhaustive geometry, exact image representation and numerical accuracy. Analysis defaults to `certified=False`, with replay requested explicitly.

Run workflows against installed wheels and include small fast-path benchmarks plus difficult root/tail cases. Record root searches, enclosure work, elapsed time and cold/warm cache state. Ball arithmetic can improve the existing enclosure engine; availability of a C library root-isolation routine does not establish that the installed Python wrapper exposes its callback interface.

[SymPy's function-range documentation](https://docs.sympy.org/latest/modules/calculus/index.html#sympy.calculus.util.function_range) describes the dependence on continuous components and critical-point discovery. [Arb's real-root algorithms](https://arblib.org/arb_calc.html) describe isolation and interval/Newton refinement; [python-flint's ball API](https://python-flint.readthedocs.io/en/latest/arb.html) documents the Python interval representation. These support bounded algorithm design without supplying a complete transcendental range solver.
