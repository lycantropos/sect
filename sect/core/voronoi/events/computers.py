from robust import (parallelogram,
                    projection)

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
    r = abs(parallelogram.signed_area(segment_start, (center_x, center_y),
                                      segment_start, segment_end))
    squared_segment_length = to_segment_squared_length(segment_start,
                                                       segment_end)
    lower_x = center_x + r / robust_sqrt(squared_segment_length)
    return CircleEvent(center_x, center_y, lower_x)


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
    segments_signed_area = parallelogram.signed_area(first_start, first_end,
                                                     second_start, second_end)
    first_squared_length = to_segment_squared_length(first_start, first_end)
    if segments_signed_area:
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
        scaled_point_x = segments_signed_area * point_x
        scaled_point_y = segments_signed_area * point_y
        if ix == scaled_point_x and iy == scaled_point_y:
            denominator = segments_signed_area
            center_x = lower_x = robust_divide(ix, denominator)
            center_y = robust_divide(iy, denominator)
        else:
            sign = ((-1 if point_index == 2 else 1)
                    * ((1 if segments_signed_area > 0 else -1)
                       if segments_signed_area
                       else 0))
            second_squared_length = to_segment_squared_length(second_start,
                                                              second_end)
            segments_scalar_product = projection.signed_length(
                    first_start, first_end, second_start, second_end)
            scaled_point = (scaled_point_x, scaled_point_y)
            i_point = (ix, iy)
            first_cross_product = parallelogram.signed_area(
                    scaled_point, i_point, first_start, first_end)
            first_scalar_product = projection.signed_length(
                    scaled_point, i_point, first_start, first_end)
            second_cross_product = parallelogram.signed_area(
                    scaled_point, i_point, second_start, second_end)
            second_scalar_product = projection.signed_length(
                    scaled_point, i_point, second_start, second_end)
            common_right_coefficients = (first_squared_length,
                                         second_squared_length,
                                         -segments_scalar_product,
                                         2 * first_cross_product
                                         * second_cross_product)
            coefficient = to_quadruplets_expression(
                    (-second_scalar_product, first_scalar_product, sign, 0),
                    common_right_coefficients)
            denominator = coefficient * segments_signed_area
            squared_length = to_segment_squared_length(i_point, scaled_point)
            center_y = robust_divide(to_quadruplets_expression(
                    (second_dy * squared_length - iy * second_scalar_product,
                     iy * first_scalar_product - first_dy * squared_length,
                     iy * sign, 0),
                    common_right_coefficients),
                    denominator)
            common_left_coefficients = (second_dx * squared_length
                                        - ix * second_scalar_product,
                                        ix * first_scalar_product
                                        - first_dx * squared_length,
                                        ix * sign)
            center_x = robust_divide(to_quadruplets_expression(
                    common_left_coefficients + (0,),
                    common_right_coefficients),
                    denominator)
            lower_x = robust_divide(to_quadruplets_expression(
                    common_left_coefficients
                    + (segments_signed_area * squared_length
                       * (-1 if coefficient < 0 else 1),),
                    common_right_coefficients), denominator)
    else:
        denominator = 2 * first_squared_length
        dx = parallelogram.signed_area(first_start, first_end, point,
                                       first_end)
        dy = parallelogram.signed_area(first_start, first_end, second_start,
                                       point)
        common_right_coefficients = (dx * dy, 1)
        squared_first_dx = first_dx * first_dx
        squared_first_dy = first_dy * first_dy
        sign = -1 if point_index == 2 else 1
        center_y = robust_divide(
                pairs_sum_expression(
                        (2 * sign * first_dy,
                         squared_first_dx * (first_end_y + second_start_y)
                         - first_dx * first_dy * (first_end_x - point_x
                                                  + second_start_x - point_x)
                         + squared_first_dy * (point_y * 2)),
                        common_right_coefficients),
                denominator)
        common_left_coefficients = (2 * sign * first_dx,
                                    squared_first_dy
                                    * (first_end_x + second_start_x)
                                    - first_dx * first_dy
                                    * (first_end_y - point_y
                                       + second_start_y - point_y)
                                    + 2 * squared_first_dx * point_x)
        center_x = robust_divide(
                pairs_sum_expression(common_left_coefficients,
                                     common_right_coefficients),
                denominator)
        lower_x = robust_divide(
                triplets_sum_expression(
                        common_left_coefficients
                        + (abs(parallelogram.signed_area(
                                first_start, first_end, first_end,
                                second_start)),),
                        common_right_coefficients
                        + (first_squared_length,)),
                denominator)
    return CircleEvent(center_x, center_y, lower_x)


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
    denominator = RobustFloat()
    denominator += first_second_signed_area * third_length
    denominator += second_third_signed_area * first_length
    denominator += third_first_signed_area * second_length
    r = RobustFloat()
    r -= first_second_signed_area * third_signed_area
    r -= second_third_signed_area * first_signed_area
    r -= third_first_signed_area * second_signed_area
    center_x = RobustFloat()
    center_x += first_dx * second_signed_area * third_length
    center_x -= second_dx * first_signed_area * third_length
    center_x += second_dx * third_signed_area * first_length
    center_x -= third_dx * second_signed_area * first_length
    center_x += third_dx * first_signed_area * second_length
    center_x -= first_dx * third_signed_area * second_length
    center_y = RobustFloat()
    center_y += first_dy * second_signed_area * third_length
    center_y -= second_dy * first_signed_area * third_length
    center_y += second_dy * third_signed_area * first_length
    center_y -= third_dy * second_signed_area * first_length
    center_y += third_dy * first_signed_area * second_length
    center_y -= first_dy * third_signed_area * second_length
    lower_x = center_x + r
    center_x /= denominator
    center_y /= denominator
    lower_x /= denominator
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
