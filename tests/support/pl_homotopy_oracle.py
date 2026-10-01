"""Small independent oracle for polygonal loops in cut coordinates.

This module is test infrastructure, not an implementation dependency.  Cuts are
horizontal rays ``p + s`` with ``s >= 0``.  Inputs must be nondegenerate: no
vertex lies on a cut and no segment passes through a puncture.
"""

import itertools


def crossing_word(vertices, punctures):
    events = []
    for segment_index, (start, end) in enumerate(itertools.pairwise(vertices)):
        x0, y0 = start
        x1, y1 = end
        for generator, puncture in enumerate(punctures, start=1):
            px, py = puncture
            # Half-open convention counts a crossing at exactly one adjacent
            # segment and prevents polygon vertices from being double-counted.
            upward = y0 < py <= y1
            downward = y1 < py <= y0
            if not (upward or downward):
                continue
            fraction = (py - y0) / (y1 - y0)
            x = x0 + fraction * (x1 - x0)
            if x <= px:
                continue
            events.append(
                (segment_index + fraction, generator if upward else -generator)
            )
    return tuple(letter for _, letter in sorted(events))


def reduce_word(word):
    current = tuple(word)
    while True:
        for index in range(len(current) - 1):
            if current[index] == -current[index + 1]:
                current = current[:index] + current[index + 2 :]
                break
        else:
            return current
