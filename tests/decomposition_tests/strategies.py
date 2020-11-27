from functools import partial
from typing import Tuple

from hypothesis import strategies
from hypothesis_geometry import planar

from sect.hints import (Contour,
                        Coordinate,
                        Multisegment,
                        Point)
from tests.strategies import (coordinates_strategies,
                              rational_coordinates_strategies)
from tests.utils import Strategy

multipoints = coordinates_strategies.flatmap(planar.contours)
rational_multipoints = rational_coordinates_strategies.flatmap(planar.contours)
to_non_empty_multisegments = partial(planar.multisegments,
                                     min_size=1)
non_empty_multisegments = (coordinates_strategies
                           .flatmap(to_non_empty_multisegments))


def to_non_empty_multisegments_with_points(coordinates: Strategy[Coordinate]
                                           ) -> Strategy[Tuple[Multisegment,
                                                               Point]]:
    return strategies.tuples(to_non_empty_multisegments(coordinates),
                             planar.points(coordinates))


non_empty_multisegments_with_points = (
    coordinates_strategies.flatmap(to_non_empty_multisegments_with_points))
polygons = coordinates_strategies.flatmap(planar.polygons)


def to_polygons_with_points(coordinates: Strategy[Coordinate]
                            ) -> Strategy[Tuple[Contour, Point]]:
    return strategies.tuples(planar.polygons(coordinates),
                             planar.points(coordinates))


polygons_with_points = coordinates_strategies.flatmap(to_polygons_with_points)
