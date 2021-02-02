from typing import (Callable,
                    Union)

from ground.hints import (Coordinate,
                          Point,
                          Segment)

CrossProducer = DotProducer = Callable[[Point, Point, Point, Point],
                                       Coordinate]
Source = Union[Point, Segment]
