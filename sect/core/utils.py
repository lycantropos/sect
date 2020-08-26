import sys
from bisect import bisect
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
    return (contour[:1] + contour[1:][::-1]
            if (orientation(contour[-1], contour[0], contour[1])
                is Orientation.COUNTERCLOCKWISE)
            else contour)


def to_clockwise_contour(contour: Contour) -> Contour:
    return (contour
            if to_contour_orientation(contour) is Orientation.CLOCKWISE
            else contour[:1] + contour[1:][::-1])


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
    element = next(iterator, None)
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


def ceil_log2(number: int) -> int:
    return number.bit_length() - (not (number & (number - 1)))


def complete_vertices(border: Contour, holes: Sequence[Contour],
                      candidates: Sequence[Point]
                      ) -> Tuple[Contour, Sequence[Contour], Sequence[Point]]:
    candidates = sorted(to_unique_objects(candidates))
    border, candidates = _complete_contour_vertices(border, candidates)
    completed_holes = []
    for hole in holes:
        hole, candidates = _complete_contour_vertices(hole, candidates)
        completed_holes.append(hole)
    return border, completed_holes, candidates


def _complete_contour_vertices(contour: Contour,
                               candidates: Sequence[Point]
                               ) -> Tuple[Contour, Sequence[Point]]:
    extra_vertices = {}
    start = contour[-1]
    for index, end in enumerate(contour):
        start_index = bisect(candidates, start)
        end_index = bisect(candidates, end)
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        extra_vertices_indices = []
        for candidate_index in range(start_index, end_index):
            extra_point = candidates[candidate_index]
            if _is_inner_segment_point(start, end, extra_point):
                extra_vertices_indices.append(candidate_index)
        if extra_vertices_indices:
            extra_vertices[index] = [candidates[index]
                                     for index in extra_vertices_indices]
            extra_vertices_indices = frozenset(extra_vertices_indices)
            candidates = [point
                          for index, point in enumerate(candidates)
                          if index not in extra_vertices_indices]
            if not candidates:
                break
        start = end
    if extra_vertices:
        contour = list(flatten((extra_vertices[index]
                                if contour[index - 1] < vertex
                                else extra_vertices[index][::-1]) + [vertex]
                               if index in extra_vertices
                               else [vertex]
                               for index, vertex in enumerate(contour)))
    return contour, candidates


def _is_inner_segment_point(start: Point, end: Point, point: Point) -> bool:
    return ((start < point < end if start < end else end < point < start)
            and orientation(start, end, point) is Orientation.COLLINEAR)
