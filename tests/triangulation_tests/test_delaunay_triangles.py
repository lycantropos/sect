from typing import Sequence

from hypothesis import given

from sect.core.contracts import is_point_inside_circumcircle
from sect.core.utils import (contour_to_segments,
                             normalize_contour,
                             to_convex_hull)
from sect.hints import (Point,
                        Triangle)
from sect.triangulation import delaunay_triangles
from tests.utils import to_boundary_endpoints
from . import strategies


@given(strategies.points_lists)
def test_basic(points: Sequence[Point]) -> None:
    result = delaunay_triangles(points)

    assert isinstance(result, list)
    assert all(isinstance(element, tuple)
               for element in result)


@given(strategies.points_lists)
def test_sizes(points: Sequence[Point]) -> None:
    result = delaunay_triangles(points)

    assert 0 < len(result) <= (2 * (len(points) - 1)
                               - len(to_convex_hull(points)))
    assert all(len(element) == 3
               for element in result)


@given(strategies.points_lists)
def test_delaunay_criterion(points: Sequence[Point]) -> None:
    result = delaunay_triangles(points)

    assert all(not any(is_point_inside_circumcircle(*triangle_contour, point)
                       for triangle_contour in result)
               for point in points)


@given(strategies.points_lists)
def test_boundary(points: Sequence[Point]) -> None:
    result = delaunay_triangles(points)

    assert (to_boundary_endpoints(result)
            == set(map(frozenset,
                       contour_to_segments(to_convex_hull(points)))))


@given(strategies.triangles)
def test_base_case(triangle: Triangle) -> None:
    result = delaunay_triangles(triangle)

    assert len(result) == 1
    assert normalize_contour(triangle) in result


@given(strategies.non_triangle_points_lists)
def test_step(next_points: Sequence[Point]) -> None:
    points = next_points[:-1]
    next_point = next_points[-1]

    result = delaunay_triangles(points)
    next_result = delaunay_triangles(next_points)

    assert len(result) <= len(next_result) + 2
    assert all(triangle not in next_result
               for triangle in result
               if is_point_inside_circumcircle(*triangle, next_point))
