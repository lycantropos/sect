from hypothesis import given
from hypothesis_geometry.hints import Polygon

from sect.core.utils import (contour_to_segments,
                             flatten)
from sect.triangulation import constrained_delaunay_triangles
from tests.utils import to_boundary_endpoints
from . import strategies


@given(strategies.polygons)
def test_basic(polygon: Polygon) -> None:
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes)

    assert isinstance(result, list)
    assert all(isinstance(element, tuple)
               for element in result)


@given(strategies.polygons)
def test_sizes(polygon: Polygon) -> None:
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes)

    assert all(len(element) == 3
               for element in result)


@given(strategies.polygons)
def test_points(polygon: Polygon) -> None:
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes)

    assert set(flatten(result)) == set(sum(holes, border))


@given(strategies.polygons)
def test_edges(polygon: Polygon) -> None:
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes)

    assert (set(flatten(map(contour_to_segments, result)))
            >= set(sum(map(contour_to_segments, holes),
                       contour_to_segments(border))))


@given(strategies.polygons)
def test_boundary(polygon: Polygon) -> None:
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes)

    assert (to_boundary_endpoints(result)
            == set(map(frozenset, sum(map(contour_to_segments, holes),
                                      contour_to_segments(border)))))
