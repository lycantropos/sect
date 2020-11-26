import ctypes
from decimal import Decimal
from fractions import Fraction
from typing import Tuple

from robust import projection

from sect.hints import (Coordinate,
                        Point)

MAX_DIGITS_COUNT = 64


def robust_product_with_sqrt(left: Coordinate,
                             right: Coordinate) -> Coordinate:
    return left * robust_sqrt(right)


def robust_sum_of_products_with_sqrt_pairs(
        left: Tuple[Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate]) -> Coordinate:
    first_left, second_left = left
    first_right, second_right = right
    a, b = (robust_product_with_sqrt(first_left, first_right),
            robust_product_with_sqrt(second_left, second_right))
    return (a + b
            if (a >= 0 and b >= 0 or a <= 0 and b <= 0)
            else ((first_left * first_left * first_right
                   - second_left * second_left * second_right)
                  / (a - b)))


def robust_sum_of_products_with_sqrt_quadruplets(
        left: Tuple[Coordinate, Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    first_left, second_left, third_left, fourth_left = left
    first_right, second_right, third_right, fourth_right = right
    a = robust_sum_of_products_with_sqrt_pairs((first_left, second_left),
                                               (first_right, second_right))
    b = robust_sum_of_products_with_sqrt_pairs((third_left, fourth_left),
                                               (third_right, fourth_right))
    return (a + b
            if a >= 0 and b >= 0 or a <= 0 and b <= 0
            else
            robust_sum_of_products_with_sqrt_triplets(
                    (first_left * first_left * first_right
                     + second_left * second_left * second_right
                     - third_left * third_left * third_right
                     - fourth_left * fourth_left * fourth_right,
                     2 * first_left * second_left,
                     -2 * third_left * fourth_left),
                    (1,
                     first_right * second_right,
                     third_right * fourth_right))
            / (a - b))


def robust_evenly_divide(dividend: Coordinate,
                         divisor: int) -> Coordinate:
    return (Fraction(dividend, divisor)
            if isinstance(dividend, int)
            else dividend / divisor)


def robust_divide(dividend: Coordinate, divisor: Coordinate) -> Coordinate:
    return (Fraction(dividend, divisor)
            if isinstance(divisor, int)
            else dividend / divisor)


def robust_sqrt(value: Coordinate) -> Coordinate:
    return Fraction.from_decimal((Decimal(value.numerator) / value.denominator
                                  if isinstance(value, Fraction)
                                  else Decimal(value))
                                 .sqrt())


def robust_sum_of_products_with_sqrt_triplets(
        left: Tuple[Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate]) -> Coordinate:
    first_left, second_left, third_left = left
    first_right, second_right, third_right = right
    a = robust_sum_of_products_with_sqrt_pairs((first_left, second_left),
                                               (first_right, second_right))
    b = robust_product_with_sqrt(third_left, third_right)
    return (a + b
            if a >= 0 and b >= 0 or a <= 0 and b <= 0
            else
            robust_sum_of_products_with_sqrt_pairs(
                    (first_left * first_left * first_right
                     + second_left * second_left * second_right
                     - third_left * third_left * third_right,
                     2 * first_left * second_left),
                    (1, first_right * second_right))
            / (a - b))


def to_first_point_segment_segment_quadruplets_expression2(
        left: Tuple[Coordinate, Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    lh = robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
    rh = robust_sum_of_products_with_sqrt_pairs(left[2:], right[2:])
    if lh >= 0 and rh >= 0 or lh <= 0 and rh <= 0:
        return lh + rh
    return robust_divide(robust_sum_of_products_with_sqrt_pairs(
            (left[0] * left[0] * right[0] + left[1] * left[1] * right[1]
             - left[2] * left[2] - left[3] * left[3] * right[0] * right[1],
             2 * (left[0] * left[1] - left[2] * left[3])), (1, right[3])),
            lh - rh)


def to_second_point_segment_segment_quadruplets_expression(
        left: Tuple[Coordinate, Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    if left[3]:
        rh = (robust_product_with_sqrt(left[2], right[3])
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
                        to_first_point_segment_segment_quadruplets_expression2(
                                (2 * left[3] * left[0],
                                 2 * left[3] * left[1],
                                 left[0] * left[0] * right[0]
                                 + left[1] * left[1] * right[1] + left[3] *
                                 left[3]
                                 - left[2] * left[2] * right[2] * right[3],
                                 2 * left[0] * left[1] - left[2] * left[2] *
                                 right[3]),
                                common_right_coefficients
                                + (right[0] * right[1],)),
                        lh - rh))
    else:
        lh = robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
        rh = (robust_product_with_sqrt(left[2], right[3])
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


def to_segment_squared_length(start: Point, end: Point) -> Coordinate:
    return projection.signed_length(start, end, start, end)


def _to_uint32(value: int) -> int:
    return ctypes.c_uint32(value).value
