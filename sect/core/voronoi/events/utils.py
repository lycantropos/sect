from typing import Tuple

from sect.core.voronoi.utils import (robust_divide,
                                     robust_sqrt)
from sect.hints import Coordinate


def robust_sum_of_products_with_sqrt_pairs(
        left: Tuple[Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate]) -> Coordinate:
    first_left, second_left = left
    first_right, second_right = right
    first_addend, second_addend = (first_left * robust_sqrt(first_right),
                                   second_left * robust_sqrt(second_right))
    return (first_addend + second_addend
            if (first_addend >= 0 and second_addend >= 0
                or first_addend <= 0 and second_addend <= 0)
            else robust_divide(first_left * first_left * first_right
                               - second_left * second_left * second_right,
                               first_addend - second_addend))


def robust_sum_of_products_with_sqrt_triplets(
        left: Tuple[Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate]) -> Coordinate:
    first_left, second_left, third_left = left
    first_right, second_right, third_right = right
    first_addend = robust_sum_of_products_with_sqrt_pairs(
            (first_left, second_left), (first_right, second_right))
    second_addend = third_left * robust_sqrt(third_right)
    return (first_addend + second_addend
            if (first_addend >= 0 and second_addend >= 0
                or first_addend <= 0 and second_addend <= 0)
            else
            robust_divide(robust_sum_of_products_with_sqrt_pairs(
                    (first_left * first_left * first_right
                     + second_left * second_left * second_right
                     - third_left * third_left * third_right,
                     2 * first_left * second_left),
                    (1, first_right * second_right)),
                    first_addend - second_addend))


def to_point_segment_segment_mixed_expression(
        left: Tuple[Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    first_addend = robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
    second_addend = left[2] * robust_sqrt(
            right[3] * robust_sum_of_products_with_sqrt_pairs(
                    (1, right[2]), (right[0] * right[1], 1)))
    return (first_addend + second_addend
            if (first_addend >= 0 and second_addend >= 0
                or first_addend <= 0 and second_addend <= 0)
            else
            robust_divide(robust_sum_of_products_with_sqrt_pairs(
                    (left[0] * left[0] * right[0]
                     + left[1] * left[1] * right[1]
                     - left[2] * left[2] * right[3] * right[2],
                     2 * left[0] * left[1] - left[2] * left[2] * right[3]),
                    (1, right[0] * right[1])),
                    first_addend - second_addend))


def to_point_segment_segment_quadruplets_expression(
        left: Tuple[Coordinate, Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    common_right_coefficients = (right[0], right[1], 1)
    first_addend = robust_sum_of_products_with_sqrt_triplets(
            (left[0], left[1], left[3]), common_right_coefficients)
    second_addend = left[2] * robust_sqrt(
            right[3] * robust_sum_of_products_with_sqrt_pairs(
                    (1, right[2]), (right[0] * right[1], 1)))
    return (first_addend + second_addend
            if (first_addend >= 0 and second_addend >= 0
                or first_addend <= 0 and second_addend <= 0)
            else
            robust_divide(_to_point_segment_segment_quadruplets_expression(
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
                    first_addend - second_addend))


def _to_point_segment_segment_quadruplets_expression(
        left: Tuple[Coordinate, Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    first_addend = robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
    second_addend = robust_sum_of_products_with_sqrt_pairs(left[2:], right[2:])
    return (first_addend + second_addend
            if (first_addend >= 0 and second_addend >= 0
                or first_addend <= 0 and second_addend <= 0)
            else
            robust_divide(robust_sum_of_products_with_sqrt_pairs(
                    (left[0] * left[0] * right[0]
                     + left[1] * left[1] * right[1]
                     - left[2] * left[2]
                     - left[3] * left[3] * right[0] * right[1],
                     2 * (left[0] * left[1] - left[2] * left[3])),
                    (1, right[3])),
                    first_addend - second_addend))
