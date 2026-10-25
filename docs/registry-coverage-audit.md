# Registry coverage

Use the registry to inspect which function-property declarations and parameter guards are available. A declaration does not establish that every composition, domain or parameter case can be solved. The [capability matrix](capabilities.md) describes executable analysis; the [generated registry matrix](../.github/registry/coverage-matrix.md) records declaration counts and native rule types.

## Rule representation

Bundled cases have stable rule identities, structured positional signatures, analysis modes, coordinate bindings and precedence. Values and conditions use SymPy constructor expressions. The registry checks integer, parity, sign, numeric and tuple premises on the actual arguments. Variadic or nested patterns without a matching theorem decline. Unsupported values have neutral opaque identifiers and establish no property.

`Family.cases(property_name)` exposes immutable `RuleCase` records. Each `RuleSignature` contains `ArgumentPattern` records and the case's mode, coordinate and priority. Instantiation substitutes named subjects into the value and guard. More specific proved cases take precedence; unresolved guards remain explicit.

Native `PropertyRule`, `IdentityRule` and `DerivativeRule` declarations bind argument positions through `FunctionSlot` objects. Transport through a composition needs the relevant subject, image, regularity and chain-rule premises. A declaration about one argument does not automatically apply to every varying argument path.

## Coverage boundaries

Catalogue columns and executable theorem support measure different things. Root coverage, multiplicity, ordering, symmetry, periodicity, metric regularity, variation and integration can have algorithmic support outside the catalogue. Conversely, a catalogue column can contain an unresolved value or a condition that the engine cannot prove.

Special-function families also differ in parameter and argument support. Domain and shape declarations for complicated special functions do not imply exact root geometry or complete branch handling. Inspect the concrete theorem's guard and the returned completion fields before consuming a global conclusion.

## Inspect and validate

`examples/audit_registry_coverage.py` produces an inventory of declarations. `tools.registry_coverage.coverage_matrix` checks the generated matrix and native capabilities. `tools.audit_dlmf_catalogue` checks rule structure and the bundled DLMF provenance inventory. These checks establish representation consistency, not new mathematical theorems.

See [source semantics](source-semantics.md), [proof design](design/index.md) and [certification](certification.md) for the boundaries between declarations, candidate search and replayed evidence.
