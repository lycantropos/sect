from functools import partial
from typing import Tuple

from ground.base import get_context
from ground.hints import Scalar
from hypothesis import strategies
from hypothesis_geometry import planar

from tests.strategies import coordinates_strategies
from tests.utils import (Multisegment,
                         Point,
                         Polygon,
                         Strategy)

contexts = strategies.just(get_context())
multisegments = coordinates_strategies.flatmap(planar.multisegments)


def to_multisegments_with_points(coordinates: Strategy[Scalar]
                                 ) -> Strategy[Tuple[Multisegment, Point]]:
    return strategies.tuples(planar.multisegments(coordinates),
                             planar.points(coordinates))


multisegments_with_points = (coordinates_strategies
                             .flatmap(to_multisegments_with_points))
polygons = coordinates_strategies.flatmap(planar.polygons)


def to_polygons_with_points(coordinates: Strategy[Scalar]
                            ) -> Strategy[Tuple[Polygon, Point]]:
    return strategies.tuples(planar.polygons(coordinates),
                             planar.points(coordinates))


polygons_with_points = coordinates_strategies.flatmap(to_polygons_with_points)
