from ground.hints import (Multipoint,
                          Multisegment)

from .core.trapezoidal.graph import Graph
from .core.trapezoidal.location import Location
from .core.voronoi.diagram import Diagram

Diagram = Diagram
Graph = Graph
Location = Location


def multipoint_voronoi(multipoint: Multipoint) -> Diagram:
    return Diagram.from_sources(multipoint.points, ())


def multisegment_voronoi(multisegment: Multisegment) -> Diagram:
    return Diagram.from_sources((), multisegment.segments)
