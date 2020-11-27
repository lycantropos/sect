from typing import Sequence

from robust import cocircular

from sect.hints import Point
from .utils import to_convex_hull


def is_point_inside_circumcircle(first_vertex: Point,
                                 second_vertex: Point,
                                 third_vertex: Point,
                                 point: Point) -> bool:
    return cocircular.determinant(first_vertex, second_vertex, third_vertex,
                                  point) > 0


def points_form_convex_quadrilateral(points: Sequence[Point]) -> bool:
    vertices = to_convex_hull(points)
    return (len(vertices) == 4
            and all(vertex in points for vertex in vertices))
