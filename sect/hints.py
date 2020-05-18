from numbers import Real
from typing import (Callable,
                    MutableSequence,
                    Sequence,
                    Tuple)

Coordinate = Real
Point = Tuple[Coordinate, Coordinate]
Segment = Tuple[Point, Point]
Multisegment = Sequence[Segment]
Triangle = Tuple[Point, Point, Point]
Contour = Sequence[Point]
Shuffler = Callable[[MutableSequence], None]
