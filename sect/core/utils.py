from enum import (IntEnum,
                  unique)
from itertools import chain
from typing import (Iterable,
                    List,
                    Sequence,
                    Tuple,
                    TypeVar)

from ground.base import (Orientation,
                         Relation,
                         get_context)
from ground.hints import (Contour,
                          Coordinate,
                          Point)

Domain = TypeVar('Domain')

Orientation = Orientation


@unique
class SegmentsRelationship(IntEnum):
    """
    Represents relationship between segments based on their intersection.
    """
    #: intersection is empty
    NONE = 0
    #: intersection is an endpoint of one of segments
    TOUCH = 1
    #: intersection is a point which is not an endpoint of any of segments
    CROSS = 2
    #: intersection is a segment itself
    OVERLAP = 3


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


def segments_intersection(first_start: Point,
                          first_end: Point,
                          second_start: Point,
                          second_end: Point) -> Point:
    context = get_context()
    return context.segments_intersection(first_start, first_end, second_start,
                                         second_end)


def segments_relationship(test_start: Point,
                          test_end: Point,
                          goal_start: Point,
                          goal_end: Point) -> SegmentsRelationship:
    context = get_context()
    result = context.segments_relation(test_start, test_end, goal_start,
                                       goal_end)
    return (SegmentsRelationship.NONE if result is Relation.DISJOINT
            else (SegmentsRelationship.TOUCH if result is Relation.TOUCH
                  else (SegmentsRelationship.CROSS if result is Relation.CROSS
                        else SegmentsRelationship.OVERLAP)))


def to_contour_orientation(contour: Contour) -> Orientation:
    vertices = contour.vertices
    index = arg_min(vertices)
    return orientation(vertices[index - 1], vertices[index],
                       vertices[(index + 1) % len(vertices)])
