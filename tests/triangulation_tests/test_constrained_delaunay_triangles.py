from typing import (Sequence,
                    Tuple)

from hypothesis import given
from hypothesis_geometry.hints import Polygon

from sect.core.utils import (complete_vertices,
                             contour_to_segments,
                             flatten)
from sect.hints import (Contour,
                        Point)
from sect.triangulation import (constrained_delaunay_triangles,
                                delaunay_triangles)
from tests.utils import (is_convex_contour,
                         to_boundary_endpoints)
from . import strategies


@given(strategies.polygons_with_extra_points)
def test_basic(polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
               ) -> None:
    polygon, extra_points = polygon_with_extra_points
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes,
                                            extra_points=extra_points)

    assert isinstance(result, list)
    assert all(isinstance(element, tuple) for element in result)


@given(strategies.polygons_with_extra_points)
def test_sizes(polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
               ) -> None:
    polygon, extra_points = polygon_with_extra_points
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes,
                                            extra_points=extra_points)

    assert all(len(element) == 3 for element in result)


@given(strategies.polygons_with_extra_points)
def test_points(polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
                ) -> None:
    polygon, extra_points = polygon_with_extra_points
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes,
                                            extra_points=extra_points)

    assert set(flatten(result)) == set(sum(holes, border)) | set(extra_points)


@given(strategies.polygons_with_extra_points)
def test_edges(polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
               ) -> None:
    polygon, extra_points = polygon_with_extra_points
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes,
                                            extra_points=extra_points)

    border, holes, _ = complete_vertices(border, holes, extra_points)
    assert (set(flatten(map(contour_to_segments, result)))
            >= set(sum(map(contour_to_segments, holes),
                       contour_to_segments(border))))


@given(strategies.polygons_with_extra_points)
def test_boundary(polygon_with_extra_points: Tuple[Polygon, Sequence[Point]]
                  ) -> None:
    polygon, extra_points = polygon_with_extra_points
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes,
                                            extra_points=extra_points)

    border, holes, _ = complete_vertices(border, holes, extra_points)
    assert (to_boundary_endpoints(result)
            == set(map(frozenset, sum(map(contour_to_segments, holes),
                                      contour_to_segments(border)))))


@given(strategies.contours)
def test_connection_with_delaunay_triangles(contour: Contour) -> None:
    result = constrained_delaunay_triangles(contour)

    assert ((result == delaunay_triangles(contour))
            is is_convex_contour(contour))
