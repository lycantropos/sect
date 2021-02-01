from collections import deque
from itertools import (accumulate,
                       chain,
                       repeat)
from types import MappingProxyType
from typing import (Callable,
                    Iterable,
                    List,
                    Mapping,
                    Optional,
                    Sequence,
                    Set,
                    Type)

from decision.partition import coin_change
from ground.base import Context
from ground.hints import (Contour,
                          Point,
                          Polygon,
                          Segment)
from reprit.base import generate_repr

from sect.core.utils import (Orientation,
                             SegmentsRelationship,
                             contour_to_edges_endpoints,
                             flatten,
                             pairwise,
                             segments_relationship)
from .contracts import points_form_convex_quadrilateral
from .events_queue import EventsQueue
from .hints import (QuaternaryPointPredicate,
                    SegmentEndpoints,
                    Triangulation)
from .quad_edge import (QuadEdge,
                        edge_to_endpoints,
                        edge_to_neighbours,
                        edge_to_non_adjacent_vertices,
                        edges_with_opposites,
                        to_quad_edge_cls)
from .utils import (ceil_log2,
                    complete_vertices,
                    normalize_contour_vertices,
                    to_clockwise_contour,
                    to_unique_objects)


def _triangulate_two_points(cls: Type[Triangulation],
                            sorted_points: Sequence[Point]) -> Triangulation:
    first_edge = cls.edge_cls.from_endpoints(*sorted_points)
    return cls.from_sides(first_edge, first_edge.opposite)


def _triangulate_three_points(cls: Type[Triangulation],
                              sorted_points: Sequence[Point]) -> Triangulation:
    left_point, mid_point, right_point = sorted_points
    first_edge, second_edge = (
        cls.edge_cls.from_endpoints(left_point, mid_point),
        cls.edge_cls.from_endpoints(mid_point, right_point))
    first_edge.opposite.splice(second_edge)
    orientation = first_edge.orientation_of(right_point)
    if orientation is Orientation.COUNTERCLOCKWISE:
        second_edge.connect(first_edge)
        return cls.from_sides(first_edge, second_edge.opposite)
    elif orientation is Orientation.CLOCKWISE:
        third_edge = second_edge.connect(first_edge)
        return cls.from_sides(third_edge.opposite, third_edge)
    else:
        return cls.from_sides(first_edge, second_edge.opposite)


_base_cases = {2: _triangulate_two_points,
               3: _triangulate_three_points}

TriangulationBaseConstructor = Callable[[Type[Triangulation], Sequence[Point]],
                                        Triangulation]


def to_triangulation_cls(context: Context,
                         base_cases: Mapping[int, TriangulationBaseConstructor]
                         = MappingProxyType(_base_cases)
                         ) -> Type[Triangulation]:
    class Result(Triangulation):
        __slots__ = 'left_side', 'right_side', '_triangular_holes_vertices'

        edge_cls = to_quad_edge_cls(context)

        def __init__(self, left_side: QuadEdge, right_side: QuadEdge) -> None:
            self.left_side, self.right_side = left_side, right_side
            self._triangular_holes_vertices = set()

        __repr__ = generate_repr(__init__)

        @classmethod
        def constrained_delaunay(cls,
                                 polygon: Polygon,
                                 *,
                                 extra_constraints: Sequence[Segment] = (),
                                 extra_points: Sequence[Point] = ()
                                 ) -> Triangulation:
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
                ``O(vertices_count ** 2)`` otherwise,
                where ``vertices_count = len(border) + sum(map(len, holes))\
         + len(extra_points) + len(extra_constraints)``.
            Memory complexity:
                ``O(vertices_count)``,
                where ``vertices_count = len(border) + sum(map(len, holes))\
         + len(extra_points) + len(extra_constraints)``.
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
            :returns:
                triangulation of the border, holes & extra points
                considering constraints.
            """
            border, holes = polygon.border, polygon.holes
            if extra_points:
                border, holes, extra_points = complete_vertices(border, holes,
                                                                extra_points)
            result = cls.delaunay(list(chain(border.vertices,
                                             flatten(hole.vertices
                                                     for hole in holes),
                                             extra_points)))
            border_endpoints = contour_to_edges_endpoints(border)
            constrain(result,
                      chain(border_endpoints,
                            flatten(map(contour_to_edges_endpoints, holes)),
                            [(segment.start, segment.end)
                             for segment in extra_constraints]),
                      context.point_point_point_incircle_test)
            bound(result, border_endpoints)
            cut(result, holes)
            result._triangular_holes_vertices.update(
                    frozenset(hole.vertices)
                    for hole in holes
                    if len(hole.vertices) == 3)
            return result

        @classmethod
        def delaunay(cls, points: Sequence[Point]) -> 'Result':
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
            :returns: triangulation of the points.
            """
            points = sorted(to_unique_objects(points))
            lengths = coin_change(len(points), _base_cases)
            result = [cls._initialize_triangulation(points[start:stop])
                      for start, stop in pairwise(accumulate((0,) + lengths))]
            incircle_test = context.point_point_point_incircle_test
            for _ in repeat(None, ceil_log2(len(result))):
                parts_to_merge_count = len(result) // 2 * 2
                result = ([merge(result[offset], result[offset + 1],
                                 incircle_test)
                           for offset in range(0, parts_to_merge_count, 2)]
                          + result[parts_to_merge_count:])
            return result[0]

        @classmethod
        def from_sides(cls,
                       left_side: QuadEdge,
                       right_side: QuadEdge) -> Triangulation:
            return cls(left_side, right_side)

        def delete(self, edge: QuadEdge) -> None:
            """
            Deletes the edge from the triangulation.

            >>> from ground.base import get_context
            >>> context = get_context()
            >>> Point = context.point_cls
            >>> points = [Point(0, 0), Point(0, 1), Point(1, 0), Point(1, 1)]
            >>> triangulation = Triangulation.from_points(points)
            >>> edges = [triangulation.left_side, triangulation.right_side]
            >>> all(edge in triangulation.edges() for edge in edges)
            True
            >>> for edge in edges:
            ...     triangulation.delete(edge)
            >>> any(edge in triangulation.edges() for edge in edges)
            False
            """
            if edge is self.right_side or edge.opposite is self.right_side:
                self.right_side = self.right_side.right_from_end.opposite
            if edge is self.left_side or edge.opposite is self.left_side:
                self.left_side = self.left_side.left_from_start
            edge.delete()

        def triangles(self) -> List[Contour]:
            """
            Returns triangles of the triangulation.

            >>> from ground.base import get_context
            >>> context = get_context()
            >>> Contour, Point = context.contour_cls, context.point_cls,
            >>> points = [Point(0, 0), Point(0, 1), Point(1, 0), Point(1, 1)]
            >>> triangulation = Triangulation.from_points(points)
            >>> (triangulation.triangles()
            ...  == [Contour([Point(0, 1), Point(1, 0), Point(1, 1)]),
            ...      Contour([Point(0, 0), Point(1, 0), Point(0, 1)])])
            True
            """
            vertices_sets = to_unique_objects(
                    frozenset((edge.start, edge.end, edge.left_from_start.end))
                    for edge in to_edges(self)
                    if (edge.left_from_start.end
                        == edge.opposite.right_from_start.end
                        and (edge.orientation_of(edge.left_from_start.end)
                             is Orientation.COUNTERCLOCKWISE)))
            contour_cls = context.contour_cls
            return [contour_cls(normalize_contour_vertices(list(vertices)))
                    for vertices in vertices_sets
                    if vertices not in self._triangular_holes_vertices]

        @classmethod
        def _initialize_triangulation(cls, points: Sequence[Point]
                                      ) -> Triangulation:
            return base_cases[len(points)](cls, points)

    Result.__name__ = Result.__qualname__ = Triangulation.__name__
    return Result


def bound(triangulation: Triangulation,
          border_endpoints: Sequence[SegmentEndpoints]) -> None:
    border_endpoints = {frozenset(endpoints)
                        for endpoints in border_endpoints}
    non_boundary = {edge
                    for edge in to_unique_boundary_edges(triangulation)
                    if edge_to_endpoints(edge) not in border_endpoints}
    while non_boundary:
        edge = non_boundary.pop()
        candidates = edge_to_neighbours(edge)
        triangulation.delete(edge)
        non_boundary.update(
                candidate
                for candidate in candidates
                if edge_to_endpoints(candidate) not in border_endpoints)


def connect(base_edge: QuadEdge,
            incircle_test: QuaternaryPointPredicate) -> None:
    while True:
        left_candidate, right_candidate = (
            to_left_candidate(base_edge, incircle_test),
            to_right_candidate(base_edge, incircle_test))
        if left_candidate is right_candidate is None:
            break
        base_edge = (
            right_candidate.connect(base_edge.opposite)
            if (left_candidate is None
                or right_candidate is not None
                and incircle_test(left_candidate.end, base_edge.end,
                                  base_edge.start, right_candidate.end) > 0)
            else base_edge.opposite.connect(left_candidate.opposite))


def constrain(triangulation: Triangulation,
              constraints: Iterable[SegmentEndpoints],
              incircle_test: QuaternaryPointPredicate) -> None:
    endpoints = {edge_to_endpoints(edge) for edge in to_edges(triangulation)}
    inner_edges = to_unique_inner_edges(triangulation)
    for constraint in constraints:
        constraint_endpoints = frozenset(constraint)
        if constraint_endpoints in endpoints:
            continue
        constraint_start, constraint_end = constraint
        crossings = detect_crossings(inner_edges, constraint_start,
                                     constraint_end)
        inner_edges.difference_update(crossings)
        endpoints.difference_update(edge_to_endpoints(edge)
                                    for edge in crossings)
        new_edges = resolve_crossings(crossings, constraint_start,
                                      constraint_end)
        set_criterion({edge
                       for edge in new_edges
                       if edge_to_endpoints(edge) != constraint_endpoints},
                      incircle_test)
        endpoints.update(edge_to_endpoints(edge) for edge in new_edges)
        inner_edges.update(new_edges)


def cut(triangulation: Triangulation, holes: Sequence[Contour]) -> None:
    if not holes:
        return
    events_queue = EventsQueue()
    for edge in to_unique_inner_edges(triangulation):
        events_queue.register_edge(edge,
                                   from_left=True,
                                   is_counterclockwise_contour=True)
    for hole in holes:
        for endpoints in contour_to_edges_endpoints(
                to_clockwise_contour(hole)):
            events_queue.register_segment(endpoints,
                                          from_left=False,
                                          is_counterclockwise_contour=False)
    for event in events_queue.sweep():
        if event.from_left and event.inside:
            triangulation.delete(event.edge)


def detect_crossings(inner_edges: Iterable[QuadEdge],
                     constraint_start: Point,
                     constraint_end: Point) -> List[QuadEdge]:
    return [edge
            for edge in inner_edges
            if (segments_relationship(edge.start, edge.end, constraint_start,
                                      constraint_end)
                is SegmentsRelationship.CROSS)]


def edge_should_be_swapped(edge: QuadEdge,
                           incircle_test: QuaternaryPointPredicate) -> bool:
    return (points_form_convex_quadrilateral(
            (edge.start, edge.left_from_start.end,
             edge.end, edge.right_from_start.end))
            and (incircle_test(edge.start, edge.end, edge.left_from_start.end,
                               edge.right_from_start.end) > 0
                 or incircle_test(edge.end, edge.start,
                                  edge.right_from_start.end,
                                  edge.left_from_start.end) > 0))


def find_base_edge(left: Triangulation, right: Triangulation) -> QuadEdge:
    while True:
        if (left.right_side.orientation_of(right.left_side.start)
                is Orientation.COUNTERCLOCKWISE):
            left.right_side = left.right_side.left_from_end
        elif (right.left_side.orientation_of(left.right_side.start)
              is Orientation.CLOCKWISE):
            right.left_side = right.left_side.right_from_end
        else:
            break
    base_edge = right.left_side.opposite.connect(left.right_side)
    if left.right_side.start == left.left_side.start:
        left.left_side = base_edge.opposite
    if right.left_side.start == right.right_side.start:
        right.right_side = base_edge
    return base_edge


def merge(left: Triangulation,
          right: Triangulation,
          incircle_test: QuaternaryPointPredicate) -> Triangulation:
    connect(find_base_edge(left, right), incircle_test)
    return left.from_sides(left.left_side, right.right_side)


def resolve_crossings(crossings: List[QuadEdge],
                      constraint_start: Point,
                      constraint_end: Point) -> List[QuadEdge]:
    result = []
    crossings = deque(crossings,
                      maxlen=len(crossings))
    while crossings:
        edge = crossings.popleft()
        (first_non_edge_vertex,
         second_non_edge_vertex) = edge_to_non_adjacent_vertices(edge)
        if points_form_convex_quadrilateral((edge.start, edge.end,
                                             first_non_edge_vertex,
                                             second_non_edge_vertex)):
            edge.swap()
            if (segments_relationship(edge.start, edge.end, constraint_start,
                                      constraint_end)
                    is SegmentsRelationship.CROSS):
                crossings.append(edge)
            else:
                result.append(edge)
        else:
            crossings.append(edge)
    return result


def set_criterion(target_edges: Set[QuadEdge],
                  incircle_test: QuaternaryPointPredicate) -> None:
    while True:
        edges_to_swap = {edge
                         for edge in target_edges
                         if edge_should_be_swapped(edge, incircle_test)}
        if not edges_to_swap:
            break
        for edge in edges_to_swap:
            edge.swap()
        target_edges.difference_update(edges_to_swap)


def to_boundary_edges(triangulation: Triangulation) -> Iterable[QuadEdge]:
    return edges_with_opposites(to_unique_boundary_edges(triangulation))


def to_edges(triangulation: Triangulation) -> Iterable[QuadEdge]:
    return edges_with_opposites(to_unique_edges(triangulation))


def to_left_candidate(base_edge: QuadEdge,
                      incircle_test: QuaternaryPointPredicate
                      ) -> Optional[QuadEdge]:
    result = base_edge.opposite.left_from_start
    if base_edge.orientation_of(result.end) is not Orientation.CLOCKWISE:
        return None
    while (incircle_test(base_edge.end, base_edge.start, result.end,
                         result.left_from_start.end) > 0
           and (base_edge.orientation_of(result.left_from_start.end)
                is Orientation.CLOCKWISE)):
        next_candidate = result.left_from_start
        result.delete()
        result = next_candidate
    return result


def to_right_candidate(base_edge: QuadEdge,
                       incircle_test: QuaternaryPointPredicate
                       ) -> Optional[QuadEdge]:
    result = base_edge.right_from_start
    if (base_edge.orientation_of(result.end)
            is not Orientation.CLOCKWISE):
        return None
    while (incircle_test(base_edge.end, base_edge.start, result.end,
                         result.right_from_start.end) > 0
           and (base_edge.orientation_of(result.right_from_start.end)
                is Orientation.CLOCKWISE)):
        next_candidate = result.right_from_start
        result.delete()
        result = next_candidate
    return result


def to_unique_boundary_edges(triangulation: Triangulation
                             ) -> Iterable[QuadEdge]:
    start = triangulation.left_side
    edge = start
    while True:
        yield edge
        if edge.right_from_end is start:
            break
        edge = edge.right_from_end


def to_unique_edges(triangulation: Triangulation) -> Iterable[QuadEdge]:
    visited_edges = set()
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


def to_unique_inner_edges(triangulation: Triangulation) -> Set[QuadEdge]:
    return (set(to_unique_edges(triangulation))
            .difference(to_boundary_edges(triangulation)))
