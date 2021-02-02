from typing import (Callable,
                    Tuple)

from ground.base import Relation
from ground.hints import Point

QuaternaryPointPredicate = Callable[[Point, Point, Point, Point], bool]
SegmentEndpoints = Tuple[Point, Point]
SegmentPointRelater = Callable[[Point, Point, Point], bool]
SegmentsRelater = Callable[[Point, Point, Point, Point], Relation]
