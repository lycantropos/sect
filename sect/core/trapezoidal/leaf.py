from ground.hints import Point
from reprit.base import generate_repr

from .abcs import Node
from .edge import Edge
from .location import Location
from .trapezoid import Trapezoid


class Leaf(Node):
    __slots__ = 'trapezoid',

    def __init__(self, trapezoid: Trapezoid) -> None:
        super().__init__()
        self.trapezoid = trapezoid
        trapezoid.node = self

    __repr__ = generate_repr(__init__)

    @property
    def height(self) -> int:
        return 0

    def locate(self, point: Point) -> Location:
        return (Location.INTERIOR
                if self.trapezoid.component
                else Location.EXTERIOR)

    def search_edge(self, edge: Edge) -> Trapezoid:
        return self.trapezoid

    def _replace_child(self, current: Node, replacement: Node) -> None:
        raise TypeError('Leaf has no children.')
