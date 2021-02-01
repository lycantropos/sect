from typing import Tuple

from ground.hints import Point

from .utils import to_convex_hull


def points_form_convex_quadrilateral(points: Tuple[Point, Point, Point, Point]
                                     ) -> bool:
    return len(to_convex_hull(points)) == 4
