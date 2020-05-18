from typing import (FrozenSet,
                    Tuple)

from sect.hints import (Coordinate,
                        Point)

BoundingBox = Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
Endpoints = FrozenSet[Point]
