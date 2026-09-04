"""Quick installation/runtime smoke test for funcprops."""

import sympy as sp

import funcprops as fp


x = sp.symbols("x", real=True)
y = sp.symbols("y", real=True)

def check(name, computation):
    """Run one smoke check and print its result."""
    try:
        result = computation()
    except Exception as exc:
        print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
        raise

    print(f"PASS  {name}: {result}")
    return result


print(f"funcprops: {fp.__file__}")
print(f"SymPy:     {sp.__version__}")
print()


# Core real-function properties
check(
    "domain",
    lambda: fp.function_domain(1 / (x - 1), x),
)

check(
    "range",
    lambda: fp.function_range(x**2, x, y),
)

check(
    "sign",
    lambda: fp.function_sign(x**2 + 1, x),
)

check(
    "zeros",
    lambda: fp.function_zeros(sp.sin(x), x),
)

check(
    "monotonicity",
    lambda: fp.function_monotonicity(sp.exp(x), x),
)

check(
    "convexity",
    lambda: fp.function_convexity(x**2, x),
)

check(
    "differentiability",
    lambda: fp.function_differentiability(sp.Abs(x), x),
)

check(
    "smoothness",
    lambda: fp.function_smoothness(sp.exp(x), x),
)


# Mapping properties
check(
    "injectivity",
    lambda: fp.function_injective(x**3, x),
)

check(
    "surjectivity",
    lambda: fp.function_surjective(x**3, x),
)

check(
    "bijectivity",
    lambda: fp.function_bijective(x**3, x),
)


# Complex analysis
z = sp.symbols("z")

check(
    "branch cuts",
    lambda: fp.function_branchcuts(sp.log(z), z),
)

check(
    "singularities",
    lambda: fp.function_singularities(1 / (z - 1), z),
)

check(
    "analytic",
    lambda: fp.function_analytic(sp.exp(z), z),
)


# New certified root machinery
check(
    "robust exp/log sign",
    lambda: fp.robust_real_sign(sp.exp(1000) - 1),
)

check(
    "exponential root count",
    lambda: fp.exponential_fourier_count(
        sp.exp(2 * x) - 3 * sp.exp(x) + 2,
        x,
        sp.Interval(-10, 10),
    ),
)

check(
    "certified monotonic inverse",
    lambda: fp.certified_monotonic_inverse(
        x + sp.exp(x),
        x,
        3,
        domain=sp.Interval(-1, 2),
    ),
)


# Complex rectangle isolation
check(
    "complex zeros",
    lambda: fp.function_complex_zeros(
        sp.exp(z) - 1,
        z,
        rectangle=(-1 - sp.I, 1 + sp.I),
    ),
)


print()
print("funcprops smoke test PASSED")
