from typing import Tuple

from sect.core.voronoi.utils import (robust_divide,
                                     robust_sqrt)
from sect.hints import Coordinate


def robust_sum_of_products_with_sqrt_pairs(
        left: Tuple[Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate]) -> Coordinate:
    first_left, second_left = left
    first_right, second_right = right
    lh, rh = (first_left * robust_sqrt(first_right),
              second_left * robust_sqrt(second_right))
    return (lh + rh
            if lh >= 0 and rh >= 0 or lh <= 0 and rh <= 0
            else robust_divide(first_left * first_left * first_right
                               - second_left * second_left * second_right,
                               lh - rh))


def robust_sum_of_products_with_sqrt_triplets(
        left: Tuple[Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate]) -> Coordinate:
    first_left, second_left, third_left = left
    first_right, second_right, third_right = right
    lh = robust_sum_of_products_with_sqrt_pairs((first_left, second_left),
                                                (first_right, second_right))
    rh = third_left * robust_sqrt(third_right)
    return (lh + rh
            if lh >= 0 and rh >= 0 or lh <= 0 and rh <= 0
            else
            robust_divide(robust_sum_of_products_with_sqrt_pairs(
                    (first_left * first_left * first_right
                     + second_left * second_left * second_right
                     - third_left * third_left * third_right,
                     2 * first_left * second_left),
                    (1, first_right * second_right)),
                    lh - rh))


def to_first_point_segment_segment_quadruplets_expression(
        left: Tuple[Coordinate, Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    lh = robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
    rh = robust_sum_of_products_with_sqrt_pairs(left[2:], right[2:])
    return (lh + rh
            if lh >= 0 and rh >= 0 or lh <= 0 and rh <= 0
            else
            robust_divide(robust_sum_of_products_with_sqrt_pairs(
                    (left[0] * left[0] * right[0]
                     + left[1] * left[1] * right[1]
                     - left[2] * left[2]
                     - left[3] * left[3] * right[0] * right[1],
                     2 * (left[0] * left[1] - left[2] * left[3])),
                    (1, right[3])),
                    lh - rh))


def to_second_point_segment_segment_quadruplets_expression(
        left: Tuple[Coordinate, Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    if left[3]:
        rh = (left[2] * robust_sqrt(right[3])
              * robust_sqrt(robust_sum_of_products_with_sqrt_pairs(
                        (1, right[2]),
                        (right[0] * right[1], 1))))
        common_right_coefficients = (right[0], right[1], 1)
        lh = robust_sum_of_products_with_sqrt_triplets(
                (left[0], left[1], left[3]), common_right_coefficients)
        return (lh + rh
                if lh >= 0 and rh >= 0 or lh <= 0 and rh <= 0
                else
                robust_divide(
                        to_first_point_segment_segment_quadruplets_expression(
                                (2 * left[0] * left[3],
                                 2 * left[1] * left[3],
                                 left[0] * left[0] * right[0]
                                 + left[1] * left[1] * right[1]
                                 + left[3] * left[3]
                                 - left[2] * left[2] * right[2] * right[3],
                                 2 * left[0] * left[1]
                                 - left[2] * left[2] * right[3]),
                                common_right_coefficients
                                + (right[0] * right[1],)),
                        lh - rh))
    else:
        lh = robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
        rh = (left[2] * robust_sqrt(right[3])
              * robust_sqrt(robust_sum_of_products_with_sqrt_pairs(
                        (1, right[2]), (right[0] * right[1], 1))))
        return (lh + rh
                if lh >= 0 and rh >= 0 or lh <= 0 and rh <= 0
                else
                robust_divide(robust_sum_of_products_with_sqrt_pairs(
                        (left[0] * left[0] * right[0]
                         + left[1] * left[1] * right[1]
                         - left[2] * left[2] * right[3] * right[2],
                         2 * left[0] * left[1] - left[2] * left[2] * right[3]),
                        (1, right[0] * right[1])),
                        lh - rh))
