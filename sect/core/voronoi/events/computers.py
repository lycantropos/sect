from copy import copy
from math import sqrt

from robust import (parallelogram,
                    projection)

from sect.core.voronoi.robust_difference import RobustDifference
from sect.core.voronoi.robust_float import RobustFloat
from sect.core.voronoi.utils import (robust_cross_product,
                                     safe_divide_floats)
from sect.hints import (Coordinate,
                        Point)
from .models import (ULPS,
                     CircleEvent,
                     SiteEvent)
from .utils import (
    robust_divide,
    robust_evenly_divide,
    robust_sqrt,
    robust_sum_of_products_with_sqrt_pairs as pairs_sum_expression,
    robust_sum_of_products_with_sqrt_quadruplets as quadruplets_sum_expression,
    robust_sum_of_products_with_sqrt_triplets as triplets_sum_expression,
    to_second_point_segment_segment_quadruplets_expression
    as to_quadruplets_expression,
    to_segment_squared_length)


def to_point_point_point_circle_event(first_site: SiteEvent,
                                      second_site: SiteEvent,
                                      third_site: SiteEvent) -> CircleEvent:
    first_x, first_y = first_point = first_site.start
    second_x, second_y = second_point = second_site.start
    third_x, third_y = third_point = third_site.start
    first_squared_norm = first_x * first_x + first_y * first_y
    second_squared_norm = second_x * second_x + second_y * second_y
    third_squared_norm = third_x * third_x + third_y * third_y
    center_x_numerator = (first_squared_norm * (second_y - third_y)
                          + second_squared_norm * (third_y - first_y)
                          + third_squared_norm * (first_y - second_y))
    center_y_numerator = -(first_squared_norm * (second_x - third_x)
                           + second_squared_norm * (third_x - first_x)
                           + third_squared_norm * (first_x - second_x))
    lower_x_numerator = center_x_numerator - robust_sqrt(
            to_segment_squared_length(first_point, second_point)
            * to_segment_squared_length(second_point, third_point)
            * to_segment_squared_length(first_point, third_point))
    signed_area = parallelogram.signed_area(first_point, second_point,
                                            second_point, third_point)
    inverted_signed_area = robust_divide(1, 2 * signed_area)
    return CircleEvent(center_x_numerator * inverted_signed_area,
                       center_y_numerator * inverted_signed_area,
                       lower_x_numerator * inverted_signed_area)


def to_point_point_segment_circle_event(first_point_event: SiteEvent,
                                        second_point_event: SiteEvent,
                                        segment_event: SiteEvent,
                                        segment_index: int) -> CircleEvent:
    first_point_x, first_point_y = first_point = first_point_event.start
    second_point_x, second_point_y = second_point = second_point_event.start
    segment_start, segment_end = segment_event.start, segment_event.end
    points_dx = second_point_y - first_point_y
    points_dy = second_point_x - first_point_x
    coefficient = _to_point_point_segment_coefficient(
            first_point, second_point, segment_start, segment_end,
            segment_index)
    center_x = robust_evenly_divide(first_point_x + second_point_x
                                    + coefficient * points_dx, 2)
    center_y = robust_evenly_divide(first_point_y + second_point_y
                                    - coefficient * points_dy, 2)
    r = abs(parallelogram.signed_area(segment_start, (center_x, center_y),
                                      segment_start, segment_end))
    squared_segment_length = to_segment_squared_length(segment_start,
                                                       segment_end)
    lower_x = center_x + r / robust_sqrt(squared_segment_length)
    return CircleEvent(center_x, center_y, lower_x)


def to_point_segment_segment_circle_event(first_site: SiteEvent,
                                          second_site: SiteEvent,
                                          third_site: SiteEvent,
                                          point_index: int) -> CircleEvent:
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
    center_x = center_x.value
    center_y = center_y.value
    lower_x = lower_x.value
    return (_to_point_segment_segment_circle_event(center_x, center_y, lower_x,
                                                   first_site, second_site,
                                                   third_site, point_index,
                                                   recompute_center_x,
                                                   recompute_center_y,
                                                   recompute_lower_x)
            if recompute_center_x or recompute_center_y or recompute_lower_x
            else CircleEvent(center_x, center_y, lower_x))


def to_segment_segment_segment_circle_event(first_site: SiteEvent,
                                            second_site: SiteEvent,
                                            third_site: SiteEvent
                                            ) -> CircleEvent:
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
    center_x = center_x.value
    center_y = center_y.value
    lower_x = lower_x.value
    return (_to_segment_segment_segment_circle_event(
            center_x, center_y, lower_x, first_site, second_site, third_site,
            recompute_center_x, recompute_center_y, recompute_lower_x)
            if recompute_center_x or recompute_center_y or recompute_lower_x
            else CircleEvent(center_x, center_y, lower_x))


def _to_point_point_segment_coefficient(first_point: Point,
                                        second_point: Point,
                                        segment_start: Point,
                                        segment_end: Point,
                                        segment_index: int) -> Coordinate:
    scalar_product = projection.signed_length(segment_start, segment_end,
                                              first_point, second_point)
    first_point_signed_area = parallelogram.signed_area(
            segment_start, segment_end, first_point, segment_end)
    signed_area = parallelogram.signed_area(first_point, second_point,
                                            segment_start, segment_end)
    if signed_area:
        second_point_signed_area = parallelogram.signed_area(
                segment_start, segment_end, second_point, segment_end)
        squared_signed_area = signed_area * signed_area
        determinant = robust_sqrt((scalar_product * scalar_product
                                   + squared_signed_area)
                                  * first_point_signed_area
                                  * second_point_signed_area)
        return robust_divide(2 * (-determinant
                                  if segment_index == 2
                                  else determinant)
                             + scalar_product * (first_point_signed_area
                                                 + second_point_signed_area),
                             squared_signed_area)
    else:
        return (robust_divide(scalar_product, 4 * first_point_signed_area)
                - robust_divide(first_point_signed_area, scalar_product))


def _to_point_segment_segment_circle_event(center_x: Coordinate,
                                           center_y: Coordinate,
                                           lower_x: Coordinate,
                                           first_site: SiteEvent,
                                           second_site: SiteEvent,
                                           third_site: SiteEvent,
                                           point_index: int,
                                           recompute_center_x: bool = True,
                                           recompute_center_y: bool = True,
                                           recompute_lower_x: bool = True
                                           ) -> CircleEvent:
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
                    * ((1 if third_second_signed_area > 0 else -1)
                       if third_second_signed_area
                       else 0))
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
                center_y = (float(to_quadruplets_expression(
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
                    center_x = (float(to_quadruplets_expression(
                            common_left_coefficients + (0,),
                            common_right_coefficients))
                                / denominator)
                if recompute_lower_x:
                    lower_x = (float(to_quadruplets_expression(
                            common_left_coefficients
                            + (third_second_signed_area * squared_length
                               * (-1 if temp < 0 else 1),),
                            common_right_coefficients))
                               / denominator)
        else:
            denominator = float(third_second_signed_area)
            center_x = lower_x = float(ix) / denominator
            center_y = float(iy) / denominator
    else:
        denominator = 2. * float(squared_second_dx + squared_second_dy)
        dx = (second_dy * (first_site_start_x - second_end_x)
              - second_dx * (first_site_start_y - second_end_y))
        dy = (second_dx * (first_site_start_y - third_start_y)
              - second_dy * (first_site_start_x - third_start_x))
        common_right_coefficients = (dx * dy, 1)
        if recompute_center_y:
            center_y = safe_divide_floats(
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
                center_x = safe_divide_floats(
                        float(pairs_sum_expression(common_left_coefficients,
                                                   common_right_coefficients)),
                        denominator)
            if recompute_lower_x:
                third_start_second_end_dx = third_start_x - second_end_x
                third_start_second_end_dy = third_start_y - second_end_y
                lower_x = safe_divide_floats(
                        float(triplets_sum_expression(
                                common_left_coefficients
                                + (abs(second_dx * third_start_second_end_dy
                                       - second_dy
                                       * third_start_second_end_dx),),
                                common_right_coefficients
                                + (squared_second_dx + squared_second_dy,))),
                        denominator)
    return CircleEvent(center_x, center_y, lower_x)


def _to_segment_segment_segment_circle_event(center_x: Coordinate,
                                             center_y: Coordinate,
                                             lower_x: Coordinate,
                                             first_site: SiteEvent,
                                             second_site: SiteEvent,
                                             third_site: SiteEvent,
                                             recompute_center_x: bool = True,
                                             recompute_center_y: bool = True,
                                             recompute_lower_x: bool = True
                                             ) -> CircleEvent:
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
        center_y = safe_divide_floats(
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
            center_x = safe_divide_floats(
                    float(triplets_sum_expression(common_left_coefficients,
                                                  segments_lengths)),
                    denominator)
        if recompute_lower_x:
            lower_x = safe_divide_floats(
                    float(quadruplets_sum_expression(
                            common_left_coefficients
                            + (common_left_coefficients[0] * first_dy
                               + common_left_coefficients[1] * second_dy
                               + common_left_coefficients[2] * third_dy,),
                            segments_lengths + (1,))),
                    denominator)
    return CircleEvent(center_x, center_y, lower_x)
