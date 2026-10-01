# Statistical special functions

`funcprops` includes theorem-backed geometry for special functions that occur in probability, statistics, reliability, stochastic processes, and statistical signal processing.

## Supported families

The core SymPy families include `loggamma`, `digamma`/`polygamma`, incomplete and regularized beta functions, `erf`/`erfc`, modified Bessel functions, and SymPy's generalized `marcumq`. The package also supplies lightweight symbolic heads for functions not present in the supported SymPy release:

- `OwenT(h, a)` for Owen's T function;
- `MittagLefflerE(alpha, z)` and `MittagLefflerE(alpha, beta, z)`;
- `RegularizedGammaP(a, x)` and `RegularizedGammaQ(a, x)`.

These symbolic heads provide exact symbolic derivatives and selected elementary special values/rewrite identities. They are not numerical-library replacements; their main purpose is to let the common funcprops theorem engines reason about them symbolically.

## Theorem coverage

On their certified probability domains, the theorem registry includes:

- strict convexity of `loggamma(x)` on `x > 0`;
- strict increase and strict concavity of `digamma(x)` on `x > 0`;
- parity-conditioned sign and monotonicity of higher `polygamma(n, x)`;
- monotonicity and probability range of regularized incomplete gamma P/Q;
- monotonicity and probability range of regularized incomplete beta on `0 < x < 1`;
- strict increase of Owen T in its second argument and positivity for positive second argument;
- generalized Marcum Q increase in noncentrality, decrease in threshold, and `(0, 1)` threshold range under positive probability parameters;
- complete monotonicity, positivity, monotone decrease, and convexity consequences for `MittagLefflerE(alpha, -x)` when `0 < alpha <= 1`;
- complete monotonicity of `besselk(nu, x)` on `x > 0` for real `nu`, alongside the existing Bessel-I/K positivity and monotonicity facts.

Every parameter-sensitive statement is a sufficient theorem with an explicit guard. Outside those guards the package returns a conditional result or `UNKNOWN`.

## Executable examples

### Regularized gamma CDF geometry

<!-- example-id: regularized-gamma-cdf -->

Application: Reason symbolically about Gamma-family CDFs without numerical sampling.

```python
a = sp.symbols('a', positive=True); result = fp.monotonicity(fp.RegularizedGammaP(a, x), x, domain=x > 0)
```

Expected: strict increase on ``x > 0`` for ``a > 0``.

### Owen T derivative

<!-- example-id: owen-t-derivative -->

Application: Certify monotonicity used in skew-normal and Gaussian probability calculations.

```python
h, a = sp.symbols('h a', real=True); result = sp.diff(fp.OwenT(h, a), a)
```

Expected: the exact positive derivative with respect to the second argument.

### Generalized Marcum Q threshold monotonicity

<!-- example-id: marcum-q-threshold -->

Application: Analyze noncentral-tail probabilities and detection thresholds structurally.

```python
m, a, b = sp.symbols('m a b', positive=True); result = fp.monotonicity(sp.marcumq(m, a, b), b, domain=b > 0)
```

Expected: strict decrease in the positive threshold.

### Mittag-Leffler complete monotonicity

<!-- example-id: mittag-leffler-complete-monotonicity -->

Application: Certify Laplace-transform geometry in fractional stochastic and reliability models.

```python
alpha = sp.symbols('alpha', positive=True); t = sp.symbols('t', nonnegative=True); result = fp.complete_monotonicity(fp.MittagLefflerE(alpha, -t), t, domain=t >= 0, assumptions=alpha <= 1)
```

Expected: complete monotonicity for ``0 < alpha <= 1``.

### Modified-Bessel ratio monotonicity

<!-- example-id: bessel-ratio-geometry -->

Application: Support directional-statistics and noncentral-distribution parameter geometry.

```python
nu = sp.symbols('nu', nonnegative=True); t = sp.symbols('t', positive=True); ratio = sp.besseli(nu + 1, t) / sp.besseli(nu, t); result = fp.monotonicity(ratio, t, domain=t > 0)
```

Expected: strict increase for nonnegative ``nu`` on ``t > 0``.
## Provenance

The Gamma/Beta/Bessel facts follow the corresponding NIST DLMF identities and real-variable properties. Mittag-Leffler complete monotonicity uses Pollard's 1948 theorem. Marcum-Q monotonicity follows the established generalized Marcum-Q literature and is consistent with SymPy's exact argument derivatives. Owen-T monotonicity follows immediately from its defining integral derivative with respect to the second argument.
