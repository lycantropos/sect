from ground.hints import (Multipoint,
                          Multisegment)

from .core.trapezoidal.abcs import Graph
from .core.trapezoidal.graph import to_graph_cls
from .core.trapezoidal.hints import Shuffler
from .core.trapezoidal.location import Location
from .core.voronoi.diagram import Diagram

Diagram = Diagram
Graph = Graph
Location = Location
Shuffler = Shuffler

to_graph_cls = to_graph_cls


def multipoint_voronoi(multipoint: Multipoint) -> Diagram:
    return Diagram.from_sources(multipoint.points, ())


def multisegment_voronoi(multisegment: Multisegment) -> Diagram:
    return Diagram.from_sources((), multisegment.segments)
