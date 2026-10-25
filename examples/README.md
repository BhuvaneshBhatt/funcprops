# Runnable examples

Install the package and run an example from the checkout root, such as `python examples/restricted_domains.py`. Each file is a self-contained session with exact mathematical assertions. The tutorials and notebook are generated from these same sources.

| Task | Example | Level |
| --- | --- | --- |
| Can I certify an optimal finite bound and a total variation? | [finite_metric_proofs.py](finite_metric_proofs.py) | introductory |
| How can I reuse branch results without losing jumps? | [piecewise_partitions.py](piecewise_partitions.py) | introductory |
| How do input restrictions and held operations affect an answer? | [restricted_domains.py](restricted_domains.py) | introductory |
| How does the algebraic backend preserve principal branches and holes? | [algebraic_roots.py](algebraic_roots.py) | intermediate |
| What can I retain when a bounded search stops? | [budgets_and_resume.py](budgets_and_resume.py) | intermediate |
| Can I bound extrema without solving the stationary equation exactly? | [certified_extrema_bounds.py](certified_extrema_bounds.py) | intermediate |
| How do I keep an algebraic coefficient on its intended real conjugate? | [algebraic_coefficients.py](algebraic_coefficients.py) | intermediate |
| How do parameter guards and singleton branches reach downstream results? | [guarded_piecewise.py](guarded_piecewise.py) | intermediate |
| Can I check a native proof with its proposer disabled? | [replay.py](replay.py) | intermediate |
| How many distinct real roots does a polynomial family have? | [parameter_geometry.py](parameter_geometry.py) | intermediate |
| When is a real-root count exhaustive? | [real_root_coverage.py](real_root_coverage.py) | intermediate |
| How should I interpret unsupported or unfinished isolation? | [unsupported_and_partial.py](unsupported_and_partial.py) | intermediate |
| Does my complex result isolate roots individually at the requested accuracy? | [complex_isolation.py](complex_isolation.py) | advanced |
| Can I shrink a root box without discarding its complement? | [newton_refinement.py](newton_refinement.py) | advanced |
| Can local logarithms cover a loop without a global logarithm? | [branch_chart_gluing.py](branch_chart_gluing.py) | advanced |
| Do my selected local solutions agree on every overlap? | [branch_recipes.py](branch_recipes.py) | advanced |
| Can I prove common zeros and their orders at an implicitly located root? | [implicit_common_orders.py](implicit_common_orders.py) | advanced |
| Which counted points are source zeros, excluded extension zeros or poles? | [quotients_and_holes.py](quotients_and_holes.py) | advanced |
| How does a selected logarithmic germ affect a local residue? | [local_branches.py](local_branches.py) | advanced |

Edit the Python example and `workflow_notes.json`, then run `python -m tools.build_workflow_docs` to regenerate the [tutorials](../docs/tutorials/index.md) and [notebook](../docs/notebooks/certified-workflows.ipynb). Section markers keep explanations beside the corresponding source.

The property reference and property tour use `property_examples.py`. See [testing](../docs/guides/testing.md) for the execution gates.
