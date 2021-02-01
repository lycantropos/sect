from functools import partial
from typing import Tuple

from ground.base import get_context
from ground.hints import Coordinate
from hypothesis import strategies
from hypothesis_geometry import planar

from sect.triangulation import to_triangulation_cls
from tests.strategies import (coordinates_strategies,
                              rational_coordinates_strategies)
from tests.utils import (Multisegment,
                         Point,
                         Polygon,
                         Strategy)

triangulation_classes = strategies.just(to_triangulation_cls(get_context()))
multipoints = coordinates_strategies.flatmap(planar.multipoints)
rational_contours = (rational_coordinates_strategies
                     .flatmap(planar.contours))
empty_multisegments = strategies.builds(Multisegment, strategies.builds(list))
rational_multisegments = (rational_coordinates_strategies
                          .flatmap(planar.multisegments))
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
                            ) -> Strategy[Tuple[Polygon, Point]]:
    return strategies.tuples(planar.polygons(coordinates),
                             planar.points(coordinates))


polygons_with_points = coordinates_strategies.flatmap(to_polygons_with_points)
