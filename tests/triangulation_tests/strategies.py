from functools import partial

from hypothesis import strategies
from hypothesis_geometry import planar

from tests.strategies import coordinates_strategies
from tests.utils import points_do_not_lie_on_the_same_line

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
