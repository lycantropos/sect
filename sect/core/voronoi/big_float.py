import ctypes
from math import (copysign,
                  frexp,
                  inf,
                  ldexp)

from reprit.base import generate_repr

from .utils import (safe_divide_floats,
                    safe_sqrt)

MAX_EXPONENTS_DIFFERENCE = 54


class BigFloat:
    __slots__ = 'mantissa', 'exponent'

    def __init__(self, mantissa: float, exponent: int) -> None:
        self.mantissa, self.exponent = frexp(mantissa)
        self.exponent += exponent

    __repr__ = generate_repr(__init__)

    def __add__(self, other: 'BigFloat') -> 'BigFloat':
        if (not self.mantissa
                or other.exponent > self.exponent + MAX_EXPONENTS_DIFFERENCE):
            return other
        elif (not other.mantissa
              or self.exponent > other.exponent + MAX_EXPONENTS_DIFFERENCE):
            return self
        elif self.exponent >= other.exponent:
            with_min_exponent, with_max_exponent = other, self
        else:
            with_min_exponent, with_max_exponent = self, other
        return BigFloat(ldexp(with_max_exponent.mantissa,
                              with_max_exponent.exponent
                              - with_min_exponent.exponent)
                        + with_min_exponent.mantissa,
                        with_min_exponent.exponent)

    def __bool__(self) -> bool:
        return bool(self.mantissa)

    def __float__(self) -> float:
        try:
            return ldexp(self.mantissa, self.exponent)
        except OverflowError:
            return copysign(inf, self.mantissa)

    def __mul__(self, other: 'BigFloat') -> 'BigFloat':
        return BigFloat(self.mantissa * other.mantissa,
                        _to_int32(self.exponent + other.exponent))

    def __neg__(self) -> 'BigFloat':
        return BigFloat(-self.mantissa, self.exponent)

    def __sub__(self, other: 'BigFloat') -> 'BigFloat':
        if (not self.mantissa
                or other.exponent > self.exponent + MAX_EXPONENTS_DIFFERENCE):
            return -other
        elif (not other.mantissa
              or self.exponent > other.exponent + MAX_EXPONENTS_DIFFERENCE):
            return self
        elif self.exponent >= other.exponent:
            return BigFloat(ldexp(self.mantissa,
                                  self.exponent - other.exponent)
                            - other.mantissa, other.exponent)
        else:
            return BigFloat(ldexp(-other.mantissa,
                                  other.exponent - self.exponent)
                            + self.mantissa, self.exponent)

    def __truediv__(self, other: 'BigFloat') -> 'BigFloat':
        return BigFloat(safe_divide_floats(self.mantissa, other.mantissa),
                        _to_int32(self.exponent - other.exponent))

    def sqrt(self) -> 'BigFloat':
        mantissa, exponent = self.mantissa, self.exponent
        if exponent % 2:
            mantissa *= 2.
            exponent -= 1
        return BigFloat(safe_sqrt(mantissa), exponent // 2)


def _to_int32(value: int) -> int:
    return ctypes.c_int32(value).value
