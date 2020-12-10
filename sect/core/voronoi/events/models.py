import ctypes
import struct
from typing import TypeVar

from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)

from sect.core.voronoi.enums import SourceCategory
from sect.core.voronoi.hints import Source
from sect.core.voronoi.utils import are_same_vertical_points
from sect.hints import (Coordinate,
                        Point)


class Site:
    __slots__ = ('start', 'end', 'source', 'source_category', 'sorted_index',
                 'is_inverse')

    def __init__(self,
                 start: Point,
                 end: Point,
                 source: Source,
                 source_category: SourceCategory,
                 sorted_index: int = 0,
                 is_inverse: bool = False) -> None:
        self.start, self.end = start, end
        self.source, self.source_category = source, source_category
        self.sorted_index = sorted_index
        self.is_inverse = is_inverse

    __repr__ = generate_repr(__init__)

    def __eq__(self, other: 'Site') -> bool:
        return (self.start == other.start and self.end == other.end
                if isinstance(other, Site)
                else NotImplemented)

    def __lt__(self, other: 'Event') -> bool:
        if isinstance(other, Site):
            start_x, start_y = self.start
            other_start_x, other_start_y = other.start
            if start_x != other_start_x:
                return start_x < other_start_x
            elif not self.is_segment:
                if not other.is_segment:
                    return start_y < other_start_y
                elif other.is_vertical:
                    return start_y <= other_start_y
                return True
            elif other.is_vertical:
                return self.is_vertical and start_y < other_start_y
            elif self.is_vertical:
                return True
            elif start_y != other_start_y:
                return start_y < other_start_y
            else:
                return (orientation(self.start, self.end, other.end)
                        is Orientation.COUNTERCLOCKWISE)
        else:
            start_x, _ = self.start
            return (less_than(start_x, other.lower_x)
                    if isinstance(other, Circle)
                    else NotImplemented)

    @property
    def is_point(self) -> bool:
        return self.start == self.end

    @property
    def is_segment(self) -> bool:
        return self.start != self.end

    @property
    def is_vertical(self) -> bool:
        return are_same_vertical_points(self.start, self.end)

    @property
    def min_point(self) -> Point:
        return min(self.start, self.end)

    def inverse(self) -> None:
        self.start, self.end, self.is_inverse = (self.end, self.start,
                                                 not self.is_inverse)


class Circle:
    __slots__ = 'center_x', 'center_y', 'lower_x', 'is_active'

    def __init__(self,
                 center_x: Coordinate,
                 center_y: Coordinate,
                 lower_x: Coordinate,
                 is_active: bool = True) -> None:
        self.center_x, self.center_y = center_x, center_y
        self.lower_x = lower_x
        self.is_active = is_active

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: 'Event') -> bool:
        if isinstance(other, Site):
            other_start_x, _ = other.start
            return less_than(self.lower_x, other_start_x)
        return ((self.lower_x, self.center_y) < (other.lower_x, other.center_y)
                if isinstance(other, Circle)
                else NotImplemented)

    def deactivate(self) -> None:
        self.is_active = False

    def lies_outside_vertical_segment(self, site: Site) -> bool:
        if not site.is_segment or not site.is_vertical:
            return False
        _, site_start_y = site.start
        _, site_end_y = site.end
        start_y, end_y = ((site_end_y, site_start_y)
                          if site.is_inverse
                          else (site_start_y, site_end_y))
        return (less_than(self.center_y, start_y)
                or less_than(end_y, self.center_y))


Event = TypeVar('Event', Circle, Site)


def less_than(left: Coordinate, right: Coordinate) -> bool:
    return not are_almost_equal(left, right) and left < right


def are_almost_equal(left: Coordinate, right: Coordinate,
                     max_ulps: int = 64) -> bool:
    return (abs(_double_to_uint(float(left)) - _double_to_uint(float(right)))
            <= max_ulps)


def _double_to_uint(value: float,
                    *,
                    sign_bit_mask: int = 2 ** 63) -> int:
    result, = struct.unpack('!Q', struct.pack('!d', value))
    return (ctypes.c_uint64(~result + 1
                            if sign_bit_mask & result
                            else sign_bit_mask | result)
            .value)
