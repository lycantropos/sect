from typing import Sequence

from ground.base import Context
from ground.hints import (Contour,
                          Point)
from hypothesis import given

from sect.triangulation import Triangulation
from tests.utils import (is_contour_triangular,
                         is_point_inside_circumcircle,
                         normalize_contour,
                         to_contours_border_endpoints,
                         to_distinct,
                         to_max_convex_hull,
                         to_max_convex_hull_border_endpoints)
from . import strategies


@given(strategies.contexts, strategies.points_lists)
def test_basic(context: Context, points: Sequence[Point]) -> None:
    result = Triangulation.delaunay(points,
                                    context=context)

    assert isinstance(result, Triangulation)


@given(strategies.contexts, strategies.points_lists)
def test_sizes(context: Context, points: Sequence[Point]) -> None:
    result = Triangulation.delaunay(points,
                                    context=context)

    triangles = result.triangles()
    assert 0 < len(triangles) <= (2 * (len(to_distinct(points)) - 1)
                                  - len(to_max_convex_hull(points)))
    assert all(is_contour_triangular(triangle) for triangle in triangles)


@given(strategies.contexts, strategies.points_lists)
def test_delaunay_criterion(context: Context, points: Sequence[Point]) -> None:
    result = Triangulation.delaunay(points,
                                    context=context)

    assert all(not any(is_point_inside_circumcircle(point, *triangle.vertices)
                       for triangle in result.triangles())
               for point in points)


@given(strategies.contexts, strategies.points_lists)
def test_boundary(context: Context, points: Sequence[Point]) -> None:
    result = Triangulation.delaunay(points,
                                    context=context)

    assert (to_contours_border_endpoints(result.triangles())
            == to_max_convex_hull_border_endpoints(points))


@given(strategies.contexts, strategies.triangles)
def test_base_case(context: Context, triangle: Contour) -> None:
    result = Triangulation.delaunay(triangle.vertices,
                                    context=context)

    triangles = result.triangles()
    assert len(triangles) == 1
    assert normalize_contour(triangle) in triangles


@given(strategies.contexts, strategies.non_triangle_points_lists)
def test_step(context: Context, points: Sequence[Point]) -> None:
    rest_points, last_point = points[:-1], points[-1]

    result = Triangulation.delaunay(rest_points,
                                    context=context)
    next_result = Triangulation.delaunay(points,
                                         context=context)

    triangles = result.triangles()
    next_triangles = next_result.triangles()
    assert len(triangles) <= len(next_triangles) + 2
    assert all(triangle not in next_triangles
               for triangle in triangles
               if is_point_inside_circumcircle(last_point, *triangle.vertices))
