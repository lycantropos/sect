from __future__ import annotations

from typing import Any

from ground.base import (Context,
                         Orientation)
from ground.hints import Point
from reprit.base import generate_repr


class Edge:
    @classmethod
    def from_endpoints(cls,
                       left: Point,
                       right: Point,
                       interior_to_left: bool,
                       context: Context) -> Edge:
        """Constructs edge given its endpoints."""
        return cls(left, right, interior_to_left, context)

    def orientation_of(self, point: Point) -> Orientation:
        """Returns orientation of the point relative to the edge."""
        return self.context.angle_orientation(self.left, self.right, point)

    __slots__ = 'context', 'interior_to_left', 'left', 'right'

    def __init__(self,
                 left: Point,
                 right: Point,
                 interior_to_left: bool,
                 context: Context) -> None:
        assert left < right, 'Incorrect endpoints order'
        self.context, self.interior_to_left, self.left, self.right = (
            context, interior_to_left, left, right
        )

    def __lt__(self, other: Edge) -> Any:
        """Checks if the edge is lower than the other."""
        other_left_orientation = self.orientation_of(other.left)
        other_right_orientation = self.orientation_of(other.right)
        if other_left_orientation is other_right_orientation:
            return other_left_orientation is Orientation.COUNTERCLOCKWISE
        elif other_left_orientation is Orientation.COLLINEAR:
            return other_right_orientation is Orientation.COUNTERCLOCKWISE
        left_orientation = other.orientation_of(self.left)
        right_orientation = other.orientation_of(self.right)
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

    __repr__ = generate_repr(__init__)
