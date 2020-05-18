from typing import Tuple

from hypothesis import strategies
from hypothesis_geometry import planar

from sect.core.utils import contour_to_segments
from sect.hints import (Contour,
                        Coordinate,
                        Multisegment,
                        Point)
from tests.strategies import coordinates_strategies
from tests.utils import Strategy


def to_multisegments(coordinates: Strategy[Coordinate]
                     ) -> Strategy[Multisegment]:
    return planar.contours(coordinates).map(contour_to_segments)


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
