import sys
from bisect import bisect
from collections import OrderedDict
from typing import (Iterable,
                    List,
                    Sequence,
                    Tuple)

from ground.base import (Context,
                         get_context)
from ground.hints import Point

from sect.core.hints import (Contour,
                             Segment)
from sect.core.utils import (Orientation,
                             arg_min,
                             flatten,
                             orientation,
                             to_contour_orientation)


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


def contour_to_segments(contour: Contour) -> List[Segment]:
    return [(contour[index - 1], contour[index])
            for index in range(len(contour))]


def normalize_contour(contour: Contour) -> Contour:
    min_index = arg_min(contour)
    contour = contour[min_index:] + contour[:min_index]
    return (contour[:1] + contour[1:][::-1]
            if (orientation(contour[-1], contour[0], contour[1])
                is Orientation.CLOCKWISE)
            else contour)


to_unique_objects = (OrderedDict
                     if sys.version_info < (3, 6)
                     else dict).fromkeys


def to_clockwise_contour(contour: Contour) -> Contour:
    return (contour
            if to_contour_orientation(contour) is Orientation.CLOCKWISE
            else contour[:1] + contour[1:][::-1])


def to_convex_hull(points: Sequence[Point]) -> List[Point]:
    points = sorted(points)
    lower = _to_sub_hull(points)
    upper = _to_sub_hull(reversed(points))
    return lower[:-1] + upper[:-1]


def _complete_contour_vertices(contour: Contour,
                               candidates: Sequence[Point]
                               ) -> Tuple[Contour, Sequence[Point]]:
    context = get_context()
    extra_vertices = {}
    vertices = contour.vertices
    start = vertices[-1]
    for index, end in enumerate(vertices):
        start_index = bisect(candidates, start)
        end_index = bisect(candidates, end)
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        extra_vertices_indices = []
        for candidate_index in range(start_index, end_index):
            extra_point = candidates[candidate_index]
            if _is_inner_segment_point(start, end, extra_point, context):
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
        contour_cls = context.contour_cls
        contour = contour_cls(
                list(flatten((extra_vertices[index]
                              if vertices[index - 1] < vertex
                              else extra_vertices[index][::-1]) + [vertex]
                             if index in extra_vertices
                             else [vertex]
                             for index, vertex in enumerate(vertices))))
    return contour, candidates


def _is_inner_segment_point(start: Point, end: Point, point: Point,
                            context: Context) -> bool:
    return (point != start and point != end
            and context.segment_contains_point(start, end, point))


def _to_sub_hull(points: Iterable[Point]) -> List[Point]:
    result = []
    for point in points:
        while len(result) >= 2:
            if orientation(result[-2], result[-1],
                           point) is not Orientation.COUNTERCLOCKWISE:
                del result[-1]
            else:
                break
        result.append(point)
    return result
