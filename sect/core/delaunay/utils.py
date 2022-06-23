import sys
from bisect import bisect
from collections import OrderedDict
from typing import (FrozenSet,
                    Iterable,
                    Sequence,
                    Tuple,
                    Type)

from ground.base import (Context,
                         Orientation)
from ground.hints import (Contour,
                          Point,
                          Segment)

from sect.core.hints import Orienteer
from sect.core.utils import (arg_min,
                             flatten,
                             rotate_sequence,
                             to_contour_orientation)
from .hints import (SegmentContainmentChecker,
                    SegmentEndpoints)


def ceil_log2(number: int) -> int:
    return number.bit_length() - (not (number & (number - 1)))


def complete_vertices(border: Contour,
                      holes: Sequence[Contour],
                      candidates: Sequence[Point],
                      context: Context
                      ) -> Tuple[Contour, Sequence[Contour], Sequence[Point]]:
    candidates = sorted(to_distinct(candidates))
    contour_cls, segment_cls, segment_point_relater = (
        context.contour_cls, context.segment_cls,
        context.segment_contains_point
    )
    border, candidates = _complete_contour_vertices(
            border, candidates, contour_cls, segment_cls,
            segment_point_relater
    )
    completed_holes = []
    for hole in holes:
        hole, candidates = _complete_contour_vertices(
                hole, candidates, contour_cls, segment_cls,
                segment_point_relater
        )
        completed_holes.append(hole)
    return border, completed_holes, candidates


def contour_to_oriented_edges_endpoints(contour: Contour,
                                        *,
                                        clockwise: bool,
                                        orienteer: Orienteer
                                        ) -> Iterable[SegmentEndpoints]:
    vertices = contour.vertices
    return (((vertices[index - 1], vertices[index])
             for index in range(len(vertices)))
            if (to_contour_orientation(contour, orienteer)
                is (Orientation.CLOCKWISE
                    if clockwise
                    else Orientation.COUNTERCLOCKWISE))
            else ((vertices[index], vertices[index - 1])
                  for index in range(len(vertices) - 1, -1, -1)))


def normalize_contour_vertices(vertices: Sequence[Point],
                               orienteer: Orienteer) -> Sequence[Point]:
    vertices = rotate_sequence(vertices, arg_min(vertices))
    return (vertices[:1] + vertices[1:][::-1]
            if (orienteer(vertices[-1], vertices[0], vertices[1])
                is Orientation.CLOCKWISE)
            else vertices)


to_distinct = (OrderedDict if sys.version_info < (3, 6) else dict).fromkeys


def _complete_contour_vertices(contour: Contour,
                               candidates: Sequence[Point],
                               contour_cls: Type[Contour],
                               segment_cls: Type[Segment],
                               containment_checker: SegmentContainmentChecker
                               ) -> Tuple[Contour, Sequence[Point]]:
    extra_vertices = {}
    vertices = contour.vertices
    start = vertices[-1]
    for index, end in enumerate(vertices):
        start_index, end_index = (bisect(candidates, start),
                                  bisect(candidates, end))
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        extra_vertices_indices = [
            candidate_index
            for candidate_index in range(start_index, end_index)
            if _is_inner_segment_point(start, end, candidates[candidate_index],
                                       segment_cls, containment_checker)
        ]
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
        contour = contour_cls(
                list(flatten((extra_vertices[index]
                              if vertices[index - 1] < vertex
                              else extra_vertices[index][::-1]) + [vertex]
                             if index in extra_vertices
                             else [vertex]
                             for index, vertex in enumerate(vertices)))
        )
    return contour, candidates


def _is_inner_segment_point(start: Point,
                            end: Point,
                            point: Point,
                            segment_cls: Type[Segment],
                            containment_checker: SegmentContainmentChecker
                            ) -> bool:
    return (point != start and point != end
            and containment_checker(segment_cls(start, end), point))


def to_endpoints(edge: Segment) -> FrozenSet[Point]:
    return frozenset((edge.start, edge.end))
