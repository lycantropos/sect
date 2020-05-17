from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)

from sect.hints import Point


class Edge:
    __slots__ = 'left', 'right', 'interior_to_the_left'

    def __init__(self,
                 left: Point,
                 right: Point,
                 interior_to_the_left: bool) -> None:
        assert left < right, 'Incorrect endpoints order'
        self.left = left
        self.right = right
        self.interior_to_the_left = interior_to_the_left

    __repr__ = generate_repr(__init__)

    def orientation_with(self, point: Point) -> Orientation:
        return orientation(self.right, self.left, point)
