from numbers import Real
from typing import (Sequence,
                    Tuple)

Coordinate = Real
Point = Tuple[Coordinate, Coordinate]
Segment = Tuple[Point, Point]
Triangle = Tuple[Point, Point, Point]
Contour = Sequence[Point]
