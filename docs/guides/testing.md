# Testing and release validation

Install the development dependencies with `python -m pip install -e '.[dev]'`. The development extra includes setuptools and wheel because distribution checks build without isolation. The build backend requires setuptools >=77 to support the existing SPDX license expression; see the [Setuptools license guide](https://setuptools.pypa.io/en/stable/userguide/license_migration.html). Run all commands from the checkout root. No audit scripts outside this repository are needed. Validation writes reports into a caller-selected directory.

## Reproducible profiles

```sh
python -m tools.validate --profile quick --report-dir validation/quick
python -m tools.validate --profile full --report-dir validation/full
python -m tools.validate --profile package --report-dir validation/package
python -m tools.check_kernel_mutations --report validation/kernel-mutations.json
```

Quick checks cover generated assets, local links and targeted contract/soundness cases. Full checks add all documentation sessions/notebooks, formatting, compilation, the entire source suite, kernel mutation probes and wheel/sdist behavior outside the checkout. Package checks build both archives, install each in isolation, verify import provenance/resources, and run representative behavior and documentation against the installed artifacts. They do not publish anything.

The source suite runs each test file in a fresh subprocess, preserving test interactions within that file and recording each result, timeout and JUnit file. A separate warm-state group runs related families together. Failures/timeouts are reported and cause failure; they are never converted into skipped successes. This is different from assuming one shared-process run equals a fresh-process run. Ordinary `python -m pytest` remains available.

## Documentation gates

```sh
python -m tools.build_property_docs --check
python -m tools.build_tutorial_notebook --check
python -m tools.build_workflow_docs --check
python -m tools.check_test_matrix --check
python -m tools.check_docs --report validation/docs.json
python -m tools.check_style
python -m tools.check_ci --check
python -m tools.build_helper_docs --check
```

All Python fences under README/docs execute; no Python block has an implicit skip. Blocks share a namespace within one page; pages start fresh. API signatures and pseudocode use text fences. Notebooks execute in cell order. Generated examples contain assertions, so execution alone is not their acceptance test. Links to local files and Markdown heading anchors are checked, including notebook Markdown cells; external URLs are not network-validated. Topical guides describe the same public contracts as the executable tutorials.

The property reference covers all 41 queries returned by properties(), including the five derived metric/variation/integrability helpers outside api.__all__. The registry fact matrix separately covers the 36 core property queries.

Property documentation uses tools/property_reference.json and examples/property_examples.py. Workflow tutorials/notebook use the standalone files listed by examples/workflow_catalog.py. Helper signatures reflect exported functions. Modify canonical sources, regenerate, and commit the generated result. Do not fix a generated page alone. Workflow sections and explanatory notes also generate the example index.

## Soundness and coverage matrix

The [test matrix](../reference/testing-matrix.md) assigns every registered replay type to maintained family tests and explicit obligations. Static assignment and API-call presence are navigational checks, not evidence of semantic coverage. The optional replay-evidence plugin records accepted/rejected registered types and the concrete test nodes that exercised them; missing observations stay gaps. Full validation requires both accepted and rejected observations for every registered type. This is an executed-fixture gate; it does not claim that observing a valid record proves every premise is tested.

Native checker probes reject omitted/duplicate/overlapping covers, altered sources, guards, boundaries, orders, totals and completion flags. A small mutation runner removes selected kernel checks in a temporary source copy; the targeted regression tests must kill each mutant. Production files are never modified. This samples the checker obligations, not an exhaustive mutation proof.

Generated adversarial cases use expressions with independently known roots, orders and exclusions. Algebraic differential tests compare scoped exact routes; floating approximations may corroborate behavior but are not expected-count oracles. Metamorphic transformations must preserve original source semantics, or explicitly compare extensions instead. Held x/x and 1 are not domain-equivalent.

## Randomized, platform and dependency checks

FUNCPROPS_TEST_PROFILE=ci is the default: bounded deterministic generation and no machine-speed Hypothesis deadlines. The extended profile uses more randomized examples. Named @settings in older tests can impose their own example counts. Mathematical correctness runs use bounded inputs and per-file timeouts; dedicated performance reports record elapsed time and work separately.

CI covers Python 3.11 to 3.14 on Linux, compatable minimum/current dependency sets, and selected budget/checkpoint/behavior smoke tests on macOS and Windows. Warm checks use multiple hash seeds. Branch-coverage reports focus attention on kernel and consumer paths; total test counts and a global percentage are not substitutes for checking theorem obligations. See the workflow files for the exact matrix.

`python -m tools.benchmark_roots --report validation/root-benchmarks.json` records correctness, complete/partial counts, work and advisory timing on a fixed construction set. Partial is a legitimate outcome. Timing is not a brittle unit test threshold; no broader theorem is inferred from a higher completion rate.

## Release gate

The release workflow tests and builds in one job, then validates the exact wheel and source archive uploaded to the publish job. It does not rebuild between validation and publication. Source/wheel resource identity and archive cleanliness are checked. Local full validation records the runtime/dependency versions; a configured CI matrix is not evidence that every environment passed locally.

## Shared selections and proof performance

`tools/test_selections.py` is the single catalog for quick, warm, platform, kernel and installed-distribution selections. CI invokes `python -m tools.run_selected_tests GROUP`; `tools.check_ci` rejects missing literal workflow paths, unknown groups and invalid catalog selectors. Warm selections prepopulate representative proof caches and run under multiple hash seeds. Platform selections include successful worker transport, timeouts, checkpoint handling and the finite/parameter/branch interfaces. A configured platform job is not a local claim that its environment passed.

`python -m tools.benchmark_proofs --report validation/proof-performance.json` reports proposal, replay and source-preserving transport costs separately for cold and warm caches. It records complete and valid partial cases, byte counts and known-answer checks. Proposal includes internal validation; transport excludes process startup. Timing is advisory, while a false mathematical claim fails the report.

`python -m tools.benchmark_routing --report validation/routing.json` checks fixed exact range answers and records raw cleared-cache/warm-cache timings, plus untimed counts of general solver calls. Its fallback controls measure the cost of unsuccessful specialized dispatch. Compare the same harness against both source trees before accepting a routing change; see [specialized property rules](fast-rules.md).

`python -m tools.benchmark_sign_routes --report validation/sign-routing.json` compares bounded sign, threshold, scalar-Jacobian and box-Hessian routes. UNKNOWN conclusions are recorded separately from proved answers. Rule ablations measure the contribution of each specialization; fallback controls expose dispatch overhead. The same environment and harness must be used for both source trees. Report cold/cleared and warm behavior separately, since a cached answer can mask changes in proposal cost.

`python -m tools.benchmark_structure --report validation/structure.json` measures the same property routes together with multivariate box proofs, certificate replay and factored scalar Jacobians. It records the full returned proof payload as well as the classification. Compare both payload identity and cleared/warm samples against the reference source tree when changing shared calculations.

Constructed property families exercise Piecewise images/order/variation, exact finite bounds, algebraic coefficient embeddings, multiple endpoint roots, assumption specialization and bounded resumption. Generated held trees and nested records check direct versus worker semantics and recovery from a truncated checkpoint frame. Mutation sentinels cover source/cover obligations, unique coefficient embeddings, owned values with internally consistent totals, parameter assumptions, geometry binding, overlap identities and worker transport. Every baseline must pass and every mutant must cause a test assertion failure; import/collection errors do not count as killed mutations.

The bounded property suite in `tests/test_practical_proofs.py` checks Jacobian root ownership, raw source holes, relative continuity, owned seam values, excluded-seam limiting gaps, interior Hessian counterexamples, exact exponential curvature moduli and entire square-root cancellations. It includes replay with proposers disabled and mutations of theorem fields. `tools.benchmark_practical` measures completed answers separately from UNKNOWN fallbacks against the same controls.
