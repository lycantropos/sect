from typing import TypeVar

from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)

from sect.core.voronoi.enums import (ComparisonResult,
                                     SourceCategory)
from sect.core.voronoi.hints import Source
from sect.core.voronoi.utils import (are_same_vertical_points,
                                     compare_floats)
from sect.hints import (Coordinate,
                        Point)

ULPS = 64


class SiteEvent:
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

    def __eq__(self, other: 'SiteEvent') -> bool:
        return (self.start == other.start and self.end == other.end
                if isinstance(other, SiteEvent)
                else NotImplemented)

    def __lt__(self, other: 'Event') -> bool:
        if isinstance(other, SiteEvent):
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
            return (compare_floats(float(start_x), float(other.lower_x),
                                   ULPS) is ComparisonResult.LESS
                    if isinstance(other, CircleEvent)
                    else NotImplemented)

    @property
    def comparison_point(self) -> Point:
        return min(self.start, self.end)

    @property
    def is_point(self) -> bool:
        return self.start == self.end

    @property
    def is_segment(self) -> bool:
        return self.start != self.end

    @property
    def is_vertical(self) -> bool:
        return are_same_vertical_points(self.start, self.end)

    def inverse(self) -> None:
        self.start, self.end, self.is_inverse = (self.end, self.start,
                                                 not self.is_inverse)


class CircleEvent:
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

    def __eq__(self, other: 'CircleEvent') -> bool:
        return (self.center_x == other.center_x
                and self.center_y == other.center_y
                and self.lower_x == other.lower_x
                and self.is_active is other.is_active
                if isinstance(other, CircleEvent)
                else NotImplemented)

    def __lt__(self, other: 'Event') -> bool:
        if isinstance(other, SiteEvent):
            other_start_x, _ = other.start
            return compare_floats(float(self.lower_x), float(other_start_x),
                                  ULPS) is ComparisonResult.LESS
        return ((self.lower_x, self.center_y) < (other.lower_x, other.center_y)
                if isinstance(other, CircleEvent)
                else NotImplemented)

    def lies_outside_vertical_segment(self, site: SiteEvent) -> bool:
        if not site.is_segment or not site.is_vertical:
            return False
        _, site_start_y = site.start
        _, site_end_y = site.end
        start_y, end_y = ((site_end_y, site_start_y)
                          if site.is_inverse
                          else (site_start_y, site_end_y))
        return (compare_floats(float(self.center_y), float(start_y),
                               ULPS) is ComparisonResult.LESS
                or compare_floats(float(self.center_y), float(end_y),
                                  ULPS) is ComparisonResult.MORE)

    def deactivate(self) -> None:
        self.is_active = False


Event = TypeVar('Event', CircleEvent, SiteEvent)
