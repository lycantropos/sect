from collections import defaultdict
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
    shrink_collinear_segments(result)
    return result


def shrink_collinear_segments(segments_endpoints: Set[Endpoints]) -> None:
    points_segments = defaultdict(set)
    for segment in map(tuple, segments_endpoints):
        start, end = segment
        points_segments[start].add(segment)
        points_segments[end].add(segment[::-1])
    for point, point_segments in points_segments.items():
        first_segment, second_segment = point_segments
        first_segment_start, first_segment_end = first_segment
        second_segment_start, second_segment_end = second_segment
        if (orientation(first_segment_end, first_segment_start,
                        second_segment_start)
                is orientation(first_segment_end, first_segment_start,
                               second_segment_end)
                is Orientation.COLLINEAR):
            segments_endpoints.remove(frozenset(first_segment))
            segments_endpoints.remove(frozenset(second_segment))
            replacement = (first_segment_end, second_segment_end)
            replace_segment(points_segments[first_segment_end],
                            first_segment[::-1], replacement)
            replace_segment(points_segments[second_segment_end],
                            second_segment[::-1], replacement[::-1])
            segments_endpoints.add(frozenset(replacement))


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
