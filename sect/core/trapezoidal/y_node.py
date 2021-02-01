from ground.hints import Point
from reprit.base import generate_repr

from sect.core.utils import Orientation
from .edge import Edge
from .location import Location
from .node import Node
from .trapezoid import Trapezoid


class YNode(Node):
    __slots__ = 'edge', 'above', 'below'

    def __init__(self, edge: Edge, below: Node, above: Node) -> None:
        super().__init__()
        self.edge = edge
        self.below = below
        self.above = above
        self.below._add_parent(self)
        self.above._add_parent(self)

    __repr__ = generate_repr(__init__)

    @property
    def height(self) -> int:
        return max(self.below.height, self.above.height) + 1

    def locate(self, point: Point) -> Location:
        point_orientation = self.edge.orientation_of(point)
        return (self.above.locate(point)
                if point_orientation is Orientation.COUNTERCLOCKWISE
                else (self.below.locate(point)
                      if point_orientation is Orientation.CLOCKWISE
                      else Location.BOUNDARY))

    def search_edge(self, edge: Edge) -> Trapezoid:
        return (self.above
                if self.edge < edge
                else self.below).search_edge(edge)

    def _replace_child(self, current: Node, replacement: Node) -> None:
        if self.below is current:
            self.below = replacement
        else:
            self.above = replacement
