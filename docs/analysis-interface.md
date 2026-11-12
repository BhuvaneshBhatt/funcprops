# Analysis primitives for consumers

Use these primitives when building an optimizer, a plotting routine or a root-analysis workflow that needs to preserve definedness and distinguish exact conclusions from unresolved work. funcprops supplies analysis facts; a consumer selects its own strategy and decides which facts suffice for its conclusion.

| Operation | Public interface | Unresolved result |
| --- | --- | --- |
| Requested condition to real set | `condition_to_real_set` | `None`, including semantic predicates and unresolved parameter guards |
| Source definedness | `track_domain` | Incomplete `DomainRecord` |
| Formula normalization | `normalize_real_expression` | A formula; original holes stay in the separate domain record |
| Finite formula/region decomposition | `function_cells` | `None`; empty tuple means empty geometry |
| Real differentiability on a region | `derivative_on_domain` | `None` |
| Outward value enclosure | `value_enclosure`, `verify_value_enclosure` | `None` from construction; `False` from failed replay |
| Derivative-root coverage | `adaptive_root_coverage`, `check_coverage`, `refine_root_cover` | Explicit unresolved regions and exhaustion |
| Critical value regions | `critical_value_regions` | Raises for mismatched source/cover geometry; unresolved regions remain explicit |
| Exact implicit real values | `implicit_real_root`, `critical_value` | Raises if root existence/uniqueness or real definedness cannot be established |
| Exact or partial images | `analyze_range`, `refine_range` | `RangeAnalysis` with inner/outer sets and unresolved source regions |
| Parameter image families | `analyze_parameter_range`, `parameter_range` | Incomplete record or `None` for unsupported families |
| Whole-tail value bounds | `bound_range_tail`, `TailValueBound`, `FiniteTailBound` | `None` if supported dominance, rational damping, continuity or bounded-remainder analysis is unsupported |
| Exact identity verification | `verify_real_identity` | `False` when unproved |
| Source-bound payload comparison | `analysis_data_equal` | `False` on different data or record types |
| Trusted local worker transport | `pack_analysis_data` | Raises on unserializable data |

An enclosure describes its supplied formula and region. It does not establish that the raw source is defined there. A consumer must bind the formula to a checked source domain or establish a valid continuous extension. Root-cover refinement retains the source context, existing unresolved regions and root counts; its policy checks wall time between symbolic contractions. Use a process budget around a higher-level operation when a hard deadline is needed.

`pack_analysis_data` preserves held arithmetic and is for trusted local process messages. Its pickle payload must not be loaded from an untrusted source.

```python
import sympy as sp
import funcprops as fp

x = sp.Symbol("x", real=True)
D = fp.condition_to_real_set(sp.And(x > 0, x <= 1), x)
assert D == sp.Interval.Lopen(0, 1)
record = fp.track_domain(1 / x, x, D)
assert record.complete and record.effective == D
witness = fp.value_enclosure(x * x + 1, x, sp.Interval(-1, 1))
assert fp.verify_value_enclosure(witness, x * x + 1, x, sp.Interval(-1, 1))
assert witness.lower <= 1 and witness.upper >= 2
```

Optimization strategy, minimizing points, attainment decisions and extrema-bound assembly belong to [symbopt](https://github.com/BhuvaneshBhatt/symbopt/blob/main/docs/guide/univariate-analysis.md). funcprops has no dependency on symbopt. Exact root discovery and enclosure support remain limited to the documented grammars and resource policies.

See the [range analysis tutorial](ranges.md) for supported cases and examples. `critical_value_regions` supplies the common endpoint/critical/unresolved geometry used by symbopt's extrema-bound driver. The driver and its infimum/supremum assembly remain in symbopt.

An exact image is a set of attainable outputs. An interval enclosure, infimum and attained minimum have different contracts; see [ranges and extrema](https://github.com/BhuvaneshBhatt/symbopt/blob/main/docs/guide/ranges-and-extrema.md). Use the [range interface table](ranges.md#choose-the-interface) to choose between automatic `range`, explicit `analyze_range` and parameter-family analysis. The general image assembler uses native closure regularity or supported real-interior and one-sided-limit analysis. `max_cells` controls per-cell root work; `max_root_order` separately bounds exact-jet deflation. `RangeAnalysis.as_condition` can describe complete images without canonical interval ordering. These limits also constrain consumers that reuse its geometry.
