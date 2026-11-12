# Source domains and analysis components

Use domain records when canceling arithmetic or reusing a formula on a restricted real set. A canceled denominator still excludes its original zero, even if the simplified formula is constant.

```python
import sympy as sp
from funcprops import track_domain, function_cells, verify_certificate

x = sp.Symbol("x", real=True)
raw = sp.Mul(x, sp.Pow(x, -1, evaluate=False), evaluate=False)
record = track_domain(raw, x, sp.Interval(-1, 1))
assert record.effective == sp.Interval(-1, 1) - sp.FiniteSet(0)
assert verify_certificate(record, expr=raw, var=x)
cells = function_cells(raw, x, record.effective)
assert sp.Union(*(region for formula, region in cells)) == record.effective
```

A `DomainRecord` preserves the requested condition, natural domain, effective intersection and exclusions. An incomplete record supplies no exhaustive definedness claim. `function_cells` decomposes supported finite real geometry, retaining isolated Piecewise seams. Keep its regions bound to the original domain record when normalizing arithmetic or differentiating.

The public [analysis interface](analysis-interface.md) exposes these operations to consumers. Finite-component minimization and global-minimum certification belong to [symbopt](https://github.com/BhuvaneshBhatt/symbopt/blob/main/docs/guide/univariate-analysis.md). Root coverage, property ranges, domain tracking and real/complex enclosures remain in funcprops. The funcprops verifier accepts its own concrete records; use symbopt’s optimization verifier for optimization certificates.
