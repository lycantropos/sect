from enum import (IntEnum,
                  unique)
from itertools import chain
from typing import (Iterable,
                    Sequence,
                    Tuple,
                    TypeVar)

from ground.base import (Orientation,
                         Relation,
                         get_context)

from sect.hints import (Contour,
                        Coordinate,
                        Point,
                        Segment)

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


def cross_product(first_start: Point,
                  first_end: Point,
                  second_start: Point,
                  second_end: Point) -> Coordinate:
    context = get_context()
    point_cls = context.point_cls
    return context.cross_product(point_cls(*first_start),
                                 point_cls(*first_end),
                                 point_cls(*second_start),
                                 point_cls(*second_end))


def dot_product(first_start: Point,
                first_end: Point,
                second_start: Point,
                second_end: Point) -> Coordinate:
    context = get_context()
    point_cls = context.point_cls
    return context.dot_product(point_cls(*first_start), point_cls(*first_end),
                               point_cls(*second_start),
                               point_cls(*second_end))


flatten = chain.from_iterable


def orientation(vertex, first, second):
    context = get_context()
    point_cls = context.point_cls
    return context.angle_orientation(point_cls(*vertex), point_cls(*first),
                                     point_cls(*second))


def pairwise(iterable: Iterable[Domain]) -> Iterable[Tuple[Domain, Domain]]:
    iterator = iter(iterable)
    element = next(iterator, None)
    for next_element in iterator:
        yield element, next_element
        element = next_element


def point_point_point_incircle_test(first_vertex: Point,
                                    second_vertex: Point,
                                    third_vertex: Point,
                                    point: Point) -> Coordinate:
    context = get_context()
    point_cls = context.point_cls
    return context.point_point_point_incircle_test(point_cls(*first_vertex),
                                                   point_cls(*second_vertex),
                                                   point_cls(*third_vertex),
                                                   point_cls(*point))


def segments_intersection(first: Segment, second: Segment) -> Point:
    first_start, first_end = first
    second_start, second_end = second
    context = get_context()
    point_cls = context.point_cls
    result = context.segments_intersection(point_cls(*first_start),
                                           point_cls(*first_end),
                                           point_cls(*second_start),
                                           point_cls(*second_end))
    return result.x, result.y


def segments_relationship(first: Segment,
                          second: Segment) -> SegmentsRelationship:
    first_start, first_end = first
    second_start, second_end = second
    context = get_context()
    point_cls = context.point_cls
    result = context.segments_relation(point_cls(*first_start),
                                       point_cls(*first_end),
                                       point_cls(*second_start),
                                       point_cls(*second_end))
    return (SegmentsRelationship.NONE if result is Relation.DISJOINT
            else (SegmentsRelationship.TOUCH if result is Relation.TOUCH
                  else (SegmentsRelationship.CROSS if result is Relation.CROSS
                        else SegmentsRelationship.OVERLAP)))


def to_contour_orientation(contour: Contour) -> Orientation:
    index = arg_min(contour)
    return orientation(contour[index - 1], contour[index],
                       contour[(index + 1) % len(contour)])
