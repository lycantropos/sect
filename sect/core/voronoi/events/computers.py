from robust import (parallelogram,
                    projection)

from sect.core.voronoi.utils import (robust_divide,
                                     robust_evenly_divide,
                                     robust_sqrt,
                                     to_segment_squared_length)
from sect.hints import (Coordinate,
                        Point)
from .models import (CircleEvent,
                     SiteEvent)
from .utils import (
    robust_sum_of_products_with_sqrt_pairs as pairs_sum_expression,
    robust_sum_of_products_with_sqrt_triplets as triplets_sum_expression,
    to_point_segment_segment_mixed_expression as to_mixed_expression,
    to_point_segment_segment_quadruplets_expression
    as to_quadruplets_expression)


def to_point_point_point_circle_event(first_point_event: SiteEvent,
                                      second_point_event: SiteEvent,
                                      third_point_event: SiteEvent
                                      ) -> CircleEvent:
    first_x, first_y = first_point = first_point_event.start
    second_x, second_y = second_point = second_point_event.start
    third_x, third_y = third_point = third_point_event.start
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
    radius = robust_divide(
            abs(parallelogram.signed_area(segment_start, (center_x, center_y),
                                          segment_start, segment_end)),
            robust_sqrt(to_segment_squared_length(segment_start, segment_end)))
    return CircleEvent(center_x, center_y, center_x + radius)


def to_point_segment_segment_circle_event(point_event: SiteEvent,
                                          first_segment_event: SiteEvent,
                                          second_segment_event: SiteEvent,
                                          point_index: int) -> CircleEvent:
    point_x, point_y = point = point_event.start
    first_start_x, first_start_y = first_start = first_segment_event.start
    first_end_x, first_end_y = first_end = first_segment_event.end
    second_start_x, second_start_y = second_start = second_segment_event.start
    second_end_x, second_end_y = second_end = second_segment_event.end
    first_dx = first_end_x - first_start_x
    first_dy = first_end_y - first_start_y
    segments_cross_product = parallelogram.signed_area(first_start, first_end,
                                                       second_start,
                                                       second_end)
    first_squared_length = to_segment_squared_length(first_start, first_end)
    if segments_cross_product:
        first_start_signed_area = parallelogram.signed_area(
                first_start, first_end, (0, 0), first_start)
        second_end_signed_area = parallelogram.signed_area(
                second_start, second_end, (0, 0), second_end)
        second_dx = second_end_x - second_start_x
        second_dy = second_end_y - second_start_y
        ix = (second_dx * first_start_signed_area
              - first_dx * second_end_signed_area)
        iy = (second_dy * first_start_signed_area
              - first_dy * second_end_signed_area)
        scaled_point_x = segments_cross_product * point_x
        scaled_point_y = segments_cross_product * point_y
        if ix == scaled_point_x and iy == scaled_point_y:
            center_x = lower_x = point_x
            center_y = point_y
        else:
            sign = ((-1 if point_index == 2 else 1)
                    * ((1 if segments_cross_product > 0 else -1)
                       if segments_cross_product
                       else 0))
            second_squared_length = to_segment_squared_length(second_start,
                                                              second_end)
            segments_dot_product = projection.signed_length(
                    first_start, first_end, second_start, second_end)
            point_first_cross_product = parallelogram.signed_area(
                    first_start, first_end, point, first_end)
            point_second_cross_product = parallelogram.signed_area(
                    second_start, second_end, point, second_end)
            common_right_coefficients = (first_squared_length,
                                         second_squared_length,
                                         -segments_dot_product,
                                         2 * point_first_cross_product
                                         * point_second_cross_product
                                         * segments_cross_product ** 2)
            first_mixed_product = (
                    segments_dot_product * point_first_cross_product
                    - first_squared_length * point_second_cross_product)
            second_mixed_product = (
                    segments_dot_product * point_second_cross_product
                    - second_squared_length * point_first_cross_product)
            total_cross_product_y = (second_dy * point_first_cross_product
                                     - first_dy * point_second_cross_product)
            total_cross_product_x = (second_dx * point_first_cross_product
                                     - first_dx * point_second_cross_product)
            center_y_first_left_coefficient = (
                    segments_cross_product
                    * (second_mixed_product * point_y
                       - total_cross_product_x * point_second_cross_product))
            center_y_second_left_coefficient = (
                    segments_cross_product
                    * (first_mixed_product * point_y
                       + total_cross_product_x * point_first_cross_product))
            center_y_numerator = to_mixed_expression(
                    (center_y_first_left_coefficient,
                     center_y_second_left_coefficient,
                     iy * sign), common_right_coefficients)
            center_x_first_left_coefficient = (
                    segments_cross_product
                    * (second_mixed_product * point_x
                       + total_cross_product_y * point_second_cross_product))
            center_x_second_left_coefficient = (
                    segments_cross_product
                    * (first_mixed_product * point_x
                       - total_cross_product_y * point_first_cross_product))
            common_left_coefficients = (center_x_first_left_coefficient,
                                        center_x_second_left_coefficient,
                                        ix * sign)
            center_x_numerator = to_mixed_expression(
                    common_left_coefficients, common_right_coefficients)
            coefficient_part = (
                    segments_dot_product
                    * parallelogram.signed_area(second_start, second_end,
                                                (0, 0), second_end)
                    - second_squared_length
                    * parallelogram.signed_area(first_start, first_end,
                                                (0, 0), first_start))
            radius_numerator = (
                    - first_mixed_product * point_second_cross_product
                    - second_mixed_product * point_first_cross_product)
            lower_x_numerator = to_quadruplets_expression(
                    common_left_coefficients
                    + (segments_cross_product * radius_numerator
                       * (-1 if coefficient_part < 0 else 1),),
                    common_right_coefficients)
            coefficient = coefficient_part * robust_sqrt(first_squared_length)
            denominator = coefficient * segments_cross_product
            center_y = robust_divide(center_y_numerator, denominator)
            center_x = robust_divide(center_x_numerator, denominator)
            lower_x = robust_divide(lower_x_numerator, denominator)
    else:
        first_start_point_signed_area = parallelogram.signed_area(
                first_start, first_end, point, first_end)
        second_start_point_signed_area = parallelogram.signed_area(
                first_start, first_end, second_start, point)
        squared_first_dx = first_dx * first_dx
        first_dx_dy = first_dx * first_dy
        squared_first_dy = first_dy * first_dy
        sign = -1 if point_index == 2 else 1
        common_right_coefficients = (first_start_point_signed_area
                                     * second_start_point_signed_area, 1)
        center_y_numerator = pairs_sum_expression(
                (2 * sign * first_dy,
                 squared_first_dx * (first_end_y + second_start_y)
                 - first_dx_dy * (first_end_x - point_x
                                  + second_start_x - point_x)
                 + 2 * squared_first_dy * point_y),
                common_right_coefficients)
        common_left_coefficients = (
            2 * sign * first_dx,
            squared_first_dy * (first_end_x + second_start_x)
            - first_dx_dy * (first_end_y - point_y + second_start_y - point_y)
            + 2 * squared_first_dx * point_x)
        center_x_numerator = pairs_sum_expression(common_left_coefficients,
                                                  common_right_coefficients)
        lower_x_numerator = triplets_sum_expression(
                common_left_coefficients
                + (abs(parallelogram.signed_area(first_start, first_end,
                                                 first_end, second_start)),),
                common_right_coefficients + (first_squared_length,))
        denominator = 2 * first_squared_length
        center_x = robust_divide(center_x_numerator, denominator)
        center_y = robust_divide(center_y_numerator, denominator)
        lower_x = robust_divide(lower_x_numerator, denominator)
    return CircleEvent(center_x, center_y, lower_x)


def to_segment_segment_segment_circle_event(first_event: SiteEvent,
                                            second_event: SiteEvent,
                                            third_event: SiteEvent
                                            ) -> CircleEvent:
    first_start_x, first_start_y = first_start = first_event.start
    first_end_x, first_end_y = first_end = first_event.end
    second_start_x, second_start_y = second_start = second_event.start
    second_end_x, second_end_y = second_end = second_event.end
    third_start_x, third_start_y = third_start = third_event.start
    third_end_x, third_end_y = third_end = third_event.end
    first_dx = first_end_x - first_start_x
    first_dy = first_end_y - first_start_y
    second_dx = second_end_x - second_start_x
    second_dy = second_end_y - second_start_y
    third_dx = third_end_x - third_start_x
    third_dy = third_end_y - third_start_y
    first_length = robust_sqrt(to_segment_squared_length(first_start,
                                                         first_end))
    second_length = robust_sqrt(to_segment_squared_length(second_start,
                                                          second_end))
    third_length = robust_sqrt(to_segment_squared_length(third_start,
                                                         third_end))
    first_signed_area = parallelogram.signed_area((0, 0), first_start,
                                                  (0, 0), first_end)
    second_signed_area = parallelogram.signed_area((0, 0), second_start,
                                                   (0, 0), second_end)
    third_signed_area = parallelogram.signed_area((0, 0), third_start,
                                                  (0, 0), third_end)
    second_third_coefficient = (second_signed_area * third_length
                                - third_signed_area * second_length)
    third_first_coefficient = (third_signed_area * first_length
                               - first_signed_area * third_length)
    first_second_coefficient = (first_signed_area * second_length
                                - second_signed_area * first_length)
    center_x_numerator = (first_dx * second_third_coefficient
                          + second_dx * third_first_coefficient
                          + third_dx * first_second_coefficient)
    center_y_numerator = (first_dy * second_third_coefficient
                          + second_dy * third_first_coefficient
                          + third_dy * first_second_coefficient)
    first_second_signed_area = parallelogram.signed_area(
            first_start, first_end, second_start, second_end)
    second_third_signed_area = parallelogram.signed_area(
            second_start, second_end, third_start, third_end)
    third_first_signed_area = parallelogram.signed_area(
            third_start, third_end, first_start, first_end)
    radius_numerator = (first_second_signed_area * third_signed_area
                        + second_third_signed_area * first_signed_area
                        + third_first_signed_area * second_signed_area)
    lower_x_numerator = center_x_numerator - radius_numerator
    denominator = (first_second_signed_area * third_length
                   + second_third_signed_area * first_length
                   + third_first_signed_area * second_length)
    center_x = robust_divide(center_x_numerator, denominator)
    center_y = robust_divide(center_y_numerator, denominator)
    lower_x = robust_divide(lower_x_numerator, denominator)
    return CircleEvent(center_x, center_y, lower_x)


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
