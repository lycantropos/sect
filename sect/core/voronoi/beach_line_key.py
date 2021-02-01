from copy import copy
from typing import Tuple

from ground.hints import Coordinate
from reprit.base import generate_repr

from sect.core.utils import (Orientation,
                             cross_product,
                             orientation)
from sect.core.hints import Point
from .events import Site
from .utils import (robust_divide,
                    robust_evenly_divide,
                    robust_sqrt,
                    to_segment_squared_length)


class BeachLineKey:
    __slots__ = '_left_site', '_right_site'

    def __init__(self, left_site: Site, right_site: Site) -> None:
        self.left_site = left_site
        self.right_site = right_site

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: 'BeachLineKey') -> bool:
        site, other_site = self.comparison_site, other.comparison_site
        x, _ = point = site.min_point
        other_x, _ = other_point = other_site.min_point
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
            # (inserted during same site processing)
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
    def comparison_site(self) -> Site:
        return (self.left_site
                if self.left_site.sorted_index > self.right_site.sorted_index
                else self.right_site)

    @property
    def left_site(self) -> Site:
        return self._left_site

    @left_site.setter
    def left_site(self, value: Site) -> None:
        self._left_site = copy(value)

    @property
    def right_site(self) -> Site:
        return self._right_site

    @right_site.setter
    def right_site(self, value: Site) -> None:
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


def distance_to_point_arc(point_site: Site, point: Point) -> Coordinate:
    start_x, _ = site_point = point_site.start
    x, _ = point
    dx = start_x - x
    return robust_divide(to_segment_squared_length(point, site_point), 2 * dx)


def distance_to_segment_arc(segment_site: Site, point: Point) -> Coordinate:
    if segment_site.is_vertical:
        start_x, _ = segment_site.start
        x, _ = point
        return robust_evenly_divide(start_x - x, 2)
    else:
        start_x, start_y = start = segment_site.start
        end_x, end_y = end = segment_site.end
        segment_length = robust_sqrt(to_segment_squared_length(start, end))
        segment_dx = end_x - start_x
        segment_dy = end_y - start_y
        coefficient = (robust_divide(segment_length - segment_dy,
                                     segment_dx * segment_dx)
                       if segment_dy < 0
                       else robust_divide(1, segment_dy + segment_length))
        return coefficient * cross_product(start, end, start, point)


def horizontal_goes_through_right_arc_first(left_site: Site,
                                            right_site: Site,
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


def point_point_horizontal_goes_through_right_arc_first(
        first_point_site: Site,
        second_point_site: Site,
        point: Point) -> bool:
    first_point_site_x, first_point_site_y = first_point_site.start
    second_point_site_x, second_point_site_y = second_point_site.start
    _, y = point
    if second_point_site_x < first_point_site_x:
        if y <= first_point_site_y:
            return False
    elif first_point_site_x < second_point_site_x:
        if second_point_site_y <= y:
            return True
    else:
        return first_point_site_y + second_point_site_y < 2 * y
    return (distance_to_point_arc(first_point_site, point)
            < distance_to_point_arc(second_point_site, point))


def point_segment_horizontal_goes_through_right_arc_first(
        point_site: Site,
        segment_site: Site,
        point: Point,
        reverse_order: bool) -> bool:
    segment_start, segment_end = segment_site.start, segment_site.end
    if (orientation(segment_start, segment_end, point)
            is not Orientation.CLOCKWISE):
        return not segment_site.is_inverse
    elif segment_site.is_vertical:
        _, point_site_y = point_site.start
        _, y = point
        if y < point_site_y and not reverse_order:
            return False
        elif y > point_site_y and reverse_order:
            return True
    elif cross_product(segment_start, segment_end, point_site.start,
                       point) > 0:
        if not segment_site.is_inverse:
            if reverse_order:
                return True
        elif not reverse_order:
            return False
    else:
        point_x, point_y = point
        point_site_x, point_site_y = point_site.start
        points_dx, points_dy = (point_x - point_site_x,
                                point_y - point_site_y)
        segment_start_x, segment_start_y = segment_start
        segment_end_x, segment_end_y = segment_end
        segment_dx, segment_dy = (segment_end_x - segment_start_x,
                                  segment_end_y - segment_start_y)
        fast_left_expr = (segment_dx * (points_dy + points_dx)
                          * (points_dy - points_dx))
        fast_right_expr = 2 * segment_dy * points_dx * points_dy
        if (fast_left_expr > fast_right_expr) is not reverse_order:
            return reverse_order
    return ((distance_to_point_arc(point_site, point)
             < distance_to_segment_arc(segment_site, point))
            is not reverse_order)


def segment_segment_horizontal_goes_through_right_arc_first(
        first_segment_site: Site,
        second_segment_site: Site,
        point: Point) -> bool:
    return (orientation(first_segment_site.start, first_segment_site.end,
                        point) is Orientation.COUNTERCLOCKWISE
            if (first_segment_site.sorted_index
                == second_segment_site.sorted_index)
            else (distance_to_segment_arc(first_segment_site, point)
                  < distance_to_segment_arc(second_segment_site, point)))
