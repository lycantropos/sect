import ctypes
import struct
from itertools import groupby
from math import (copysign,
                  inf,
                  isnan,
                  nan,
                  sqrt)
from typing import (List,
                    TypeVar)

from .enums import (ComparisonResult,
                    Orientation)
from .point import Point

Domain = TypeVar('Domain')


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


def deltas_to_orientation(first_dx: int,
                          first_dy: int,
                          second_dx: int,
                          second_dy: int) -> Orientation:
    return Orientation(to_sign(robust_cross_product(first_dx, first_dy,
                                                    second_dx, second_dy)))


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


def safe_divide_floats(dividend: float, divisor: float) -> float:
    try:
        return dividend / divisor
    except ZeroDivisionError:
        return (copysign(inf, dividend * divisor)
                if dividend and not isnan(dividend)
                else nan)


def safe_sqrt(value: float) -> float:
    try:
        return sqrt(value)
    except ValueError:
        return nan


def to_orientation(vertex: Point,
                   first_ray_point: Point,
                   second_ray_point: Point) -> Orientation:
    return deltas_to_orientation(first_ray_point.x - vertex.x,
                                 first_ray_point.y - vertex.y,
                                 second_ray_point.x - vertex.x,
                                 second_ray_point.y - vertex.y)


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
