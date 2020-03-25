from enum import (IntEnum,
                  unique)
from reprlib import recursive_repr
from typing import Optional

from reprit.base import generate_repr
from robust.linear import segments_intersection

from sect.hints import (Coordinate,
                        Point,
                        Segment)
from .subdivisional import QuadEdge


@unique
class EdgeKind(IntEnum):
    NORMAL = 0
    NON_CONTRIBUTING = 1
    SAME_TRANSITION = 2
    DIFFERENT_TRANSITION = 3


class Event:
    __slots__ = ('is_left_endpoint', 'start', 'complement',
                 'from_test_contour', 'in_out', 'other_in_out',
                 'edge_kind', 'edge')

    def __init__(self,
                 is_left_endpoint: bool,
                 start: Point,
                 complement: Optional['Event'],
                 from_test_contour: bool,
                 edge_kind: EdgeKind,
                 edge: Optional[QuadEdge] = None,
                 in_out: Optional[bool] = None,
                 other_in_out: Optional[bool] = None) -> None:
        self.is_left_endpoint = is_left_endpoint
        self.start = start
        self.complement = complement
        self.from_test_contour = from_test_contour
        self.edge_kind = edge_kind
        self.edge = edge
        self.in_out = in_out
        self.other_in_out = other_in_out

    __repr__ = recursive_repr()(generate_repr(__init__))

    @property
    def end(self) -> Point:
        return self.complement.start

    @property
    def is_vertical(self) -> bool:
        start_x, _ = self.start
        end_x, _ = self.end
        return start_x == end_x

    @property
    def is_horizontal(self) -> bool:
        _, start_y = self.start
        _, end_y = self.end
        return start_y == end_y

    @property
    def in_intersection(self) -> bool:
        edge_kind = self.edge_kind
        return (edge_kind is EdgeKind.NORMAL and not self.other_in_out
                or edge_kind is EdgeKind.SAME_TRANSITION)

    @property
    def segment(self) -> Segment:
        return self.start, self.end

    def y_at(self, x: Coordinate) -> Coordinate:
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
