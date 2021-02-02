from ground.base import get_context
from hypothesis import strategies
from hypothesis_geometry import planar

from sect.triangulation import to_triangulation_cls
from tests.strategies import (coordinates_strategies,
                              rational_coordinates_strategies)
from tests.utils import Multisegment

triangulation_classes = strategies.just(to_triangulation_cls(get_context()))
multipoints = coordinates_strategies.flatmap(planar.multipoints)
rational_contours = (rational_coordinates_strategies
                     .flatmap(planar.contours))
empty_multisegments = strategies.builds(Multisegment, strategies.builds(list))
rational_multisegments = (rational_coordinates_strategies
                          .flatmap(planar.multisegments))
