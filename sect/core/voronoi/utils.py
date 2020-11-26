import ctypes
import struct
from decimal import Decimal
from fractions import Fraction
from itertools import groupby
from math import (copysign,
                  inf,
                  isnan,
                  nan)
from typing import (List,
                    TypeVar)

from robust import projection

from sect.hints import (Coordinate,
                        Point)
from .enums import ComparisonResult

Domain = TypeVar('Domain')


def are_same_vertical_points(start: Point, end: Point) -> bool:
    start_x, _ = start
    end_x, _ = end
    return start_x == end_x


def compare_floats(left: float, right: float, max_ulps: int
                   ) -> ComparisonResult:
    left_uint, right_uint = _float_to_uint(left), _float_to_uint(right)
    return ((ComparisonResult.EQUAL
             if left_uint - right_uint <= max_ulps
             else ComparisonResult.LESS)
            if left_uint > right_uint
            else (ComparisonResult.EQUAL
                  if right_uint - left_uint <= max_ulps
                  else ComparisonResult.MORE))


def robust_cross_product(first_dx: int,
                         first_dy: int,
                         second_dx: int,
                         second_dy: int) -> float:
    absolute_minuend, absolute_subtrahend = (_to_uint64(abs(first_dx
                                                            * second_dy)),
                                             _to_uint64(abs(second_dx
                                                            * first_dy)))
    if (first_dx < 0) is (second_dy < 0):
        if (first_dy < 0) is (second_dx < 0):
            return (-float(_to_uint64(absolute_subtrahend - absolute_minuend))
                    if absolute_minuend < absolute_subtrahend
                    else float(_to_uint64(absolute_minuend
                                          - absolute_subtrahend)))
        else:
            return float(_to_uint64(absolute_minuend + absolute_subtrahend))
    elif (first_dy < 0) is (second_dx < 0):
        return -float(_to_uint64(absolute_minuend + absolute_subtrahend))
    else:
        return (-float(_to_uint64(absolute_minuend - absolute_subtrahend))
                if absolute_minuend > absolute_subtrahend
                else float(_to_uint64(absolute_subtrahend - absolute_minuend)))


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


def safe_divide_floats(dividend: float, divisor: float) -> float:
    try:
        return dividend / divisor
    except ZeroDivisionError:
        return (copysign(inf, dividend * divisor)
                if dividend and not isnan(dividend)
                else nan)


def to_segment_squared_length(start: Point, end: Point) -> Coordinate:
    return projection.signed_length(start, end, start, end)


def to_sign(value: float) -> int:
    return 1 if value > 0 else (-1 if value < 0 else 0)


def to_unique_just_seen(iterable: List[Domain]) -> List[Domain]:
    return [key for key, _ in groupby(iterable)]


def _float_to_uint(value: float,
                   *,
                   sign_bit_mask: int = 2 ** 63) -> int:
    result = int.from_bytes(struct.pack('!d', value), 'big')
    return sign_bit_mask - result if result < sign_bit_mask else result


def _to_uint64(value: int) -> int:
    return ctypes.c_uint64(value).value
