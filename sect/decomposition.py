import random
from typing import Sequence

from .core.location import Location
from .core.trapezoidal import Graph
from .core.voronoi.diagram import Diagram
from .hints import (Contour,
                    Multipoint,
                    Multisegment,
                    Shuffler)

Diagram = Diagram
Graph = Graph
Location = Location


def multisegment_trapezoidal(multisegment: Multisegment,
                             *,
                             shuffler: Shuffler = random.shuffle) -> Graph:
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

    :param multisegment:
        non-empty sequence of non-crossing & non-overlapping segments.
    :param shuffler:
        function which mutates sequence by shuffling its elements,
        required for randomization.
    :returns: trapezoidal decomposition graph of the multisegment.

    >>> graph = multisegment_trapezoidal([((0, 0), (1, 0)), ((0, 0), (0, 1))])
    >>> (1, 0) in graph
    True
    >>> (0, 1) in graph
    True
    >>> (1, 1) in graph
    False
    >>> graph.locate((1, 0)) is Location.BOUNDARY
    True
    >>> graph.locate((0, 1)) is Location.BOUNDARY
    True
    >>> graph.locate((1, 1)) is Location.EXTERIOR
    True
    """
    return Graph.from_multisegment(multisegment, shuffler)


def polygon_trapezoidal(border: Contour, holes: Sequence[Contour] = (),
                        *,
                        shuffler: Shuffler = random.shuffle) -> Graph:
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

    :param border: border of the polygon.
    :param holes: holes of the polygon.
    :param shuffler:
        function which mutates sequence by shuffling its elements,
        required for randomization.
    :returns: trapezoidal decomposition graph of the border and holes.

    >>> graph = polygon_trapezoidal([(0, 0), (6, 0), (6, 6), (0, 6)],
    ...                             [[(2, 2), (2, 4), (4, 4), (4, 2)]])
    >>> (1, 1) in graph
    True
    >>> (2, 2) in graph
    True
    >>> (3, 3) in graph
    False
    >>> graph.locate((1, 1)) is Location.INTERIOR
    True
    >>> graph.locate((2, 2)) is Location.BOUNDARY
    True
    >>> graph.locate((3, 3)) is Location.EXTERIOR
    True
    """
    return Graph.from_polygon(border, holes, shuffler)


def multipoint_voronoi(multipoint: Multipoint) -> Diagram:
    return Diagram.from_sources(multipoint, ())
