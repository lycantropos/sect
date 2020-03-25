import sys
from collections import OrderedDict
from itertools import chain
from typing import (Iterable,
                    List,
                    Sequence,
                    TypeVar)

from robust.angular import (Orientation,
                            orientation)

from sect.hints import (Point,
                        Triangle)

Domain = TypeVar('Domain')


def to_convex_hull(points: Sequence[Point]) -> List[Point]:
    points = sorted(points)
    lower = _to_sub_hull(points)
    upper = _to_sub_hull(reversed(points))
    return lower[:-1] + upper[:-1]


def _to_sub_hull(points: Iterable[Point]) -> List[Point]:
    result = []
    for point in points:
        while len(result) >= 2:
            if orientation(result[-1], result[-2],
                           point) is not Orientation.COUNTERCLOCKWISE:
                del result[-1]
            else:
                break
        result.append(point)
    return result


def split_sequence(sequence: Sequence[Domain],
                   *,
                   size: int = 2) -> List[Sequence[Domain]]:
    step, offset = divmod(len(sequence), size)
    return [sequence[number * step + min(number, offset):
                     (number + 1) * step + min(number + 1, offset)]
            for number in range(size)]


flatten = chain.from_iterable


def normalize_triangle(triangle: Triangle) -> Triangle:
    min_index = min(range(len(triangle)),
                    key=triangle.__getitem__)
    triangle = triangle[min_index:] + triangle[:min_index]
    if orientation(triangle[-1], triangle[0],
                   triangle[1]) is Orientation.COUNTERCLOCKWISE:
        triangle = triangle[:1] + triangle[1:][::-1]
    return triangle


to_unique_objects = (OrderedDict
                     if sys.version_info < (3, 6)
                     else dict).fromkeys
