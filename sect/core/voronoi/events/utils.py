from typing import Tuple

from ground.hints import Coordinate

from sect.core.voronoi.utils import to_sqrt


def robust_sum_of_products_with_sqrt_pairs(
        left: Tuple[Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate]) -> Coordinate:
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
    """
    first_left, second_left = left
    first_right, second_right = right
    return (first_left * to_sqrt(first_right)
            + second_left * to_sqrt(second_right))


def robust_sum_of_products_with_sqrt_triplets(
        left: Tuple[Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate]) -> Coordinate:
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
        + left[2] * sqrt(right[2])
    """
    return (robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
            + left[2] * to_sqrt(right[2]))


def to_point_segment_segment_mixed_expression(
        left: Tuple[Coordinate, Coordinate, Coordinate],
        right: Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
) -> Coordinate:
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
        + left[2] * sqrt(right[3] * (sqrt(right[0] * right[1]) + right[2]))
    """
    return (robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
            + left[2] * to_sqrt(right[3]
                                * (to_sqrt(right[0] * right[1]) + right[2])))
