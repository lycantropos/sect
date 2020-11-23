from typing import Union

from reprit.base import generate_repr

from .robust_float import RobustFloat


class RobustDifference:
    __slots__ = 'minuend', 'subtrahend'

    def __init__(self, minuend: RobustFloat, subtrahend: RobustFloat) -> None:
        self.minuend = minuend
        self.subtrahend = subtrahend

    __repr__ = generate_repr(__init__)

    def __abs__(self) -> 'RobustDifference':
        return (-self
                if self.minuend.value < self.subtrahend.value
                else self)

    def __add__(self, other: Union[RobustFloat, 'RobustDifference']
                ) -> 'RobustDifference':
        if isinstance(other, RobustDifference):
            minuend, subtrahend = (self.minuend + other.minuend,
                                   self.subtrahend + other.subtrahend)
        elif other < 0:
            minuend, subtrahend = self.minuend, self.subtrahend - other
        else:
            minuend, subtrahend = self.minuend + other, self.subtrahend
        return RobustDifference(minuend, subtrahend)

    def __iadd__(self, other: Union[RobustFloat, 'RobustDifference']
                 ) -> 'RobustDifference':
        if isinstance(other, RobustDifference):
            self.minuend += other.minuend
            self.subtrahend += other.subtrahend
        elif other < 0:
            self.subtrahend -= other
        else:
            self.minuend += other
        return self

    def __imul__(self, other: Union[RobustFloat, 'RobustDifference']
                 ) -> 'RobustDifference':
        if isinstance(other, RobustDifference):
            self.minuend, self.subtrahend = (
                self.minuend * other.minuend
                + self.subtrahend * other.subtrahend,
                self.minuend * other.subtrahend
                + self.subtrahend * other.minuend)
        elif other < 0:
            other = -other
            self.minuend *= other
            self.subtrahend *= other
            self.minuend, self.subtrahend = self.subtrahend, self.minuend
        else:
            self.minuend *= other
            self.subtrahend *= other
        return self

    def __isub__(self, other: Union[RobustFloat, 'RobustDifference']
                 ) -> 'RobustDifference':
        if isinstance(other, RobustDifference):
            self.minuend += other.subtrahend
            self.subtrahend += other.minuend
        elif other < 0:
            self.minuend -= other
        else:
            self.subtrahend += other
        return self

    def __itruediv__(self, other: RobustFloat) -> 'RobustDifference':
        if other < 0:
            other = -other
            self.subtrahend /= other
            self.minuend /= other
            self.minuend, self.subtrahend = self.subtrahend, self.minuend
        else:
            self.minuend /= other
            self.subtrahend /= other
        return self

    def __mul__(self, other: Union[RobustFloat, 'RobustDifference']
                ) -> 'RobustDifference':
        if isinstance(other, RobustDifference):
            minuend, subtrahend = (self.minuend * other.minuend
                                   + self.subtrahend * other.subtrahend,
                                   self.minuend * other.subtrahend
                                   + self.subtrahend * other.minuend)
        elif other < 0:
            other = -other
            minuend, subtrahend = self.subtrahend * other, self.minuend * other
        else:
            minuend, subtrahend = self.minuend * other, self.subtrahend * other
        return RobustDifference(minuend, subtrahend)

    def __neg__(self) -> 'RobustDifference':
        return RobustDifference(self.subtrahend, self.minuend)

    def __sub__(self, other: Union[RobustFloat, 'RobustDifference']
                ) -> 'RobustDifference':
        if isinstance(other, RobustDifference):
            minuend, subtrahend = (self.minuend + other.subtrahend,
                                   self.subtrahend + other.minuend)
        elif other < 0:
            minuend, subtrahend = self.minuend - other, self.subtrahend
        else:
            minuend, subtrahend = self.minuend, self.subtrahend + other
        return RobustDifference(minuend, subtrahend)

    def __truediv__(self, other: RobustFloat) -> 'RobustDifference':
        if other < 0:
            other = -other
            minuend, subtrahend = self.subtrahend / other, self.minuend / other
        else:
            minuend, subtrahend = self.minuend / other, self.subtrahend / other
        return RobustDifference(minuend, subtrahend)

    @classmethod
    def zero(cls) -> 'RobustDifference':
        return cls(RobustFloat(), RobustFloat())

    def evaluate(self) -> RobustFloat:
        return self.minuend - self.subtrahend
