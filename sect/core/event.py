from reprlib import recursive_repr
from typing import Optional

from reprit.base import generate_repr

from sect.hints import (Point,
                        Segment)
from .quad_edge import QuadEdge


class Event:
    __slots__ = ('is_left_endpoint', 'start', 'complement', 'from_left',
                 'is_overlap', 'interior_to_left', 'other_interior_to_left',
                 'edge')

    def __init__(self,
                 is_left_endpoint: bool,
                 start: Point,
                 complement: Optional['Event'],
                 from_left_contour: bool,
                 interior_to_left: bool,
                 edge: Optional[QuadEdge] = None) -> None:
        self.is_left_endpoint = is_left_endpoint
        self.start = start
        self.complement = complement
        self.from_left = from_left_contour
        self.is_overlap = False
        self.interior_to_left = interior_to_left
        self.other_interior_to_left = False
        self.edge = edge

    __repr__ = recursive_repr()(generate_repr(__init__))

    @property
    def end(self) -> Point:
        """
        Returns end of the event's segment.

        >>> event = Event(True, (0, 0), None, False, False)
        >>> event.complement = Event(False, (1, 0), event, False, False)
        >>> event.end == (1, 0)
        True
        """
        return self.complement.start

    @property
    def in_intersection(self) -> bool:
        """
        Checks whether the event's segment belongs to intersection.

        >>> event = Event(True, (0, 0), None, False, False)
        >>> event.complement = Event(False, (1, 0), event, False, False)
        >>> event.in_intersection
        False
        """
        return self.other_interior_to_left or self.is_overlap

    @property
    def segment(self) -> Segment:
        """
        Returns segment of the event.

        >>> event = Event(True, (0, 0), None, False, False)
        >>> event.complement = Event(False, (1, 0), event, False, False)
        >>> event.segment == ((0, 0), (1, 0))
        True
        """
        return self.start, self.end
