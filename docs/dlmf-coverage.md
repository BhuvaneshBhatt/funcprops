# DLMF property-table audit

`funcprops` uses SymPy semantics as its execution model, the NIST Digital Library of Mathematical Functions (DLMF) as the primary reference for standard special functions, and the imported property catalogue as a source of candidate facts. The audit therefore verifies catalogue claims.

The generated machine-readable manifest is `src/funcprops/data/dlmf_audit.json`. Regenerate it with:

```bash
python tools/audit_dlmf_catalogue.py
```

## Evidence classes

The audit distinguishes three kinds of DLMF relationship:

- `formula-verified-core`: the SymPy family represents a DLMF-native standard function and the audited property has an exact formula reference;
- `formula-verified-derived`: the SymPy object is a helper, wrapper, or representation class whose property follows from an exact DLMF formula for the underlying standard function; and
- `dlmf-related-not-native`: DLMF contains relevant surrounding material but does not define the catalogue family itself.

A chapter or section mapping alone is not treated as formula verification.

## Audit scope

High-use families receive formula- or section-level review for hypotheses, endpoint attainment, poles, branch conventions, and zero distributions. The review includes Airy, Bessel, Gamma/Beta, incomplete Gamma/Beta, error/exponential integrals, zeta, hypergeometric, Legendre/Ferrers, elliptic, and classical orthogonal-polynomial families.

The mpmath inventory is tracked for coverage but is not assumed to have exactly the same semantic contract as the corresponding SymPy family.

## Executable facts

Audited facts feed property reasoning only when their hypotheses can be retained exactly. Examples include:

- generalized hypergeometric termination, analyticity, and principal cuts;
- Ferrers/associated-Legendre interior zero counts under integer parameter conditions;
- incomplete elliptic-integral branch radicands;
- classical orthogonal-polynomial zero counts, simplicity, support, and consecutive-degree interlacing;
- exact indexed Chebyshev zero sets;
- spherical-Bessel positive-zero families; and
- parameter-dependent endpoint behavior for selected Bessel and incomplete Gamma/Beta functions.

The exact zeta pole at `s = 1` is retained explicitly.

## Zero-distribution records

`ParametricZeroFamily` stores symbolic zero geometry without replacing unknown roots by numerical approximations. A record can include a symbolic root count, support interval, parameter guard, simplicity, interlacing information, and a completeness flag.

`complete=True` is reserved for the domain on which the cited theorem actually exhausts the zeros. An interior zero theorem, for example, is not promoted to an all-real completeness statement.
