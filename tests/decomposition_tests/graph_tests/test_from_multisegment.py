from typing import Tuple

from ground.base import (Context,
                         Location)
from ground.hints import (Multisegment,
                          Point)
from hypothesis import given
from orient.planar import point_in_multisegment

from sect.decomposition import Graph
from . import strategies


@given(strategies.contexts, strategies.multisegments)
def test_basic(context: Context, multisegment: Multisegment) -> None:
    result = Graph.from_multisegment(multisegment,
                                     context=context)

    assert isinstance(result, Graph)


@given(strategies.contexts, strategies.multisegments)
def test_height(context: Context, multisegment: Multisegment) -> None:
    result = Graph.from_multisegment(multisegment,
                                     context=context)

    assert 0 < result.height <= 2 * (len(multisegment.segments) + 2)


@given(strategies.contexts, strategies.multisegments_with_points)
def test_contains(context: Context,
                  multisegment_with_point: Tuple[Multisegment, Point]) -> None:
    multisegment, point = multisegment_with_point

    result = Graph.from_multisegment(multisegment,
                                     context=context)

    assert (point in result) is (point_in_multisegment(point, multisegment)
                                 is not Location.EXTERIOR)


@given(strategies.contexts, strategies.multisegments_with_points)
def test_locate(context: Context,
                multisegment_with_point: Tuple[Multisegment, Point]) -> None:
    multisegment, point = multisegment_with_point

    result = Graph.from_multisegment(multisegment,
                                     context=context)

    assert result.locate(point) is point_in_multisegment(point, multisegment)
