from typing import (Sequence,
                    Tuple,
                    Type)

from ground.hints import Point
from hypothesis import given

from sect.core.utils import flatten
from sect.triangulation import Triangulation
from tests.utils import (Polygon,
                         complete_vertices,
                         contour_to_edges_endpoints,
                         is_contour,
                         is_contour_triangular,
                         is_convex_contour,
                         to_contours_border_endpoints)
from . import strategies


@given(strategies.triangulation_classes, strategies.polygons_with_extra_points)
def test_basic(triangulation_cls: Type[Triangulation],
               polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
               ) -> None:
    polygon, extra_points = polygon_with_extra_points

    result = triangulation_cls.constrained_delaunay(polygon,
                                                    extra_points=extra_points)

    assert isinstance(result, triangulation_cls)


@given(strategies.triangulation_classes, strategies.polygons_with_extra_points)
def test_sizes(triangulation_cls: Type[Triangulation],
               polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
               ) -> None:
    polygon, extra_points = polygon_with_extra_points

    result = triangulation_cls.constrained_delaunay(polygon,
                                                    extra_points=extra_points)

    assert all(is_contour(element) and is_contour_triangular(element)
               for element in result.triangles())


@given(strategies.triangulation_classes, strategies.polygons_with_extra_points)
def test_points(triangulation_cls: Type[Triangulation],
                polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
                ) -> None:
    polygon, extra_points = polygon_with_extra_points

    result = triangulation_cls.constrained_delaunay(polygon,
                                                    extra_points=extra_points)

    assert (set(flatten(triangle.vertices for triangle in result.triangles()))
            == (set(sum([hole.vertices for hole in polygon.holes],
                        polygon.border.vertices))
                | set(extra_points)))


@given(strategies.triangulation_classes, strategies.polygons_with_extra_points)
def test_edges(triangulation_cls: Type[Triangulation],
               polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
               ) -> None:
    polygon, extra_points = polygon_with_extra_points

    result = triangulation_cls.constrained_delaunay(polygon,
                                                    extra_points=extra_points)

    border, holes, _ = complete_vertices(polygon.border, polygon.holes,
                                         extra_points)
    assert (set(flatten(map(contour_to_edges_endpoints, result.triangles())))
            >= set(sum(map(contour_to_edges_endpoints, holes),
                       contour_to_edges_endpoints(border))))


@given(strategies.triangulation_classes, strategies.polygons_with_extra_points)
def test_boundary(triangulation_cls: Type[Triangulation],
                  polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
                  ) -> None:
    polygon, extra_points = polygon_with_extra_points

    result = triangulation_cls.constrained_delaunay(polygon,
                                                    extra_points=extra_points)

    border, holes, _ = complete_vertices(polygon.border, polygon.holes,
                                         extra_points)
    assert (to_contours_border_endpoints(result.triangles())
            == set(map(frozenset, sum(map(contour_to_edges_endpoints, holes),
                                      contour_to_edges_endpoints(border)))))


@given(strategies.triangulation_classes, strategies.whole_polygons)
def test_connection_with_delaunay_triangles(triangulation_cls
                                            : Type[Triangulation],
                                            polygon: Polygon) -> None:
    result = triangulation_cls.constrained_delaunay(polygon)

    border = polygon.border
    assert ((result.triangles()
             == triangulation_cls.delaunay(border.vertices).triangles())
            is is_convex_contour(border))
