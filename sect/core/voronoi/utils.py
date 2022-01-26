from fractions import Fraction
from itertools import groupby
from typing import (List,
                    TypeVar)

from ground.base import (Context,
                         Mode)
from ground.hints import (Point,
                          Scalar)
from symba.base import sqrt

from .hints import DotProducer

Domain = TypeVar('Domain')


def are_same_vertical_points(start: Point, end: Point) -> bool:
    return start.x == end.x


def robust_evenly_divide(dividend: Scalar, divisor: int) -> Scalar:
    return (Fraction(dividend, divisor)
            if isinstance(dividend, int)
            else dividend / divisor)


def robust_divide(dividend: Scalar, divisor: Scalar) -> Scalar:
    return (Fraction(dividend, divisor)
            if isinstance(dividend, int) and isinstance(divisor, int)
            else dividend / divisor)


def to_sqrt(value: Scalar) -> Scalar:
    return sqrt(value)


def to_segment_squared_length(start: Point,
                              end: Point,
                              dot_producer: DotProducer) -> Scalar:
    return dot_producer(start, end, start, end)


plain_cross_product = Context(mode=Mode.PLAIN).cross_product


def to_unique_just_seen(iterable: List[Domain]) -> List[Domain]:
    return [key for key, _ in groupby(iterable)]
