from fractions import Fraction
from functools import partial
from typing import (Sequence,
                    Tuple)

from ground.base import get_context
from hypothesis import strategies
from hypothesis_geometry import planar

from tests.strategies import coordinates_strategies
from tests.strategies.base import MAX_COORDINATE
from tests.utils import (Point,
                         Polygon,
                         Segment,
                         Strategy,
                         contour_to_edges,
                         points_do_not_lie_on_the_same_line,
                         segment_contains_point,
                         sub_lists)

contexts = strategies.just(get_context())
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
                                              min_size=4))
                             .filter(points_do_not_lie_on_the_same_line))
triangles = coordinates_strategies.flatmap(planar.triangular_contours)
polygons = coordinates_strategies.flatmap(planar.polygons)
whole_polygons = coordinates_strategies.flatmap(partial(planar.polygons,
                                                        max_holes_size=0))


def to_polygons_with_extra_points(polygon: Polygon
                                  ) -> Strategy[Tuple[Polygon,
                                                      Sequence[Point]]]:
    return strategies.tuples(strategies.just(polygon),
                             sub_lists(sum(map(contour_to_edges,
                                               polygon.holes),
                                           contour_to_edges(polygon.border)))
                             .flatmap(to_segments_points))


def to_segments_points(segments: Sequence[Segment]
                       ) -> Strategy[Sequence[Point]]:
    return strategies.tuples(*map(to_segment_points, segments))


def to_segment_points(segment: Segment) -> Strategy[Point]:
    start, end = segment.start, segment.end
    delta_x, delta_y = end.x - start.x, end.y - start.y

    def to_segment_point(alpha: Fraction) -> Point:
        return Point(start.x + alpha * delta_x, start.y + alpha * delta_y)

    return (strategies.fractions(0, 1,
                                 max_denominator=MAX_COORDINATE)
            .map(to_segment_point)
            .filter(partial(segment_contains_point, segment)))


polygons_with_extra_points = polygons.flatmap(to_polygons_with_extra_points)
