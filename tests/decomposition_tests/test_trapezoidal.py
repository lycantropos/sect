from typing import Tuple

from hypothesis import given
from orient.planar import (Relation,
                           point_in_region)

from sect.core.location import Location
from sect.decomposition import (Node,
                                trapezoidal)
from sect.hints import (Contour,
                        Point)
from . import strategies


@given(strategies.contours)
def test_basic(contour: Contour) -> None:
    assert isinstance(trapezoidal(contour), Node)


@given(strategies.contours_with_points)
def test_contains(contour_with_point: Tuple[Contour, Point]) -> None:
    contour, point = contour_with_point

    result = trapezoidal(contour)

    assert ((point in result)
            is (point_in_region(point, contour) is not Relation.DISJOINT))


@given(strategies.contours_with_points)
def test_locate(contour_with_point: Tuple[Contour, Point]) -> None:
    contour, point = contour_with_point

    result = trapezoidal(contour)

    location = result.locate(point)
    relation = point_in_region(point, contour)
    assert (location is Location.EXTERIOR) is (relation is Relation.DISJOINT)
    assert (location is Location.BOUNDARY) is (relation is Relation.COMPONENT)
    assert (location is Location.INTERIOR) is (relation is Relation.WITHIN)
