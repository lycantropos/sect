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
        point, other_point = site.comparison_point, other_site.comparison_point
        if point.x < other_point.x:
            # second node contains a new site
            return horizontal_goes_through_right_arc_first(
                    self.left_site, self.right_site, other_point)
        elif point.x > other_point.x:
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
            return self.left_site.start.y, 0
        elif self.left_site.sorted_index > self.right_site.sorted_index:
            comparison_point = (self.left_site.start
                                if (not is_new_node
                                    and self.left_site.is_segment
                                    and self.left_site.is_vertical)
                                else self.left_site.end)
            return comparison_point.y, 1
        else:
            return self.right_site.start.y, -1


def distance_to_point_arc(site: SiteEvent, point: Point) -> float:
    dx = float(site.start.x) - float(point.x)
    dy = float(site.start.y) - float(point.y)
    # the relative error is at most 3EPS
    return safe_divide_floats(dx * dx + dy * dy, 2.0 * dx)


def distance_to_segment_arc(site: SiteEvent, point: Point) -> float:
    if site.is_vertical:
        return (float(site.start.x) - float(point.x)) * 0.5
    else:
        start, end = site.start, site.end
        a1 = float(end.x) - float(start.x)
        b1 = float(end.y) - float(start.y)
        k = sqrt(a1 * a1 + b1 * b1)
        # avoid subtraction while computing k
        if not b1 < 0:
            k = 1. / (b1 + k)
        else:
            k = (k - b1) / (a1 * a1)
        return k * robust_cross_product(end.x - start.x, end.y - start.y,
                                        point.x - start.x, point.y - start.y)


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
    left_point, right_point = left_site.start, right_site.start
    if left_point.x > right_point.x:
        if point.y <= left_point.y:
            return False
    elif left_point.x < right_point.x:
        if point.y >= right_point.y:
            return True
    else:
        return left_point.y + right_point.y < 2 * point.y
    distance_from_left = distance_to_point_arc(left_site, point)
    distance_from_right = distance_to_point_arc(right_site, point)
    # undefined ulp range is equal to 3EPS + 3EPS <= 6ULP
    return distance_from_left < distance_from_right


def point_segment_horizontal_goes_through_right_arc_first(
        left_site: SiteEvent,
        right_site: SiteEvent,
        point: Point,
        reverse_order: bool) -> bool:
    site_point = left_site.start
    segment_start, segment_end = right_site.start, right_site.end
    if (to_orientation(segment_start, segment_end, point)
            is not Orientation.RIGHT):
        return not right_site.is_inverse
    points_dx, points_dy = (float(point.x) - float(site_point.x),
                            float(point.y) - float(site_point.y))
    segment_dx, segment_dy = (float(segment_end.x) - float(segment_start.x),
                              float(segment_end.y) - float(segment_start.y))
    if right_site.is_vertical:
        if point.y < site_point.y and not reverse_order:
            return False
        elif point.y > site_point.y and reverse_order:
            return True
    else:
        if (deltas_to_orientation(segment_end.x - segment_start.x,
                                  segment_end.y - segment_start.y,
                                  point.x - site_point.x,
                                  point.y - site_point.y)
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
