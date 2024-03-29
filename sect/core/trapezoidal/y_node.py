from ground.base import (Location,
                         Orientation)
from ground.hints import Point
from reprit.base import generate_repr

from .edge import Edge
from .node import Node
from .trapezoid import Trapezoid


class YNode(Node):
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

    __slots__ = 'above', 'below', 'edge'

    def __init__(self, edge: Edge, below: Node, above: Node) -> None:
        super().__init__()
        self.above, self.below, self.edge = above, below, edge
        self.above._add_parent(self)
        self.below._add_parent(self)

    __repr__ = generate_repr(__init__)

    def _replace_child(self, current: Node, replacement: Node) -> None:
        if self.below is current:
            self.below = replacement
        else:
            self.above = replacement
