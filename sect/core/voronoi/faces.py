from typing import Optional

from reprit.base import generate_repr
from symba.base import Expression

from .enums import (GeometryCategory,
                    SourceCategory)
from .hints import Source


class Cell:
    __slots__ = 'source', 'source_category', 'incident_edge'

    def __init__(self,
                 source: Source,
                 source_category: SourceCategory) -> None:
        self.source, self.source_category = source, source_category
        self.incident_edge = None  # type: Optional[Edge]

    __repr__ = generate_repr(__init__)

    @property
    def contains_point(self) -> bool:
        return self.source_category.belongs(GeometryCategory.POINT)

    @property
    def contains_segment(self) -> bool:
        return self.source_category.belongs(GeometryCategory.SEGMENT)

    @property
    def is_degenerate(self) -> bool:
        return self.incident_edge is None


class Vertex:
    __slots__ = 'x', 'y', 'incident_edge'

    def __init__(self, x: Expression, y: Expression) -> None:
        self.x, self.y = x, y
        self.incident_edge = None  # type: Optional[Edge]

    __repr__ = generate_repr(__init__)

    def __eq__(self, other: 'Vertex') -> bool:
        return (self.x == other.x and self.y == other.y
                if isinstance(other, Vertex)
                else NotImplemented)

    @property
    def is_degenerate(self) -> bool:
        return self.incident_edge is None


class Edge:
    __slots__ = ('cell', 'is_linear', 'is_primary', 'left_from_end',
                 'left_in_start', 'opposite', 'start')

    def __init__(self,
                 start: Optional[Vertex],
                 cell: Cell,
                 is_linear: bool,
                 is_primary: bool) -> None:
        self.start = start
        self.cell = cell
        self.is_linear, self.is_primary = is_linear, is_primary
        self.opposite = self.left_in_start = self.left_from_end = None

    __repr__ = generate_repr(__init__)

    @property
    def end(self) -> Optional[Vertex]:
        return None if self.opposite is None else self.opposite.start

    @property
    def is_curved(self) -> bool:
        return not self.is_linear

    @property
    def is_degenerate(self) -> bool:
        return (self.start is not None
                and self.end is not None
                and self.start == self.end)

    @property
    def is_finite(self) -> bool:
        return not self.is_infinite

    @property
    def is_infinite(self) -> bool:
        return self.start is None or self.end is None

    @property
    def is_secondary(self) -> bool:
        return not self.is_primary

    @property
    def left_from_start(self) -> Optional['Edge']:
        return (None
                if self.left_in_start is None
                else self.left_in_start.opposite)

    @property
    def right_from_start(self) -> Optional['Edge']:
        return None if self.opposite is None else self.opposite.left_from_end

    def disconnect(self) -> None:
        vertex = self.start
        cursor = self.opposite.left_from_start
        while cursor is not self.opposite:
            cursor.start = vertex
            cursor = cursor.left_from_start
        right_from_start, left_from_start = (self.right_from_start,
                                             self.left_from_start)
        opposite_right_from_start, opposite_left_from_start = (
            self.opposite.right_from_start, self.opposite.left_from_start)
        # update prev/next pointers for the incident edges
        left_from_start.opposite.left_from_end = opposite_right_from_start
        opposite_right_from_start.left_in_start = left_from_start.opposite
        right_from_start.left_in_start = opposite_left_from_start.opposite
        opposite_left_from_start.opposite.left_from_end = right_from_start

    def set_as_incident(self) -> None:
        self.cell.incident_edge = self
        if self.start is not None:
            self.start.incident_edge = self
