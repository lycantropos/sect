from decimal import Decimal
from fractions import Fraction
from itertools import groupby
from typing import (List,
                    TypeVar)

from robust import projection

from sect.hints import (Coordinate,
                        Point)

Domain = TypeVar('Domain')


def are_same_vertical_points(start: Point, end: Point) -> bool:
    start_x, _ = start
    end_x, _ = end
    return start_x == end_x


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


def to_segment_squared_length(start: Point, end: Point) -> Coordinate:
    return projection.signed_length(start, end, start, end)


def to_unique_just_seen(iterable: List[Domain]) -> List[Domain]:
    return [key for key, _ in groupby(iterable)]
