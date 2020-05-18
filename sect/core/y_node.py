from typing import Optional

from reprit.base import generate_repr
from robust.angular import Orientation

from sect.hints import Point
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

    def locate(self, point: Point) -> Location:
        point_orientation = self.edge.orientation_with(point)
        if point_orientation is Orientation.COUNTERCLOCKWISE:
            return self.above.locate(point)
        elif point_orientation is Orientation.CLOCKWISE:
            return self.below.locate(point)
        else:
            return Location.BOUNDARY

    __repr__ = generate_repr(__init__)

    def search_edge(self, edge: Edge) -> Optional[Trapezoid]:
        if edge.left == self.edge.left:
            # Coinciding left edge points.
            right_orientation = self.edge.orientation_with(edge.right)
            if right_orientation is Orientation.COUNTERCLOCKWISE:
                return self.above.search_edge(edge)
            elif right_orientation is Orientation.CLOCKWISE:
                return self.below.search_edge(edge)
            else:
                return None
        else:
            left_orientation = self.edge.orientation_with(edge.left)
            if left_orientation is Orientation.COUNTERCLOCKWISE:
                return self.above.search_edge(edge)
            elif left_orientation is Orientation.CLOCKWISE:
                return self.below.search_edge(edge)
            else:
                return None

    def _replace_child(self, current: 'Node', replacement: 'Node') -> None:
        if self.below is current:
            self.below = replacement
        else:
            self.above = replacement
        current._remove_parent(self)
        replacement._add_parent(self)
