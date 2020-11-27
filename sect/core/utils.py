from itertools import chain
from typing import (Iterable,
                    Sequence,
                    Tuple,
                    TypeVar)

from robust.angular import (Orientation,
                            orientation)

from sect.hints import Contour

Domain = TypeVar('Domain')

flatten = chain.from_iterable


def to_contour_orientation(contour: Contour) -> Orientation:
    index = arg_min(contour)
    return orientation(contour[index], contour[index - 1],
                       contour[(index + 1) % len(contour)])


def arg_min(sequence: Sequence[Domain]) -> int:
    return min(range(len(sequence)),
               key=sequence.__getitem__)


def pairwise(iterable: Iterable[Domain]) -> Iterable[Tuple[Domain, Domain]]:
    iterator = iter(iterable)
    element = next(iterator, None)
    for next_element in iterator:
        yield element, next_element
        element = next_element
