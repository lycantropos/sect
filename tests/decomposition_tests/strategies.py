from functools import partial
from typing import Tuple

from hypothesis import strategies
from hypothesis_geometry import planar

from sect.hints import (Contour,
                        Coordinate,
                        Multisegment,
                        Point)
from tests.strategies import coordinates_strategies
from tests.utils import Strategy

to_multisegments = partial(planar.multisegments,
                           min_size=1)
multisegments = coordinates_strategies.flatmap(to_multisegments)


def to_multisegments_with_points(coordinates: Strategy[Coordinate]
                                 ) -> Strategy[Tuple[Multisegment, Point]]:
    return strategies.tuples(to_multisegments(coordinates),
                             planar.points(coordinates))


multisegments_with_points = (coordinates_strategies
                             .flatmap(to_multisegments_with_points))
polygons = coordinates_strategies.flatmap(planar.polygons)


def to_polygons_with_points(coordinates: Strategy[Coordinate]
                            ) -> Strategy[Tuple[Contour, Point]]:
    return strategies.tuples(planar.polygons(coordinates),
                             planar.points(coordinates))


polygons_with_points = coordinates_strategies.flatmap(to_polygons_with_points)
