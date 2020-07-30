from fractions import Fraction
from functools import partial
from typing import (Sequence,
                    Tuple)

from hypothesis import strategies
from hypothesis_geometry import planar
from robust.linear import segment_contains

from sect.core.utils import contour_to_segments
from sect.hints import (Point,
                        Segment)
from tests.strategies import coordinates_strategies
from tests.strategies.base import MAX_COORDINATE
from tests.utils import (Polygon,
                         Strategy,
                         points_do_not_lie_on_the_same_line,
                         sub_lists)

to_points_lists = partial(strategies.lists,
                          unique=True)
points_lists = (coordinates_strategies
                .map(planar.points)
                .flatmap(partial(to_points_lists,
                                 min_size=3))
                .filter(points_do_not_lie_on_the_same_line))
non_triangle_points_lists = (coordinates_strategies
                             .map(planar.points)
                             .flatmap(partial(to_points_lists,
                                              min_size=4)))
triangles = (coordinates_strategies.flatmap(planar.triangular_contours)
             .map(tuple))
contours = coordinates_strategies.flatmap(planar.contours)
polygons = coordinates_strategies.flatmap(planar.polygons)


def to_polygons_with_extra_points(polygon: Polygon
                                  ) -> Strategy[Tuple[Polygon,
                                                      Sequence[Point]]]:
    border, holes = polygon
    return strategies.tuples(strategies.just(polygon),
                             sub_lists(sum(map(contour_to_segments, holes),
                                           contour_to_segments(border)))
                             .flatmap(to_segments_points))


def to_segments_points(segments: Sequence[Segment]
                       ) -> Strategy[Sequence[Point]]:
    return strategies.tuples(*map(to_segment_points, segments))


def to_segment_points(segment: Segment) -> Strategy[Point]:
    (start_x, start_y), (end_x, end_y) = segment
    delta_x, delta_y = end_x - start_x, end_y - start_y

    def to_segment_point(alpha: Fraction) -> Point:
        return start_x + alpha * delta_x, start_y + alpha * delta_y

    return (strategies.fractions(0, 1,
                                 max_denominator=MAX_COORDINATE)
            .map(to_segment_point)
            .filter(partial(segment_contains, segment)))


polygons_with_extra_points = polygons.flatmap(to_polygons_with_extra_points)
