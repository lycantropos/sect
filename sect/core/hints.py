from typing import (Sequence,
                    Tuple)

from ground.hints import Point as _Point

Segment = Tuple[_Point, _Point]
Multisegment = Sequence[Segment]
