from typing import Optional

from reprit.base import generate_repr

from .events import Circle
from .faces import Edge


class BeachLineValue:
    __slots__ = 'circle', 'edge'

    def __init__(self,
                 edge: Optional[Edge],
                 circle: Optional[Circle] = None) -> None:
        self.edge, self.circle = edge, circle

    __repr__ = generate_repr(__init__)

    def deactivate_circle(self) -> None:
        if self.circle is not None:
            self.circle.deactivate()
            self.circle = None
