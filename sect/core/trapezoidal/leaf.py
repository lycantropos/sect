from ground.base import Location
from ground.hints import Point
from reprit.base import generate_repr

from .edge import Edge
from .node import Node
from .trapezoid import Trapezoid


class Leaf(Node):
    @property
    def above(self) -> Edge:
        return self.trapezoid.above

    @property
    def below(self) -> Edge:
        return self.trapezoid.below

    @property
    def height(self) -> int:
        return 0

    @property
    def left(self) -> Point:
        return self.trapezoid.left

    @property
    def right(self) -> Point:
        return self.trapezoid.right

    def locate(self, point: Point) -> Location:
        return (Location.INTERIOR
                if self.trapezoid.component
                else Location.EXTERIOR)

    def search_edge(self, edge: Edge) -> Trapezoid:
        return self.trapezoid

    __slots__ = 'trapezoid',

    def __init__(self,
                 left: Point,
                 right: Point,
                 below: Edge,
                 above: Edge) -> None:
        super().__init__()
        self.trapezoid = Trapezoid(left, right, below, above, self)

    __repr__ = generate_repr(__init__)

    def _replace_child(self, current: Node, replacement: Node) -> None:
        raise TypeError('Leaf has no children.')
