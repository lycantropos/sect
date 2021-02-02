from .core.trapezoidal.abcs import Graph
from .core.trapezoidal.graph import to_graph_cls
from .core.trapezoidal.hints import Shuffler
from .core.trapezoidal.location import Location
from .core.voronoi.abcs import Diagram
from .core.voronoi.diagram import to_diagram_cls

Diagram = Diagram
Graph = Graph
Location = Location
Shuffler = Shuffler

to_diagram_cls = to_diagram_cls
to_graph_cls = to_graph_cls
