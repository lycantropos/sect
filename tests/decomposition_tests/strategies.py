from typing import Tuple

from hypothesis import strategies
from hypothesis_geometry import planar

from sect.hints import (Contour,
                        Coordinate,
                        Point)
from tests.strategies import coordinates_strategies
from tests.utils import Strategy

contours = coordinates_strategies.flatmap(planar.contours)


def to_contours_with_points(coordinates: Strategy[Coordinate]
                            ) -> Strategy[Tuple[Contour, Point]]:
    return strategies.tuples(planar.contours(coordinates),
                             planar.points(coordinates))


contours_with_points = coordinates_strategies.flatmap(to_contours_with_points)
