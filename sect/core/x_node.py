from reprit.base import generate_repr

from sect.hints import Point
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

    def __contains__(self, point: Point) -> bool:
        if point == self.point:
            return True
        elif self.point < point:
            return point in self.right
        else:
            return point in self.left

    def search_edge(self, edge: Edge) -> Trapezoid:
        if self.point <= edge.left:
            return self.right.search_edge(edge)
        else:
            return self.left.search_edge(edge)

    def _replace_child(self, current: Node, replacement: Node) -> None:
        if self.left is current:
            self.left = replacement
        else:
            self.right = replacement
        current._remove_parent(self)
        replacement._add_parent(self)
