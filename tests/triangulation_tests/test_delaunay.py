from typing import Sequence

from ground.hints import (Contour,
                          Point)
from hypothesis import given

from sect.triangulation import (Triangulation,
                                delaunay)
from tests.utils import (is_contour_triangular,
                         is_point_inside_circumcircle,
                         normalize_contour,
                         to_boundary_endpoints,
                         to_convex_hull,
                         to_convex_hull_boundary_endpoints)
from . import strategies


@given(strategies.points_lists)
def test_basic(points: Sequence[Point]) -> None:
    result = delaunay(points)

    assert isinstance(result, Triangulation)


@given(strategies.points_lists)
def test_sizes(points: Sequence[Point]) -> None:
    result = delaunay(points)

    triangles = result.triangles()
    assert 0 < len(triangles) <= (2 * (len(points) - 1)
                                  - len(to_convex_hull(points)))
    assert all(is_contour_triangular(triangle) for triangle in triangles)


@given(strategies.points_lists)
def test_delaunay_criterion(points: Sequence[Point]) -> None:
    result = delaunay(points)

    assert all(not any(is_point_inside_circumcircle(*triangle.vertices, point)
                       for triangle in result.triangles())
               for point in points)


@given(strategies.points_lists)
def test_boundary(points: Sequence[Point]) -> None:
    result = delaunay(points)

    assert (to_boundary_endpoints(result.triangles())
            == set(map(frozenset,
                       to_convex_hull_boundary_endpoints(points))))


@given(strategies.triangles)
def test_base_case(triangle: Contour) -> None:
    result = delaunay(triangle.vertices)

    triangles = result.triangles()
    assert len(triangles) == 1
    assert normalize_contour(triangle) in triangles


@given(strategies.non_triangle_points_lists)
def test_step(next_points: Sequence[Point]) -> None:
    points = next_points[:-1]
    next_point = next_points[-1]

    result = delaunay(points)
    next_result = delaunay(next_points)

    triangles = result.triangles()
    next_triangles = next_result.triangles()
    assert len(triangles) <= len(next_triangles) + 2
    assert all(triangle not in next_triangles
               for triangle in triangles
               if is_point_inside_circumcircle(*triangle.vertices, next_point))
