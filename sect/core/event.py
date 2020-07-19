from enum import (IntEnum,
                  unique)
from reprlib import recursive_repr
from typing import Optional

from reprit.base import generate_repr
from robust.linear import segments_intersection

from sect.hints import (Coordinate,
                        Point,
                        Segment)
from .quad_edge import QuadEdge


@unique
class EdgeKind(IntEnum):
    NORMAL = 0
    NON_CONTRIBUTING = 1
    SAME_TRANSITION = 2
    DIFFERENT_TRANSITION = 3


class Event:
    __slots__ = ('is_left_endpoint', 'start', 'complement', 'from_left',
                 'edge_kind', 'edge', 'in_out', 'other_in_out')

    def __init__(self,
                 is_left_endpoint: bool,
                 start: Point,
                 complement: Optional['Event'],
                 from_left_contour: bool,
                 edge_kind: EdgeKind,
                 edge: Optional[QuadEdge] = None,
                 in_out: Optional[bool] = None,
                 other_in_out: Optional[bool] = None) -> None:
        self.is_left_endpoint = is_left_endpoint
        self.start = start
        self.complement = complement
        self.from_left = from_left_contour
        self.edge_kind = edge_kind
        self.edge = edge
        self.in_out = in_out
        self.other_in_out = other_in_out

    __repr__ = recursive_repr()(generate_repr(__init__))

    @property
    def end(self) -> Point:
        """
        Returns end of the event's segment.

        >>> event = Event(True, (0, 0), None, False, EdgeKind.NORMAL)
        >>> event.complement = Event(False, (1, 0), event, False,
        ...                          EdgeKind.NORMAL)
        >>> event.end == (1, 0)
        True
        """
        return self.complement.start

    @property
    def is_vertical(self) -> bool:
        """
        Checks whether the event's segment aligned with y-axis.

        >>> event = Event(True, (0, 0), None, False, EdgeKind.NORMAL)
        >>> event.complement = Event(False, (0, 1), event, False,
        ...                          EdgeKind.NORMAL)
        >>> event.is_vertical
        True
        """
        start_x, _ = self.start
        end_x, _ = self.end
        return start_x == end_x

    @property
    def is_horizontal(self) -> bool:
        """
        Checks whether the event's segment aligned with x-axis.

        >>> event = Event(True, (0, 0), None, False, EdgeKind.NORMAL)
        >>> event.complement = Event(False, (1, 0), event, False,
        ...                          EdgeKind.NORMAL)
        >>> event.is_horizontal
        True
        """
        _, start_y = self.start
        _, end_y = self.end
        return start_y == end_y

    @property
    def in_intersection(self) -> bool:
        """
        Checks whether the event's segment belongs to intersection.

        >>> event = Event(True, (0, 0), None, False, EdgeKind.NORMAL)
        >>> event.complement = Event(False, (1, 0), event, False,
        ...                          EdgeKind.NORMAL)
        >>> event.in_intersection
        True
        """
        edge_kind = self.edge_kind
        return (edge_kind is EdgeKind.NORMAL and not self.other_in_out
                or edge_kind is EdgeKind.SAME_TRANSITION)

    @property
    def segment(self) -> Segment:
        """
        Returns segment of the event.

        >>> event = Event(True, (0, 0), None, False, EdgeKind.NORMAL)
        >>> event.complement = Event(False, (1, 0), event, False,
        ...                          EdgeKind.NORMAL)
        >>> event.segment == ((0, 0), (1, 0))
        True
        """
        return self.start, self.end

    def y_at(self, x: Coordinate) -> Coordinate:
        """
        Returns y-coordinate of the segment point by the x-coordinate.

        >>> event = Event(True, (0, 0), None, False, EdgeKind.NORMAL)
        >>> event.complement = Event(False, (1, 1), event, False,
        ...                          EdgeKind.NORMAL)
        >>> event.y_at(0) == 0
        True
        >>> event.y_at(1) == 1
        True
        """
        if self.is_vertical or self.is_horizontal:
            _, start_y = self.start
            return start_y
        else:
            start_x, start_y = self.start
            if x == start_x:
                return start_y
            end_x, end_y = self.end
            if x == end_x:
                return end_y
            _, result = segments_intersection(self.segment,
                                              ((x, start_y), (x, end_y)))
            return result
