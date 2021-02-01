from operator import getitem
from typing import (FrozenSet,
                    Iterable,
                    List,
                    Sequence,
                    Set,
                    TypeVar)

from ground.base import (Orientation,
                         Relation,
                         get_context)
from hypothesis import strategies
from hypothesis.strategies import SearchStrategy
from orient.planar import point_in_segment

from sect.core.delaunay.contracts import is_point_inside_circumcircle
from sect.core.delaunay.utils import normalize_contour_vertices
from sect.core.utils import contour_to_edges_endpoints
from sect.core.voronoi.utils import robust_divide

Strategy = SearchStrategy
context = get_context()
Contour = context.contour_cls
Multipoint = context.multipoint_cls
Multisegment = context.multisegment_cls
Point = context.point_cls
Polygon = context.polygon_cls
Segment = context.segment_cls

MAX_COORDINATE_EXPONENT = 15
MAX_RATIONAL_COORDINATE_EXPONENT = 7

is_contour = Contour.__instancecheck__


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


to_convex_hull = context.points_convex_hull
is_point_inside_circumcircle = is_point_inside_circumcircle


def is_convex_contour(contour: Contour) -> bool:
    contour = normalize_contour(contour)
    vertices = contour.vertices
    return all(context.angle_orientation(vertices[index - 2],
                                         vertices[index - 1], vertices[index])
               is Orientation.COUNTERCLOCKWISE
               for index in range(len(vertices)))


def normalize_contour(contour: Contour) -> Contour:
    return Contour(normalize_contour_vertices(contour.vertices))


Element = TypeVar('Element')


def sub_lists(sequence: Sequence[Element]) -> SearchStrategy[List[Element]]:
    return strategies.builds(getitem,
                             strategies.permutations(sequence),
                             strategies.slices(max(len(sequence), 1)))


def to_circumcenter(triangle: Contour) -> Point:
    first, second, third = triangle.vertices
    first_x, first_y = first.x, first.y
    second_x, second_y = second.x, second.y
    third_x, third_y = third.x, third.y
    first_squared_norm = first_x * first_x + first_y * first_y
    second_squared_norm = second_x * second_x + second_y * second_y
    third_squared_norm = third_x * third_x + third_y * third_y
    center_x_numerator = (first_squared_norm * (second_y - third_y)
                          + second_squared_norm * (third_y - first_y)
                          + third_squared_norm * (first_y - second_y))
    center_y_numerator = -(first_squared_norm * (second_x - third_x)
                           + second_squared_norm * (third_x - first_x)
                           + third_squared_norm * (first_x - second_x))
    denominator = 2 * context.cross_product(first, second, second, third)
    inverted_denominator = robust_divide(1, denominator)
    center_x = center_x_numerator * inverted_denominator
    center_y = center_y_numerator * inverted_denominator
    return Point(center_x, center_y)


def contour_to_multipoint(contour: Contour) -> Multipoint:
    return Multipoint(contour.vertices)


def contour_to_edges(contour: Contour) -> Sequence[Segment]:
    vertices = contour.vertices
    return [Segment(vertices[index - 1], vertices[index])
            for index in range(len(vertices))]


contour_to_edges_endpoints = contour_to_edges_endpoints


def segment_contains_point(segment: Segment, point: Point) -> bool:
    return context.segment_contains_point(segment.start, segment.end, point)


def to_convex_hull_border_endpoints(points: Sequence[Point]
                                    ) -> Set[FrozenSet[Point]]:
    convex_hull_border = Contour(to_convex_hull(points))
    return set(map(frozenset, contour_to_edges_endpoints(convex_hull_border)))
