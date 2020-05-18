from typing import Tuple

from hypothesis import strategies
from hypothesis_geometry import planar

from sect.hints import (Contour,
                        Coordinate,
                        Point)
from tests.strategies import coordinates_strategies
from tests.utils import Strategy

polygons = coordinates_strategies.flatmap(planar.polygons)


def to_polygons_with_points(coordinates: Strategy[Coordinate]
                            ) -> Strategy[Tuple[Contour, Point]]:
    return strategies.tuples(planar.polygons(coordinates),
                             planar.points(coordinates))


polygons_with_points = coordinates_strategies.flatmap(to_polygons_with_points)
