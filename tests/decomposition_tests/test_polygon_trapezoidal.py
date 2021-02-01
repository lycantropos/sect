from typing import Tuple

from ground.hints import Point
from hypothesis import given
from orient.planar import (Relation,
                           point_in_polygon)

from sect.decomposition import (Graph,
                                Location,
                                polygon_trapezoidal)
from tests.utils import Polygon
from . import strategies


@given(strategies.polygons)
def test_basic(polygon: Polygon) -> None:
    assert isinstance(polygon_trapezoidal(polygon), Graph)


@given(strategies.polygons_with_points)
def test_height(polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = polygon_trapezoidal(polygon)

    assert 0 < result.height < 2 * (len(polygon.border.vertices)
                                    + sum(len(hole.vertices)
                                          for hole in polygon.holes))


@given(strategies.polygons_with_points)
def test_contains(polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = polygon_trapezoidal(polygon)

    assert ((point in result)
            is (point_in_polygon(point, polygon) is not Relation.DISJOINT))


@given(strategies.polygons_with_points)
def test_locate(polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = polygon_trapezoidal(polygon)

    location = result.locate(point)
    relation = point_in_polygon(point, polygon)
    assert (location is Location.EXTERIOR) is (relation is Relation.DISJOINT)
    assert (location is Location.BOUNDARY) is (relation is Relation.COMPONENT)
    assert (location is Location.INTERIOR) is (relation is Relation.WITHIN)
