import sys
from collections import OrderedDict
from itertools import chain
from typing import (Iterable,
                    List,
                    Sequence,
                    Tuple,
                    TypeVar)

from robust.angular import (Orientation,
                            orientation)

from sect.hints import (Contour,
                        Point,
                        Segment)
from .hints import BoundingBox

Domain = TypeVar('Domain')

flatten = chain.from_iterable


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


def normalize_contour(contour: Contour) -> Contour:
    min_index = arg_min(contour)
    contour = contour[min_index:] + contour[:min_index]
    if orientation(contour[-1], contour[0],
                   contour[1]) is Orientation.COUNTERCLOCKWISE:
        contour = contour[:1] + contour[1:][::-1]
    return contour


def contour_to_segments(contour: Contour) -> List[Segment]:
    return [(contour[index - 1], contour[index])
            for index in range(len(contour))]


def to_contour_orientation(contour: Contour) -> Orientation:
    index = arg_min(contour)
    return orientation(contour[index], contour[index - 1],
                       contour[(index + 1) % len(contour)])


def arg_min(sequence: Sequence[Domain]) -> int:
    return min(range(len(sequence)),
               key=sequence.__getitem__)


to_unique_objects = (OrderedDict
                     if sys.version_info < (3, 6)
                     else dict).fromkeys


def pairwise(iterable: Iterable[Domain]) -> Iterable[Tuple[Domain, Domain]]:
    iterator = iter(iterable)
    try:
        element = next(iterator)
    except StopIteration:
        return
    for next_element in iterator:
        yield element, next_element
        element = next_element


def points_to_bounding_box(points: Iterable[Point]) -> BoundingBox:
    points = iter(points)
    first_point = next(points)
    min_x, min_y = max_x, max_y = first_point
    for x, y in points:
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
    return min_x, min_y, max_x, max_y


def to_min_max(iterable: Iterable[Domain]) -> Tuple[Domain, Domain]:
    iterator = iter(iterable)
    minimum = maximum = next(iterator)
    for element in iterator:
        if element < minimum:
            minimum = element
        elif maximum < element:
            maximum = element
    return minimum, maximum


def ceil_log2(number: int) -> int:
    return number.bit_length() - (not (number & (number - 1)))
