# Capability matrix and limitations

The table describes proof-strength support, not every expression that may simplify successfully.

| Operation | Strongest supported class | Evidence | Common reason for `None` |
| --- | --- | --- | --- |
| Inverse | functions with a certified domain, image, and two-sided inverse identities | inverse certificate | image or injectivity unresolved |
| Equation solving | supported exact finite solution sets | solution certificate | completeness cannot be proved |
| Contour integration | exact pullbacks and validated analytic contour quadrature | integral result | singularity on path or enclosure failure |
| Winding number | supported closed analytic contours | winding certificate | crossing/integral unresolved |
| Homotopy, ≤1 puncture | supported closed based loops | winding normal form | winding unresolved |
| Homotopy, ≥2 punctures | exact transverse cut-crossing geometry | free-group normal form | ambiguous cut geometry |
| Contour deformation | rational meromorphic integrands and certified loop homotopy | deformation certificate | poles/topology unresolved |
| Residue/Laurent data | supported isolated local forms | local certificate | local expansion/order unresolved |
| Argument principle | rational meromorphic functions with complete finite divisor | divisor + winding evidence | meromorphicity/divisor unresolved |
| Singularity classification | supported local orders, logs, rational powers, elementary essential forms | classification certificate | local structure unresolved |
| Analytic continuation | structural logs and rational powers on supported loops | continuation certificate | unsupported germ/branch structure |

## Limitations

Funcprops does not turn heuristic numerical evidence into a mathematical certificate. General transcendental divisor analysis, arbitrary Riemann-surface continuation, non-isolated singular sets, and unresolved symbolic cut geometry remain outside current proof-strength coverage. See [Certification model](https://github.com/BhuvaneshBhatt/funcprops/blob/main/docs/certification.md) for result semantics.
