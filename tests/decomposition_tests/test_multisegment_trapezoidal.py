from typing import Tuple

from hypothesis import given
from orient.planar import Relation

from sect.decomposition import (Graph,
                                Location,
                                multisegment_trapezoidal)
from sect.hints import (Multisegment,
                        Point)
from tests.utils import point_in_multisegment
from . import strategies


@given(strategies.multisegments)
def test_basic(multisegment: Multisegment) -> None:
    assert isinstance(multisegment_trapezoidal(multisegment), Graph)


@given(strategies.multisegments)
def test_height(multisegment: Multisegment) -> None:
    result = multisegment_trapezoidal(multisegment)

    assert 0 < result.height < 2 * len(multisegment)


@given(strategies.multisegments_with_points)
def test_contains(multisegment_with_point: Tuple[Multisegment, Point]) -> None:
    multisegment, point = multisegment_with_point

    result = multisegment_trapezoidal(multisegment)

    assert (point in result) is (point_in_multisegment(point, multisegment)
                                 is Relation.COMPONENT)


@given(strategies.multisegments_with_points)
def test_locate(multisegment_with_point: Tuple[Multisegment, Point]) -> None:
    multisegment, point = multisegment_with_point

    result = multisegment_trapezoidal(multisegment)

    location = result.locate(point)
    relation = point_in_multisegment(point, multisegment)
    assert (location is Location.EXTERIOR) is (relation is Relation.DISJOINT)
    assert (location is Location.BOUNDARY) is (relation is Relation.COMPONENT)
