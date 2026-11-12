# Documentation

Funcprops studies where a SymPy expression is defined, which outputs it attains and which structural or analytic properties can be established on a chosen domain. Start with an executable task, then use its result contract to decide whether the answer covers your question.

## Start with a task

- [Workflow tutorials](tutorials/index.md), [standalone examples](../examples/README.md), the [property tour](notebooks/function-properties-tour.ipynb) and the [workflow notebook](notebooks/certified-workflows.ipynb).
- [Domains and branches](guides/domains-and-branches.md), [real outputs and source restrictions](real-source-contracts.md), [range interfaces](ranges.md) and [oscillatory and parameter applications](range-applications.md).
- [Real root coverage](tutorials/real-root-coverage.md), [polynomial parameter geometry](tutorials/parameter-geometry.md) and [exact coefficient fields](tutorials/algebraic-coefficients.md).
- [Complex isolation](tutorials/complex-isolation.md), [quotients and source holes](tutorials/quotients-and-holes.md), [Newton refinement](tutorials/newton-refinement.md) and [branch recipes](tutorials/branch-recipes.md).

## Interpret and reuse results

- [Capabilities and limitations](capabilities.md), [result contracts and glossary](reference/result-contracts.md), [troubleshooting](troubleshooting.md) and [known issues](known-issues.md).
- [Assumptions and caches](using-results.md), [budgets and resumption](guides/budgets-and-resume.md), [certification and trust](certification.md) and [input/replay robustness](robustness.md).
- [Public analysis interface](analysis-interface.md), [exact images and missing values](range-images.md), [differential proofs](differential-proofs.md) and [source semantics](source-semantics.md).

## Reference

- [Property reference](properties/index.md), [public helpers](reference/helpers.md) and [helper/proof field contracts](reference/helper-contracts.md).
- [Real coverage checker](root-coverage-checker.md), [enclosures](enclosures.md), [adaptive search](adaptive-coverage.md) and [infinite and parameter coverage](infinite-and-parameter-coverage.md).
- [Algebraic complex backend](algroots-complex-backend.md), [native complex isolation](native-complex-isolation.md), [completion](complex-completion.md) and [complex Newton refinement](complex-newton-refinement.md).
- [Quotient ledger](quotient-isolation.md), [shared orders and search](quotient-search.md), [branch atlases](branch-atlas.md) and [implicit common orders](implicit-orders.md).
- [Extrema analysis for optimization consumers](certified-extrema-bounds.md), [certified operations](certified-operations.md), [integration](integration.md), [complex analysis](complex-analysis.md), [homotopy](homotopy.md) and [contour examples](examples.md).
- [Mathematical conventions](mathematical-conventions.md), [Piecewise proofs](piecewise.md) and [statistical functions](statistical-special-functions.md).

## Design and development

- [Architecture](architecture.md), [proof design](design/index.md) and [real image methods](design/real-images.md).
- [Testing](guides/testing.md), [replay test matrix](reference/testing-matrix.md), [dispatch benchmarks](guides/fast-rules.md) and [bounded regularity and curvature](guides/bounded-proofs.md).
- [Registry coverage](registry-coverage-audit.md) and [DLMF declarations](dlmf-coverage.md).
