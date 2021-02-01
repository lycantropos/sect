from typing import Iterable

from ground.hints import Point

from .hints import BoundingBox


def points_to_bounding_box(points: Iterable[Point]) -> BoundingBox:
    points = iter(points)
    first_point = next(points)
    min_x = max_x = first_point.x
    min_y = max_y = first_point.y
    for point in points:
        x, y = point.x, point.y
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
    return min_x, min_y, max_x, max_y
