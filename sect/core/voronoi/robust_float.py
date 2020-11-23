from functools import total_ordering
from typing import Any

from reprit.base import generate_repr

from .utils import (safe_divide_floats,
                    safe_sqrt)

ROUNDING_ERROR = 1


@total_ordering
class RobustFloat:
    __slots__ = 'value', 'relative_error'

    def __init__(self, value: float = 0., relative_error: float = 0.) -> None:
        self.value = value
        self.relative_error = relative_error

    __repr__ = generate_repr(__init__)

    def __abs__(self) -> 'RobustFloat':
        return RobustFloat(abs(self.value), self.relative_error)

    def __add__(self, other: 'RobustFloat') -> 'RobustFloat':
        value = self.value + other.value
        relative_error = (max(self.relative_error, other.relative_error)
                          + ROUNDING_ERROR
                          if (not self.value or not other.value
                              or (self.value > 0) is (other.value > 0))
                          else
                          abs(safe_divide_floats(
                                  self.value * self.relative_error
                                  - other.value * other.relative_error, value))
                          + ROUNDING_ERROR)
        return RobustFloat(value, relative_error)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __eq__(self, other: Any) -> bool:
        return self.value == other

    def __gt__(self, other: Any) -> bool:
        return self.value > other

    def __imul__(self, other: 'RobustFloat') -> 'RobustFloat':
        self.value *= other.value
        self.relative_error += other.relative_error + ROUNDING_ERROR
        return self

    def __itruediv__(self, other: 'RobustFloat') -> 'RobustFloat':
        self.value = safe_divide_floats(self.value, other.value)
        self.relative_error += other.relative_error + ROUNDING_ERROR
        return self

    def __lt__(self, other: Any) -> bool:
        return self.value < other

    def __mul__(self, other: 'RobustFloat') -> 'RobustFloat':
        return RobustFloat(self.value * other.value,
                           self.relative_error + other.relative_error
                           + ROUNDING_ERROR)

    def __neg__(self) -> 'RobustFloat':
        return RobustFloat(-self.value, self.relative_error)

    def __sub__(self, other: 'RobustFloat') -> 'RobustFloat':
        value = self.value - other.value
        relative_error = (max(self.relative_error, other.relative_error)
                          + ROUNDING_ERROR
                          if (not self.value or not other.value
                              or (self.value > 0) is not (other.value > 0))
                          else
                          abs(safe_divide_floats(
                                  self.value * self.relative_error
                                  + other.value * other.relative_error, value))
                          + ROUNDING_ERROR)
        return RobustFloat(value, relative_error)

    def __truediv__(self, other: 'RobustFloat') -> 'RobustFloat':
        return RobustFloat(safe_divide_floats(self.value, other.value),
                           self.relative_error + other.relative_error
                           + ROUNDING_ERROR)

    def sqrt(self) -> 'RobustFloat':
        return RobustFloat(safe_sqrt(self.value),
                           self.relative_error * 0.5 + ROUNDING_ERROR)
