from functools import partial

from bentley_ottmann.planar import (segments_cross_or_overlap,
                                    segments_intersect)
from clipping.planar import segments_to_multisegment
from ground.base import get_context
from ground.hints import Coordinate
from hypothesis import strategies
from hypothesis_geometry import planar

from sect.decomposition import to_diagram_cls
from sect.triangulation import to_triangulation_cls
from tests.strategies import (coordinates_strategies,
                              rational_coordinates_strategies)
from tests.utils import (Multisegment,
                         Strategy)

diagram_classes = strategies.just(to_diagram_cls(get_context()))
triangulation_classes = strategies.just(to_triangulation_cls(get_context()))
multipoints = coordinates_strategies.flatmap(planar.multipoints)
rational_contours = (rational_coordinates_strategies
                     .flatmap(planar.contours))
empty_multisegments = strategies.builds(Multisegment, strategies.builds(list))


def coordinates_to_multisegments(coordinates: Strategy[Coordinate],
                                 *,
                                 min_size: int = 0) -> Strategy[Multisegment]:
    return (strategies.lists(planar.segments(coordinates),
                             min_size=min_size,
                             max_size=5)
            .map(segments_to_multisegment))


rational_multisegments = (rational_coordinates_strategies
                          .flatmap(coordinates_to_multisegments))
non_empty_rational_multisegments = (
    (rational_coordinates_strategies
     .flatmap(partial(coordinates_to_multisegments,
                      min_size=1))))
