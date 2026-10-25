"""Formula-level DLMF audit metadata for core catalogue families.

References are tied to DLMF equations or narrowly scoped sections.
``derived=True`` means DLMF verifies the underlying standard
identity/property and funcprops derives the SymPy helper/wrapper statement.
"""

FORMULA_AUDIT = {
    "appellf1": (["16.13.E1"], "definition and convergence domain", False),
    "assoc_laguerre": (
        ["18.5.E12", "18.16.E9"],
        "explicit representation; n simple positive zeros for alpha>-1",
        False,
    ),
    "chebyshevt": (
        ["18.5.E1", "18.16.iii"],
        "trigonometric representation and zeros in (-1,1)",
        False,
    ),
    "chebyshevt_root": (
        ["18.5.E1"],
        "root formula derived from T_n(cos theta)=cos(n theta)",
        True,
    ),
    "chebyshevu": (
        ["18.5.E2", "18.16.iii"],
        "trigonometric representation and zeros in (-1,1)",
        False,
    ),
    "chebyshevu_root": (["18.5.E2"], "root formula derived from U_n(cos theta)", True),
    "dirichlet_eta": (
        ["25.2.E3"],
        "alternating zeta representation / analytic continuaition relation",
        True,
    ),
    "erf2": (["7.2.E1"], "difference of entire erf values", True),
    "erf2inv": (
        ["7.17.E1"],
        "inverse error-function branch/domain inherited from inverse erf",
        True,
    ),
    "erfcinv": (["7.17.E1"], "inverse complementary error function", False),
    "erfi": (
        ["7.2.E1"],
        "erfi(z)=-i erf(i z), entire; real monotonicity derived",
        True,
    ),
    "erfinv": (["7.17.E1"], "inverse error function", False),
    "expint": (
        ["8.19.E1", "8.19.E18"],
        "generalized exponential integral and branch point at zero",
        False,
    ),
    "gegenbauer": (
        ["18.5.E9", "18.16.iii"],
        "ultraspherical polynomial representation and zeros",
        False,
    ),
    "hermite": (
        ["18.5.E13", "18.16.v"],
        "Hermite polynomial representation and real simple zeros",
        False,
    ),
    "hermite_prob": (
        ["18.7.E11", "18.16.v"],
        "probabilists Hermite scaling from Hermite family; zero distribution inherited",
        True,
    ),
    "hn1": (["10.47.E5"], "spherical Hankel h_n^(1) definition", False),
    "hn2": (["10.47.E6"], "spherical Hankel h_n^(2) definition", False),
    "HyperRep_asin1": (
        ["15.4.E4"],
        "elementary inverse-sine hypergeometric special case",
        True,
    ),
    "HyperRep_asin2": (
        ["15.4.E4", "15.5.E1"],
        "elementary inverse-sine hypergeometric special case",
        True,
    ),
    "HyperRep_atanh": (["15.4.E2"], "atanh hypergeometric special case", True),
    "HyperRep_cosasin": (
        ["15.4.E12"],
        "trigonometric/hypergeometric special case",
        True,
    ),
    "HyperRep_log1": (["15.4.E1"], "logarithmic hypergeometric special case", True),
    "HyperRep_log2": (
        ["16.2.E1", "15.4.E17"],
        "logarithmic hypergeometric special case",
        True,
    ),
    "HyperRep_power1": (["16.2.E1"], "binomial hypergeometric special case", True),
    "HyperRep_power2": (["15.4.E17"], "binomial hypergeometric special case", True),
    "HyperRep_sinasin": (
        ["15.4.E12", "15.5.E1"],
        "trigonometric/hypergeometric special case",
        True,
    ),
    "HyperRep_sqrts1": (["15.4.E7"], "square-root hypergeometric special case", True),
    "HyperRep_sqrts2": (
        ["15.4.E7", "15.5.E1"],
        "square-root hypergeometric special case",
        True,
    ),
    "jacobi": (
        ["18.5.E7", "18.16.E1"],
        "Jacobi representation; n simple zeros in (-1,1) for alpha,beta>-1",
        False,
    ),
    "jn": (["10.47.E3", "10.58"], "spherical Bessel j_n and zero distribution", False),
    "laguerre": (
        ["18.5.E12", "18.16.E9"],
        "Laguerre representation; n simple positive zeros for alpha=0",
        False,
    ),
    "lerchphi": (
        ["25.14.E1", "25.14"],
        "Lerch transcendent definition and continuation",
        False,
    ),
    "Li": (["6.2.E8"], "offset logarithmic integral relation", True),
    "li": (
        ["6.2.E8"],
        "logarithmic integral principal value and branch structure",
        False,
    ),
    "loggamma": (
        ["5.2.E1", "5.11.E1"],
        "principal log-Gamma and asymptotic/branch conventions",
        False,
    ),
    "mathieuc": (
        ["28.2.E29", "28.2.E38"],
        "even Mathieu solution and characteristic values/periodicity",
        False,
    ),
    "mathieucprime": (["28.2.E38"], "derivative of even Mathieu solution", True),
    "mathieus": (
        ["28.2.E29", "28.2.E39"],
        "odd Mathieu solution and characteristic values/periodicity",
        False,
    ),
    "mathieusprime": (["28.2.E39"], "derivative of odd Mathieu solution", True),
    "meijerg": (
        ["16.17.E1"],
        "Mellin-Barnes definition and convergence sectors",
        False,
    ),
    "multigamma": (
        ["35.3.E1", "35.3.E4"],
        "multivariate gamma definition/domain",
        False,
    ),
    "polylog": (
        ["25.12.E10", "25.12"],
        "polylogarithm definition/analytic continuation and principal branch",
        False,
    ),
    "riemann_xi": (
        ["25.4.E4", "25.4.E3"],
        "xi definition and functional equation; entire by cancellation",
        False,
    ),
    "stieltjes": (
        ["25.2.E4", "25.2.E5"],
        "Stieltjes constants from Laurent expansion of zeta",
        False,
    ),
    "yn": (["10.47.E4", "10.58"], "spherical Bessel y_n and zero distribution", False),
    "Ynm": (
        ["14.30.E1"],
        "complex spherical harmonic definition and normalization",
        False,
    ),
    "Znm": (
        ["14.30.E1"],
        "real spherical harmonic derived from complex spherical harmonics",
        True,
    ),
}
