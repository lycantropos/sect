from reprit.base import generate_repr

from sect.hints import (Point,
                        Segment)
from .node import Node
from .trapezoid import Trapezoid


class Leaf(Node):
    __slots__ = 'trapezoid',

    def __init__(self, trapezoid: Trapezoid) -> None:
        super().__init__()
        self.trapezoid = trapezoid
        trapezoid.trapezoid_node = self

    __repr__ = generate_repr(__init__)

    def search_segment(self, segment: Segment) -> Trapezoid:
        return self.trapezoid

    def search_point(self, point: Point) -> 'Node':
        return self

    def _replace_child(self, current: 'Node', replacement: 'Node') -> None:
        raise TypeError('Leaf has no children.')
