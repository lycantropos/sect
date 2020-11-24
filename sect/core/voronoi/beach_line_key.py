from copy import copy
from math import sqrt
from typing import Tuple

from reprit.base import generate_repr

from .enums import (ComparisonResult,
                    Orientation)
from .events import SiteEvent
from .point import Point
from .utils import (compare_floats,
                    deltas_to_orientation,
                    robust_cross_product,
                    safe_divide_floats,
                    to_orientation)


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


def distance_to_point_arc(site: SiteEvent, point: Point) -> float:
    start_x, start_y = site.start
    x, y = point
    dx = float(start_x) - float(x)
    dy = float(start_y) - float(y)
    # the relative error is at most 3EPS
    return safe_divide_floats(dx * dx + dy * dy, 2.0 * dx)


def distance_to_segment_arc(site: SiteEvent, point: Point) -> float:
    if site.is_vertical:
        start_x, _ = site.start
        x, _ = point
        return (float(start_x) - float(x)) * 0.5
    else:
        start_x, start_y = site.start
        end_x, end_y = site.end
        a1 = float(end_x) - float(start_x)
        b1 = float(end_y) - float(start_y)
        k = sqrt(a1 * a1 + b1 * b1)
        # avoid subtraction while computing k
        if not b1 < 0:
            k = 1. / (b1 + k)
        else:
            k = (k - b1) / (a1 * a1)
        x, y = point
        return k * robust_cross_product(end_x - start_x, end_y - start_y,
                                        x - start_x, y - start_y)


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
        left_site: SiteEvent,
        right_site: SiteEvent,
        point: Point,
        reverse_order: bool) -> bool:
    segment_start = right_site.start
    segment_end = right_site.end
    if (to_orientation(segment_start, segment_end, point)
            is not Orientation.RIGHT):
        return not right_site.is_inverse
    site_point_x, site_point_y = left_site.start
    segment_start_x, segment_start_y = segment_start
    segment_end_x, segment_end_y = segment_end
    x, y = point
    points_dx, points_dy = (float(x) - float(site_point_x),
                            float(y) - float(site_point_y))
    segment_dx, segment_dy = (float(segment_end_x) - float(segment_start_x),
                              float(segment_end_y) - float(segment_start_y))
    if right_site.is_vertical:
        if y < site_point_y and not reverse_order:
            return False
        elif y > site_point_y and reverse_order:
            return True
    else:
        if (deltas_to_orientation(segment_end_x - segment_start_x,
                                  segment_end_y - segment_start_y,
                                  x - site_point_x, y - site_point_y)
                is Orientation.LEFT):
            if not right_site.is_inverse:
                if reverse_order:
                    return True
            elif not reverse_order:
                return False
        else:
            fast_left_expr = (segment_dx * (points_dy + points_dx)
                              * (points_dy - points_dx))
            fast_right_expr = 2. * segment_dy * points_dx * points_dy
            if ((compare_floats(fast_left_expr, fast_right_expr, 4)
                 is ComparisonResult.MORE)
                    is not reverse_order):
                return reverse_order
    distance_from_left = distance_to_point_arc(left_site, point)
    distance_from_right = distance_to_segment_arc(right_site, point)
    # undefined ulp range is equal to 3EPS + 7EPS <= 10ULP.
    return (distance_from_left < distance_from_right) is not reverse_order


def segment_segment_horizontal_goes_through_right_arc_first(
        left_site: SiteEvent,
        right_site: SiteEvent,
        point: Point) -> bool:
    # handle temporary segment sites
    if left_site.sorted_index == right_site.sorted_index:
        return (to_orientation(left_site.start, left_site.end, point)
                is Orientation.LEFT)
    distance_from_left = distance_to_segment_arc(left_site, point)
    distance_from_right = distance_to_segment_arc(right_site, point)
    # undefined ulp range is equal to 7EPS + 7EPS <= 14ULP
    return distance_from_left < distance_from_right
