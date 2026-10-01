import pytest

from funcprops.certified_operations import _free_reduce


@pytest.mark.parametrize(
    ("word", "normal_form"),
    [
        ((), ()),
        ((1,), (1,)),
        ((1, -1), ()),
        ((1, 2, -2, -1), ()),
        ((1, 2, -1, -2), (1, 2, -1, -2)),
        ((1, 2), (1, 2)),
        ((2, 1), (2, 1)),
        ((1, 1, -1), (1,)),
        ((1, 2, 3, -3, -2, -1), ()),
        ((1, 2, -1, 3, -2), (1, 2, -1, 3, -2)),
    ],
)
def test_reference_words(word, normal_form):
    assert _free_reduce(word) == normal_form


def test_winding_vector_does_not_classify_words():
    commutator = _free_reduce((1, 2, -1, -2))
    assert commutator == (1, 2, -1, -2)
    assert tuple(
        sum(1 if x == j else -1 if x == -j else 0 for x in commutator) for j in (1, 2)
    ) == (0, 0)
