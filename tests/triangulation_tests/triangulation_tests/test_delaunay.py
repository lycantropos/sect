from typing import (Sequence,
                    Type)

from ground.hints import (Contour,
                          Point)
from hypothesis import given

from sect.triangulation import Triangulation
from tests.utils import (is_contour_triangular,
                         is_point_inside_circumcircle,
                         normalize_contour,
                         to_contours_border_endpoints,
                         to_max_convex_hull,
                         to_max_convex_hull_border_endpoints)
from . import strategies


@given(strategies.triangulation_classes, strategies.points_lists)
def test_basic(triangulation_cls: Type[Triangulation],
               points: Sequence[Point]) -> None:
    result = triangulation_cls.delaunay(points)

    assert isinstance(result, triangulation_cls)


@given(strategies.triangulation_classes, strategies.points_lists)
def test_sizes(triangulation_cls: Type[Triangulation],
               points: Sequence[Point]) -> None:
    result = triangulation_cls.delaunay(points)

    triangles = result.triangles()
    assert 0 < len(triangles) <= (2 * (len(points) - 1)
                                  - len(to_max_convex_hull(points)))
    assert all(is_contour_triangular(triangle) for triangle in triangles)


@given(strategies.triangulation_classes, strategies.points_lists)
def test_delaunay_criterion(triangulation_cls: Type[Triangulation],
                            points: Sequence[Point]) -> None:
    result = triangulation_cls.delaunay(points)

    assert all(not any(is_point_inside_circumcircle(*triangle.vertices, point)
                       for triangle in result.triangles())
               for point in points)


@given(strategies.triangulation_classes, strategies.points_lists)
def test_boundary(triangulation_cls: Type[Triangulation],
                  points: Sequence[Point]) -> None:
    result = triangulation_cls.delaunay(points)

    assert (to_contours_border_endpoints(result.triangles())
            == to_max_convex_hull_border_endpoints(points))


@given(strategies.triangulation_classes, strategies.triangles)
def test_base_case(triangulation_cls: Type[Triangulation],
                   triangle: Contour) -> None:
    result = triangulation_cls.delaunay(triangle.vertices)

    triangles = result.triangles()
    assert len(triangles) == 1
    assert normalize_contour(triangle) in triangles


@given(strategies.triangulation_classes, strategies.non_triangle_points_lists)
def test_step(triangulation_cls: Type[Triangulation],
              next_points: Sequence[Point]) -> None:
    points = next_points[:-1]
    next_point = next_points[-1]

    result = triangulation_cls.delaunay(points)
    next_result = triangulation_cls.delaunay(next_points)

    triangles = result.triangles()
    next_triangles = next_result.triangles()
    assert len(triangles) <= len(next_triangles) + 2
    assert all(triangle not in next_triangles
               for triangle in triangles
               if is_point_inside_circumcircle(*triangle.vertices, next_point))
