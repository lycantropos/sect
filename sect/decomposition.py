import random
from typing import Sequence

from .core.location import Location
from .core.trapezoidal import Map
from .hints import (Contour,
                    Shuffler)

Map = Map
Location = Location


def trapezoidal(border: Contour, holes: Sequence[Contour] = (),
                *,
                shuffler: Shuffler = random.shuffle) -> Map:
    return Map.from_polygon(border, holes, shuffler)
