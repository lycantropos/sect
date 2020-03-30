from itertools import chain

from hypothesis import given
from hypothesis_geometry.hints import Polygon

from sect.core.utils import contour_to_segments
from sect.hints import Contour
from sect.triangulation import (constrained_delaunay_triangles,
                                delaunay_triangles)
from tests.utils import (is_convex_contour,
                         to_boundary_endpoints)
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

    assert set(chain.from_iterable(result)) == set(sum(holes, border))


@given(strategies.polygons)
def test_edges(polygon: Polygon) -> None:
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes)

    assert (set(chain.from_iterable(map(contour_to_segments, result)))
            >= set(sum(map(contour_to_segments, holes),
                       contour_to_segments(border))))


@given(strategies.polygons)
def test_boundary(polygon: Polygon) -> None:
    border, holes = polygon

    result = constrained_delaunay_triangles(border, holes)

    assert (to_boundary_endpoints(result)
            == set(map(frozenset, sum(map(contour_to_segments, holes),
                                      contour_to_segments(border)))))


@given(strategies.contours)
def test_connection_with_delaunay_triangles(contour: Contour) -> None:
    result = constrained_delaunay_triangles(contour)

    assert ((result == delaunay_triangles(contour))
            is is_convex_contour(contour))
