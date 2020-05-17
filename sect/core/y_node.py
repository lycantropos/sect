from typing import Optional

from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)

from sect.hints import (Point,
                        Segment)
from .node import Node
from .trapezoid import Trapezoid


class YNode(Node):
    __slots__ = 'segment', 'above', 'below'

    def __init__(self, segment: Segment, below: Node, above: Node) -> None:
        super().__init__()
        self.segment = segment
        self.below = below
        self.above = above
        self.below._add_parent(self)
        self.above._add_parent(self)

    __repr__ = generate_repr(__init__)

    def search_segment(self, segment: Segment) -> Optional[Trapezoid]:
        left, right = segment
        self_left, self_right = self.segment
        if left == self_left:
            # Coinciding left segment points.
            right_orientation = orientation(self_right, self_left, right)
            if right_orientation is Orientation.COUNTERCLOCKWISE:
                return self.above.search_segment(segment)
            elif right_orientation is Orientation.CLOCKWISE:
                return self.below.search_segment(segment)
            else:
                return None
        else:
            left_orientation = orientation(self_right, self_left, left)
            if left_orientation is Orientation.COUNTERCLOCKWISE:
                return self.above.search_segment(segment)
            elif left_orientation is Orientation.CLOCKWISE:
                return self.below.search_segment(segment)
            else:
                return None

    def _replace_child(self, current: 'Node', replacement: 'Node') -> None:
        if self.below is current:
            self.below = replacement
        else:
            self.above = replacement
        current._remove_parent(self)
        replacement._add_parent(self)
