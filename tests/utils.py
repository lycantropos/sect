from functools import partial
from operator import getitem
from typing import (AbstractSet,
                    Callable,
                    FrozenSet,
                    Hashable,
                    Iterable,
                    List,
                    Sequence,
                    Set,
                    TypeVar)

from ground.base import (Location,
                         Orientation,
                         Relation,
                         get_context)
from hypothesis import strategies
from hypothesis.strategies import SearchStrategy
from orient.planar import point_in_segment

from sect.core.delaunay.utils import (complete_vertices as _complete_vertices,
                                      normalize_contour_vertices,
                                      to_distinct)
from sect.core.utils import contour_to_edges_endpoints

Strategy = SearchStrategy
context = get_context()
Contour = context.contour_cls
Multipoint = context.multipoint_cls
Multisegment = context.multisegment_cls
Point = context.point_cls
Polygon = context.polygon_cls
Segment = context.segment_cls

MAX_COORDINATE_EXPONENT = 15

complete_vertices = partial(_complete_vertices,
                            context=context)


def is_contour_triangular(contour: Contour) -> bool:
    return len(contour.vertices) == 3


def point_in_multisegment(point: Point,
                          multisegment: Multisegment) -> Relation:
    return (Relation.COMPONENT
            if any(point_in_segment(point, segment) is Relation.COMPONENT
                   for segment in multisegment.segments)
            else Relation.DISJOINT)


def points_do_not_lie_on_the_same_line(points: Sequence[Point]) -> bool:
    return any(context.angle_orientation(points[index - 1], points[index],
                                         points[(index + 1) % len(points)])
               is not Orientation.COLLINEAR
               for index in range(len(points)))


def to_contours_border_endpoints(contours: Iterable[Contour]
                                 ) -> Set[FrozenSet[Point]]:
    result = set()
    for contour in contours:
        result.symmetric_difference_update(
                map(frozenset, contour_to_edges_endpoints(contour)))
    return result


def to_max_convex_hull(points: Sequence[Point]) -> List[Point]:
    points = sorted(to_distinct(points))
    lower, upper = _to_sub_hull(points), _to_sub_hull(reversed(points))
    return lower[:-1] + upper[:-1] or points


def _to_sub_hull(points: Iterable[Point]) -> List[Point]:
    result = []
    for point in points:
        while len(result) >= 2:
            if (context.angle_orientation(result[-2], result[-1], point)
                    is Orientation.CLOCKWISE):
                del result[-1]
            else:
                break
        result.append(point)
    return result


def is_point_inside_circumcircle(point: Point,
                                 first_vertex: Point,
                                 second_vertex: Point,
                                 third_vertex: Point) -> bool:
    return (context.locate_point_in_point_point_point_circle(
            point, first_vertex, second_vertex, third_vertex)
            is Location.INTERIOR)


def is_convex_contour(contour: Contour) -> bool:
    contour = normalize_contour(contour)
    vertices = contour.vertices
    return all(context.angle_orientation(vertices[index - 2],
                                         vertices[index - 1], vertices[index])
               is Orientation.COUNTERCLOCKWISE
               for index in range(len(vertices)))


def normalize_contour(contour: Contour) -> Contour:
    return Contour(normalize_contour_vertices(contour.vertices,
                                              context.angle_orientation))


Element = TypeVar('Element')


def sub_lists(sequence: Sequence[Element]) -> SearchStrategy[List[Element]]:
    return strategies.builds(getitem,
                             strategies.permutations(sequence),
                             strategies.slices(max(len(sequence), 1)))


def contour_to_edges(contour: Contour) -> Sequence[Segment]:
    return [Segment(start, end)
            for start, end in contour_to_edges_endpoints(contour)]


contour_to_edges_endpoints = contour_to_edges_endpoints
segment_contains_point = context.segment_contains_point

_T = TypeVar('_T',
             bound=Hashable)
to_distinct = to_distinct  # type: Callable[[Iterable[_T]], AbstractSet[_T]]


def to_max_convex_hull_border_endpoints(points: Sequence[Point]
                                        ) -> Set[FrozenSet[Point]]:
    max_convex_hull = to_max_convex_hull(points)
    return set(map(frozenset,
                   contour_to_edges_endpoints(Contour(max_convex_hull))))
