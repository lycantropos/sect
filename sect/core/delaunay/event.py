from __future__ import annotations

from abc import (ABC,
                 abstractmethod)
from reprlib import recursive_repr
from typing import Optional

from ground.hints import Point
from reprit.base import generate_repr

from .hints import SegmentEndpoints
from .quad_edge import QuadEdge


class Event(ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def end(self) -> Point:
        """Returns end of the event."""

    @property
    @abstractmethod
    def is_left(self) -> bool:
        """Checks if event's start corresponds to the leftmost endpoint."""

    @property
    @abstractmethod
    def start(self) -> Point:
        """Returns start of the event."""

    @property
    @abstractmethod
    def from_first(self) -> bool:
        """Checks if event is from left."""


class LeftEvent(Event):
    is_left = True

    @property
    def end(self) -> Point:
        return self.right.start

    @property
    def right(self) -> RightEvent:
        result = self._right
        assert result is not None
        return result

    @property
    def from_first(self) -> bool:
        return self._from_first

    @property
    def inside(self) -> bool:
        """
        Checks if the segment enclosed by
        or lies within the region of the intersection.
        """
        return self.other_interior_to_left and not self.is_overlap

    @property
    def start(self) -> Point:
        return self._start

    def divide(self, point: Point) -> LeftEvent:
        tail = self.right.left = LeftEvent(point, self.right, True,
                                           self.interior_to_left, self.edge)
        self._right = RightEvent(point, self)
        return tail

    @classmethod
    def from_segment_endpoints(
            cls,
            endpoints: SegmentEndpoints,
            from_first: bool,
            is_counterclockwise_contour: bool
    ) -> LeftEvent:
        start, end = endpoints
        interior_to_left = is_counterclockwise_contour
        if start > end:
            start, end = end, start
            interior_to_left = not interior_to_left
        result = cls(start, None, from_first, interior_to_left)
        result._right = RightEvent(end, result)
        return result

    _right: Optional[RightEvent]

    __slots__ = ('edge', 'interior_to_left', 'is_overlap',
                 'other_interior_to_left', '_right', '_from_first', '_start')

    def __init__(self,
                 start: Point,
                 right: Optional[RightEvent],
                 from_first: bool,
                 interior_to_left: bool,
                 edge: Optional[QuadEdge] = None) -> None:
        self._from_first, self._right, self._start = from_first, right, start
        self.interior_to_left = interior_to_left
        self.edge = edge
        self.is_overlap = self.other_interior_to_left = False

    __repr__ = recursive_repr()(generate_repr(__init__))


class RightEvent(Event):
    is_left = False
    __slots__ = 'left', '_start'

    def __init__(self, start: Point, left: LeftEvent) -> None:
        self.left, self._start = left, start

    __repr__ = recursive_repr()(generate_repr(__init__))

    @property
    def end(self) -> Point:
        return self.left.start

    @property
    def from_first(self) -> bool:
        return self.left.from_first

    @property
    def start(self) -> Point:
        return self._start
