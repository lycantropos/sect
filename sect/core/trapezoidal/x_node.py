from ground.base import Location
from ground.hints import Point
from reprit.base import generate_repr

from .edge import Edge
from .node import Node
from .trapezoid import Trapezoid


class XNode(Node):
    __slots__ = 'point', 'left', 'right'

    def __init__(self, point: Point, left: Node, right: Node) -> None:
        super().__init__()
        self.point = point
        self.left = left
        self.right = right
        self.left._add_parent(self)
        self.right._add_parent(self)

    __repr__ = generate_repr(__init__)

    @property
    def height(self) -> int:
        return max(self.left.height, self.right.height) + 1

    def locate(self, point: Point) -> Location:
        return (self.left.locate(point)
                if point < self.point
                else (self.right.locate(point)
                      if self.point < point
                      else Location.BOUNDARY))

    def search_edge(self, edge: Edge) -> Trapezoid:
        return (self.right
                if self.point <= edge.left
                else self.left).search_edge(edge)

    def _replace_child(self, current: Node, replacement: Node) -> None:
        if self.left is current:
            self.left = replacement
        else:
            self.right = replacement
