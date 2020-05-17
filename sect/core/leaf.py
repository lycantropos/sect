from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)

from sect.hints import (Contour,
                        Point)
from .edge import Edge
from .node import Node
from .trapezoid import Trapezoid
from .utils import contour_to_segments


def point_within_region(point: Point, contour: Contour) -> bool:
    result = False
    _, point_y = point
    for edge in contour_to_segments(contour):
        start, end = edge
        (_, start_y), (_, end_y) = start, end
        if ((start_y > point_y) is not (end_y > point_y)
                and ((end_y > start_y) is (orientation(end, start, point)
                                           is Orientation.COUNTERCLOCKWISE))):
            result = not result
    return result


class Leaf(Node):
    __slots__ = 'trapezoid',

    def __init__(self, trapezoid: Trapezoid) -> None:
        super().__init__()
        self.trapezoid = trapezoid
        trapezoid.node = self

    __repr__ = generate_repr(__init__)

    def __contains__(self, point: Point) -> bool:
        return point in self.trapezoid

    def search_edge(self, edge: Edge) -> Trapezoid:
        return self.trapezoid

    def _replace_child(self, current: 'Node', replacement: 'Node') -> None:
        raise TypeError('Leaf has no children.')
