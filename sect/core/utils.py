import typing as _t
from itertools import chain

import typing_extensions as _te
from ground.base import Orientation
from ground.hints import (Contour,
                          Point)

from .hints import (Domain,
                    Orienteer)


class _Sortable(_te.Protocol):
    def __lt__(self, other: _te.Self) -> _t.Any:
        ...


_SortableT = _t.TypeVar('_SortableT',
                        bound=_Sortable)


def arg_min(sequence: _t.Sequence[_SortableT]) -> int:
    return min(range(len(sequence)),
               key=sequence.__getitem__)


def contour_to_edges_endpoints(contour: Contour) -> _t.List[
    _t.Tuple[Point, Point]]:
    vertices = contour.vertices
    return [(vertices[index - 1], vertices[index])
            for index in range(len(vertices))]


flatten = chain.from_iterable


def pairwise(
        iterable: _t.Iterable[Domain]
) -> _t.Iterable[_t.Tuple[Domain, Domain]]:
    iterator = iter(iterable)
    try:
        element = next(iterator)
    except StopIteration:
        return
    for next_element in iterator:
        yield element, next_element
        element = next_element


def rotate_list(value: _t.List[Domain], index: int) -> _t.List[Domain]:
    return value[index:] + value[:index] if index else value


def to_contour_orientation(contour: Contour,
                           orienteer: Orienteer) -> Orientation:
    vertices = contour.vertices
    index = arg_min(vertices)
    return orienteer(vertices[index - 1], vertices[index],
                     vertices[(index + 1) % len(vertices)])
