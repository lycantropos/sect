import random

from ground.hints import (Multipoint,
                          Multisegment,
                          Polygon)

from .core import raw as _raw
from .core.trapezoidal.graph import Graph
from .core.trapezoidal.location import Location
from .core.voronoi.diagram import Diagram
from .hints import Shuffler as _Shuffler

Diagram = Diagram
Graph = Graph
Location = Location


def multisegment_trapezoidal(multisegment: Multisegment,
                             *,
                             shuffler: _Shuffler = random.shuffle) -> Graph:
    """
    Returns trapezoidal decomposition graph of the multisegment.

    Based on incremental randomized algorithm by R. Seidel.

    Time complexity:
        ``O(segments_count * log segments_count)`` expected,
        ``O(segments_count ** 2)`` worst,
        where ``segments_count = len(multisegment)``.
    Memory complexity:
        ``O(segments_count)``,
        where ``segments_count = len(multisegment)``.
    Reference:
        https://doi.org/10.1016%2F0925-7721%2891%2990012-4
        https://www.cs.princeton.edu/courses/archive/fall05/cos528/handouts/A%20Simple%20and%20fast.pdf

    :param multisegment: target multisegment.
    :param shuffler:
        function which mutates sequence by shuffling its elements,
        required for randomization.
    :returns: trapezoidal decomposition graph of the multisegment.

    >>> from ground.base import get_context
    >>> context = get_context()
    >>> Multisegment, Point, Segment = (context.multisegment_cls,
    ...                                 context.point_cls,
    ...                                 context.segment_cls)
    >>> graph = multisegment_trapezoidal(
    ...     Multisegment([Segment(Point(0, 0), Point(1, 0)),
    ...                   Segment(Point(0, 0), Point(0, 1))]))
    >>> Point(1, 0) in graph
    True
    >>> Point(0, 1) in graph
    True
    >>> Point(1, 1) in graph
    False
    >>> graph.locate(Point(1, 0)) is Location.BOUNDARY
    True
    >>> graph.locate(Point(0, 1)) is Location.BOUNDARY
    True
    >>> graph.locate(Point(1, 1)) is Location.EXTERIOR
    True
    """
    return Graph.from_multisegment(_raw.from_multisegment(multisegment),
                                   shuffler)


def polygon_trapezoidal(polygon: Polygon,
                        *,
                        shuffler: _Shuffler = random.shuffle) -> Graph:
    """
    Returns trapezoidal decomposition graph of the polygon
    given by border and holes.

    Based on incremental randomized algorithm by R. Seidel.

    Time complexity:
        ``O(vertices_count * log vertices_count)`` expected,
        ``O(vertices_count ** 2)`` worst,
        where ``vertices_count = len(border) + sum(map(len, holes))``.
    Memory complexity:
        ``O(vertices_count)``,
        where ``vertices_count = len(border) + sum(map(len, holes))``.
    Reference:
        https://doi.org/10.1016%2F0925-7721%2891%2990012-4
        https://www.cs.princeton.edu/courses/archive/fall05/cos528/handouts/A%20Simple%20and%20fast.pdf

    :param polygon: target polygon.
    :param shuffler:
        function which mutates sequence by shuffling its elements,
        required for randomization.
    :returns: trapezoidal decomposition graph of the border and holes.

    >>> from ground.base import get_context
    >>> context = get_context()
    >>> Contour, Point, Polygon = (context.contour_cls, context.point_cls,
    ...                            context.polygon_cls)
    >>> graph = polygon_trapezoidal(
    ...     Polygon(Contour([Point(0, 0), Point(6, 0), Point(6, 6),
    ...                      Point(0, 6)]),
    ...             [Contour([Point(2, 2), Point(2, 4), Point(4, 4),
    ...                       Point(4, 2)])]))
    >>> Point(1, 1) in graph
    True
    >>> Point(2, 2) in graph
    True
    >>> Point(3, 3) in graph
    False
    >>> graph.locate(Point(1, 1)) is Location.INTERIOR
    True
    >>> graph.locate(Point(2, 2)) is Location.BOUNDARY
    True
    >>> graph.locate(Point(3, 3)) is Location.EXTERIOR
    True
    """
    return Graph.from_polygon(polygon.border, polygon.holes, shuffler)


def multipoint_voronoi(multipoint: Multipoint) -> Diagram:
    return Diagram.from_sources(multipoint.points, ())


def multisegment_voronoi(multisegment: Multisegment) -> Diagram:
    return Diagram.from_sources((), _raw.from_multisegment(multisegment))
