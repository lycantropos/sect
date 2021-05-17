from reprlib import recursive_repr
from typing import Optional

from ground.hints import Point
from reprit.base import generate_repr

from .quad_edge import QuadEdge


class Event:
    __slots__ = ('edge', 'from_left', 'interior_to_left', 'is_left_endpoint',
                 'is_overlap', 'opposite', 'other_interior_to_left', 'start')

    def __init__(self,
                 start: Point,
                 opposite: Optional['Event'],
                 is_left_endpoint: bool,
                 from_left: bool,
                 interior_to_left: bool,
                 edge: Optional[QuadEdge] = None) -> None:
        self.is_left_endpoint, self.opposite, self.start = (is_left_endpoint,
                                                            opposite, start)
        self.from_left, self.interior_to_left, self.other_interior_to_left = (
            from_left, interior_to_left, False)
        self.is_overlap = False
        self.edge = edge

    __repr__ = recursive_repr()(generate_repr(__init__))

    @property
    def end(self) -> Point:
        """Returns end of the event's segment."""
        return self.opposite.start

    @property
    def inside(self) -> bool:
        """
        Checks if the segment enclosed by
        or lies within the region of the intersection.
        """
        return self.other_interior_to_left and not self.is_overlap

    def divide(self, point: Point) -> 'Event':
        tail = self.opposite.opposite = Event(point, self.opposite, True,
                                              self.from_left,
                                              self.interior_to_left, self.edge)
        self.opposite = Event(point, self, False, self.from_left,
                              self.interior_to_left, self.edge)
        return tail
