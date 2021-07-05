from typing import (Callable,
                    Tuple)

from ground.base import (Location,
                         Relation)
from ground.hints import (Point,
                          Segment)

PointInCircleLocator = Callable[[Point, Point, Point, Point], Location]
SegmentEndpoints = Tuple[Point, Point]
SegmentContainmentChecker = Callable[[Segment, Point], bool]
SegmentsRelater = Callable[[Segment, Segment], Relation]
