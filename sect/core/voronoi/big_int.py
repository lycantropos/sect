import ctypes
from math import (copysign,
                  inf,
                  ldexp)
from typing import (List,
                    Tuple)

from reprit.base import generate_repr

from .big_float import BigFloat
from .utils import to_sign

MAX_DIGITS_COUNT = 64


class BigInt:
    __slots__ = 'digits', 'sign'

    def __init__(self, sign: int, digits: List[int]) -> None:
        if not (sign and digits):
            sign, digits = 0, []
        self.digits = digits
        self.sign = sign if digits else 0

    __repr__ = generate_repr(__init__)

    def __abs__(self) -> 'BigInt':
        return BigInt(abs(self.sign), self.digits)

    def __add__(self, other: 'BigInt') -> 'BigInt':
        result = BigInt(0, [])
        result._add(self, other)
        return result

    def __bool__(self) -> bool:
        return bool(self.sign)

    def __int__(self) -> int:
        result = 0
        multiplier = 1
        for digit in self.digits:
            result += multiplier * digit
            multiplier <<= 32
        return self.sign * result

    def __float__(self) -> float:
        mantissa, exponent = self.frexp()
        try:
            return ldexp(mantissa, exponent)
        except OverflowError:
            return copysign(inf, mantissa)

    def __mul__(self, other: 'BigInt') -> 'BigInt':
        result = BigInt(0, [])
        result._multiply(self, other)
        return result

    def __neg__(self) -> 'BigInt':
        return BigInt(-self.sign, self.digits[:])

    def __sub__(self, other: 'BigInt') -> 'BigInt':
        result = BigInt(0, [])
        result._subtract(self, other)
        return result

    @classmethod
    def from_int32(cls, value: int) -> 'BigInt':
        if value > 0:
            sign, digits = 1, [_to_uint32(value)]
        elif value < 0:
            sign, digits = -1, [_to_uint32(-value)]
        else:
            sign, digits = 0, []
        return cls(sign, digits)

    @classmethod
    def from_int64(cls, value: int) -> 'BigInt':
        if value > 0:
            sign, digits = 1, [_to_uint32(value)]
            value >>= 32
            if value:
                digits.append(value)
        elif value < 0:
            value = -value
            sign, digits = -1, [_to_uint32(value)]
            value >>= 32
            if value:
                digits.append(value)
        else:
            sign, digits = 0, []
        return cls(sign, digits)

    def frexp(self) -> Tuple[float, int]:
        mantissa, exponent = 0., 0
        size = len(self.digits)
        if not size:
            return mantissa, exponent
        else:
            if size == 1:
                mantissa = float(self.digits[0])
            elif size == 2:
                mantissa = (float(self.digits[1]) * float(0x100000000)
                            + float(self.digits[0]))
            else:
                for index in range(1, 4):
                    mantissa *= float(0x100000000)
                    mantissa += float(self.digits[size - index])
                exponent = (size - 3) << 5
        if self.sign < 0:
            mantissa = -mantissa
        return mantissa, exponent

    def _add(self, left: 'BigInt', right: 'BigInt') -> None:
        if not left.sign:
            self.sign, self.digits = right.sign, right.digits[:]
            return
        elif not right.sign:
            self.sign, self.digits = left.sign, left.digits[:]
            return
        elif left.sign == right.sign:
            self._add_digits(left.digits, right.digits)
        else:
            self._subtract_digits(left.digits, len(left.digits), right.digits,
                                  len(right.digits))
        if left.sign < 0:
            self.sign = -self.sign

    def _add_digits(self,
                    left_digits: List[int],
                    right_digits: List[int]) -> None:
        left_size, right_size = len(left_digits), len(right_digits)
        if left_size < right_size:
            self._add_digits(right_digits, left_digits)
            return
        self.sign = to_sign(left_size)
        cursor = 0
        for index, right_digit in enumerate(right_digits):
            cursor += left_digits[index] + right_digit
            self.digits.append(_to_uint32(cursor))
            cursor >>= 32
        for index in range(right_size, left_size):
            cursor += left_digits[index]
            self.digits.append(cursor)
            cursor >>= 32
        if cursor and len(self.digits) < MAX_DIGITS_COUNT:
            self.digits.append(cursor)

    def _multiply(self, left: 'BigInt', right: 'BigInt') -> None:
        if not left.sign or not right.sign:
            return
        self._multiply_digits(left.digits, right.digits)
        if left.sign != right.sign:
            self.sign = -self.sign

    def _multiply_digits(self,
                         left_digits: List[int],
                         right_digits: List[int]) -> None:
        current_digit = 0
        self.sign = 1
        left_size, right_size = len(left_digits), len(right_digits)
        for shift in range(min(MAX_DIGITS_COUNT, left_size + right_size - 1)):
            next_digit = 0
            for left_index in range(shift + 1):
                if left_index >= left_size:
                    break
                right_index = shift - left_index
                if right_index >= right_size:
                    continue
                step = left_digits[left_index] * right_digits[right_index]
                current_digit += _to_uint32(step)
                next_digit += step >> 32
            self.digits.append(_to_uint32(current_digit))
            current_digit = next_digit + (current_digit >> 32)
        if current_digit and len(self.digits) < MAX_DIGITS_COUNT:
            self.digits.append(_to_uint32(current_digit))

    def _subtract(self, left: 'BigInt', right: 'BigInt') -> None:
        if not left.sign:
            self.sign, self.digits = -right.sign, right.digits[:]
            return
        elif not right.sign:
            self.sign, self.digits = left.sign, left.digits[:]
            return
        elif left.sign == right.sign:
            self._subtract_digits(left.digits, len(left.digits), right.digits,
                                  len(right.digits))
        else:
            self._add_digits(left.digits, right.digits)
        if left.sign < 0:
            self.sign = -self.sign

    def _subtract_digits(self,
                         left_digits: List[int],
                         left_limit: int,
                         right_digits: List[int],
                         right_limit: int,
                         is_recursive_call: bool = False) -> None:
        if left_limit < right_limit:
            self._subtract_digits(right_digits, right_limit, left_digits,
                                  left_limit, True)
            self.sign = -self.sign
            return
        elif not is_recursive_call and left_limit == right_limit:
            left_limit = left_limit
            while True:
                left_limit -= 1
                if left_digits[left_limit] < right_digits[left_limit]:
                    left_limit += 1
                    self._subtract_digits(right_digits, left_limit,
                                          left_digits,
                                          left_limit, True)
                    self.sign = -self.sign
                    return
                elif left_digits[left_limit] > right_digits[left_limit]:
                    left_limit += 1
                    break
                elif not left_limit:
                    break
            if not left_limit:
                self.sign = 0
                return
            right_limit = left_limit
        self.sign = to_sign(left_limit - 1)
        flag = False
        for index in range(right_limit):
            self.digits.append(_to_uint32(left_digits[index]
                                          - right_digits[index] - flag))
            flag = (left_digits[index] < right_digits[index]
                    or left_digits[index] == right_digits[index] and flag)
        for index in range(right_limit, left_limit):
            self.digits.append(_to_uint32(left_digits[index] - flag))
            flag = not left_digits[index] and flag
        if self.digits[-1]:
            self.sign = 1
        else:
            self.digits.pop()


def robust_product_with_sqrt(left: BigInt, right: BigInt) -> BigFloat:
    return to_big_float(left) * to_big_float(right).sqrt()


def robust_sum_of_products_with_sqrt_pairs(left: Tuple[BigInt, BigInt],
                                           right: Tuple[BigInt, BigInt]
                                           ) -> BigFloat:
    first_left, second_left = left
    first_right, second_right = right
    a, b = (robust_product_with_sqrt(first_left, first_right),
            robust_product_with_sqrt(second_left, second_right))
    return (a + b
            if (a.mantissa >= 0 and b.mantissa >= 0
                or a.mantissa <= 0 and b.mantissa <= 0)
            else (to_big_float(first_left * first_left * first_right
                               - second_left * second_left * second_right)
                  / (a - b)))


def robust_sum_of_products_with_sqrt_quadruplets(
        left: Tuple[BigInt, BigInt, BigInt, BigInt],
        right: Tuple[BigInt, BigInt, BigInt, BigInt]) -> BigFloat:
    first_left, second_left, third_left, fourth_left = left
    first_right, second_right, third_right, fourth_right = right
    a = robust_sum_of_products_with_sqrt_pairs((first_left, second_left),
                                               (first_right, second_right))
    b = robust_sum_of_products_with_sqrt_pairs((third_left, fourth_left),
                                               (third_right, fourth_right))
    return (a + b
            if (a.mantissa >= 0 and b.mantissa >= 0
                or a.mantissa <= 0 and b.mantissa <= 0)
            else
            robust_sum_of_products_with_sqrt_triplets(
                    (first_left * first_left * first_right
                     + second_left * second_left * second_right
                     - third_left * third_left * third_right
                     - fourth_left * fourth_left * fourth_right,
                     first_left * second_left * BigInt.from_int32(2),
                     third_left * fourth_left * BigInt.from_int32(-2)),
                    (BigInt.from_int32(1),
                     first_right * second_right,
                     third_right * fourth_right))
            / (a - b))


def robust_sum_of_products_with_sqrt_triplets(
        left: Tuple[BigInt, BigInt, BigInt],
        right: Tuple[BigInt, BigInt, BigInt]) -> BigFloat:
    first_left, second_left, third_left = left
    first_right, second_right, third_right = right
    a = robust_sum_of_products_with_sqrt_pairs((first_left, second_left),
                                               (first_right, second_right))
    b = robust_product_with_sqrt(third_left, third_right)
    return (a + b
            if (a.mantissa >= 0 and b.mantissa >= 0
                or a.mantissa <= 0 and b.mantissa <= 0)
            else
            robust_sum_of_products_with_sqrt_pairs(
                    (first_left * first_left * first_right
                     + second_left * second_left * second_right
                     - third_left * third_left * third_right,
                     first_left * second_left * BigInt.from_int32(2)),
                    (BigInt.from_int32(1), first_right * second_right))
            / (a - b))


def to_big_float(value: BigInt) -> BigFloat:
    mantissa, exponent = value.frexp()
    return BigFloat(mantissa, exponent)


def to_first_point_segment_segment_quadruplets_expression(
        left: Tuple[BigInt, BigInt, BigInt, BigInt],
        right: Tuple[BigInt, BigInt, BigInt, BigInt]) -> BigFloat:
    lh = robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
    rh = robust_sum_of_products_with_sqrt_pairs(left[2:], right[2:])
    if (lh.mantissa >= 0 and rh.mantissa >= 0
            or lh.mantissa <= 0 and rh.mantissa <= 0):
        return lh + rh
    return (robust_sum_of_products_with_sqrt_pairs(
            (left[0] * left[0] * right[0] + left[1] * left[1] * right[1]
             - left[2] * left[2] - left[3] * left[3] * right[0] * right[1],
             (left[0] * left[1] - left[2] * left[3]) * BigInt.from_int32(2)),
            (BigInt.from_int32(1), right[3]))
            / (lh - rh))


def to_second_point_segment_segment_quadruplets_expression(
        left: Tuple[BigInt, BigInt, BigInt, BigInt],
        right: Tuple[BigInt, BigInt, BigInt, BigInt]) -> BigFloat:
    if left[3]:
        rh = (robust_product_with_sqrt(left[2], right[3])
              * robust_sum_of_products_with_sqrt_pairs(
                        (BigInt.from_int32(1), right[2]),
                        (right[0] * right[1], BigInt.from_int32(1))).sqrt())
        common_right_coefficients = (right[0], right[1], BigInt.from_int32(1))
        lh = robust_sum_of_products_with_sqrt_triplets(
                (left[0], left[1], left[3]), common_right_coefficients)
        return (lh + rh
                if (lh.mantissa >= 0 and rh.mantissa >= 0
                    or lh.mantissa <= 0 and rh.mantissa <= 0)
                else
                to_first_point_segment_segment_quadruplets_expression(
                        (left[3] * left[0] * BigInt.from_int32(2),
                         left[3] * left[1] * BigInt.from_int32(2),
                         left[0] * left[0] * right[0]
                         + left[1] * left[1] * right[1] + left[3] * left[3]
                         - left[2] * left[2] * right[2] * right[3],
                         left[0] * left[1] * BigInt.from_int32(2)
                         - left[2] * left[2] * right[3]),
                        common_right_coefficients + (right[0] * right[1],))
                / (lh - rh))
    else:
        lh = robust_sum_of_products_with_sqrt_pairs(left[:2], right[:2])
        rh = (robust_product_with_sqrt(left[2], right[3])
              * robust_sum_of_products_with_sqrt_pairs(
                        (BigInt.from_int32(1), right[2]),
                        (right[0] * right[1], BigInt.from_int32(1))).sqrt())
        return (lh + rh
                if (lh.mantissa >= 0 and rh.mantissa >= 0
                    or lh.mantissa <= 0 and rh.mantissa <= 0)
                else
                robust_sum_of_products_with_sqrt_pairs(
                        (left[0] * left[0] * right[0]
                         + left[1] * left[1] * right[1]
                         - left[2] * left[2] * right[3] * right[2],
                         left[0] * left[1] * BigInt.from_int32(2)
                         - left[2] * left[2] * right[3]),
                        (BigInt.from_int32(1), right[0] * right[1]))
                / (lh - rh))


def _to_uint32(value: int) -> int:
    return ctypes.c_uint32(value).value
