from robust import (parallelogram,
                    projection)

from sect.core.voronoi.utils import (robust_divide,
                                     robust_evenly_divide,
                                     robust_sqrt,
                                     to_segment_squared_length)
from sect.hints import (Coordinate,
                        Point)
from .models import (Circle,
                     Site)
from .utils import (
    robust_sum_of_products_with_sqrt_pairs as pairs_sum_expression,
    robust_sum_of_products_with_sqrt_triplets as triplets_sum_expression,
    to_point_segment_segment_mixed_expression as to_mixed_expression)


def to_point_point_point_circle(first_point_site: Site,
                                second_point_site: Site,
                                third_point_site: Site) -> Circle:
    first_x, first_y = first_point = first_point_site.start
    second_x, second_y = second_point = second_point_site.start
    third_x, third_y = third_point = third_point_site.start
    first_squared_norm = first_x * first_x + first_y * first_y
    second_squared_norm = second_x * second_x + second_y * second_y
    third_squared_norm = third_x * third_x + third_y * third_y
    center_x_numerator = (first_squared_norm * (second_y - third_y)
                          + second_squared_norm * (third_y - first_y)
                          + third_squared_norm * (first_y - second_y))
    center_y_numerator = -(first_squared_norm * (second_x - third_x)
                           + second_squared_norm * (third_x - first_x)
                           + third_squared_norm * (first_x - second_x))
    squared_radius_numerator = (
            to_segment_squared_length(first_point, second_point)
            * to_segment_squared_length(second_point, third_point)
            * to_segment_squared_length(first_point, third_point))
    lower_x_numerator = (center_x_numerator
                         - robust_sqrt(squared_radius_numerator))
    denominator = 2 * parallelogram.signed_area(first_point, second_point,
                                                second_point, third_point)
    inverted_denominator = robust_divide(1, denominator)
    center_x = center_x_numerator * inverted_denominator
    center_y = center_y_numerator * inverted_denominator
    lower_x = lower_x_numerator * inverted_denominator
    return Circle(center_x, center_y, lower_x)


def to_point_point_segment_circle(first_point_site: Site,
                                  second_point_site: Site,
                                  segment_site: Site,
                                  segment_index: int) -> Circle:
    first_point_x, first_point_y = first_point = first_point_site.start
    second_point_x, second_point_y = second_point = second_point_site.start
    segment_start, segment_end = segment_site.start, segment_site.end
    points_dx = second_point_x - first_point_x
    points_dy = second_point_y - first_point_y
    coefficient = _to_point_point_segment_coefficient(
            first_point, second_point, segment_start, segment_end,
            segment_index)
    center_x = robust_evenly_divide(first_point_x + second_point_x
                                    + coefficient * points_dy, 2)
    center_y = robust_evenly_divide(first_point_y + second_point_y
                                    - coefficient * points_dx, 2)
    radius = robust_divide(
            abs(parallelogram.signed_area(segment_start, (center_x, center_y),
                                          segment_start, segment_end)),
            robust_sqrt(to_segment_squared_length(segment_start, segment_end)))
    return Circle(center_x, center_y, center_x + radius)


def to_point_segment_segment_circle(point_site: Site,
                                    first_segment_site: Site,
                                    second_segment_site: Site,
                                    point_index: int) -> Circle:
    point_x, point_y = point = point_site.start
    first_start_x, first_start_y = first_start = first_segment_site.start
    first_end_x, first_end_y = first_end = first_segment_site.end
    second_start_x, second_start_y = second_start = second_segment_site.start
    second_end_x, second_end_y = second_end = second_segment_site.end
    first_dx = first_end_x - first_start_x
    first_dy = first_end_y - first_start_y
    segments_cross_product = parallelogram.signed_area(
            first_start, first_end, second_start, second_end)
    first_squared_length = to_segment_squared_length(first_start, first_end)
    if segments_cross_product:
        second_dx = second_end_x - second_start_x
        second_dy = second_end_y - second_start_y
        point_first_cross_product = parallelogram.signed_area(
                first_start, first_end, point, first_end)
        point_second_cross_product = parallelogram.signed_area(
                second_start, second_end, point, second_end)
        total_cross_product_x = (second_dx * point_first_cross_product
                                 - first_dx * point_second_cross_product)
        total_cross_product_y = (second_dy * point_first_cross_product
                                 - first_dy * point_second_cross_product)
        if total_cross_product_x or total_cross_product_y:
            sign = -1 if point_index == 2 else 1
            second_squared_length = to_segment_squared_length(second_start,
                                                              second_end)
            segments_dot_product = projection.signed_length(
                    first_start, first_end, second_start, second_end)
            common_right_coefficients = (first_squared_length,
                                         second_squared_length,
                                         -segments_dot_product,
                                         2 * point_first_cross_product
                                         * point_second_cross_product)
            first_mixed_product = (
                    segments_dot_product * point_first_cross_product
                    - first_squared_length * point_second_cross_product)
            second_mixed_product = (
                    segments_dot_product * point_second_cross_product
                    - second_squared_length * point_first_cross_product)
            center_x_first_left_coefficient = (
                    second_mixed_product * point_x
                    + total_cross_product_y * point_second_cross_product)
            center_x_second_left_coefficient = (
                    first_mixed_product * point_x
                    - total_cross_product_y * point_first_cross_product)
            center_x_third_left_coefficient = (
                    (total_cross_product_x + point_x * segments_cross_product)
                    * sign)
            center_x_numerator = to_mixed_expression(
                    (center_x_first_left_coefficient,
                     center_x_second_left_coefficient,
                     center_x_third_left_coefficient),
                    common_right_coefficients)
            center_y_first_left_coefficient = (
                    second_mixed_product * point_y
                    - total_cross_product_x * point_second_cross_product)
            center_y_second_left_coefficient = (
                    first_mixed_product * point_y
                    + total_cross_product_x * point_first_cross_product)
            center_y_third_left_coefficient = (
                    (total_cross_product_y + point_y * segments_cross_product)
                    * sign)
            center_y_numerator = to_mixed_expression(
                    (center_y_first_left_coefficient,
                     center_y_second_left_coefficient,
                     center_y_third_left_coefficient),
                    common_right_coefficients)
            denominator = to_mixed_expression(
                    (second_mixed_product, first_mixed_product,
                     sign * segments_cross_product),
                    common_right_coefficients)
            center_x = robust_divide(center_x_numerator, denominator)
            center_y = robust_divide(center_y_numerator, denominator)
            radius = robust_divide(
                    -first_mixed_product * point_second_cross_product
                    - second_mixed_product * point_first_cross_product,
                    abs(denominator))
            lower_x = center_x + radius
        else:
            center_x = lower_x = point_x
            center_y = point_y
    else:
        sign = -1 if point_index == 2 else 1
        point_first_dot_product = projection.signed_length(
                (0, 0), point, first_start, first_end)
        minus_second_start = (-second_start_x, -second_start_y)
        minus_second_point_cross_product = parallelogram.signed_area(
                first_start, first_end, minus_second_start, first_end)
        center_x_second_left_coefficient = (
                2 * first_dx * point_first_dot_product
                - first_dy * minus_second_point_cross_product)
        center_y_second_left_coefficient = (
                2 * first_dy * point_first_dot_product
                + first_dx * minus_second_point_cross_product)
        center_x_left_coefficients = (2 * sign * first_dx,
                                      center_x_second_left_coefficient)
        common_right_coefficients = (
            parallelogram.signed_area(first_start, first_end, point, first_end)
            * parallelogram.signed_area(first_start, first_end, second_start,
                                        point),
            1)
        center_x_numerator = pairs_sum_expression(center_x_left_coefficients,
                                                  common_right_coefficients)
        center_y_numerator = pairs_sum_expression(
                (2 * sign * first_dy, center_y_second_left_coefficient),
                common_right_coefficients)
        lower_x_numerator = triplets_sum_expression(
                center_x_left_coefficients
                + (abs(parallelogram.signed_area(first_start, first_end,
                                                 first_end, second_start)),),
                common_right_coefficients + (first_squared_length,))
        denominator = 2 * first_squared_length
        center_x = robust_divide(center_x_numerator, denominator)
        center_y = robust_divide(center_y_numerator, denominator)
        lower_x = robust_divide(lower_x_numerator, denominator)
    return Circle(center_x, center_y, lower_x)


def to_segment_segment_segment_circle(first_site: Site,
                                      second_site: Site,
                                      third_site: Site) -> Circle:
    first_start_x, first_start_y = first_start = first_site.start
    first_end_x, first_end_y = first_end = first_site.end
    second_start_x, second_start_y = second_start = second_site.start
    second_end_x, second_end_y = second_end = second_site.end
    third_start_x, third_start_y = third_start = third_site.start
    third_end_x, third_end_y = third_end = third_site.end
    first_dx = first_end_x - first_start_x
    first_dy = first_end_y - first_start_y
    second_dx = second_end_x - second_start_x
    second_dy = second_end_y - second_start_y
    third_dx = third_end_x - third_start_x
    third_dy = third_end_y - third_start_y
    first_squared_length = to_segment_squared_length(first_start, first_end)
    second_squared_length = to_segment_squared_length(second_start,
                                                      second_end)
    third_squared_length = to_segment_squared_length(third_start, third_end)
    first_signed_area = parallelogram.signed_area((0, 0), first_start,
                                                  (0, 0), first_end)
    second_signed_area = parallelogram.signed_area((0, 0), second_start,
                                                   (0, 0), second_end)
    third_signed_area = parallelogram.signed_area((0, 0), third_start,
                                                  (0, 0), third_end)
    center_x_numerator = triplets_sum_expression(
            (second_dx * third_signed_area - third_dx * second_signed_area,
             third_dx * first_signed_area - first_dx * third_signed_area,
             first_dx * second_signed_area - second_dx * first_signed_area),
            (first_squared_length, second_squared_length,
             third_squared_length))
    center_y_numerator = triplets_sum_expression(
            (second_dy * third_signed_area - third_dy * second_signed_area,
             third_dy * first_signed_area - first_dy * third_signed_area,
             first_dy * second_signed_area - second_dy * first_signed_area),
            (first_squared_length, second_squared_length,
             third_squared_length))
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
    denominator = triplets_sum_expression(
            (first_second_signed_area, second_third_signed_area,
             third_first_signed_area),
            (third_squared_length, first_squared_length,
             second_squared_length))
    center_x = robust_divide(center_x_numerator, denominator)
    center_y = robust_divide(center_y_numerator, denominator)
    lower_x = robust_divide(lower_x_numerator, denominator)
    return Circle(center_x, center_y, lower_x)


def _to_point_point_segment_coefficient(first_point: Point,
                                        second_point: Point,
                                        segment_start: Point,
                                        segment_end: Point,
                                        segment_index: int) -> Coordinate:
    cross_product = parallelogram.signed_area(segment_start, segment_end,
                                              first_point, second_point)
    dot_product = projection.signed_length(segment_start, segment_end,
                                           first_point, second_point)
    first_point_cross_product = parallelogram.signed_area(
            segment_start, segment_end, first_point, segment_end)
    if cross_product:
        sign = -1 if segment_index == 2 else 1
        second_point_cross_product = parallelogram.signed_area(
                segment_start, segment_end, second_point, segment_end)
        determinant = robust_sqrt(
                to_segment_squared_length(first_point, second_point)
                * to_segment_squared_length(segment_start, segment_end)
                * first_point_cross_product
                * second_point_cross_product)
        return robust_divide(2 * sign * determinant
                             + dot_product * (first_point_cross_product
                                              + second_point_cross_product),
                             cross_product * cross_product)
    else:
        return (robust_divide(dot_product, 4 * first_point_cross_product)
                - robust_divide(first_point_cross_product, dot_product))
