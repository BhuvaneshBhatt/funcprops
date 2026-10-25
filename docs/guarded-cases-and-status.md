# Guarded cases and certification status

Polynomial parity at a finite real explicit center carries exhaustive coefficient-zero cases for BOTH, EVEN, ODD and NEITHER. Polynomial periodicity carries CONSTANT versus APERIODIC cases. Rich results expose `cases`; compact calls return the classification implied by supplied assumptions, otherwise UNKNOWN. Finite/source-definition guards retain undefined parameter strata as UNKNOWN. Center discovery remains supported and retains `query_center` separately from its discovered `center`, so replay repeats the correct query.

Full-real affine mapping results retain real-coefficient/offset guards, rank cases, and UNKNOWN outside the supported real/defined region. Assumptions such as Q.real(u) and Ne(u,0) can resolve these cases. Original source definition guards are collected before extraction: cancelled a/a or log(a)-log(a) cannot restore a map at a=0. Unproved coordinate holes decline full-space theorems. This source inspection is conservative; it is not a complete analytic domain solver.

The common detailed view separates `complete`, `certified` and `has_certificate`:

- `complete` describes whether the supported query is fully covered; a complete guarded polynomial partition need not have one unconditional classification.
- `certified` is explicit provider/replay status, independent of completeness. None means not reported. Affine/structural providers mark their supported guarded proof cases; these flags are not a substitute for validating arbitrary records. Structural replay checks the generated cases, query options and status.
- `has_certificate` means a certificate record is attached, not that it was verified. The detailed HTML view labels this as a recorded certificate.

Root results distinguish `evidence_certified` (recorded count/local evidence passes exact replay), `certified` (returned mathematical data agree with supported exact replay), `complete` (global coverage), and certificate/local-record presence. A valid partial root list can be certified and incomplete. A valid root count cannot certify corrupted returned roots. Supported complete payloads must agree with complete replay; partial payloads may contain verified subsets. Source expression, variable and requested domain are retained for this check.

Root replay status is computed on access and may be expensive. Numerical-only or factory-based unbound payloads can retain useful certificates while failing the current exact replay route; certified=False does not by itself prove the mathematics wrong. Certificate presence and local-record presence remain visible in detailed projection. Other package result families have not all migrated to explicit certification fields; unknown status is kept as None.

Symmetry/periodicity retain their expression-identity scope. These guarded cases do not add a general proof of arbitrary restricted-domain shift/reflection invariance, joint multivariate constraints, or all analytic singularities.
