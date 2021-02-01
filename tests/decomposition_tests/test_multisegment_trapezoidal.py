from typing import Tuple

from ground.hints import (Multisegment,
                          Point)
from hypothesis import given
from orient.planar import Relation

from sect.decomposition import (Graph,
                                Location,
                                multisegment_trapezoidal)
from tests.utils import point_in_multisegment
from . import strategies


@given(strategies.non_empty_multisegments)
def test_basic(multisegment: Multisegment) -> None:
    assert isinstance(multisegment_trapezoidal(multisegment), Graph)


@given(strategies.non_empty_multisegments)
def test_height(multisegment: Multisegment) -> None:
    result = multisegment_trapezoidal(multisegment)

    assert 0 < result.height <= 2 * (len(multisegment.segments) + 2)


@given(strategies.non_empty_multisegments_with_points)
def test_contains(multisegment_with_point: Tuple[Multisegment, Point]) -> None:
    multisegment, point = multisegment_with_point

    result = multisegment_trapezoidal(multisegment)

    assert (point in result) is (point_in_multisegment(point, multisegment)
                                 is Relation.COMPONENT)


@given(strategies.non_empty_multisegments_with_points)
def test_locate(multisegment_with_point: Tuple[Multisegment, Point]) -> None:
    multisegment, point = multisegment_with_point

    result = multisegment_trapezoidal(multisegment)

    location = result.locate(point)
    relation = point_in_multisegment(point, multisegment)
    assert (location is Location.EXTERIOR) is (relation is Relation.DISJOINT)
    assert (location is Location.BOUNDARY) is (relation is Relation.COMPONENT)
