from typing import Tuple

from ground.base import (Context,
                         Location)
from ground.hints import Point
from hypothesis import given
from orient.planar import point_in_polygon

from sect.decomposition import Graph
from tests.utils import Polygon
from . import strategies


@given(strategies.contexts, strategies.polygons)
def test_basic(context: Context, polygon: Polygon) -> None:
    result = Graph.from_polygon(polygon,
                                context=context)

    assert isinstance(result, Graph)


@given(strategies.contexts, strategies.polygons_with_points)
def test_height(context: Context,
                polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = Graph.from_polygon(polygon,
                                context=context)

    assert 0 < result.height < 2 * (len(polygon.border.vertices)
                                    + sum(len(hole.vertices)
                                          for hole in polygon.holes))


@given(strategies.contexts, strategies.polygons_with_points)
def test_contains(context: Context,
                  polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = Graph.from_polygon(polygon,
                                context=context)

    assert ((point in result)
            is (point_in_polygon(point, polygon) is not Location.EXTERIOR))


@given(strategies.contexts, strategies.polygons_with_points)
def test_locate(context: Context,
                polygon_with_point: Tuple[Polygon, Point]) -> None:
    polygon, point = polygon_with_point

    result = Graph.from_polygon(polygon,
                                context=context)

    assert result.locate(point) is point_in_polygon(point, polygon)
