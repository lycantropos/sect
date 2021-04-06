from typing import (Tuple,
                    Type)

from ground.base import Relation
from ground.hints import (Multisegment,
                          Point)
from hypothesis import given

from sect.decomposition import (Graph,
                                Location)
from tests.utils import point_in_multisegment
from . import strategies


@given(strategies.graph_classes, strategies.non_empty_multisegments)
def test_basic(graph_cls: Type[Graph],
               multisegment: Multisegment) -> None:
    assert isinstance(graph_cls.from_multisegment(multisegment), graph_cls)


@given(strategies.graph_classes, strategies.non_empty_multisegments)
def test_height(graph_cls: Type[Graph],
                multisegment: Multisegment) -> None:
    result = graph_cls.from_multisegment(multisegment)

    assert 0 < result.height <= 2 * (len(multisegment.segments) + 2)


@given(strategies.graph_classes,
       strategies.non_empty_multisegments_with_points)
def test_contains(graph_cls: Type[Graph],
                  multisegment_with_point: Tuple[Multisegment, Point]) -> None:
    multisegment, point = multisegment_with_point

    result = graph_cls.from_multisegment(multisegment)

    assert (point in result) is (point_in_multisegment(point, multisegment)
                                 is Relation.COMPONENT)


@given(strategies.graph_classes,
       strategies.non_empty_multisegments_with_points)
def test_locate(graph_cls: Type[Graph],
                multisegment_with_point: Tuple[Multisegment, Point]) -> None:
    multisegment, point = multisegment_with_point

    result = graph_cls.from_multisegment(multisegment)

    location = result.locate(point)
    relation = point_in_multisegment(point, multisegment)
    assert (location is Location.EXTERIOR) is (relation is Relation.DISJOINT)
    assert (location is Location.BOUNDARY) is (relation is Relation.COMPONENT)
