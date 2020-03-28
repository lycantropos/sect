from collections import deque
from itertools import accumulate
from typing import (Iterable,
                    List,
                    Optional,
                    Sequence,
                    Set)

from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)
from robust.linear import (SegmentsRelationship,
                           segments_relationship)

from sect.hints import (Contour,
                        Point,
                        Segment,
                        Triangle)
from .contracts import (is_point_inside_circumcircle,
                        points_form_convex_quadrilateral)
from .events_queue import EventsQueue
from .subdivisional import (QuadEdge,
                            edge_to_endpoints,
                            edge_to_neighbours,
                            edge_to_non_adjacent_vertices,
                            edge_to_segment)
from .sweep import sweep
from .utils import (coin_change,
                    contour_to_segments,
                    flatten,
                    normalize_triangle,
                    pairwise,
                    to_unique_objects)


class Triangulation:
    __slots__ = 'left_edge', 'right_edge', '_triangular_holes_vertices'

    def __init__(self, left_edge: QuadEdge, right_edge: QuadEdge) -> None:
        self.left_edge = left_edge
        self.right_edge = right_edge
        self._triangular_holes_vertices = set()

    __repr__ = generate_repr(__init__)

    @classmethod
    def from_points(cls, points: Iterable[Point]) -> 'Triangulation':
        points = sorted(to_unique_objects(points))
        lengths = coin_change(len(points), _initializers)
        result = [_initialize_triangulation(points[start:stop])
                  for start, stop in pairwise(accumulate([0] + lengths))]
        while len(result) > 1:
            parts_to_merge_count = len(result) // 2 * 2
            result = ([result[offset]._merge_with(result[offset + 1])
                       for offset in range(0, parts_to_merge_count, 2)]
                      + result[parts_to_merge_count:])
        return result[0]

    def constrain(self, constraints: Iterable[Segment]) -> None:
        endpoints = {edge_to_endpoints(edge) for edge in self._to_edges()}
        inner_edges = self._to_unique_inner_edges()
        for constraint in constraints:
            constraint_endpoints = frozenset(constraint)
            if constraint_endpoints in endpoints:
                continue
            crossings = _detect_crossings(inner_edges, constraint)
            inner_edges.difference_update(crossings)
            endpoints.difference_update(edge_to_endpoints(edge)
                                        for edge in crossings)
            new_edges = _resolve_crossings(crossings, constraint)
            _set_criterion(edge
                           for edge in new_edges
                           if edge_to_endpoints(edge) != constraint_endpoints)
            endpoints.update(edge_to_endpoints(edge) for edge in new_edges)
            inner_edges.update(new_edges)

    def bound(self, border_segments: Sequence[Segment]) -> None:
        border_endpoints = {frozenset(segment) for segment in border_segments}
        non_boundary = {edge
                        for edge in self._to_boundary_edges()
                        if edge_to_endpoints(edge) not in border_endpoints}
        while non_boundary:
            edge = non_boundary.pop()
            non_boundary.remove(edge.opposite)
            candidates = edge_to_neighbours(edge)
            self.delete(edge)
            non_boundary.update(flatten(
                    (candidate, candidate.opposite)
                    for candidate in candidates
                    if edge_to_endpoints(candidate) not in border_endpoints))

    def cut(self, holes: Sequence[Contour]) -> None:
        if not holes:
            return
        events_queue = EventsQueue()
        for edge in self._to_unique_inner_edges():
            events_queue.register_edge(edge,
                                       from_test_contour=False)
        for hole in holes:
            for segment in contour_to_segments(hole):
                events_queue.register_segment(segment,
                                              from_test_contour=True)
        hole_segments_endpoints, candidates = set(), []
        for event in sweep(events_queue):
            if event.from_test_contour:
                hole_segments_endpoints.add(frozenset(event.segment))
            elif event.in_intersection:
                candidates.append(event.edge)
        for edge in candidates:
            if edge_to_endpoints(edge) not in hole_segments_endpoints:
                self.delete(edge)
        for hole in holes:
            if len(hole) == 3:
                self._triangular_holes_vertices.add(frozenset(hole))

    def triangles(self) -> List[Triangle]:
        return list(self._triangles())

    def _triangles(self) -> Iterable[Triangle]:
        visited_vertices = set(self._triangular_holes_vertices)
        edges = tuple(self._to_edges())
        edges_endpoints = {edge_to_endpoints(edge) for edge in edges}
        for edge in edges:
            if (edge.orientation_with(edge.left_from_start.end)
                    is Orientation.COUNTERCLOCKWISE):
                triangle = (edge.start, edge.end, edge.left_from_start.end)
                vertices = frozenset(triangle)
                if (vertices not in visited_vertices
                        and (frozenset((edge.end, edge.left_from_start.end))
                             in edges_endpoints)):
                    visited_vertices.add(vertices)
                    yield normalize_triangle(triangle)

    def _merge_with(self, other: 'Triangulation') -> 'Triangulation':
        _merge(self._find_base_edge(other))
        return Triangulation(self.left_edge, other.right_edge)

    def _find_base_edge(self, other: 'Triangulation') -> QuadEdge:
        while True:
            if (self.right_edge.orientation_with(other.left_edge.start)
                    is Orientation.COUNTERCLOCKWISE):
                self.right_edge = self.right_edge.left_from_end
            elif (other.left_edge.orientation_with(self.right_edge.start)
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
        if edge is self.right_edge or edge.opposite is self.right_edge:
            self.right_edge = self.right_edge.right_from_end.opposite
        if edge is self.left_edge or edge.opposite is self.left_edge:
            self.left_edge = self.left_edge.left_from_start
        edge.delete()

    def _to_boundary_edges(self) -> List[QuadEdge]:
        return list(flatten((edge, edge.opposite)
                            for edge in self._to_ccw_boundary_edges()))

    def _to_edges(self) -> Set[QuadEdge]:
        for edge in self._to_unique_edges():
            yield edge
            yield edge.opposite

    def _to_unique_edges(self) -> Set[QuadEdge]:
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

    def _to_ccw_boundary_edges(self) -> Iterable[QuadEdge]:
        start = self.left_edge
        edge = start
        while True:
            yield edge
            if edge.right_from_end is start:
                break
            edge = edge.right_from_end

    def _to_inner_edges(self) -> Set[QuadEdge]:
        return set(self._to_edges()).difference(self._to_boundary_edges())

    def _to_unique_inner_edges(self) -> Set[QuadEdge]:
        return (set(self._to_unique_edges())
                .difference(self._to_boundary_edges()))


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
            if (segments_relationship(edge_to_segment(edge), constraint)
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
            if segments_relationship(edge_to_segment(edge), constraint)
            is SegmentsRelationship.CROSS]


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
    if base_edge.orientation_with(result.end) is not Orientation.CLOCKWISE:
        return None
    while (is_point_inside_circumcircle(base_edge.end, base_edge.start,
                                        result.end, result.left_from_start.end)
           and (base_edge.orientation_with(result.left_from_start.end)
                is Orientation.CLOCKWISE)):
        next_candidate = result.left_from_start
        result.delete()
        result = next_candidate
    return result


def _to_right_candidate(base_edge: QuadEdge) -> Optional[QuadEdge]:
    result = base_edge.right_from_start
    if base_edge.orientation_with(result.end) is not Orientation.CLOCKWISE:
        return None
    while (is_point_inside_circumcircle(base_edge.end, base_edge.start,
                                        result.end,
                                        result.right_from_start.end)
           and (base_edge.orientation_with(result.right_from_start.end)
                is Orientation.CLOCKWISE)):
        next_candidate = result.right_from_start
        result.delete()
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
