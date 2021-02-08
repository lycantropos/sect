from ground.base import Context
from ground.hints import (Coordinate,
                          Point)

from sect.core.voronoi.hints import (CrossProducer,
                                     DotProducer)
from sect.core.voronoi.utils import (robust_divide,
                                     robust_evenly_divide,
                                     robust_sqrt,
                                     to_segment_squared_length)
from .models import (BaseCircle,
                     Circle,
                     LeftCircle,
                     RightCircle,
                     Site)
from .utils import (
    robust_sum_of_products_with_sqrt_pairs as pairs_sum_expression,
    robust_sum_of_products_with_sqrt_triplets as triplets_sum_expression,
    to_point_segment_segment_mixed_expression as to_mixed_expression)


def to_point_point_point_circle(first_site: Site,
                                second_site: Site,
                                third_site: Site,
                                context: Context) -> BaseCircle:
    first_point, second_point, third_point = (
        first_site.start, second_site.start, third_site.start)
    first_x, first_y = first_point.x, first_point.y
    second_x, second_y = second_point.x, second_point.y
    third_x, third_y = third_point.x, third_point.y
    first_squared_norm = first_x * first_x + first_y * first_y
    second_squared_norm = second_x * second_x + second_y * second_y
    third_squared_norm = third_x * third_x + third_y * third_y
    center_x_numerator = (first_squared_norm * (second_y - third_y)
                          + second_squared_norm * (third_y - first_y)
                          + third_squared_norm * (first_y - second_y))
    center_y_numerator = -(first_squared_norm * (second_x - third_x)
                           + second_squared_norm * (third_x - first_x)
                           + third_squared_norm * (first_x - second_x))
    dot_producer = context.dot_product
    squared_radius_numerator = (
            to_segment_squared_length(first_point, second_point, dot_producer)
            * to_segment_squared_length(second_point, third_point,
                                        dot_producer)
            * to_segment_squared_length(first_point, third_point,
                                        dot_producer))
    denominator = 2 * context.cross_product(first_point, second_point,
                                            second_point, third_point)
    inverted_denominator = robust_divide(1, denominator)
    center_x = center_x_numerator * inverted_denominator
    center_y = center_y_numerator * inverted_denominator
    return ((LeftCircle if denominator > 0 else RightCircle)
            (center_x, center_y,
             squared_radius_numerator * inverted_denominator
             * inverted_denominator))


def to_point_point_segment_circle(first_point_site: Site,
                                  second_point_site: Site,
                                  segment_site: Site,
                                  segment_index: int,
                                  context: Context) -> BaseCircle:
    first_point, second_point = first_point_site.start, second_point_site.start
    segment_start, segment_end = segment_site.start, segment_site.end
    first_point_x, first_point_y = first_point.x, first_point.y
    second_point_x, second_point_y = second_point.x, second_point.y
    points_dx = second_point_x - first_point_x
    points_dy = second_point_y - first_point_y
    cross_producer, dot_producer = context.cross_product, context.dot_product
    coefficient = _to_point_point_segment_coefficient(
            first_point, second_point, segment_start, segment_end,
            segment_index, cross_producer, dot_producer)
    center_x = robust_evenly_divide(first_point_x + second_point_x
                                    + coefficient * points_dy, 2)
    center_y = robust_evenly_divide(first_point_y + second_point_y
                                    - coefficient * points_dx, 2)
    radius = robust_divide(
            abs(cross_producer(segment_start,
                               context.point_cls(center_x, center_y),
                               segment_start, segment_end)),
            robust_sqrt(to_segment_squared_length(segment_start, segment_end,
                                                  dot_producer)))
    return Circle(center_x, center_y, center_x + radius)


def to_point_segment_segment_circle(point_site: Site,
                                    first_segment_site: Site,
                                    second_segment_site: Site,
                                    point_index: int,
                                    context: Context) -> BaseCircle:
    point = point_site.start
    first_start, first_end = first_segment_site.start, first_segment_site.end
    second_start, second_end = (second_segment_site.start,
                                second_segment_site.end)
    point_x, point_y = point.x, point.y
    first_start_x, first_start_y = first_start.x, first_start.y
    first_end_x, first_end_y = first_end.x, first_end.y
    second_start_x, second_start_y = second_start.x, second_start.y
    second_end_x, second_end_y = second_end.x, second_end.y
    first_dx, first_dy = (first_end_x - first_start_x,
                          first_end_y - first_start_y)
    cross_producer, dot_producer = context.cross_product, context.dot_product
    segments_cross_product = cross_producer(first_start, first_end,
                                            second_start, second_end)
    first_squared_length = to_segment_squared_length(first_start, first_end,
                                                     dot_producer)
    if segments_cross_product:
        second_dx = second_end_x - second_start_x
        second_dy = second_end_y - second_start_y
        point_first_cross_product = cross_producer(
                first_start, first_end, point, first_end)
        point_second_cross_product = cross_producer(
                second_start, second_end, point, second_end)
        total_cross_product_x = (second_dx * point_first_cross_product
                                 - first_dx * point_second_cross_product)
        total_cross_product_y = (second_dy * point_first_cross_product
                                 - first_dy * point_second_cross_product)
        if total_cross_product_x or total_cross_product_y:
            sign = -1 if point_index == 2 else 1
            second_squared_length = to_segment_squared_length(
                    second_start, second_end, dot_producer)
            segments_dot_product = dot_producer(first_start, first_end,
                                                second_start, second_end)
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
        point_cls = context.point_cls
        point_first_dot_product = dot_producer(point_cls(0, 0), point,
                                               first_start, first_end)
        minus_second_start = point_cls(-second_start_x, -second_start_y)
        minus_second_point_cross_product = cross_producer(
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
            cross_producer(first_start, first_end, point, first_end)
            * cross_producer(first_start, first_end, second_start, point),
            1)
        center_x_numerator = pairs_sum_expression(center_x_left_coefficients,
                                                  common_right_coefficients)
        center_y_numerator = pairs_sum_expression(
                (2 * sign * first_dy, center_y_second_left_coefficient),
                common_right_coefficients)
        lower_x_numerator = triplets_sum_expression(
                center_x_left_coefficients
                + (abs(cross_producer(first_start, first_end, first_end,
                                      second_start)),),
                common_right_coefficients + (first_squared_length,))
        denominator = 2 * first_squared_length
        center_x = robust_divide(center_x_numerator, denominator)
        center_y = robust_divide(center_y_numerator, denominator)
        lower_x = robust_divide(lower_x_numerator, denominator)
    return Circle(center_x, center_y, lower_x)


def to_segment_segment_segment_circle(first_site: Site,
                                      second_site: Site,
                                      third_site: Site,
                                      context: Context) -> BaseCircle:
    first_start, first_end = first_site.start, first_site.end
    second_start, second_end = second_site.start, second_site.end
    third_start, third_end = third_site.start, third_site.end
    first_start_x, first_start_y = first_start.x, first_start.y
    first_end_x, first_end_y = first_end.x, first_end.y
    second_start_x, second_start_y = second_start.x, second_start.y
    second_end_x, second_end_y = second_end.x, second_end.y
    third_start_x, third_start_y = third_start.x, third_start.y
    third_end_x, third_end_y = third_end.x, third_end.y
    first_dx = first_end_x - first_start_x
    first_dy = first_end_y - first_start_y
    second_dx = second_end_x - second_start_x
    second_dy = second_end_y - second_start_y
    third_dx = third_end_x - third_start_x
    third_dy = third_end_y - third_start_y
    dot_producer = context.dot_product
    first_squared_length = to_segment_squared_length(first_start, first_end,
                                                     dot_producer)
    second_squared_length = to_segment_squared_length(second_start, second_end,
                                                      dot_producer)
    third_squared_length = to_segment_squared_length(third_start, third_end,
                                                     dot_producer)
    cross_producer, point_cls = context.cross_product, context.point_cls
    first_cross_product = cross_producer(point_cls(0, 0), first_start,
                                         point_cls(0, 0), first_end)
    second_cross_product = cross_producer(point_cls(0, 0), second_start,
                                          point_cls(0, 0), second_end)
    third_cross_product = cross_producer(point_cls(0, 0), third_start,
                                         point_cls(0, 0), third_end)
    center_x_numerator = triplets_sum_expression(
            (second_dx * third_cross_product - third_dx * second_cross_product,
             third_dx * first_cross_product - first_dx * third_cross_product,
             first_dx * second_cross_product
             - second_dx * first_cross_product),
            (first_squared_length, second_squared_length,
             third_squared_length))
    center_y_numerator = triplets_sum_expression(
            (second_dy * third_cross_product - third_dy * second_cross_product,
             third_dy * first_cross_product - first_dy * third_cross_product,
             first_dy * second_cross_product
             - second_dy * first_cross_product),
            (first_squared_length, second_squared_length,
             third_squared_length))
    first_second_cross_product = cross_producer(first_start, first_end,
                                                second_start, second_end)
    second_third_cross_product = cross_producer(second_start, second_end,
                                                third_start, third_end)
    third_first_cross_product = cross_producer(third_start, third_end,
                                               first_start, first_end)
    radius_numerator = (first_second_cross_product * third_cross_product
                        + second_third_cross_product * first_cross_product
                        + third_first_cross_product * second_cross_product)
    lower_x_numerator = center_x_numerator - radius_numerator
    denominator = triplets_sum_expression(
            (first_second_cross_product, second_third_cross_product,
             third_first_cross_product),
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
                                        segment_index: int,
                                        cross_producer: CrossProducer,
                                        dot_producer: DotProducer
                                        ) -> Coordinate:
    points_cross_product = cross_producer(segment_start, segment_end,
                                          first_point, second_point)
    points_dot_product = dot_producer(segment_start, segment_end, first_point,
                                      second_point)
    first_point_cross_product = cross_producer(
            segment_start, segment_end, first_point, segment_end)
    if points_cross_product:
        sign = -1 if segment_index == 2 else 1
        second_point_cross_product = cross_producer(
                segment_start, segment_end, second_point, segment_end)
        determinant = robust_sqrt(
                to_segment_squared_length(first_point, second_point,
                                          dot_producer)
                * to_segment_squared_length(segment_start, segment_end,
                                            dot_producer)
                * first_point_cross_product
                * second_point_cross_product)
        return robust_divide(2 * sign * determinant
                             + points_dot_product
                             * (first_point_cross_product
                                + second_point_cross_product),
                             points_cross_product * points_cross_product)
    else:
        return (robust_divide(points_dot_product,
                              4 * first_point_cross_product)
                - robust_divide(first_point_cross_product, points_dot_product))
