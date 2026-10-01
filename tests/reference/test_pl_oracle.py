from tests.support.pl_homotopy_oracle import crossing_word, reduce_word


def test_polygonal_oracle_distinguishes_order():
    punctures = ((-1.0, 0.0), (1.0, 0.0))
    # Two rectangles whose right edges cross both cuts in opposite traversal
    # order after reversing orientation.
    loop = ((-3.0, -2.0), (3.0, -2.0), (3.0, 2.0), (-3.0, 2.0), (-3.0, -2.0))
    word = crossing_word(loop, punctures)
    reversed_word = crossing_word(tuple(reversed(loop)), punctures)
    assert word == (1, 2)
    assert reversed_word == (-2, -1)
    assert reduce_word(word) != reduce_word(reversed_word)
