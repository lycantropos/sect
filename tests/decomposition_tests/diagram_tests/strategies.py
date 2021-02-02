from ground.base import get_context
from hypothesis import strategies
from hypothesis_geometry import planar

from sect.decomposition import to_diagram_cls
from sect.triangulation import to_triangulation_cls
from tests.strategies import (coordinates_strategies,
                              rational_coordinates_strategies)
from tests.utils import Multisegment

diagram_classes = strategies.just(to_diagram_cls(get_context()))
triangulation_classes = strategies.just(to_triangulation_cls(get_context()))
multipoints = coordinates_strategies.flatmap(planar.multipoints)
rational_contours = (rational_coordinates_strategies
                     .flatmap(planar.contours))
empty_multisegments = strategies.builds(Multisegment, strategies.builds(list))
rational_multisegments = (rational_coordinates_strategies
                          .flatmap(planar.multisegments))
