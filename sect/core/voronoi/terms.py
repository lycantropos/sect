import math
from abc import (ABC,
                 abstractmethod)
from collections import defaultdict
from fractions import Fraction
from numbers import Real
from typing import (Any,
                    Callable,
                    Optional,
                    SupportsFloat,
                    SupportsInt,
                    Union)

from reprit.base import generate_repr

SquareRooter = Callable[[SupportsFloat], Real]


class Expression(ABC):
    @abstractmethod
    def evaluate(self, square_rooter: Optional[SquareRooter] = None) -> Real:
        """Evaluates the expression."""


class Constant(Expression):
    __slots__ = 'value',

    def __init__(self, value: Real = 0) -> None:
        assert isinstance(value, Real)
        self.value = Fraction(value)

    __repr__ = generate_repr(__init__)

    def __abs__(self) -> 'Constant':
        return Constant(abs(self.value))

    def __add__(self, other: Union[Real, 'Constant']) -> 'Constant':
        return (Constant(self.value + other)
                if isinstance(other, Real)
                else (Constant(self.value + other.value)
                      if isinstance(other, Constant)
                      else NotImplemented))

    def __bool__(self) -> bool:
        return bool(self.value)

    def __eq__(self, other: Union[Real, 'Constant']) -> bool:
        return (self.value == other
                if isinstance(other, Real)
                else (self.value == other.value
                      if isinstance(other, Constant)
                      else NotImplemented))

    def __gt__(self, other: Union[Real, 'Constant']) -> bool:
        return (self.value > other
                if isinstance(other, (Real, Constant))
                else NotImplemented)

    def __ge__(self, other: Union[Real, 'Constant']) -> bool:
        return (self.value >= other
                if isinstance(other, (Real, Constant))
                else NotImplemented)

    def __hash__(self) -> int:
        return hash(self.value)

    def __int__(self) -> int:
        assert self.value.denominator == 1
        return self.value.numerator

    def __le__(self, other: Union[Real, 'Constant']) -> bool:
        return (self.value <= other
                if isinstance(other, (Real, Constant))
                else NotImplemented)

    def __lt__(self, other: Union[Real, 'Constant']) -> bool:
        return (self.value < other
                if isinstance(other, (Real, Constant))
                else NotImplemented)

    def __mul__(self, other: Union[Real, 'Constant']) -> 'Constant':
        return (Constant(self.value * other.value)
                if isinstance(other, Constant)
                else (Constant(self.value * other)
                      if isinstance(other, Real)
                      else NotImplemented))

    def __neg__(self) -> 'Constant':
        return Constant(-self.value)

    def __radd__(self, other: Real) -> 'Constant':
        return (Constant(other + self.value)
                if isinstance(other, Real)
                else NotImplemented)

    def __rmul__(self, other: Real) -> 'Constant':
        return (Constant(self.value * other)
                if isinstance(other, Real)
                else NotImplemented)

    def __rsub__(self, other: Real) -> 'Constant':
        return other + (-self)

    def __rtruediv__(self, other: Real) -> 'Constant':
        return (Constant(other / self.value)
                if isinstance(other, Real)
                else NotImplemented)

    def __str__(self) -> str:
        return str(self.value)

    def __sub__(self, other: Union[Real, 'Constant']) -> 'Constant':
        return self + (-other)

    def __truediv__(self, other: Union[Real, 'Constant']) -> 'Constant':
        return (Constant(self.value / other)
                if isinstance(other, Real)
                else (Constant(self.value / other.value)
                      if isinstance(other, Constant)
                      else NotImplemented))

    def evaluate(self, square_rooter: Optional[SquareRooter] = None) -> Real:
        return self.value


Zero, One = Constant(0), Constant(1)


class Term(Expression):
    __slots__ = 'argument', 'scale'

    @classmethod
    def from_components(cls,
                        scale: Constant,
                        argument: Union[Constant, 'Term', 'Form']
                        ) -> Union[Constant, 'Term']:
        if not (scale and argument):
            return Zero
        if isinstance(argument, Constant):
            argument_value = argument.value
            argument_numerator = argument_value.numerator
            argument_numerator_sqrt_floor = _sqrt_floor(argument_numerator)
            if square(argument_numerator_sqrt_floor) == argument_numerator:
                scale *= argument_numerator_sqrt_floor
                argument /= argument_numerator
            argument_denominator = argument_value.denominator
            argument_denominator_sqrt_floor = _sqrt_floor(argument_denominator)
            if square(argument_denominator_sqrt_floor) == argument_denominator:
                scale /= argument_denominator_sqrt_floor
                argument *= argument_denominator
                if argument == One:
                    return scale
            elif argument_denominator != 1:
                scale /= argument_denominator
                argument = Constant(argument_numerator * argument_denominator)
        return cls(scale, argument)

    def __init__(self,
                 scale: Constant,
                 argument: Union[Constant, 'Term', 'Form']) -> None:
        assert isinstance(scale, Constant)
        assert isinstance(argument, (Constant, Term, Form))
        assert scale and argument
        assert argument > Zero
        assert (not isinstance(argument, Constant)
                or argument.value.denominator == 1)
        self.scale, self.argument = scale, argument

    __repr__ = generate_repr(__init__)

    def __add__(self, other: Union[Real, Constant, 'Term']) -> 'Form':
        return (Form(self,
                     tail=Constant(other))
                if isinstance(other, Real)
                else (Form(self,
                           tail=other)
                      if isinstance(other, Constant)
                      else (Form.from_components(self, other)
                            if isinstance(other, Term)
                            else NotImplemented)))

    def __eq__(self, other: 'Term') -> bool:
        return (self.scale == other.scale and self.argument == other.argument
                if isinstance(other, Term)
                else NotImplemented)

    def __ge__(self, other: Union[Real, Constant, 'Term']) -> bool:
        return (((other <= 0
                  or square(other) <= square(self.scale) * self.argument)
                 if self.scale > 0
                 else
                 (other <= 0
                  and square(other) >= square(self.scale) * self.argument))
                if isinstance(other, (Real, Constant, Term))
                else NotImplemented)

    def __gt__(self, other: Union[Real, Constant, 'Term']) -> bool:
        return (((other <= 0
                  or square(other) < square(self.scale) * self.argument)
                 if self.scale > 0
                 else (other <= 0
                       and square(other) > square(
                        self.scale) * self.argument))
                if isinstance(other, (Real, Constant, Term))
                else NotImplemented)

    def __hash__(self) -> int:
        return hash((self.scale, self.argument))

    def __le__(self, other: Union[Real, Constant, 'Term']) -> bool:
        return (((other > 0
                  and square(other) >= square(self.scale) * self.argument)
                 if self.scale > 0
                 else other > 0 or (square(other)
                                    <= square(self.scale) * self.argument))
                if isinstance(other, (Real, Constant, Term))
                else NotImplemented)

    def __lt__(self, other: Union[Real, Constant, 'Term']) -> bool:
        return (((other > 0
                  and square(other) > square(self.scale) * self.argument)
                 if self.scale > 0
                 else (other > 0
                       or square(other) < square(
                        self.scale) * self.argument))
                if isinstance(other, (Real, Constant, Term))
                else NotImplemented)

    def __mul__(self, other: Union[Real, Constant, 'Term']
                ) -> Union[Constant, 'Term']:
        return ((Term(self.scale * other, self.argument)
                 if other
                 else Zero)
                if isinstance(other, (Real, Constant))
                else (self._multiply_with_term(other)
                      if isinstance(other, Term)
                      else NotImplemented))

    def __neg__(self) -> 'Term':
        return Term(-self.scale, self.argument)

    def __radd__(self, other: Union[Real, Constant, 'Term']) -> 'Form':
        return (Form(self,
                     tail=Constant(other))
                if isinstance(other, Real)
                else (Form(self,
                           tail=other)
                      if isinstance(other, Constant)
                      else NotImplemented))

    def __rmul__(self, other: Union[Real, Constant]
                 ) -> Union[Constant, 'Term']:
        return ((Term(self.scale * other, self.argument)
                 if other
                 else Zero)
                if isinstance(other, (Real, Constant))
                else NotImplemented)

    def __rsub__(self, other: Union[Real, Constant]) -> 'Form':
        return (Form(self,
                     tail=Constant(-other))
                if isinstance(other, Real)
                else (Form(self,
                           tail=-other)
                      if isinstance(other, Constant)
                      else NotImplemented))

    def __rtruediv__(self, other: Union[Real, Constant]) -> 'Term':
        return (Term.from_components(other / self.scale, One / self.argument)
                if isinstance(other, (Real, Constant))
                else NotImplemented)

    def __str__(self) -> str:
        return '{} * sqrt({})'.format(self.scale, self.argument)

    def __sub__(self, other: Union[Real, Constant, 'Term']) -> 'Form':
        return (Form(self,
                     tail=Constant(-other))
                if isinstance(other, Real)
                else (Form(self,
                           tail=-other)
                      if isinstance(other, Constant)
                      else (Form.from_components(self, -other)
                            if isinstance(other, Term)
                            else NotImplemented)))

    def __truediv__(self, other: Union[Real, Constant, 'Term']) -> 'Term':
        return (Term(self.scale / other, self.argument)
                if isinstance(other, (Real, Constant))
                else (self._multiply_with_term(One / other)
                      if isinstance(other, Term)
                      else NotImplemented))

    def evaluate(self, square_rooter: Optional[SquareRooter] = None) -> Real:
        return (self.scale.evaluate(square_rooter)
                * (math.sqrt
                   if square_rooter is None
                   else square_rooter)(self.argument.evaluate(square_rooter)))

    def _multiply_with_term(self, other: 'Term') -> Union[Constant, 'Term']:
        scale = self.scale * other.scale
        argument, other_argument = self.argument, other.argument
        if argument == other_argument:
            return scale * argument
        elif (isinstance(argument, Constant)
              and isinstance(other_argument, Constant)):
            arguments_gcd = _gcd(argument, other_argument)
            argument /= arguments_gcd
            other_argument /= arguments_gcd
            scale *= arguments_gcd
        return Term.from_components(scale, argument * other_argument)


def _to_signed_value(value: Union[Constant, Term]) -> str:
    return ('+ ' + str(value)
            if value > 0
            else '- ' + str(-value))


class Form(Expression):
    __slots__ = 'tail', 'terms'

    @classmethod
    def from_components(cls,
                        *terms: Term,
                        tail: Constant = Zero
                        ) -> Union[Constant, Term, 'Form']:
        arguments_scales = defaultdict(Constant)
        for term in terms:
            arguments_scales[term.argument] += term.scale
        terms = list(filter(None,
                            [Term(scale, argument)
                             for argument, scale in arguments_scales.items()
                             if argument and scale]))
        return ((cls(*terms,
                     tail=tail)
                 if tail or len(terms) > 1
                 else terms[0])
                if terms
                else tail)

    def __init__(self, *terms: Term, tail: Constant = Zero) -> None:
        assert all(isinstance(term, Term) for term in terms)
        assert isinstance(tail, Constant)
        self.terms, self.tail = terms, tail

    __repr__ = generate_repr(__init__)

    def __abs__(self) -> 'Form':
        return self if _is_form_positive(self) else -self

    def __add__(self, other: Union[Real, Constant, Term, 'Form']
                ) -> Union[Constant, 'Form']:
        return (Form(*self.terms,
                     tail=self.tail + other)
                if isinstance(other, (Real, Constant))
                else (Form.from_components(*self.terms, other,
                                           tail=self.tail)
                      if isinstance(other, Term)
                      else (Form.from_components(*self.terms, *other.terms,
                                                 tail=self.tail + other.tail)
                            if isinstance(other, Form)
                            else NotImplemented)))

    def __eq__(self, other: 'Form') -> bool:
        return (self is other
                or (self.tail == other.tail
                    and len(self.terms) == len(other.terms)
                    and sorted(self.terms) == sorted(other.terms))
                if isinstance(other, Form)
                else (False
                      if isinstance(other, (Real, Constant, Term))
                      else NotImplemented))

    def __gt__(self, other: Union[Real, Constant, Term, 'Form']) -> bool:
        return (_is_positive(self - other)
                if isinstance(other, (Real, Constant, Term, Form))
                else NotImplemented)

    def __hash__(self) -> int:
        return hash((self.terms, self.tail))

    def __lt__(self, other: Union[Real, Constant, Term, 'Form']) -> bool:
        return (_is_positive(other - self)
                if isinstance(other, (Real, Constant, Term, Form))
                else NotImplemented)

    def __mul__(self, other: Union[Real, Constant, Term, 'Form']
                ) -> Union[Constant, 'Form']:
        return (((self._square()
                  if self == other
                  else sum([term * other for term in self.terms],
                           self.tail * other))
                 if other
                 else Zero)
                if isinstance(other, (Real, Constant, Term, Form))
                else NotImplemented)

    def __neg__(self) -> 'Form':
        return Form(*[-term for term in self.terms],
                    tail=-self.tail)

    def __radd__(self, other: Union[Real, Constant, Term]
                 ) -> Union[Constant, 'Form']:
        return (Form(*self.terms,
                     tail=other + self.tail)
                if isinstance(other, (Real, Constant))
                else (Form.from_components(other, *self.terms,
                                           tail=self.tail)
                      if isinstance(other, Term)
                      else NotImplemented))

    __rmul__ = __mul__

    def __rsub__(self, other: Union[Real, Constant, Term]
                 ) -> Union[Constant, 'Form']:
        return (other + (-self)
                if isinstance(other, (Real, Constant, Term))
                else NotImplemented)

    def __rtruediv__(self, other: Union[Real, Constant, Term]
                     ) -> Union[Constant, 'Form', 'Ratio']:
        components = (*self.terms, self.tail) if self.tail else self.terms
        components_count = len(components)
        if components_count > 2:
            return Ratio.from_components(Constant(other)
                                         if isinstance(other, Real)
                                         else other,
                                         self)
        delimiter = _ceil_half(components_count)
        subtrahend, minuend = (sum(components[:delimiter]),
                               sum(components[delimiter:]))
        return ((other * (subtrahend - minuend))
                / (square(subtrahend) - square(minuend)))

    def __str__(self) -> str:
        return (str(self.terms[0])
                + (' ' + ' '.join(map(_to_signed_value, self.terms[1:]))
                   if len(self.terms) > 1
                   else '')
                + (' ' + _to_signed_value(self.tail)
                   if self.tail
                   else ''))

    def __sub__(self, other: Union[Real, Constant, Term, 'Form']
                ) -> Union[Constant, Term, 'Form']:
        return (Form(*self.terms,
                     tail=self.tail - other)
                if isinstance(other, (Real, Constant))
                else (Form.from_components(*self.terms, -other,
                                           tail=self.tail)
                      if isinstance(other, Term)
                      else (Form.from_components(*self.terms, *(-other).terms,
                                                 tail=self.tail - other.tail)
                            if isinstance(other, Form)
                            else NotImplemented)))

    def __truediv__(self, other: Union[Real, Constant, Term, 'Form']
                    ) -> Union[Constant, 'Form']:
        return (Form(*[term / other for term in self.terms],
                     tail=self.tail / other)
                if isinstance(other, (Real, Constant))
                else (sum([term / other for term in self.terms],
                          self.tail / other)
                      if isinstance(other, Term)
                      else (Ratio.from_components(self, other)
                            if isinstance(other, Form)
                            else NotImplemented)))

    def evaluate(self, square_rooter: Optional[SquareRooter] = None) -> Real:
        return sum([term.evaluate(square_rooter) for term in self.terms],
                   self.tail.evaluate(square_rooter))

    def _square(self) -> 'Form':
        return sum([2 * (self.terms[step] * self.terms[index])
                    for step in range(1, len(self.terms))
                    for index in range(step)]
                   + ([(2 * self.tail) * term for term in self.terms]
                      if self.tail
                      else [])
                   + [square(term) for term in self.terms],
                   square(self.tail))


class Ratio(Expression):
    __slots__ = 'denominator', 'numerator'

    @classmethod
    def from_components(cls,
                        numerator: Union[Constant, Term, Form],
                        denominator: Form) -> Union[Constant, 'Ratio']:
        if not _is_form_positive(denominator):
            numerator, denominator = -numerator, -denominator
        return cls(numerator, denominator) if numerator else Zero

    def __init__(self,
                 numerator: Union[Constant, Term, Form],
                 denominator: Form) -> None:
        assert numerator
        assert isinstance(numerator, (Constant, Term, Form))
        assert isinstance(denominator, Form)
        assert _is_positive(denominator)
        self.numerator, self.denominator = numerator, denominator

    __repr__ = generate_repr(__init__)

    def __add__(self, other: Union[Constant, Term, Form, 'Ratio']
                ) -> Union[Constant, 'Ratio']:
        return (Ratio.from_components(self.numerator * other.denominator
                                      + other.numerator * self.denominator,
                                      self.denominator * other.denominator)
                if isinstance(other, Ratio)
                else Ratio.from_components(self.numerator
                                           + other * self.denominator,
                                           self.denominator))

    def __gt__(self, other: Union[Real, Constant, Term, Form, 'Ratio']
               ) -> bool:
        return (self.numerator > self.denominator * other
                if isinstance(other, (Real, Constant, Term, Form))
                else (self.numerator * other.denominator
                      > self.denominator * other.numerator
                      if isinstance(other, Ratio)
                      else NotImplemented))

    def __lt__(self, other: Union[Real, Constant, Term, Form, 'Ratio']
               ) -> bool:
        return (self.numerator < self.denominator * other
                if isinstance(other, (Real, Constant, Term, Form))
                else (self.numerator * other.denominator
                      < self.denominator * other.numerator
                      if isinstance(other, Ratio)
                      else NotImplemented))

    def __radd__(self, other: Union[Constant, Term, Form]
                 ) -> Union[Constant, 'Ratio']:
        return Ratio.from_components(self.numerator + other * self.denominator,
                                     self.denominator)

    def __str__(self) -> str:
        return '{} / ({})'.format('({})'.format(self.numerator)
                                  if isinstance(self.numerator, Form)
                                  else self.numerator,
                                  self.denominator)

    def evaluate(self, square_rooter: Optional[SquareRooter] = None) -> Real:
        return (self.numerator.evaluate(square_rooter)
                / self.denominator.evaluate(square_rooter))


def square(value: Any) -> Any:
    return value * value


def _ceil_half(value: int) -> int:
    return -(-value // 2)


def _constant_sqrt_ceil(value: Constant) -> Constant:
    fraction = value.value
    return Constant(Fraction(_sqrt_ceil(fraction.numerator),
                             _sqrt_floor(fraction.denominator)))


def _constant_sqrt_floor(value: Constant) -> Constant:
    fraction = value.value
    return Constant(Fraction(_sqrt_floor(fraction.numerator),
                             _sqrt_ceil(fraction.denominator)))


def _form_ceil(value: Form) -> Constant:
    return sum([_term_ceil(term) for term in value.terms], value.tail)


def _form_floor(value: Form) -> Constant:
    return sum([_term_floor(term) for term in value.terms], value.tail)


def _gcd(left: SupportsInt, right: SupportsInt) -> int:
    return math.gcd(int(left), int(right))


def _is_positive(value: Union[Constant, Term, Form]) -> bool:
    return (_is_form_positive(value)
            if isinstance(value, Form)
            else value > Zero)


def _is_form_positive(value: Union[Constant, Term, Form]) -> bool:
    components = (*value.terms, value.tail) if value.tail else value.terms
    positive, negative = [], []
    for component in components:
        if component > Zero:
            positive.append(component)
        else:
            negative.append(component)
    if not (positive and negative):
        return not negative
    positive_count, negative_count = len(positive), len(negative)
    positive_squares_sum, negative_squares_sum = (
        sum(map(square, positive)), sum(map(square, negative)))
    if not _is_positive(positive_count * positive_squares_sum
                        - negative_squares_sum):
        return False
    elif _is_positive(positive_squares_sum
                      - negative_count * negative_squares_sum):
        return True
    if not _form_ceil(value) > Zero:
        return False
    elif _form_floor(value) >= Zero:
        return True
    return not _is_form_positive(-value)


def _term_floor(term: Term) -> Constant:
    argument = term.argument
    argument_floor = _constant_sqrt_floor(argument
                                          if isinstance(argument, Constant)
                                          else
                                          (_term_floor(argument)
                                           if isinstance(argument, Term)
                                           else
                                           (sum(map(_term_floor,
                                                    argument.terms),
                                                argument.tail)
                                            if isinstance(argument, Form)
                                            else NotImplemented)))
    assert not square(argument_floor) > argument
    return term.scale * argument_floor


def _term_ceil(term: Term) -> Constant:
    argument = term.argument
    argument_ceil = _constant_sqrt_ceil(argument
                                        if isinstance(argument, Constant)
                                        else
                                        (_term_ceil(argument)
                                         if isinstance(argument, Term)
                                         else
                                         (sum(map(_term_ceil, argument.terms),
                                              argument.tail)
                                          if isinstance(argument, Form)
                                          else NotImplemented)))
    assert not square(argument_ceil) < argument
    return term.scale * argument_ceil


def _sqrt_ceil(value: int) -> int:
    sqrt_floor = _sqrt_floor(value)
    result = sqrt_floor + (value > square(sqrt_floor))
    assert not square(result) < value
    return result


try:
    _sqrt_floor = math.isqrt
except AttributeError:
    def _sqrt_floor(value: int) -> int:
        if value > 0:
            candidate = 1 << (value.bit_length() + 1 >> 1)
            while True:
                next_candidate = (candidate + value // candidate) >> 1
                if next_candidate >= candidate:
                    return candidate
                candidate = next_candidate
        elif value:
            raise ValueError('Argument must be non-negative.')
        else:
            return 0
