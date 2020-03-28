import sys
from collections import OrderedDict
from itertools import (chain,
                       cycle)
from typing import (Iterable,
                    List,
                    Sequence,
                    Tuple,
                    TypeVar)

from dendroid import red_black
from robust.angular import (Orientation,
                            orientation)

from sect.hints import (Contour,
                        Point,
                        Segment,
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


flatten = chain.from_iterable


def normalize_triangle(triangle: Triangle) -> Triangle:
    min_index = min(range(len(triangle)),
                    key=triangle.__getitem__)
    triangle = triangle[min_index:] + triangle[:min_index]
    if orientation(triangle[-1], triangle[0],
                   triangle[1]) is Orientation.COUNTERCLOCKWISE:
        triangle = triangle[:1] + triangle[1:][::-1]
    return triangle


def contour_to_segments(contour: Contour) -> List[Segment]:
    return [(contour[index - 1], contour[index])
            for index in range(len(contour))]


to_unique_objects = (OrderedDict
                     if sys.version_info < (3, 6)
                     else dict).fromkeys


def coin_change(amount: int, denominations: Iterable[int]) -> List[int]:
    denominations = red_black.tree(*denominations)
    result = []
    poppers = cycle((red_black.Tree.popmax, red_black.Tree.popmax))
    while amount and denominations:
        denomination = next(poppers)(denominations)
        denomination_count, amount = divmod(amount, denomination)
        if amount and amount < denominations.min():
            denomination_count -= 1
            amount += denomination
        result += [denomination] * denomination_count
    return result


def pairwise(iterable: Iterable[Domain]) -> Iterable[Tuple[Domain, Domain]]:
    iterator = iter(iterable)
    try:
        element = next(iterator)
    except StopIteration:
        return
    for next_element in iterator:
        yield element, next_element
        element = next_element
