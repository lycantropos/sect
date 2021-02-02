from typing import (Callable,
                    MutableSequence,
                    Tuple)

from ground.hints import Coordinate

Box = Tuple[Coordinate, Coordinate, Coordinate, Coordinate]
Shuffler = Callable[[MutableSequence], None]
