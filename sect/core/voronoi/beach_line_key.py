from copy import copy
from typing import Tuple

from reprit.base import generate_repr
from robust import parallelogram
from robust.angular import (Orientation,
                            orientation)

from sect.hints import (Coordinate,
                        Point)
from .events import SiteEvent
from .utils import (robust_divide,
                    robust_evenly_divide,
                    robust_sqrt,
                    to_segment_squared_length)


class BeachLineKey:
    __slots__ = '_left_site', '_right_site'

    def __init__(self, left_site: SiteEvent, right_site: SiteEvent) -> None:
        self.left_site = left_site
        self.right_site = right_site

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: 'BeachLineKey') -> bool:
        site, other_site = self.comparison_site, other.comparison_site
        x, _ = point = site.comparison_point
        other_x, _ = other_point = other_site.comparison_point
        if x < other_x:
            # second node contains a new site
            return horizontal_goes_through_right_arc_first(
                    self.left_site, self.right_site, other_point)
        elif other_x < x:
            # first node contains a new site
            return not horizontal_goes_through_right_arc_first(
                    other.left_site, other.right_site, point)
        elif site.sorted_index == other_site.sorted_index:
            # both nodes are new
            # (inserted during same site event processing)
            return self.to_comparison_y() < other.to_comparison_y()
        elif site.sorted_index < other_site.sorted_index:
            y, flag = self.to_comparison_y(False)
            other_y, _ = other.to_comparison_y(True)
            return (not site.is_segment and flag < 0
                    if y == other_y
                    else y < other_y)
        else:
            y, _ = self.to_comparison_y(True)
            other_y, other_flag = other.to_comparison_y(False)
            return (other_site.is_segment or other_flag > 0
                    if y == other_y
                    else y < other_y)

    @property
    def comparison_site(self) -> SiteEvent:
        return (self.left_site
                if self.left_site.sorted_index > self.right_site.sorted_index
                else self.right_site)

    @property
    def left_site(self) -> SiteEvent:
        return self._left_site

    @left_site.setter
    def left_site(self, value: SiteEvent) -> None:
        self._left_site = copy(value)

    @property
    def right_site(self) -> SiteEvent:
        return self._right_site

    @right_site.setter
    def right_site(self, value: SiteEvent) -> None:
        self._right_site = copy(value)

    def to_comparison_y(self, is_new_node: bool = True) -> Tuple[int, int]:
        if self.left_site.sorted_index == self.right_site.sorted_index:
            _, left_site_start_y = self.left_site.start
            return left_site_start_y, 0
        elif self.left_site.sorted_index > self.right_site.sorted_index:
            _, comparison_point_y = (self.left_site.start
                                     if (not is_new_node
                                         and self.left_site.is_segment
                                         and self.left_site.is_vertical)
                                     else self.left_site.end)
            return comparison_point_y, 1
        else:
            _, right_site_start_y = self.right_site.start
            return right_site_start_y, -1


def distance_to_point_arc(site: SiteEvent, point: Point) -> Coordinate:
    start_x, _ = site.start
    x, _ = point
    dx = start_x - x
    return robust_divide(to_segment_squared_length(point, site.start), 2 * dx)


def distance_to_segment_arc(segment_event: SiteEvent,
                            point: Point) -> Coordinate:
    if segment_event.is_vertical:
        start_x, _ = segment_event.start
        x, _ = point
        return robust_evenly_divide(start_x - x, 2)
    else:
        start_x, start_y = start = segment_event.start
        end_x, end_y = end = segment_event.end
        segment_length = robust_sqrt(to_segment_squared_length(start, end))
        segment_dx = end_x - start_x
        segment_dy = end_y - start_y
        coefficient = (robust_divide(segment_length - segment_dy,
                                     segment_dx * segment_dx)
                       if segment_dy < 0
                       else robust_divide(1, segment_dy + segment_length))
        return coefficient * parallelogram.signed_area(start, end, start,
                                                       point)


def horizontal_goes_through_right_arc_first(left_site: SiteEvent,
                                            right_site: SiteEvent,
                                            point: Point) -> bool:
    if left_site.is_segment:
        if right_site.is_segment:
            return segment_segment_horizontal_goes_through_right_arc_first(
                    left_site, right_site, point)
        else:
            return point_segment_horizontal_goes_through_right_arc_first(
                    right_site, left_site, point, True)
    elif right_site.is_segment:
        return point_segment_horizontal_goes_through_right_arc_first(
                left_site, right_site, point, False)
    else:
        return point_point_horizontal_goes_through_right_arc_first(
                left_site, right_site, point)


def point_point_horizontal_goes_through_right_arc_first(left_site: SiteEvent,
                                                        right_site: SiteEvent,
                                                        point: Point) -> bool:
    left_x, left_y = left_site.start
    right_x, right_y = right_site.start
    _, y = point
    if right_x < left_x:
        if y <= left_y:
            return False
    elif left_x < right_x:
        if right_y <= y:
            return True
    else:
        return left_y + right_y < 2 * y
    distance_from_left = distance_to_point_arc(left_site, point)
    distance_from_right = distance_to_point_arc(right_site, point)
    # undefined ulp range is equal to 3EPS + 3EPS <= 6ULP
    return distance_from_left < distance_from_right


def point_segment_horizontal_goes_through_right_arc_first(
        point_event: SiteEvent,
        segment_event: SiteEvent,
        point: Point,
        reverse_order: bool) -> bool:
    segment_start, segment_end = segment_event.start, segment_event.end
    if (orientation(segment_end, segment_start, point)
            is not Orientation.CLOCKWISE):
        return not segment_event.is_inverse
    elif segment_event.is_vertical:
        _, point_event_y = point_event.start
        _, y = point
        if y < point_event_y and not reverse_order:
            return False
        elif y > point_event_y and reverse_order:
            return True
    elif parallelogram.signed_area(segment_start, segment_end,
                                   point_event.start, point) > 0:
        if not segment_event.is_inverse:
            if reverse_order:
                return True
        elif not reverse_order:
            return False
    else:
        return ((distance_to_point_arc(point_event, point)
                 < distance_to_segment_arc(segment_event, point))
                is not reverse_order)


def segment_segment_horizontal_goes_through_right_arc_first(
        left_site: SiteEvent,
        right_site: SiteEvent,
        point: Point) -> bool:
    # handle temporary segment sites
    if left_site.sorted_index == right_site.sorted_index:
        return (orientation(left_site.end, left_site.start, point)
                is Orientation.COUNTERCLOCKWISE)
    distance_from_left = distance_to_segment_arc(left_site, point)
    distance_from_right = distance_to_segment_arc(right_site, point)
    # undefined ulp range is equal to 7EPS + 7EPS <= 14ULP
    return distance_from_left < distance_from_right
