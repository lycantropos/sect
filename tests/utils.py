from operator import getitem
from typing import (Iterable,
                    List,
                    Sequence,
                    Set,
                    Tuple,
                    TypeVar)

from hypothesis import strategies
from hypothesis.strategies import SearchStrategy
from orient.planar import (Relation,
                           point_in_segment)
from robust.angular import (Orientation,
                            orientation)

from sect.core.hints import Endpoints
from sect.core.utils import (contour_to_segments,
                             normalize_contour)
from sect.hints import (Contour,
                        Multisegment,
                        Point,
                        Segment)

Strategy = SearchStrategy
Polygon = Tuple[Contour, Sequence[Contour]]


def point_in_multisegment(point: Point,
                          multisegment: Multisegment) -> Relation:
    return (Relation.COMPONENT
            if any(point_in_segment(point, segment) is Relation.COMPONENT
                   for segment in multisegment)
            else Relation.DISJOINT)


def points_do_not_lie_on_the_same_line(points: Sequence[Point]) -> bool:
    return any(orientation(points[index - 1], points[index],
                           points[(index + 1) % len(points)])
               is not Orientation.COLLINEAR
               for index in range(len(points)))


def to_boundary_endpoints(contours: Iterable[Contour]) -> Set[Endpoints]:
    result = set()
    for contour in contours:
        result.symmetric_difference_update(map(frozenset,
                                               contour_to_segments(contour)))
    return result


def to_convex_border(points: Sequence[Point]) -> List[Point]:
    points = sorted(points)
    lower = _to_sub_border(points)
    upper = _to_sub_border(reversed(points))
    return lower[:-1] + upper[:-1]


def _to_sub_border(points: Iterable[Point]) -> List[Point]:
    result = []
    for point in points:
        while len(result) >= 2:
            if orientation(result[-1], result[-2],
                           point) is Orientation.CLOCKWISE:
                del result[-1]
            else:
                break
        result.append(point)
    return result


def replace_segment(segments: Set[Segment],
                    source: Segment,
                    target: Segment) -> None:
    segments.remove(source)
    segments.add(target)


def is_convex_contour(contour: Contour) -> bool:
    contour = normalize_contour(contour)
    return all(orientation(contour[index - 2], contour[index - 1],
                           contour[index]) is Orientation.CLOCKWISE
               for index in range(len(contour)))


Element = TypeVar('Element')


def sub_lists(sequence: Sequence[Element]) -> SearchStrategy[List[Element]]:
    return strategies.builds(getitem,
                             strategies.permutations(sequence),
                             strategies.slices(max(len(sequence), 1)))
