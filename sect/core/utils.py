from itertools import chain
from typing import (Iterable,
                    List,
                    Sequence,
                    Tuple,
                    TypeVar)

from ground.base import (Orientation,
                         get_context)
from ground.hints import (Contour,
                          Coordinate,
                          Point)

from .hints import Orienteer

Domain = TypeVar('Domain')


def arg_min(sequence: Sequence[Domain]) -> int:
    return min(range(len(sequence)),
               key=sequence.__getitem__)


def contour_to_edges_endpoints(contour: Contour) -> List[Tuple[Point, Point]]:
    vertices = contour.vertices
    return [(vertices[index - 1], vertices[index])
            for index in range(len(vertices))]


def cross_product(first_start: Point,
                  first_end: Point,
                  second_start: Point,
                  second_end: Point) -> Coordinate:
    context = get_context()
    return context.cross_product(first_start, first_end, second_start,
                                 second_end)


def dot_product(first_start: Point,
                first_end: Point,
                second_start: Point,
                second_end: Point) -> Coordinate:
    context = get_context()
    return context.dot_product(first_start, first_end, second_start,
                               second_end)


flatten = chain.from_iterable


def orientation(vertex, first, second):
    context = get_context()
    return context.angle_orientation(vertex, first, second)


def pairwise(iterable: Iterable[Domain]) -> Iterable[Tuple[Domain, Domain]]:
    iterator = iter(iterable)
    element = next(iterator, None)
    for next_element in iterator:
        yield element, next_element
        element = next_element


def rotate_sequence(sequence: Sequence[Domain],
                    index: int) -> Sequence[Domain]:
    return (sequence[index:] + sequence[:index]
            if index
            else sequence)


def to_contour_orientation(contour: Contour,
                           orienteer: Orienteer) -> Orientation:
    vertices = contour.vertices
    index = arg_min(vertices)
    return orienteer(vertices[index - 1], vertices[index],
                     vertices[(index + 1) % len(vertices)])
