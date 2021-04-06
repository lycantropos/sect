from typing import (Tuple,
                    Type)

from ground.base import Relation
from ground.hints import Point
from hypothesis import given
from orient.planar import point_in_polygon

from sect.decomposition import (Graph,
                                Location)
from tests.utils import Polygon
from . import strategies


@given(strategies.graph_classes, strategies.polygons)
def test_basic(graph_cls: Type[Graph],
               polygon: Polygon) -> None:
    assert isinstance(graph_cls.from_polygon(polygon), Graph)


@given(strategies.graph_classes, strategies.polygons_with_points)
def test_height(graph_cls: Type[Graph],
                polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = graph_cls.from_polygon(polygon)

    assert 0 < result.height < 2 * (len(polygon.border.vertices)
                                    + sum(len(hole.vertices)
                                          for hole in polygon.holes))


@given(strategies.graph_classes, strategies.polygons_with_points)
def test_contains(graph_cls: Type[Graph],
                  polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = graph_cls.from_polygon(polygon)

    assert ((point in result)
            is (point_in_polygon(point, polygon) is not Relation.DISJOINT))


@given(strategies.graph_classes, strategies.polygons_with_points)
def test_locate(graph_cls: Type[Graph],
                polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = graph_cls.from_polygon(polygon)

    location = result.locate(point)
    relation = point_in_polygon(point, polygon)
    assert (location is Location.EXTERIOR) is (relation is Relation.DISJOINT)
    assert (location is Location.BOUNDARY) is (relation is Relation.COMPONENT)
    assert (location is Location.INTERIOR) is (relation is Relation.WITHIN)
