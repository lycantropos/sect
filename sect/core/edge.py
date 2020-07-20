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

    def __lt__(self, other: 'Edge') -> bool:
        """
        Checks if the edge is lower than the other.

        >>> horizontal = Edge((0, 0), (2, 0), False)
        >>> diagonal = Edge((1, 1), (2, 2), False)
        >>> vertical = Edge((0, 0), (0, 2), False)
        >>> all(not (edge < edge) for edge in (horizontal, diagonal, vertical))
        True
        >>> horizontal < vertical
        True
        >>> horizontal < diagonal < vertical
        True
        """
        other_left_orientation = self.orientation_with(other.left)
        other_right_orientation = self.orientation_with(other.right)
        if other_left_orientation is other_right_orientation:
            return other_left_orientation is Orientation.COUNTERCLOCKWISE
        elif other_left_orientation is Orientation.COLLINEAR:
            return other_right_orientation is Orientation.COUNTERCLOCKWISE
        left_orientation = other.orientation_with(self.left)
        right_orientation = other.orientation_with(self.right)
        if left_orientation is right_orientation:
            return left_orientation is Orientation.CLOCKWISE
        elif left_orientation is Orientation.COLLINEAR:
            return right_orientation is Orientation.CLOCKWISE
        elif other_right_orientation is Orientation.COLLINEAR:
            return other_left_orientation is Orientation.COUNTERCLOCKWISE
        else:
            return (left_orientation is Orientation.CLOCKWISE
                    if right_orientation is Orientation.COLLINEAR
                    # crossing edges are incomparable
                    else NotImplemented)

    def orientation_with(self, point: Point) -> Orientation:
        return orientation(self.right, self.left, point)
