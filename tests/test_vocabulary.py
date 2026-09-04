from funcprops.results import Analyticity, Convexity, Meromorphicity, Monotonicity, Sign


def test_canonical_vocabulary_is_compact():
    assert Monotonicity.STRICTLY_INCREASING.value == "strictly_increasing"
    assert Convexity.STRICTLY_CONVEX.value == "strictly_convex"
    assert Sign.POSITIVE.value == "positive"
    assert Analyticity.ANALYTIC.value == "analytic"
    assert Meromorphicity.MEROMORPHIC.value == "meromorphic"
