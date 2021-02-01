from typing import Tuple

from ground.core.shewchuk import (scale_expansion,
                                  square,
                                  sum_expansions,
                                  two_mul,
                                  two_two_sub,
                                  two_two_sum)
from ground.hints import Coordinate

from sect.core.voronoi.utils import (robust_divide,
                                     robust_sqrt)


def robust_sum_of_products_with_sqrt_pairs(
        left: Tuple[Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate]) -> Coordinate:
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
    """
    first_left, second_left = left
    first_right, second_right = right
    first_addend, second_addend = (two_mul(first_left,
                                           robust_sqrt(first_right)),
                                   two_mul(second_left,
                                           robust_sqrt(second_right)))
    return (sum(two_two_sum(*first_addend, *second_addend))
            if (first_addend[-1] >= 0 and second_addend[-1] >= 0
                or first_addend[-1] <= 0 and second_addend[-1] <= 0)
            else
            sum(scale_expansion(sum_expansions(
                    scale_expansion(square(first_left), first_right),
                    scale_expansion(square(second_left), -second_right)),
                    robust_divide(1, sum(two_two_sub(*first_addend,
                                                     *second_addend))))))


def robust_sum_of_products_with_sqrt_triplets(
        left: Tuple[Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate]) -> Coordinate:
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
        + left[2] * sqrt(right[2])
    """
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
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
        + left[2] * sqrt(right[3] * (sqrt(right[0] * right[1]) + right[2]))
    """
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
