from copy import copy
from typing import Tuple

from ground.base import (Context,
                         Orientation)
from ground.hints import (Point,
                          Scalar)
from reprit.base import generate_repr

from sect.core.hints import Orienteer
from .events import Site
from .hints import (CrossProducer,
                    DotProducer)
from .utils import (robust_divide,
                    robust_evenly_divide,
                    to_segment_squared_length,
                    to_sqrt)


class BeachLineKey:
    __slots__ = 'context', '_left_site', '_right_site'

    def __init__(self,
                 left_site: Site,
                 right_site: Site,
                 *,
                 context: Context) -> None:
        self.left_site, self.right_site, self.context = (left_site, right_site,
                                                         context)

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: 'BeachLineKey') -> bool:
        site, other_site = self.comparison_site, other.comparison_site
        point, other_point = site.min_point, other_site.min_point
        if point.x < other_point.x:
            # second node contains a new site
            return horizontal_goes_through_right_arc_first(
                    self.left_site, self.right_site, other_point,
                    context=self.context)
        elif other_point.x < point.x:
            # first node contains a new site
            return not horizontal_goes_through_right_arc_first(
                    other.left_site, other.right_site, point,
                    context=self.context)
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


def distance_to_point_arc(point_site: Site,
                          point: Point,
                          dot_producer: DotProducer) -> Scalar:
    site_point = point_site.start
    return robust_divide(to_segment_squared_length(point, site_point,
                                                   dot_producer),
                         2 * (site_point.x - point.x))


def distance_to_segment_arc(segment_site: Site,
                            point: Point,
                            cross_producer: CrossProducer,
                            dot_producer: DotProducer) -> Scalar:
    if segment_site.is_vertical:
        return robust_evenly_divide(segment_site.start.x - point.x, 2)
    else:
        start, end = segment_site.start, segment_site.end
        segment_length = to_sqrt(to_segment_squared_length(start, end,
                                                           dot_producer))
        segment_dx, segment_dy = end.x - start.x, end.y - start.y
        coefficient = (robust_divide(segment_length - segment_dy,
                                     segment_dx * segment_dx)
                       if segment_dy < 0
                       else robust_divide(1, segment_dy + segment_length))
        return coefficient * cross_producer(start, end, start, point)


def horizontal_goes_through_right_arc_first(left_site: Site,
                                            right_site: Site,
                                            point: Point,
                                            *,
                                            context: Context) -> bool:
    cross_producer, dot_producer, orienteer = (context.cross_product,
                                               context.dot_product,
                                               context.angle_orientation)
    if left_site.is_segment:
        if right_site.is_segment:
            return segment_segment_horizontal_goes_through_right_arc_first(
                    left_site, right_site, point, cross_producer, dot_producer,
                    orienteer)
        else:
            return point_segment_horizontal_goes_through_right_arc_first(
                    right_site, left_site, point, True, cross_producer,
                    dot_producer, orienteer)
    elif right_site.is_segment:
        return point_segment_horizontal_goes_through_right_arc_first(
                left_site, right_site, point, False, cross_producer,
                dot_producer, orienteer)
    else:
        return point_point_horizontal_goes_through_right_arc_first(
                left_site, right_site, point, dot_producer)


def point_point_horizontal_goes_through_right_arc_first(
        first_site: Site,
        second_site: Site,
        point: Point,
        dot_producer: DotProducer) -> bool:
    first_site_point, second_site_point = (first_site.start,
                                           second_site.start)
    if second_site_point.x < first_site_point.x:
        if point.y <= first_site_point.y:
            return False
    elif first_site_point.x < second_site_point.x:
        if second_site_point.y <= point.y:
            return True
    else:
        return first_site_point.y + second_site_point.y < 2 * point.y
    return (distance_to_point_arc(first_site, point, dot_producer)
            < distance_to_point_arc(second_site, point, dot_producer))


def point_segment_horizontal_goes_through_right_arc_first(
        point_site: Site,
        segment_site: Site,
        point: Point,
        reverse_order: bool,
        cross_producer: CrossProducer,
        dot_producer: DotProducer,
        orienteer: Orienteer) -> bool:
    segment_start, segment_end = segment_site.start, segment_site.end
    if (orienteer(segment_start, segment_end, point)
            is not Orientation.CLOCKWISE):
        return not segment_site.is_inverse
    elif segment_site.is_vertical:
        site_point = point_site.start
        if point.y < site_point.y and not reverse_order:
            return False
        elif point.y > site_point.y and reverse_order:
            return True
    elif cross_producer(segment_start, segment_end, point_site.start,
                        point) > 0:
        if not segment_site.is_inverse:
            if reverse_order:
                return True
        elif not reverse_order:
            return False
    else:
        site_point = point_site.start
        points_dx, points_dy = (point.x - site_point.x,
                                point.y - site_point.y)
        segment_dx, segment_dy = (segment_end.x - segment_start.x,
                                  segment_end.y - segment_start.y)
        fast_left_expr = (segment_dx * (points_dy + points_dx)
                          * (points_dy - points_dx))
        fast_right_expr = 2 * segment_dy * points_dx * points_dy
        if (fast_left_expr > fast_right_expr) is not reverse_order:
            return reverse_order
    return ((distance_to_point_arc(point_site, point, dot_producer)
             < distance_to_segment_arc(segment_site, point, cross_producer,
                                       dot_producer))
            is not reverse_order)


def segment_segment_horizontal_goes_through_right_arc_first(
        first_segment_site: Site,
        second_segment_site: Site,
        point: Point,
        cross_producer: CrossProducer,
        dot_producer: DotProducer,
        orienteer: Orienteer) -> bool:
    return (orienteer(first_segment_site.start, first_segment_site.end,
                      point) is Orientation.COUNTERCLOCKWISE
            if (first_segment_site.sorted_index
                == second_segment_site.sorted_index)
            else (distance_to_segment_arc(first_segment_site, point,
                                          cross_producer, dot_producer)
                  < distance_to_segment_arc(second_segment_site, point,
                                            cross_producer, dot_producer)))
