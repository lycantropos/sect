from typing import (Sequence,
                    Tuple)

from ground.hints import Point as _Point

Multipoint = Sequence[_Point]
Segment = Tuple[_Point, _Point]
Multisegment = Sequence[Segment]
Contour = Sequence[_Point]
