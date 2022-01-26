from typing import (Callable,
                    Union)

from ground.hints import (Point,
                          Scalar,
                          Segment)

CrossProducer = DotProducer = Callable[[Point, Point, Point, Point], Scalar]
Source = Union[Point, Segment]
