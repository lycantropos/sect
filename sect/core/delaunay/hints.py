from typing import (Callable,
                    Tuple)

from ground.base import Relation
from ground.hints import (Point,
                          Segment)

QuaternaryPointPredicate = Callable[[Point, Point, Point, Point], bool]
SegmentEndpoints = Tuple[Point, Point]
SegmentContainmentChecker = Callable[[Segment, Point], bool]
SegmentsRelater = Callable[[Segment, Segment], Relation]
