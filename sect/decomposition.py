import random
from typing import Sequence

from .core.location import Location
from .core.trapezoidal import Map
from .hints import (Contour,
                    Multisegment,
                    Shuffler)

Map = Map
Location = Location


def trapezoidal_polygon(border: Contour, holes: Sequence[Contour] = (),
                        *,
                        shuffler: Shuffler = random.shuffle) -> Map:
    """
    Returns trapezoidal map of the polygon.

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
    :returns: trapezoidal map of polygon.

    >>> map_ = trapezoidal_polygon([(0, 0), (6, 0), (6, 6), (0, 6)],
    ...                            [[(2, 2), (2, 4), (4, 4), (4, 2)]])
    >>> (1, 1) in map_
    True
    >>> (2, 2) in map_
    True
    >>> (3, 3) in map_
    False
    >>> map_.locate((1, 1)) is Location.INTERIOR
    True
    >>> map_.locate((2, 2)) is Location.BOUNDARY
    True
    >>> map_.locate((3, 3)) is Location.EXTERIOR
    True
    """
    return Map.from_polygon(border, holes, shuffler)


def trapezoidal_multisegment(multisegment: Multisegment,
                             *,
                             shuffler: Shuffler = random.shuffle) -> Map:
    return Map.from_multisegment(multisegment, shuffler)
