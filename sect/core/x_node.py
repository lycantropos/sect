from reprit.base import generate_repr

from sect.hints import (Point,
                        Segment)
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

    def search_segment(self, segment: Segment) -> Trapezoid:
        left, _ = segment
        if self.point <= left:
            return self.right.search_segment(segment)
        else:
            return self.left.search_segment(segment)

    def _replace_child(self, current: Node, replacement: Node) -> None:
        if self.left is current:
            self.left = replacement
        else:
            self.right = replacement
        current._remove_parent(self)
        replacement._add_parent(self)
