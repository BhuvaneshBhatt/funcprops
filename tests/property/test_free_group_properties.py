from hypothesis import given
from hypothesis import strategies as st

from funcprops.certified_operations import _free_reduce

letters = st.integers(min_value=-4, max_value=4).filter(lambda value: value != 0)
words = st.lists(letters, max_size=30).map(tuple)


def oracle_reduce(word):
    """Independent adjacent-cancellation normal form used only by tests."""
    current = tuple(word)
    while True:
        for index in range(len(current) - 1):
            if current[index] == -current[index + 1]:
                current = current[:index] + current[index + 2 :]
                break
        else:
            return current


@given(words)
def test_normal_form_matches_oracle(word):
    assert _free_reduce(word) == oracle_reduce(word)


@given(words)
def test_normal_form_idempotent(word):
    reduced = _free_reduce(word)
    assert _free_reduce(reduced) == reduced


@given(words)
def test_word_times_inverse_is_identity(word):
    inverse = tuple(-letter for letter in reversed(word))
    assert _free_reduce(word + inverse) == ()
