from __future__ import annotations

import typing as _t
from collections import deque
from functools import partial
from itertools import (accumulate,
                       chain,
                       repeat)

from decision.partition import coin_change
from ground.base import (Context,
                         Location,
                         Orientation,
                         Relation)
from ground.hints import (Contour,
                          Point,
                          Polygon,
                          Segment)
from reprit.base import generate_repr

from sect.core.utils import (flatten,
                             pairwise)
from .events_queue import EventsQueue
from .hints import (PointInCircleLocator,
                    SegmentsRelater)
from .quad_edge import (QuadEdge,
                        edge_to_neighbours,
                        edges_with_opposites)
from .utils import (ceil_log2,
                    complete_vertices,
                    contour_to_oriented_edges_endpoints,
                    normalize_contour_vertices,
                    to_distinct,
                    to_endpoints)


class Triangulation:
    """Represents triangulation."""

    @classmethod
    def constrained_delaunay(cls,
                             polygon: Polygon,
                             *,
                             extra_constraints: _t.Sequence[Segment] = (),
                             extra_points: _t.Sequence[Point] = (),
                             context: Context) -> Triangulation:
        """
        Constructs constrained Delaunay triangulation of given polygon
        (with potentially extra points and constraints).

        Based on

        * divide-and-conquer algorithm by L. Guibas & J. Stolfi
          for generating Delaunay triangulation,

        * algorithm by S. W. Sloan for adding constraints to Delaunay
          triangulation,

        * clipping algorithm by F. Martinez et al. for deleting in-hole
          triangles.

        Time complexity:
            ``O(vertices_count * log vertices_count)`` for convex polygons
            without extra constraints,
            ``O(vertices_count ** 2)`` otherwise
        Memory complexity:
            ``O(vertices_count)``

        where

        .. code-block:: python

            vertices_count = (len(polygon.border.vertices)
                              + sum(len(hole.vertices)
                                    for hole in polygon.holes)
                              + len(extra_points) + len(extra_constraints))

        Reference:
            http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf
            https://www.newcastle.edu.au/__data/assets/pdf_file/0019/22519/23_A-fast-algortithm-for-generating-constrained-Delaunay-triangulations.pdf
            https://doi.org/10.1016/j.advengsoft.2013.04.004
            http://www4.ujaen.es/~fmartin/bool_op.html

        :param polygon: target polygon.
        :param extra_points:
            additional points to be presented in the triangulation.
        :param extra_constraints:
            additional constraints to be presented in the triangulation.
        :param context: geometric context.
        :returns:
            triangulation of the border, holes & extra points
            considering constraints.
        """
        border, holes = polygon.border, polygon.holes
        if extra_points:
            border, holes, extra_points = complete_vertices(
                    border, holes, extra_points, context
            )
        result = cls.delaunay(list(chain(border.vertices,
                                         flatten(hole.vertices
                                                 for hole in holes),
                                         extra_points)),
                              context=context)
        border_edges = context.contour_segments(border)
        constrain(result, chain(border_edges,
                                flatten(map(context.contour_segments, holes)),
                                extra_constraints))
        bound(result, border_edges)
        cut(result, holes)
        result._triangular_holes_vertices.update(
                frozenset(hole.vertices)
                for hole in holes
                if len(hole.vertices) == 3
        )
        return result

    @classmethod
    def delaunay(cls,
                 points: _t.Sequence[Point],
                 *,
                 context: Context) -> Triangulation:
        """
        Constructs Delaunay triangulation of given points.

        Based on divide-and-conquer algorithm by L. Guibas & J. Stolfi.

        Time complexity:
            ``O(len(points) * log len(points))``
        Memory complexity:
            ``O(len(points))``
        Reference:
            http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf

        :param points: 3 or more points to triangulate.
        :param context: geometric context.
        :returns: triangulation of the points.
        """
        points = sorted(to_distinct(points))
        lengths = coin_change(len(points), base_cases)
        result = [cls._initialize_triangulation(points[start:stop], context)
                  for start, stop in pairwise(accumulate((0,) + lengths))]
        for _ in repeat(None, ceil_log2(len(result))):
            parts_to_merge_count = len(result) // 2 * 2
            result = ([merge(result[offset], result[offset + 1])
                       for offset in range(0, parts_to_merge_count, 2)]
                      + result[parts_to_merge_count:])
        return result[0]

    __slots__ = ('context', 'left_side', 'right_side',
                 '_triangular_holes_vertices')

    def __init__(self,
                 left_side: QuadEdge,
                 right_side: QuadEdge,
                 context: Context) -> None:
        self.context, self.left_side, self.right_side = (context, left_side,
                                                         right_side)
        self._triangular_holes_vertices: _t.Set[_t.FrozenSet[Point]] = set()

    __repr__ = generate_repr(__init__)

    def delete(self, edge: QuadEdge) -> None:
        """Deletes given edge from the triangulation."""
        if edge is self.right_side or edge.opposite is self.right_side:
            self.right_side = self.right_side.right_from_end.opposite
        if edge is self.left_side or edge.opposite is self.left_side:
            self.left_side = self.left_side.left_from_start
        edge.delete()

    def triangles(self) -> _t.List[Contour]:
        """Returns triangles of the triangulation."""
        vertices_sets = to_distinct(
                frozenset((edge.start, edge.end, edge.left_from_start.end))
                for edge in to_edges(self)
                if (edge.left_from_start.end
                    == edge.opposite.right_from_start.end
                    and (edge.orientation_of(edge.left_from_start.end)
                         is Orientation.COUNTERCLOCKWISE))
        )
        contour_cls, orienteer = (self.context.contour_cls,
                                  self.context.angle_orientation)
        return [contour_cls(normalize_contour_vertices(list(vertices),
                                                       orienteer))
                for vertices in vertices_sets
                if vertices not in self._triangular_holes_vertices]

    @classmethod
    def _initialize_triangulation(cls,
                                  points: _t.Sequence[Point],
                                  context: Context) -> Triangulation:
        return base_cases[len(points)](cls, points, context)


def bound(triangulation: Triangulation,
          border_edges: _t.Sequence[Segment]) -> None:
    border_endpoints = {to_endpoints(edge) for edge in border_edges}
    non_boundary = {edge
                    for edge in to_unique_boundary_edges(triangulation)
                    if to_endpoints(edge) not in border_endpoints}
    while non_boundary:
        edge = non_boundary.pop()
        candidates = edge_to_neighbours(edge)
        triangulation.delete(edge)
        non_boundary.update(candidate
                            for candidate in candidates
                            if to_endpoints(candidate) not in border_endpoints)


def connect(base_edge: QuadEdge,
            point_in_circle_locator: PointInCircleLocator) -> None:
    while True:
        left_candidate, right_candidate = (
            to_left_candidate(base_edge, point_in_circle_locator),
            to_right_candidate(base_edge, point_in_circle_locator)
        )
        if left_candidate is right_candidate is None:
            break
        elif (left_candidate is not None
              and (right_candidate is None
                   or not (point_in_circle_locator(right_candidate.end,
                                                   left_candidate.end,
                                                   base_edge.end,
                                                   base_edge.start)
                           is Location.INTERIOR))):
            base_edge = base_edge.opposite.connect(left_candidate.opposite)
        else:
            assert right_candidate is not None
            base_edge = right_candidate.connect(base_edge.opposite)


def constrain(triangulation: Triangulation,
              constraints: _t.Iterable[Segment]) -> None:
    endpoints = {to_endpoints(edge) for edge in to_edges(triangulation)}
    inner_edges = to_unique_inner_edges(triangulation)
    point_in_circle_locator, segments_relater = (
        triangulation.context.locate_point_in_point_point_point_circle,
        triangulation.context.segments_relation
    )
    for constraint in constraints:
        constraint_endpoints = to_endpoints(constraint)
        if constraint_endpoints in endpoints:
            continue
        crossings = detect_crossings(inner_edges, constraint, segments_relater)
        inner_edges.difference_update(crossings)
        endpoints.difference_update(to_endpoints(edge) for edge in crossings)
        new_edges = resolve_crossings(crossings, constraint, segments_relater)
        set_criterion({edge
                       for edge in new_edges
                       if to_endpoints(edge) != constraint_endpoints},
                      point_in_circle_locator)
        endpoints.update(to_endpoints(edge) for edge in new_edges)
        inner_edges.update(new_edges)


def cut(triangulation: Triangulation, holes: _t.Sequence[Contour]) -> None:
    if not holes:
        return
    events_queue = EventsQueue(triangulation.context)
    for edge in to_unique_inner_edges(triangulation):
        events_queue.register_edge(edge,
                                   from_first=True,
                                   is_counterclockwise_contour=True)
    orienteer = triangulation.context.angle_orientation
    for hole in holes:
        for endpoints in contour_to_oriented_edges_endpoints(
                hole,
                clockwise=True,
                orienteer=orienteer
        ):
            events_queue.register_segment(endpoints,
                                          from_first=False,
                                          is_counterclockwise_contour=False)
    for event in events_queue.sweep():
        if event.from_first and event.inside:
            event_edge = event.edge
            assert event_edge is not None
            triangulation.delete(event_edge)


def detect_crossings(inner_edges: _t.Iterable[QuadEdge],
                     constraint: Segment,
                     segments_relater: SegmentsRelater) -> _t.List[QuadEdge]:
    return [edge
            for edge in inner_edges
            if segments_relater(edge, constraint) is Relation.CROSS]


def edge_should_be_swapped(
        edge: QuadEdge, point_in_circle_locator: PointInCircleLocator
) -> bool:
    return (is_convex_quadrilateral_diagonal(edge)
            and (point_in_circle_locator(edge.right_from_start.end,
                                         edge.start, edge.end,
                                         edge.left_from_start.end)
                 is Location.INTERIOR
                 or (point_in_circle_locator(edge.left_from_start.end,
                                             edge.end, edge.start,
                                             edge.right_from_start.end)
                     is Location.INTERIOR)))


def find_base_edge(first: Triangulation, second: Triangulation) -> QuadEdge:
    while True:
        if (first.right_side.orientation_of(second.left_side.start)
                is Orientation.COUNTERCLOCKWISE):
            first.right_side = first.right_side.left_from_end
        elif (second.left_side.orientation_of(first.right_side.start)
              is Orientation.CLOCKWISE):
            second.left_side = second.left_side.right_from_end
        else:
            break
    base_edge = second.left_side.opposite.connect(first.right_side)
    if first.right_side.start == first.left_side.start:
        first.left_side = base_edge.opposite
    if second.left_side.start == second.right_side.start:
        second.right_side = base_edge
    return base_edge


def is_convex_quadrilateral_diagonal(edge: QuadEdge) -> bool:
    return (edge.right_from_start.orientation_of(edge.end)
            is Orientation.COUNTERCLOCKWISE
            is edge.right_from_end.opposite.orientation_of(
                    edge.left_from_start.end
            )
            is edge.left_from_end.orientation_of(edge.start)
            is edge.left_from_start.opposite.orientation_of(
                    edge.right_from_start.end
            ))


def merge(first: Triangulation, second: Triangulation) -> Triangulation:
    connect(find_base_edge(first, second),
            first.context.locate_point_in_point_point_point_circle)
    return type(first)(first.left_side, second.right_side, first.context)


def resolve_crossings(crossings: _t.List[QuadEdge],
                      constraint: Segment,
                      segments_relater: SegmentsRelater) -> _t.List[QuadEdge]:
    result = []
    crossings_queue = deque(crossings,
                            maxlen=len(crossings))
    while crossings_queue:
        edge = crossings_queue.popleft()
        if is_convex_quadrilateral_diagonal(edge):
            edge.swap()
            if segments_relater(edge, constraint) is Relation.CROSS:
                crossings_queue.append(edge)
            else:
                result.append(edge)
        else:
            crossings_queue.append(edge)
    return result


def set_criterion(target_edges: _t.Set[QuadEdge],
                  point_in_circle_locator: PointInCircleLocator) -> None:
    while True:
        edges_to_swap = {
            edge
            for edge in target_edges
            if edge_should_be_swapped(edge, point_in_circle_locator)
        }
        if not edges_to_swap:
            break
        for edge in edges_to_swap:
            edge.swap()
        target_edges.difference_update(edges_to_swap)


def to_boundary_edges(triangulation: Triangulation) -> _t.Iterable[QuadEdge]:
    return edges_with_opposites(to_unique_boundary_edges(triangulation))


def to_edges(triangulation: Triangulation) -> _t.Iterable[QuadEdge]:
    return edges_with_opposites(to_unique_edges(triangulation))


def to_left_candidate(
        base_edge: QuadEdge, point_in_circle_locator: PointInCircleLocator
) -> _t.Optional[QuadEdge]:
    result = base_edge.opposite.left_from_start
    if base_edge.orientation_of(result.end) is not Orientation.CLOCKWISE:
        return None
    while (point_in_circle_locator(result.left_from_start.end,
                                   base_edge.end, base_edge.start, result.end)
           is Location.INTERIOR
           and (base_edge.orientation_of(result.left_from_start.end)
                is Orientation.CLOCKWISE)):
        next_candidate = result.left_from_start
        result.delete()
        result = next_candidate
    return result


def to_right_candidate(
        base_edge: QuadEdge, point_in_circle_locator: PointInCircleLocator
) -> _t.Optional[QuadEdge]:
    result = base_edge.right_from_start
    if (base_edge.orientation_of(result.end)
            is not Orientation.CLOCKWISE):
        return None
    while (point_in_circle_locator(result.right_from_start.end,
                                   base_edge.end, base_edge.start, result.end)
           is Location.INTERIOR
           and (base_edge.orientation_of(result.right_from_start.end)
                is Orientation.CLOCKWISE)):
        next_candidate = result.right_from_start
        result.delete()
        result = next_candidate
    return result


def to_unique_boundary_edges(
        triangulation: Triangulation
) -> _t.Iterable[QuadEdge]:
    start = triangulation.left_side
    edge = start
    while True:
        yield edge
        if edge.right_from_end is start:
            break
        edge = edge.right_from_end


def to_unique_edges(triangulation: Triangulation) -> _t.Iterable[QuadEdge]:
    visited_edges: _t.Set[QuadEdge] = set()
    is_visited, visit_multiple = (visited_edges.__contains__,
                                  visited_edges.update)
    queue = [triangulation.left_side, triangulation.right_side]
    while queue:
        edge = queue.pop()
        if is_visited(edge):
            continue
        yield edge
        visit_multiple((edge, edge.opposite))
        queue.extend((edge.left_from_start, edge.left_from_end,
                      edge.right_from_start, edge.right_from_end))


def to_unique_inner_edges(triangulation: Triangulation) -> _t.Set[QuadEdge]:
    return (set(to_unique_edges(triangulation))
            .difference(to_boundary_edges(triangulation)))


BaseCase = _t.Callable[
    [_t.Type[Triangulation], _t.Sequence[Point], Context], Triangulation
]
base_cases: _t.Dict[int, BaseCase] = {}
register_base_case = partial(partial, base_cases.setdefault)


@register_base_case(2)
def triangulate_two_points(cls: _t.Type[Triangulation],
                           sorted_points: _t.Sequence[Point],
                           context: Context) -> Triangulation:
    first_edge = QuadEdge.from_endpoints(*sorted_points,
                                         context=context)
    return cls(first_edge, first_edge.opposite, context)


@register_base_case(3)
def triangulate_three_points(cls: _t.Type[Triangulation],
                             sorted_points: _t.Sequence[Point],
                             context: Context) -> Triangulation:
    left_point, mid_point, right_point = sorted_points
    first_edge, second_edge = (QuadEdge.from_endpoints(left_point, mid_point,
                                                       context=context),
                               QuadEdge.from_endpoints(mid_point, right_point,
                                                       context=context))
    first_edge.opposite.splice(second_edge)
    orientation = first_edge.orientation_of(right_point)
    if orientation is Orientation.COUNTERCLOCKWISE:
        second_edge.connect(first_edge)
        return cls(first_edge, second_edge.opposite, context)
    elif orientation is Orientation.CLOCKWISE:
        third_edge = second_edge.connect(first_edge)
        return cls(third_edge.opposite, third_edge, context)
    else:
        return cls(first_edge, second_edge.opposite, context)
