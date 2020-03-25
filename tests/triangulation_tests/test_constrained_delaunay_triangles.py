from hypothesis import given
from hypothesis_geometry.hints import Polygon

from sect.triangulation import constrained_delaunay_triangles
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
