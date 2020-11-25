from copy import copy
from math import sqrt

from sect.core.voronoi.robust_difference import RobustDifference
from sect.core.voronoi.robust_float import RobustFloat
from sect.core.voronoi.utils import (robust_cross_product,
                                     safe_divide_floats)
from .models import (ULPS,
                     CircleEvent,
                     SiteEvent)
from .predicates import (point_point_point_circle_exists,
                         point_point_segment_circle_exists,
                         point_segment_segment_circle_exists,
                         segment_segment_segment_circle_exists)
from .utils import (
    robust_sum_of_products_with_sqrt_pairs as pairs_sum_expression,
    robust_sum_of_products_with_sqrt_quadruplets as quadruplets_sum_expression,
    robust_sum_of_products_with_sqrt_triplets as triplets_sum_expression,
    to_second_point_segment_segment_quadruplets_expression
    as to_quadruplets_expression)


def compute_circle_event(circle_event: CircleEvent,
                         first_site: SiteEvent,
                         second_site: SiteEvent,
                         third_site: SiteEvent) -> bool:
    if first_site.is_point:
        if second_site.is_point:
            if third_site.is_point:
                # (point, point, point) sites
                if not point_point_point_circle_exists(first_site, second_site,
                                                       third_site):
                    return False
                compute_point_point_point_circle_event(circle_event,
                                                       first_site, second_site,
                                                       third_site)
            else:
                # (point, point, segment) sites
                if not point_point_segment_circle_exists(first_site,
                                                         second_site,
                                                         third_site, 3):
                    return False
                compute_point_point_segment_circle_event(circle_event,
                                                         first_site,
                                                         second_site,
                                                         third_site, 3)
        elif third_site.is_point:
            # (point, segment, point) sites
            if not point_point_segment_circle_exists(first_site, third_site,
                                                     second_site, 2):
                return False
            compute_point_point_segment_circle_event(circle_event,
                                                     first_site,
                                                     third_site,
                                                     second_site, 2)
        else:
            # (point, segment, segment) sites.
            if not point_segment_segment_circle_exists(first_site, second_site,
                                                       third_site, 1):
                return False
            compute_point_segment_segment_circle_event(circle_event,
                                                       first_site, second_site,
                                                       third_site, 1)
    elif second_site.is_point:
        if third_site.is_point:
            # (segment, point, point) sites
            if (not point_point_segment_circle_exists(second_site, third_site,
                                                      first_site, 1)):
                return False
            compute_point_point_segment_circle_event(circle_event, second_site,
                                                     third_site, first_site, 1)
        else:
            # (segment, point, segment) sites
            if (not point_segment_segment_circle_exists(second_site,
                                                        first_site, third_site,
                                                        2)):
                return False
            compute_point_segment_segment_circle_event(circle_event,
                                                       second_site, first_site,
                                                       third_site, 2)
    else:
        if third_site.is_point:
            # (segment, segment, point) sites
            if (not point_segment_segment_circle_exists(third_site, first_site,
                                                        second_site, 3)):
                return False
            compute_point_segment_segment_circle_event(circle_event,
                                                       third_site, first_site,
                                                       second_site, 3)
        else:
            # (segment, segment, segment) sites
            if not segment_segment_segment_circle_exists(first_site,
                                                         second_site,
                                                         third_site):
                return False
            compute_segment_segment_segment_circle_event(circle_event,
                                                         first_site,
                                                         second_site,
                                                         third_site)
    return not (circle_event.lies_outside_vertical_segment(first_site)
                or circle_event.lies_outside_vertical_segment(second_site)
                or circle_event.lies_outside_vertical_segment(third_site))


def compute_point_point_point_circle_event(circle_event: CircleEvent,
                                           first_site: SiteEvent,
                                           second_site: SiteEvent,
                                           third_site: SiteEvent) -> None:
    first_site_start_x, first_site_start_y = first_site.start
    second_site_start_x, second_site_start_y = second_site.start
    third_site_start_x, third_site_start_y = third_site.start
    first_second_dx = float(first_site_start_x) - float(second_site_start_x)
    second_third_dx = float(second_site_start_x) - float(third_site_start_x)
    first_second_dy = float(first_site_start_y) - float(second_site_start_y)
    second_third_dy = float(second_site_start_y) - float(third_site_start_y)
    signed_area = robust_cross_product(
            first_site_start_x - second_site_start_x,
            second_site_start_x - third_site_start_x,
            first_site_start_y - second_site_start_y,
            second_site_start_y - third_site_start_y)
    inverted_signed_area = RobustFloat(safe_divide_floats(0.5, signed_area),
                                       2.)
    first_sx = float(first_site_start_x) + float(second_site_start_x)
    second_sx = float(second_site_start_x) + float(third_site_start_x)
    first_sy = float(first_site_start_y) + float(second_site_start_y)
    second_sy = float(second_site_start_y) + float(third_site_start_y)
    first_third_dx = float(first_site_start_x) - float(third_site_start_x)
    first_third_dy = float(first_site_start_y) - float(third_site_start_y)
    center_x, center_y = RobustDifference.zero(), RobustDifference.zero()
    center_x += RobustFloat(first_second_dx * first_sx * second_third_dy, 2.)
    center_x += RobustFloat(first_second_dy * first_sy * second_third_dy, 2.)
    center_x -= RobustFloat(second_third_dx * second_sx * first_second_dy, 2.)
    center_x -= RobustFloat(second_third_dy * second_sy * first_second_dy, 2.)
    center_y += RobustFloat(second_third_dx * second_sx * first_second_dx, 2.)
    center_y += RobustFloat(second_third_dy * second_sy * first_second_dx, 2.)
    center_y -= RobustFloat(first_second_dx * first_sx * second_third_dx, 2.)
    center_y -= RobustFloat(first_second_dy * first_sy * second_third_dx, 2.)
    lower_x = copy(center_x)
    lower_x -= RobustFloat(sqrt((first_second_dx * first_second_dx
                                 + first_second_dy * first_second_dy)
                                * (second_third_dx * second_third_dx
                                   + second_third_dy * second_third_dy)
                                * (first_third_dx * first_third_dx
                                   + first_third_dy * first_third_dy)),
                           5.)
    center_x = center_x.evaluate()
    center_y = center_y.evaluate()
    lower_x = lower_x.evaluate()
    circle_event.center_x = center_x.value * inverted_signed_area.value
    circle_event.center_y = center_y.value * inverted_signed_area.value
    circle_event.lower_x = lower_x.value * inverted_signed_area.value
    circle_event.is_active = True
    recompute_center_x = center_x.relative_error > ULPS
    recompute_center_y = center_y.relative_error > ULPS
    recompute_lower_x = lower_x.relative_error > ULPS
    if recompute_center_x or recompute_center_y or recompute_lower_x:
        recompute_point_point_point_circle_event(circle_event, first_site,
                                                 second_site, third_site,
                                                 recompute_center_x,
                                                 recompute_center_y,
                                                 recompute_lower_x)


def compute_point_point_segment_circle_event(circle_event: CircleEvent,
                                             first_site: SiteEvent,
                                             second_site: SiteEvent,
                                             third_site: SiteEvent,
                                             segment_index: int) -> None:
    first_site_start_x, first_site_start_y = first_site.start
    second_site_start_x, second_site_start_y = second_site.start
    third_site_start_x, third_site_start_y = third_site.start
    third_site_end_x, third_site_end_y = third_site.end
    segment_dx = float(third_site_end_x) - float(third_site_start_x)
    segment_dy = float(third_site_end_y) - float(third_site_start_y)
    points_dx = float(second_site_start_y) - float(first_site_start_y)
    points_dy = float(second_site_start_x) - float(first_site_start_x)
    theta = RobustFloat(
            robust_cross_product(third_site_end_y - third_site_start_y,
                                 third_site_start_x - third_site_end_x,
                                 second_site_start_x - first_site_start_x,
                                 second_site_start_y - first_site_start_y),
            1.)
    first_signed_area = RobustFloat(
            robust_cross_product(third_site_start_y - third_site_end_y,
                                 third_site_start_x - third_site_end_x,
                                 third_site_end_y - first_site_start_y,
                                 third_site_end_x - first_site_start_x),
            1.)
    second_signed_area = RobustFloat(
            robust_cross_product(third_site_start_y - third_site_end_y,
                                 third_site_start_x - third_site_end_x,
                                 third_site_end_y - second_site_start_y,
                                 third_site_end_x - second_site_start_x),
            1.)
    denominator = RobustFloat(
            robust_cross_product(first_site_start_y - second_site_start_y,
                                 first_site_start_x - second_site_start_x,
                                 third_site_end_y - third_site_start_y,
                                 third_site_end_x - third_site_start_x),
            1.)
    inverted_segment_length = RobustFloat(
            safe_divide_floats(1., sqrt(segment_dy * segment_dy
                                        + segment_dx * segment_dx)),
            3.)
    t = RobustDifference.zero()
    if denominator:
        squared_denominator = denominator * denominator
        determinant = ((theta * theta + squared_denominator)
                       * first_signed_area * second_signed_area).sqrt()
        t += (-determinant
              if segment_index == 2
              else determinant) / squared_denominator
        t += (theta * (first_signed_area + second_signed_area)
              / (RobustFloat(2.) * squared_denominator))
    else:
        t += theta / (RobustFloat(8.) * first_signed_area)
        t -= first_signed_area / (RobustFloat(2.) * theta)
    center_x = RobustDifference.zero()
    center_x += RobustFloat(0.5 * (float(first_site_start_x)
                                   + float(second_site_start_x)))
    center_x += t * RobustFloat(points_dx)
    center_y = RobustDifference.zero()
    center_y += RobustFloat(0.5 * (float(first_site_start_y)
                                   + float(second_site_start_y)))
    center_y -= t * RobustFloat(points_dy)
    r = RobustDifference.zero()
    r -= RobustFloat(segment_dy) * RobustFloat(third_site_start_x)
    r += RobustFloat(segment_dx) * RobustFloat(third_site_start_y)
    r += center_x * RobustFloat(segment_dy)
    r -= center_y * RobustFloat(segment_dx)
    r = abs(r)
    lower_x = copy(center_x)
    lower_x += r * inverted_segment_length
    center_x = center_x.evaluate()
    center_y = center_y.evaluate()
    lower_x = lower_x.evaluate()
    circle_event.center_x = center_x.value
    circle_event.center_y = center_y.value
    circle_event.lower_x = lower_x.value
    circle_event.is_active = True
    recompute_center_x = center_x.relative_error > ULPS
    recompute_center_y = center_y.relative_error > ULPS
    recompute_lower_x = lower_x.relative_error > ULPS
    if recompute_center_x or recompute_center_y or recompute_lower_x:
        recompute_point_point_segment_circle_event(circle_event, first_site,
                                                   second_site, third_site,
                                                   segment_index,
                                                   recompute_center_x,
                                                   recompute_center_y,
                                                   recompute_lower_x)


def compute_point_segment_segment_circle_event(circle_event: CircleEvent,
                                               first_site: SiteEvent,
                                               second_site: SiteEvent,
                                               third_site: SiteEvent,
                                               point_index: int) -> None:
    first_segment_start_x, first_segment_start_y = second_site.start
    first_segment_end_x, first_segment_end_y = second_site.end
    second_segment_start_x, second_segment_start_y = third_site.start
    second_segment_end_x, second_segment_end_y = third_site.end
    first_segment_dx = (float(first_segment_end_x)
                        - float(first_segment_start_x))
    first_segment_dy = (float(first_segment_end_y)
                        - float(first_segment_start_y))
    second_segment_dx = (float(second_segment_end_x)
                         - float(second_segment_start_x))
    second_segment_dy = (float(second_segment_end_y)
                         - float(second_segment_start_y))
    segments_signed_area = RobustFloat(
            robust_cross_product(
                    first_segment_start_y - first_segment_end_y,
                    first_segment_start_x - first_segment_end_x,
                    second_segment_end_y - second_segment_start_y,
                    second_segment_end_x - second_segment_start_x),
            1.)
    first_segment_squared_length = (first_segment_dx * first_segment_dx
                                    + first_segment_dy * first_segment_dy)
    first_site_start_x, first_site_start_y = first_site.start
    if segments_signed_area:
        first_segment_length = RobustFloat(sqrt(first_segment_squared_length),
                                           2.)
        second_segment_length = RobustFloat(
                sqrt(second_segment_dx * second_segment_dx
                     + second_segment_dy * second_segment_dy),
                2.)
        a = RobustFloat(
                robust_cross_product(
                        first_segment_start_x - first_segment_end_x,
                        first_segment_start_y - first_segment_end_y,
                        second_segment_start_y - second_segment_end_y,
                        second_segment_end_x - second_segment_start_x),
                1.)
        if a < 0:
            a = ((segments_signed_area * segments_signed_area)
                 / (first_segment_length * second_segment_length - a))
        else:
            a += first_segment_length * second_segment_length
        first_signed_area = RobustFloat(
                robust_cross_product(
                        first_segment_start_y - first_segment_end_y,
                        first_segment_start_x - first_segment_end_x,
                        first_segment_start_y - first_site_start_y,
                        first_segment_start_x - first_site_start_x),
                1.)
        second_signed_area = RobustFloat(
                robust_cross_product(
                        second_segment_end_x - second_segment_start_x,
                        second_segment_end_y - second_segment_start_y,
                        second_segment_end_x - first_site_start_x,
                        second_segment_end_y - first_site_start_y),
                1.)
        determinant = (RobustFloat(2.) * a * first_signed_area
                       * second_signed_area)
        first_segment_signed_area = RobustFloat(
                robust_cross_product(
                        first_segment_start_y - first_segment_end_y,
                        first_segment_start_x - first_segment_end_x,
                        first_segment_start_y, first_segment_start_x),
                1.)
        second_segment_signed_area = RobustFloat(
                robust_cross_product(
                        second_segment_end_x - second_segment_start_x,
                        second_segment_end_y - second_segment_start_y,
                        second_segment_end_x, second_segment_end_y),
                1.)
        inverted_segments_signed_area = RobustFloat(1.) / segments_signed_area
        t = RobustDifference.zero()
        b = RobustDifference.zero()
        ix = RobustDifference.zero()
        ix += (RobustFloat(second_segment_dx) * first_segment_signed_area
               * inverted_segments_signed_area)
        ix -= (RobustFloat(first_segment_dx) * second_segment_signed_area
               * inverted_segments_signed_area)
        iy = RobustDifference.zero()
        iy -= (RobustFloat(first_segment_dy) * second_segment_signed_area
               * inverted_segments_signed_area)
        iy += (RobustFloat(second_segment_dy) * first_segment_signed_area
               * inverted_segments_signed_area)
        b -= ix * (RobustFloat(first_segment_dx) * second_segment_length)
        b += ix * (RobustFloat(second_segment_dx) * first_segment_length)
        b -= iy * (RobustFloat(first_segment_dy) * second_segment_length)
        b += iy * (RobustFloat(second_segment_dy) * first_segment_length)
        b -= (first_segment_length
              * RobustFloat(robust_cross_product(
                        second_segment_end_x - second_segment_start_x,
                        second_segment_end_y - second_segment_start_y,
                        -first_site_start_y,
                        first_site_start_x),
                        1.))
        b -= (second_segment_length
              * RobustFloat(robust_cross_product(
                        first_segment_start_x - first_segment_end_x,
                        first_segment_start_y - first_segment_end_y,
                        -first_site_start_y,
                        first_site_start_x),
                        1.))
        t -= b
        t += determinant.sqrt() if point_index == 2 else -determinant.sqrt()
        t /= a * a
        center_x = copy(ix)
        center_x -= t * (RobustFloat(first_segment_dx) * second_segment_length)
        center_x += t * (RobustFloat(second_segment_dx) * first_segment_length)
        center_y = copy(iy)
        center_y -= t * (RobustFloat(first_segment_dy) * second_segment_length)
        center_y += t * (RobustFloat(second_segment_dy) * first_segment_length)
        lower_x = copy(center_x)
        lower_x += abs(t) * abs(segments_signed_area)
    else:
        a = RobustFloat(first_segment_squared_length, 2.)
        c = RobustFloat(
                robust_cross_product(
                        first_segment_start_y - first_segment_end_y,
                        first_segment_start_x - first_segment_end_x,
                        second_segment_start_y - first_segment_end_y,
                        second_segment_start_x - first_segment_end_x),
                1.)
        determinant = RobustFloat(
                robust_cross_product(
                        first_segment_start_x - first_segment_end_x,
                        first_segment_start_y - first_segment_end_y,
                        first_site_start_x - first_segment_end_x,
                        first_site_start_y - first_segment_end_y)
                * robust_cross_product(
                        first_segment_start_y - first_segment_end_y,
                        first_segment_start_x - first_segment_end_x,
                        first_site_start_y - second_segment_start_y,
                        first_site_start_x - second_segment_start_x),
                3.)
        t = RobustDifference.zero()
        t += (RobustFloat(first_segment_dx)
              * RobustFloat(0.5 * (float(first_segment_end_x)
                                   + float(second_segment_start_x))
                            - float(first_site_start_x)))
        t += (RobustFloat(first_segment_dy)
              * RobustFloat(0.5 * (float(first_segment_end_y)
                                   + float(second_segment_start_y))
                            - float(first_site_start_y)))
        t += determinant.sqrt() if point_index == 2 else -determinant.sqrt()
        t /= a
        center_x = RobustDifference.zero()
        center_x += RobustFloat(0.5 * (float(first_segment_end_x)
                                       + float(second_segment_start_x)))
        center_x -= t * RobustFloat(first_segment_dx)
        center_y = RobustDifference.zero()
        center_y += RobustFloat(0.5 * (float(first_segment_end_y)
                                       + float(second_segment_start_y)))
        center_y -= t * RobustFloat(first_segment_dy)
        lower_x = copy(center_x)
        lower_x += RobustFloat(0.5) * abs(c) / a.sqrt()
    center_x = center_x.evaluate()
    center_y = center_y.evaluate()
    lower_x = lower_x.evaluate()
    recompute_center_x = center_x.relative_error > ULPS
    recompute_center_y = center_y.relative_error > ULPS
    recompute_lower_x = lower_x.relative_error > ULPS
    circle_event.center_x = center_x.value
    circle_event.center_y = center_y.value
    circle_event.lower_x = lower_x.value
    circle_event.is_active = True
    if recompute_center_x or recompute_center_y or recompute_lower_x:
        recompute_point_segment_segment_circle_event(circle_event, first_site,
                                                     second_site, third_site,
                                                     point_index,
                                                     recompute_center_x,
                                                     recompute_center_y,
                                                     recompute_lower_x)


def compute_segment_segment_segment_circle_event(circle_event: CircleEvent,
                                                 first_site: SiteEvent,
                                                 second_site: SiteEvent,
                                                 third_site: SiteEvent
                                                 ) -> None:
    first_site_start_x, first_site_start_y = first_site.start
    first_site_end_x, first_site_end_y = first_site.end
    second_site_start_x, second_site_start_y = second_site.start
    second_site_end_x, second_site_end_y = second_site.end
    third_site_start_x, third_site_start_y = third_site.start
    third_site_end_x, third_site_end_y = third_site.end
    first_dx = RobustFloat(float(first_site_end_x) - float(first_site_start_x))
    first_dy = RobustFloat(float(first_site_end_y) - float(first_site_start_y))
    first_signed_area = RobustFloat(robust_cross_product(first_site_start_x,
                                                         first_site_start_y,
                                                         first_site_end_x,
                                                         first_site_end_y),
                                    1.)
    second_dx = RobustFloat(float(second_site_end_x)
                            - float(second_site_start_x))
    second_dy = RobustFloat(float(second_site_end_y)
                            - float(second_site_start_y))
    second_signed_area = RobustFloat(
            robust_cross_product(second_site_start_x, second_site_start_y,
                                 second_site_end_x, second_site_end_y),
            1.)
    third_dx = RobustFloat(float(third_site_end_x) - float(third_site_start_x))
    third_dy = RobustFloat(float(third_site_end_y) - float(third_site_start_y))
    third_signed_area = RobustFloat(
            robust_cross_product(third_site_start_x, third_site_start_y,
                                 third_site_end_x, third_site_end_y),
            1.)
    first_length = (first_dx * first_dx + first_dy * first_dy).sqrt()
    second_length = (second_dx * second_dx + second_dy * second_dy).sqrt()
    third_length = (third_dx * third_dx + third_dy * third_dy).sqrt()
    first_second_signed_area = RobustFloat(
            robust_cross_product(first_site_end_x - first_site_start_x,
                                 first_site_end_y - first_site_start_y,
                                 second_site_end_x - second_site_start_x,
                                 second_site_end_y - second_site_start_y),
            1.)
    second_third_signed_area = RobustFloat(
            robust_cross_product(second_site_end_x - second_site_start_x,
                                 second_site_end_y - second_site_start_y,
                                 third_site_end_x - third_site_start_x,
                                 third_site_end_y - third_site_start_y),
            1.)
    third_first_signed_area = RobustFloat(
            robust_cross_product(third_site_end_x - third_site_start_x,
                                 third_site_end_y - third_site_start_y,
                                 first_site_end_x - first_site_start_x,
                                 first_site_end_y - first_site_start_y),
            1.)
    denominator = RobustDifference.zero()
    denominator += first_second_signed_area * third_length
    denominator += second_third_signed_area * first_length
    denominator += third_first_signed_area * second_length
    r = RobustDifference.zero()
    r -= first_second_signed_area * third_signed_area
    r -= second_third_signed_area * first_signed_area
    r -= third_first_signed_area * second_signed_area
    center_x = RobustDifference.zero()
    center_x += first_dx * second_signed_area * third_length
    center_x -= second_dx * first_signed_area * third_length
    center_x += second_dx * third_signed_area * first_length
    center_x -= third_dx * second_signed_area * first_length
    center_x += third_dx * first_signed_area * second_length
    center_x -= first_dx * third_signed_area * second_length
    center_y = RobustDifference.zero()
    center_y += first_dy * second_signed_area * third_length
    center_y -= second_dy * first_signed_area * third_length
    center_y += second_dy * third_signed_area * first_length
    center_y -= third_dy * second_signed_area * first_length
    center_y += third_dy * first_signed_area * second_length
    center_y -= first_dy * third_signed_area * second_length
    lower_x = center_x + r
    denominator = denominator.evaluate()
    center_x = center_x.evaluate() / denominator
    center_y = center_y.evaluate() / denominator
    lower_x = lower_x.evaluate() / denominator
    recompute_center_x = center_x.relative_error > ULPS
    recompute_center_y = center_y.relative_error > ULPS
    recompute_lower_x = lower_x.relative_error > ULPS
    circle_event.center_x = center_x.value
    circle_event.center_y = center_y.value
    circle_event.lower_x = lower_x.value
    circle_event.is_active = True
    if recompute_center_x or recompute_center_y or recompute_lower_x:
        recompute_segment_segment_segment_circle_event(circle_event,
                                                       first_site, second_site,
                                                       third_site,
                                                       recompute_center_x,
                                                       recompute_center_y,
                                                       recompute_lower_x)


def recompute_point_point_point_circle_event(circle_event: CircleEvent,
                                             first_site: SiteEvent,
                                             second_site: SiteEvent,
                                             third_site: SiteEvent,
                                             recompute_center_x: bool = True,
                                             recompute_center_y: bool = True,
                                             recompute_lower_x: bool = True
                                             ) -> None:
    first_site_start_x, first_site_start_y = first_site.start
    second_site_start_x, second_site_start_y = second_site.start
    third_site_start_x, third_site_start_y = third_site.start
    first_dx = first_site_start_x - second_site_start_x
    first_dy = first_site_start_y - second_site_start_y
    second_dx = second_site_start_x - third_site_start_x
    second_dy = second_site_start_y - third_site_start_y
    inverted_denominator = safe_divide_floats(0.5,
                                              float(first_dx * second_dy
                                                    - second_dx * first_dy))
    first_sx = first_site_start_x + second_site_start_x
    first_sy = first_site_start_y + second_site_start_y
    second_sx = second_site_start_x + third_site_start_x
    second_sy = second_site_start_y + third_site_start_y
    first_numerator = first_dx * first_sx + first_dy * first_sy
    second_numerator = second_dx * second_sx + second_dy * second_sy
    if recompute_center_x or recompute_lower_x:
        center_x_numerator = (first_numerator * second_dy
                              - second_numerator * first_dy)
        center_x = circle_event.center_x = (float(center_x_numerator)
                                            * inverted_denominator)
        if recompute_lower_x:
            third_dx = first_site_start_x - third_site_start_x
            third_dy = first_site_start_y - third_site_start_y
            squared_radius = ((first_dx * first_dx + first_dy * first_dy)
                              * (second_dx * second_dx + second_dy * second_dy)
                              * (third_dx * third_dx + third_dy * third_dy))
            radius = sqrt(float(squared_radius))
            # if ``center_x >= 0`` then ``lower_x = center_x + r``,
            # else ``lower_x = (center_x * center_x - r * r) / (center_x - r)``
            # to guarantee epsilon relative error
            circle_event.lower_x = (
                safe_divide_floats(
                        float(center_x_numerator * center_x_numerator
                              - squared_radius) * inverted_denominator,
                        float(center_x_numerator) + radius)
                if center_x < 0
                else (center_x - radius * inverted_denominator
                      if inverted_denominator < 0
                      else center_x + radius * inverted_denominator))
    if recompute_center_y:
        circle_event.center_y = (float(second_numerator * first_dx
                                       - first_numerator * second_dx)
                                 * inverted_denominator)


def recompute_point_point_segment_circle_event(circle_event: CircleEvent,
                                               first_site: SiteEvent,
                                               second_site: SiteEvent,
                                               third_site: SiteEvent,
                                               segment_index: int,
                                               recompute_center_x: bool = True,
                                               recompute_center_y: bool = True,
                                               recompute_lower_x: bool = True
                                               ) -> None:
    first_site_start_x, first_site_start_y = first_site.start
    third_site_start_x, third_site_start_y = third_site.start
    third_site_end_x, third_site_end_y = third_site.end
    segment_dx = third_site_end_x - third_site_start_x
    segment_dy = third_site_end_y - third_site_start_y
    segment_length = segment_dx * segment_dx + segment_dy * segment_dy
    second_site_start_x, second_site_start_y = second_site.start
    perpendicular_x = second_site_start_y - first_site_start_y
    perpendicular_y = first_site_start_x - second_site_start_x
    points_sx = first_site_start_x + second_site_start_x
    points_sy = first_site_start_y + second_site_start_y
    signed_perpendicular_area = (perpendicular_x * segment_dy
                                 - segment_dx * perpendicular_y)
    signed_perpendicular_projection_length = (perpendicular_x * segment_dx
                                              + perpendicular_y * segment_dy)
    # signed area of parallelogram built on
    signed_first_point_area = (
            segment_dy * (first_site_start_x - third_site_end_x)
            - segment_dx * (first_site_start_y - third_site_end_y))
    signed_second_point_area = (
            segment_dy * (second_site_start_x - third_site_end_x)
            - segment_dx * (second_site_start_y - third_site_end_y))
    signed_points_area = signed_first_point_area + signed_second_point_area
    squared_perpendicular_area = (signed_perpendicular_area
                                  * signed_perpendicular_area)
    if not signed_perpendicular_projection_length:
        squared_points_area = signed_points_area * signed_points_area
        numerator = squared_perpendicular_area - squared_points_area
        determinant = signed_perpendicular_area * signed_points_area
        coefficients = (2 * determinant * points_sx
                        + numerator * perpendicular_x,
                        signed_perpendicular_area
                        * (2 * squared_points_area + numerator))
        inverted_denominator = safe_divide_floats(1., float(determinant))
        if recompute_center_x:
            circle_event.center_x = (0.25 * float(coefficients[0])
                                     * inverted_denominator)
        if recompute_center_y:
            circle_event.center_y = (0.25
                                     * float((2 * determinant * points_sy)
                                             + numerator * perpendicular_y)
                                     * inverted_denominator)
        if recompute_lower_x:
            circle_event.lower_x = safe_divide_floats(
                    0.25 * float(pairs_sum_expression(coefficients[:2],
                                                      (segment_length, 1)))
                    * inverted_denominator,
                    sqrt(float(segment_length)))
    else:
        squared_perpendicular_projection_length = (
                signed_perpendicular_projection_length
                * signed_perpendicular_projection_length)
        determinant = (4 * (squared_perpendicular_area
                            + squared_perpendicular_projection_length)
                       * signed_first_point_area * signed_second_point_area)
        squared_inverted_denominator = 1. / float(
                signed_perpendicular_projection_length)
        squared_inverted_denominator *= squared_inverted_denominator
        if recompute_center_x or recompute_lower_x:
            coefficients = (points_sx * squared_perpendicular_projection_length
                            + (signed_perpendicular_area * signed_points_area
                               * perpendicular_x),
                            -perpendicular_x
                            if segment_index == 2
                            else perpendicular_x)
            if recompute_center_x:
                circle_event.center_x = (0.5 * float(
                        pairs_sum_expression(coefficients, (1, determinant)))
                                         * squared_inverted_denominator)
            if recompute_lower_x:
                circle_event.lower_x = (0.5 * float(quadruplets_sum_expression(
                        coefficients
                        + (signed_points_area
                           * (squared_perpendicular_projection_length
                              + squared_perpendicular_area),
                           -signed_perpendicular_area
                           if segment_index == 2
                           else signed_perpendicular_area),
                        (segment_length, determinant * segment_length, 1,
                         determinant)))
                                        * squared_inverted_denominator
                                        / sqrt(float(segment_length)))
        if recompute_center_y:
            circle_event.center_y = (0.5 * float(pairs_sum_expression(
                    (points_sy * squared_perpendicular_projection_length
                     + (signed_perpendicular_area * signed_points_area
                        * perpendicular_y),
                     -perpendicular_y
                     if segment_index == 2
                     else perpendicular_y),
                    (1, determinant))) * squared_inverted_denominator)


def recompute_point_segment_segment_circle_event(
        circle_event: CircleEvent,
        first_site: SiteEvent,
        second_site: SiteEvent,
        third_site: SiteEvent,
        point_index: int,
        recompute_center_x: bool = True,
        recompute_center_y: bool = True,
        recompute_lower_x: bool = True) -> None:
    first_site_start_x, first_site_start_y = first_site.start
    second_start_x, second_start_y = second_site.start
    second_end_x, second_end_y = second_site.end
    third_start_x, third_start_y = third_site.start
    third_end_x, third_end_y = third_site.end
    second_dx = second_end_x - second_start_x
    second_dy = second_end_y - second_start_y
    third_dx = third_end_x - third_start_x
    third_dy = third_end_y - third_start_y
    third_second_signed_area = second_dx * third_dy - third_dx * second_dy
    squared_second_dx = second_dx * second_dx
    squared_second_dy = second_dy * second_dy
    if third_second_signed_area:
        third_signed_area = third_dx * third_end_y - third_dy * third_end_x
        second_signed_area = (second_dx * second_start_y
                              - second_dy * second_start_x)
        ix = third_dx * second_signed_area - second_dx * third_signed_area
        iy = third_dy * second_signed_area - second_dy * third_signed_area
        dx = ix - third_second_signed_area * first_site_start_x
        dy = iy - third_second_signed_area * first_site_start_y
        if dx or dy:
            sign = ((-1 if point_index == 2 else 1)
                    * third_second_signed_area.sign)
            common_right_coefficients = (
                squared_second_dx + squared_second_dy,
                third_dx * third_dx + third_dy * third_dy,
                -second_dx * third_dx - second_dy * third_dy,
                -2 * (second_dy * dx - second_dx * dy)
                * (third_dx * dy - third_dy * dx))
            temp = float(to_quadruplets_expression(
                    (-third_dx * dx - third_dy * dy,
                     second_dx * dx + second_dy * dy, sign, 0),
                    common_right_coefficients))
            denominator = temp * float(third_second_signed_area)
            squared_length = dx * dx + dy * dy
            if recompute_center_y:
                circle_event.center_y = (float(to_quadruplets_expression(
                        (third_dy * squared_length
                         - iy * (dx * third_dx + dy * third_dy),
                         iy * (dx * second_dx + dy * second_dy)
                         - second_dy * squared_length,
                         iy * sign, 0),
                        common_right_coefficients))
                                         / denominator)
            if recompute_center_x or recompute_lower_x:
                common_left_coefficients = (
                    third_dx * squared_length
                    - ix * (dx * third_dx + dy * third_dy),
                    ix * (dx * second_dx + dy * second_dy)
                    - second_dx * squared_length,
                    ix * sign)
                if recompute_center_x:
                    circle_event.center_x = (float(to_quadruplets_expression(
                            common_left_coefficients + ((0),),
                            common_right_coefficients))
                                             / denominator)
                if recompute_lower_x:
                    circle_event.lower_x = (float(to_quadruplets_expression(
                            common_left_coefficients
                            + (third_second_signed_area * squared_length
                               * (-1 if temp < 0 else 1),),
                            common_right_coefficients))
                                            / denominator)
        else:
            denominator = float(third_second_signed_area)
            circle_event.center_x = circle_event.lower_x = (float(ix)
                                                            / denominator)
            circle_event.center_y = float(iy) / denominator
            circle_event.is_active = True
    else:
        denominator = 2. * float(squared_second_dx + squared_second_dy)
        dx = (second_dy * (first_site_start_x - second_end_x)
              - second_dx * (first_site_start_y - second_end_y))
        dy = (second_dx * (first_site_start_y - third_start_y)
              - second_dy * (first_site_start_x - third_start_x))
        common_right_coefficients = (dx * dy, 1)
        if recompute_center_y:
            circle_event.center_y = safe_divide_floats(
                    float(pairs_sum_expression(
                            (second_dy * (-2 if point_index == 2 else 2),
                             squared_second_dx * (second_end_y + third_start_y)
                             - second_dx * second_dy
                             * (second_end_x + third_start_x
                                - first_site_start_x * 2)
                             + squared_second_dy * (first_site_start_y * 2)),
                            common_right_coefficients)),
                    denominator)
        if recompute_center_x or recompute_lower_x:
            common_left_coefficients = ((-2 if point_index == 2 else 2)
                                        * second_dx,
                                        squared_second_dy
                                        * (second_end_x + third_start_x)
                                        - second_dx * second_dy
                                        * (second_end_y + third_start_y
                                           - 2 * first_site_start_y)
                                        + squared_second_dx
                                        * (2 * first_site_start_x))
            if recompute_center_x:
                circle_event.center_x = safe_divide_floats(
                        float(pairs_sum_expression(common_left_coefficients,
                                                   common_right_coefficients)),
                        denominator)
            if recompute_lower_x:
                third_start_second_end_dx = third_start_x - second_end_x
                third_start_second_end_dy = third_start_y - second_end_y
                circle_event.lower_x = safe_divide_floats(
                        float(triplets_sum_expression(
                                common_left_coefficients
                                + (abs(second_dx * third_start_second_end_dy
                                       - second_dy
                                       * third_start_second_end_dx),),
                                common_right_coefficients
                                + (squared_second_dx + squared_second_dy,))),
                        denominator)


def recompute_segment_segment_segment_circle_event(
        circle_event: CircleEvent,
        first_site: SiteEvent,
        second_site: SiteEvent,
        third_site: SiteEvent,
        recompute_center_x: bool = True,
        recompute_center_y: bool = True,
        recompute_lower_x: bool = True) -> None:
    first_site_start_x, first_site_start_y = first_site.start
    first_site_end_x, first_site_end_y = first_site.end
    second_site_start_x, second_site_start_y = second_site.start
    second_site_end_x, second_site_end_y = second_site.end
    third_site_start_x, third_site_start_y = third_site.start
    third_site_end_x, third_site_end_y = third_site.end
    first_dx = first_site_end_x - first_site_start_x
    first_dy = first_site_end_y - first_site_start_y
    second_dx = second_site_end_x - second_site_start_x
    second_dy = second_site_end_y - second_site_start_y
    third_dx = third_site_end_x - third_site_start_x
    third_dy = third_site_end_y - third_site_start_y
    segments_lengths = (first_dx * first_dx + first_dy * first_dy,
                        second_dx * second_dx + second_dy * second_dy,
                        third_dx * third_dx + third_dy * third_dy)
    denominator = float(triplets_sum_expression(
            (second_dx * third_dy - third_dx * second_dy,
             third_dx * first_dy - first_dx * third_dy,
             first_dx * second_dy - second_dx * first_dy),
            segments_lengths))
    first_signed_area = (first_site_start_x * first_site_end_y
                         - first_site_start_y * first_site_end_x)
    second_signed_area = (second_site_start_x * second_site_end_y
                          - second_site_start_y * second_site_end_x)
    third_signed_area = (third_site_start_x * third_site_end_y
                         - third_site_start_y * third_site_end_x)
    if recompute_center_y:
        circle_event.center_y = safe_divide_floats(
                float(triplets_sum_expression(
                        (second_dy * third_signed_area
                         - third_dy * second_signed_area,
                         third_dy * first_signed_area
                         - first_dy * third_signed_area,
                         first_dy * second_signed_area
                         - second_dy * first_signed_area),
                        segments_lengths)),
                denominator)
    if recompute_center_x or recompute_lower_x:
        common_left_coefficients = (second_dx * third_signed_area
                                    - third_dx * second_signed_area,
                                    third_dx * first_signed_area
                                    - first_dx * third_signed_area,
                                    first_dx * second_signed_area
                                    - second_dx * first_signed_area)
        if recompute_center_x:
            circle_event.center_x = safe_divide_floats(
                    float(triplets_sum_expression(common_left_coefficients,
                                                  segments_lengths)),
                    denominator)
        if recompute_lower_x:
            circle_event.lower_x = safe_divide_floats(
                    float(quadruplets_sum_expression(
                            common_left_coefficients
                            + (common_left_coefficients[0] * first_dy
                               + common_left_coefficients[1] * second_dy
                               + common_left_coefficients[2] * third_dy,),
                            segments_lengths + (1,))),
                    denominator)
