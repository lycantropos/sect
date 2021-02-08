import ctypes
import struct
from typing import TypeVar

from ground.base import Orientation
from ground.hints import (Coordinate,
                          Point)
from reprit.base import generate_repr

from sect.core.hints import Orienteer
from sect.core.voronoi.enums import SourceCategory
from sect.core.voronoi.hints import Source
from sect.core.voronoi.utils import are_same_vertical_points


class Site:
    __slots__ = ('end', 'is_inverse', 'orienteer', 'sorted_index', 'source',
                 'source_category', 'start')

    def __init__(self,
                 orienteer: Orienteer,
                 start: Point,
                 end: Point,
                 source: Source,
                 source_category: SourceCategory,
                 sorted_index: int = 0,
                 is_inverse: bool = False) -> None:
        self.orienteer = orienteer
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
            start = self.start
            other_start = other.start
            if start.x != other_start.x:
                return start.x < other_start.x
            elif not self.is_segment:
                if not other.is_segment:
                    return start.y < other_start.y
                elif other.is_vertical:
                    return start.y <= other_start.y
                return True
            elif other.is_vertical:
                return self.is_vertical and start.y < other_start.y
            elif self.is_vertical:
                return True
            elif start.y != other_start.y:
                return start.y < other_start.y
            else:
                return (self.orienteer(self.end, self.start, other.end)
                        is Orientation.COUNTERCLOCKWISE)
        else:
            start = self.start
            return (less_than(start.x, other.lower_x)
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


class BaseCircle:
    center_x = center_y = ...  # type: Coordinate
    is_active = ...  # type: bool

    def deactivate(self) -> None:
        self.is_active = False

    def lies_outside_vertical_segment(self, site: Site) -> bool:
        if not site.is_segment or not site.is_vertical:
            return False
        start_y, end_y = ((site.end.y, site.start.y)
                          if site.is_inverse
                          else (site.start.y, site.end.y))
        return (less_than(self.center_y, start_y)
                or less_than(end_y, self.center_y))


class LeftCircle(BaseCircle):
    __slots__ = 'center_x', 'center_y', 'is_active', 'squared_radius'

    def __init__(self,
                 center_x: Coordinate,
                 center_y: Coordinate,
                 squared_radius: Coordinate,
                 is_active: bool = True) -> None:
        self.center_x, self.center_y, self.squared_radius, self.is_active = (
            center_x, center_y, squared_radius, is_active)

    __repr__ = generate_repr(__init__)

    def __gt__(self, other: 'Event') -> bool:
        if isinstance(other, Site):
            return (other.start.x < self.center_x
                    and (self.squared_radius
                         < (self.center_x - other.start.x) ** 2))
        return (other.lower_x < self.center_x
                and ((self.squared_radius, other.center_y)
                     < (self.center_x - other.lower_x, self.center_y))
                if isinstance(other, Circle)
                else NotImplemented)

    def __lt__(self, other: 'Event') -> bool:
        if isinstance(other, Site):
            return (self.center_x <= other.start.x
                    or ((self.center_x - other.start.x) ** 2
                        < self.squared_radius))
        elif isinstance(other, RightCircle):
            if self.center_x < other.center_x:
                return True
            else:
                squared_centers_dx = (other.center_x - self.center_x) ** 2
                squared_radius_sum = self.squared_radius + other.squared_radius
                return (squared_centers_dx <= squared_radius_sum
                        or (((squared_centers_dx - squared_radius_sum) ** 2,
                             self.center_y)
                            < (4 * self.squared_radius * other.squared_radius,
                               other.center_y)))
        elif isinstance(other, LeftCircle):
            if self.center_x < other.center_x:
                if other.squared_radius <= self.squared_radius:
                    return True
                else:
                    squared_centers_dx = (other.center_x - self.center_x) ** 2
                    squared_radius_sum = (self.squared_radius
                                          + other.squared_radius)
                    return (squared_centers_dx > squared_radius_sum
                            and
                            (4 * self.squared_radius * other.squared_radius,
                             self.center_y)
                            < ((squared_centers_dx - squared_radius_sum) ** 2,
                               other.center_y))
            elif other.center_x < self.center_x:
                if self.squared_radius <= other.squared_radius:
                    return False
                else:
                    squared_centers_dx = (other.center_x - self.center_x) ** 2
                    squared_radius_sum = (self.squared_radius
                                          + other.squared_radius)
                    return (squared_centers_dx < squared_radius_sum
                            and
                            ((4 * self.squared_radius * other.squared_radius,
                              self.center_y)
                             < ((squared_radius_sum - squared_centers_dx) ** 2,
                                other.center_y)))
            else:
                return ((other.squared_radius, self.center_y)
                        < (self.squared_radius, other.center_y))
        return (self.center_x <= other.lower_x
                or (((self.center_x - other.lower_x) ** 2, self.center_y)
                    < (self.squared_radius, other.center_y))
                if isinstance(other, Circle)
                else NotImplemented)


class RightCircle(BaseCircle):
    __slots__ = 'center_x', 'center_y', 'is_active', 'squared_radius'

    def __init__(self,
                 center_x: Coordinate,
                 center_y: Coordinate,
                 squared_radius: Coordinate,
                 is_active: bool = True) -> None:
        self.center_x, self.center_y, self.squared_radius, self.is_active = (
            center_x, center_y, squared_radius, is_active)

    __repr__ = generate_repr(__init__)

    def __gt__(self, other: 'Event') -> bool:
        if isinstance(other, Site):
            return (other.start.x <= self.center_x
                    or ((other.start.x - self.center_x) ** 2
                        < self.squared_radius))
        return (other.lower_x < self.center_x
                and ((self.squared_radius, other.center_y)
                     < ((self.center_x - other.lower_x) ** 2, self.center_y))
                if isinstance(other, Circle)
                else NotImplemented)

    def __lt__(self, other: 'Event') -> bool:
        if isinstance(other, Site):
            return (self.center_x < other.start.x
                    and (self.squared_radius
                         < (other.start.x - self.center_x) ** 2))
        elif isinstance(other, RightCircle):
            if self.center_x < other.center_x:
                if self.squared_radius <= other.squared_radius:
                    return True
                else:
                    squared_centers_dx = (other.center_x - self.center_x) ** 2
                    squared_radius_sum = (self.squared_radius
                                          + other.squared_radius)
                    return (squared_radius_sum <= squared_centers_dx
                            or
                            (((squared_radius_sum - squared_centers_dx) ** 2,
                              self.center_y)
                             < (4 * self.squared_radius * other.squared_radius,
                                other.center_y)))
            elif other.center_x < self.center_x:
                if other.squared_radius <= self.squared_radius:
                    return False
                else:
                    squared_centers_dx = (other.center_x - self.center_x) ** 2
                    squared_radius_sum = (self.squared_radius
                                          + other.squared_radius)
                    return (squared_centers_dx < squared_radius_sum
                            and
                            ((4 * self.squared_radius * other.squared_radius,
                              self.center_y)
                             < ((squared_radius_sum - squared_centers_dx) ** 2,
                                other.center_y)))
            else:
                return ((self.squared_radius, self.center_y)
                        < (other.squared_radius, other.center_y))
        elif isinstance(other, LeftCircle):
            if other.center_x <= self.center_x:
                return False
            else:
                squared_centers_dx = (other.center_x - self.center_x) ** 2
                squared_radius_sum = self.squared_radius + other.squared_radius
                return (squared_radius_sum < squared_centers_dx
                        and ((4 * self.squared_radius * other.squared_radius,
                              self.center_y)
                             < ((squared_centers_dx - squared_radius_sum) ** 2,
                                other.center_y)))
        return (other.lower_x > self.center_x
                and ((self.squared_radius, self.center_y)
                     < ((other.lower_x - self.center_x) ** 2, other.center_y))
                if isinstance(other, Circle)
                else NotImplemented)


class Circle(BaseCircle):
    __slots__ = 'center_x', 'center_y', 'lower_x', 'is_active'

    def __init__(self,
                 center_x: Coordinate,
                 center_y: Coordinate,
                 lower_x: Coordinate,
                 is_active: bool = True) -> None:
        self.center_x, self.center_y, self.lower_x, self.is_active = (
            center_x, center_y, lower_x, is_active)

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: 'Event') -> bool:
        if isinstance(other, Site):
            return less_than(self.lower_x, other.start.x)
        return ((self.lower_x, self.center_y) < (other.lower_x, other.center_y)
                if isinstance(other, Circle)
                else NotImplemented)


Event = TypeVar('Event', Circle, Site)


def less_than(left: Coordinate, right: Coordinate) -> bool:
    return ((not (isinstance(left, float) and isinstance(right, float))
             or not are_floats_almost_equal(left, right))
            and left < right)


def are_floats_almost_equal(left: float,
                            right: float,
                            max_ulps: int = 64) -> bool:
    return abs(_double_to_uint(left) - _double_to_uint(right)) <= max_ulps


def _double_to_uint(value: float,
                    *,
                    sign_bit_mask: int = 2 ** 63) -> int:
    result, = struct.unpack('!Q', struct.pack('!d', value))
    return (ctypes.c_uint64(~result + 1
                            if sign_bit_mask & result
                            else sign_bit_mask | result)
            .value)
