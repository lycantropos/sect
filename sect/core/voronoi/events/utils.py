from typing import Tuple

from ground.hints import Scalar
from symba.base import Expression

from sect.core.voronoi.utils import to_sqrt


def sum_of_products_with_sqrt_pairs(left: Tuple[Scalar, Scalar],
                                    right: Tuple[Scalar, Scalar]) -> Scalar:
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
    """
    first_left, second_left = left
    first_right, second_right = right
    return (first_left * to_sqrt(first_right)
            + second_left * to_sqrt(second_right))


def sum_of_products_with_sqrt_triplets(left: Tuple[Scalar, Scalar, Scalar],
                                       right: Tuple[Scalar, Scalar, Scalar]
                                       ) -> Scalar:
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
        + left[2] * sqrt(right[2])
    """
    return (sum_of_products_with_sqrt_pairs(left[:2], right[:2])
            + left[2] * to_sqrt(right[2]))


def point_segment_segment_mixed_expression(
        left: Tuple[Scalar, Scalar, Scalar],
        right: Tuple[Scalar, Scalar, Scalar, Scalar]
) -> Scalar:
    """
    Evaluates expression:
        left[0] * sqrt(right[0]) + left[1] * sqrt(right[1])
        + left[2] * sqrt(right[3] * (sqrt(right[0] * right[1]) + right[2]))
    """
    return (sum_of_products_with_sqrt_pairs(left[:2], right[:2])
            + left[2] * to_sqrt(right[3]
                                * (to_sqrt(right[0] * right[1]) + right[2])))


def to_constant(value: Scalar, _zero: Expression = to_sqrt(0)) -> Expression:
    return _zero + value
