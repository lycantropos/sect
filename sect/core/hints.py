from typing import (Sequence,
                    Tuple)

from ground.hints import Coordinate

Point = Tuple[Coordinate, Coordinate]
Multipoint = Sequence[Point]
Segment = Tuple[Point, Point]
Multisegment = Sequence[Segment]
Contour = Sequence[Point]
