from collections import deque
from itertools import (accumulate,
                       chain,
                       repeat)
from typing import (FrozenSet,
                    Iterable,
                    List,
                    Optional,
                    Sequence,
                    Set)

from decision.partition import coin_change
from reprit.base import generate_repr

from sect.core.utils import (Orientation,
                             SegmentsRelationship,
                             orientation,
                             pairwise,
                             segments_relationship)
from sect.hints import (Contour,
                        Point,
                        Segment,
                        Triangle)
from .contracts import (is_point_inside_circumcircle,
                        points_form_convex_quadrilateral)
from .events_queue import EventsQueue
from .quad_edge import (QuadEdge,
                        edge_to_neighbours,
                        edge_to_non_adjacent_vertices,
                        edges_with_opposites)
from .utils import (ceil_log2,
                    contour_to_segments, normalize_contour,
                    to_clockwise_contour,
                    to_unique_objects)


class Triangulation:
    __slots__ = 'left_edge', 'right_edge', '_triangular_holes_vertices'

    def __init__(self, left_edge: QuadEdge, right_edge: QuadEdge) -> None:
        self.left_edge, self.right_edge = left_edge, right_edge
        self._triangular_holes_vertices = set()  # type: Set[FrozenSet[Point]]

    __repr__ = generate_repr(__init__)

    @classmethod
    def from_points(cls, points: Iterable[Point]) -> 'Triangulation':
        points = sorted(to_unique_objects(points))
        lengths = coin_change(len(points), _initializers)
        result = [_initialize_triangulation(points[start:stop])
                  for start, stop in pairwise(accumulate(chain((0,),
                                                               lengths)))]
        for _ in repeat(None, ceil_log2(len(result))):
            parts_to_merge_count = len(result) // 2 * 2
            result = ([result[offset]._merge_with(result[offset + 1])
                       for offset in range(0, parts_to_merge_count, 2)]
                      + result[parts_to_merge_count:])
        return result[0]

    def constrain(self, constraints: Iterable[Segment]) -> None:
        endpoints = {edge.endpoints for edge in self.edges()}
        inner_edges = self._to_unique_inner_edges()
        for constraint in constraints:
            constraint_endpoints = frozenset(constraint)
            if constraint_endpoints in endpoints:
                continue
            crossings = _detect_crossings(inner_edges, constraint)
            inner_edges.difference_update(crossings)
            endpoints.difference_update(edge.endpoints for edge in crossings)
            new_edges = _resolve_crossings(crossings, constraint)
            _set_criterion(edge
                           for edge in new_edges
                           if edge.endpoints != constraint_endpoints)
            endpoints.update(edge.endpoints for edge in new_edges)
            inner_edges.update(new_edges)

    def bound(self, border_segments: Sequence[Segment]) -> None:
        border_endpoints = {frozenset(segment) for segment in border_segments}
        non_boundary = {edge
                        for edge in self.unique_boundary_edges()
                        if edge.endpoints not in border_endpoints}
        while non_boundary:
            edge = non_boundary.pop()
            candidates = edge_to_neighbours(edge)
            self.delete(edge)
            non_boundary.update(candidate
                                for candidate in candidates
                                if candidate.endpoints not in border_endpoints)

    def cut(self, holes: Sequence[Contour]) -> None:
        if not holes:
            return
        events_queue = EventsQueue()
        for edge in self._to_unique_inner_edges():
            events_queue.register_edge(edge,
                                       from_left=True,
                                       is_counterclockwise_contour=True)
        for hole in holes:
            for segment in contour_to_segments(to_clockwise_contour(hole)):
                events_queue.register_segment(
                        segment,
                        from_left=False,
                        is_counterclockwise_contour=False)
        for event in events_queue.sweep():
            if event.from_left and event.inside:
                self.delete(event.edge)
        self._triangular_holes_vertices.update(frozenset(hole)
                                               for hole in holes
                                               if len(hole) == 3)

    def triangles(self) -> List[Triangle]:
        """
        Returns triangles of the triangulation.

        >>> points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        >>> triangulation = Triangulation.from_points(points)
        >>> (triangulation.triangles()
        ...  == [((0, 1), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1))])
        True
        """
        return list(self._triangles())

    def _triangles(self) -> Iterable[Triangle]:
        visited_vertices = set(self._triangular_holes_vertices)
        for edge in self.edges():
            if (edge.left_from_start.end == edge.opposite.right_from_start.end
                    and (edge.orientation_of(edge.left_from_start.end)
                         is Orientation.COUNTERCLOCKWISE)):
                triangle = edge.start, edge.end, edge.left_from_start.end
                vertices = frozenset(triangle)
                if vertices not in visited_vertices:
                    visited_vertices.add(vertices)
                    yield normalize_contour(triangle)

    def _merge_with(self, other: 'Triangulation') -> 'Triangulation':
        _merge(self._find_base_edge(other))
        return Triangulation(self.left_edge, other.right_edge)

    def _find_base_edge(self, other: 'Triangulation') -> QuadEdge:
        while True:
            if (self.right_edge.orientation_of(other.left_edge.start)
                    is Orientation.COUNTERCLOCKWISE):
                self.right_edge = self.right_edge.left_from_end
            elif (other.left_edge.orientation_of(self.right_edge.start)
                  is Orientation.CLOCKWISE):
                other.left_edge = other.left_edge.right_from_end
            else:
                break
        base_edge = other.left_edge.opposite.connect(self.right_edge)
        if self.right_edge.start == self.left_edge.start:
            self.left_edge = base_edge.opposite
        if other.left_edge.start == other.right_edge.start:
            other.right_edge = base_edge
        return base_edge

    def delete(self, edge: QuadEdge) -> None:
        """
        Deletes the edge from the triangulation.

        >>> points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        >>> triangulation = Triangulation.from_points(points)
        >>> edges = [triangulation.left_edge, triangulation.right_edge]
        >>> all(edge in triangulation.edges() for edge in edges)
        True
        >>> for edge in edges:
        ...     triangulation.delete(edge)
        >>> any(edge in triangulation.edges() for edge in edges)
        False
        """
        if edge is self.right_edge or edge.opposite is self.right_edge:
            self.right_edge = self.right_edge.right_from_end.opposite
        if edge is self.left_edge or edge.opposite is self.left_edge:
            self.left_edge = self.left_edge.left_from_start
        edge.disconnect()

    def boundary_edges(self) -> Iterable[QuadEdge]:
        """
        Returns boundary edges of the triangulation in counterclockwise order.

        >>> points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        >>> triangulation = Triangulation.from_points(points)
        >>> ([edge.segment for edge in triangulation.boundary_edges()]
        ...  == [((0, 0), (1, 0)), ((1, 0), (0, 0)),
        ...      ((1, 0), (1, 1)), ((1, 1), (1, 0)),
        ...      ((1, 1), (0, 1)), ((0, 1), (1, 1)),
        ...      ((0, 1), (0, 0)), ((0, 0), (0, 1))])
        True
        """
        return edges_with_opposites(self.unique_boundary_edges())

    def edges(self) -> Iterable[QuadEdge]:
        """
        Returns edges of the triangulation.

        >>> points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        >>> triangulation = Triangulation.from_points(points)
        >>> ([edge.segment for edge in triangulation.edges()]
        ...  == [((1, 1), (1, 0)), ((1, 0), (1, 1)),
        ...      ((1, 0), (0, 1)), ((0, 1), (1, 0)),
        ...      ((0, 1), (1, 1)), ((1, 1), (0, 1)),
        ...      ((0, 1), (0, 0)), ((0, 0), (0, 1)),
        ...      ((0, 0), (1, 0)), ((1, 0), (0, 0))])
        True
        """
        return edges_with_opposites(self.unique_edges())

    def unique_boundary_edges(self) -> Iterable[QuadEdge]:
        """
        Returns boundary edges of the triangulation in counterclockwise order.

        >>> points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        >>> triangulation = Triangulation.from_points(points)
        >>> ([edge.segment for edge in triangulation.unique_boundary_edges()]
        ...  == [((0, 0), (1, 0)), ((1, 0), (1, 1)),
        ...      ((1, 1), (0, 1)), ((0, 1), (0, 0))])
        True
        """
        start = self.left_edge
        edge = start
        while True:
            yield edge
            if edge.right_from_end is start:
                break
            edge = edge.right_from_end

    def unique_edges(self) -> Iterable[QuadEdge]:
        """
        Returns edges of the triangulation with unique endpoints.

        >>> points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        >>> triangulation = Triangulation.from_points(points)
        >>> ([edge.segment for edge in triangulation.unique_edges()]
        ...  == [((1, 1), (1, 0)), ((1, 0), (0, 1)), ((0, 1), (1, 1)),
        ...      ((0, 1), (0, 0)), ((0, 0), (1, 0))])
        True
        """
        visited_edges = set()
        is_visited, visit_multiple = (visited_edges.__contains__,
                                      visited_edges.update)
        queue = [self.left_edge, self.right_edge]
        while queue:
            edge = queue.pop()
            if is_visited(edge):
                continue
            yield edge
            visit_multiple((edge, edge.opposite))
            queue.extend((edge.left_from_start, edge.left_from_end,
                          edge.right_from_start, edge.right_from_end))

    def _to_unique_inner_edges(self) -> Set[QuadEdge]:
        return set(self.unique_edges()).difference(self.boundary_edges())


def _resolve_crossings(crossings: List[QuadEdge],
                       constraint: Segment) -> List[QuadEdge]:
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
            if (segments_relationship(edge.segment, constraint)
                    is SegmentsRelationship.CROSS):
                crossings.append(edge)
            else:
                result.append(edge)
        else:
            crossings.append(edge)
    return result


def _detect_crossings(inner_edges: Iterable[QuadEdge],
                      constraint: Segment) -> List[QuadEdge]:
    return [edge
            for edge in inner_edges
            if (segments_relationship(edge.segment, constraint)
                is SegmentsRelationship.CROSS)]


def _merge(base_edge: QuadEdge) -> None:
    while True:
        left_candidate, right_candidate = (_to_left_candidate(base_edge),
                                           _to_right_candidate(base_edge))
        if left_candidate is right_candidate is None:
            break
        elif (left_candidate is None
              or right_candidate is not None
              and is_point_inside_circumcircle(left_candidate.end,
                                               base_edge.end,
                                               base_edge.start,
                                               right_candidate.end)):
            base_edge = right_candidate.connect(base_edge.opposite)
        else:
            base_edge = base_edge.opposite.connect(left_candidate.opposite)


def _to_left_candidate(base_edge: QuadEdge) -> Optional[QuadEdge]:
    result = base_edge.opposite.left_from_start
    if base_edge.orientation_of(result.end) is not Orientation.CLOCKWISE:
        return None
    while (is_point_inside_circumcircle(base_edge.end, base_edge.start,
                                        result.end, result.left_from_start.end)
           and (base_edge.orientation_of(result.left_from_start.end)
                is Orientation.CLOCKWISE)):
        next_candidate = result.left_from_start
        result.disconnect()
        result = next_candidate
    return result


def _to_right_candidate(base_edge: QuadEdge) -> Optional[QuadEdge]:
    result = base_edge.right_from_start
    if base_edge.orientation_of(result.end) is not Orientation.CLOCKWISE:
        return None
    while (is_point_inside_circumcircle(base_edge.end, base_edge.start,
                                        result.end,
                                        result.right_from_start.end)
           and (base_edge.orientation_of(result.right_from_start.end)
                is Orientation.CLOCKWISE)):
        next_candidate = result.right_from_start
        result.disconnect()
        result = next_candidate
    return result


def _set_criterion(target_edges: Iterable[QuadEdge]) -> None:
    target_edges = set(target_edges)
    while True:
        edges_to_swap = {edge
                         for edge in target_edges
                         if _edge_should_be_swapped(edge)}
        if not edges_to_swap:
            break
        for edge in edges_to_swap:
            edge.swap()
        target_edges.difference_update(edges_to_swap)


def _edge_should_be_swapped(edge: QuadEdge) -> bool:
    return (points_form_convex_quadrilateral(
            (edge.start, edge.left_from_start.end,
             edge.end, edge.right_from_start.end))
            and (is_point_inside_circumcircle(edge.start, edge.end,
                                              edge.left_from_start.end,
                                              edge.right_from_start.end)
                 or is_point_inside_circumcircle(edge.end, edge.start,
                                                 edge.right_from_start.end,
                                                 edge.left_from_start.end)))


def _triangulate_two_points(sorted_points: Sequence[Point]) -> Triangulation:
    first_edge = QuadEdge.factory(*sorted_points)
    return Triangulation(first_edge, first_edge.opposite)


def _triangulate_three_points(sorted_points: Sequence[Point]) -> Triangulation:
    left_point, mid_point, right_point = sorted_points
    first_edge, second_edge = (QuadEdge.factory(left_point, mid_point),
                               QuadEdge.factory(mid_point, right_point))
    first_edge.opposite.splice(second_edge)
    angle_orientation = orientation(left_point, mid_point, right_point)
    if angle_orientation is Orientation.COUNTERCLOCKWISE:
        third_edge = second_edge.connect(first_edge)
        return Triangulation(third_edge.opposite, third_edge)
    elif angle_orientation is Orientation.CLOCKWISE:
        second_edge.connect(first_edge)
        return Triangulation(first_edge, second_edge.opposite)
    else:
        return Triangulation(first_edge, second_edge.opposite)


_initializers = {2: _triangulate_two_points,
                 3: _triangulate_three_points}


def _initialize_triangulation(points: Sequence[Point]) -> Triangulation:
    return _initializers[len(points)](points)
