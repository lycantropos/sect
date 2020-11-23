from typing import Optional

from reprit.base import generate_repr

from .events import CircleEvent
from .faces import Edge


class BeachLineValue:
    def __init__(self,
                 edge: Optional[Edge],
                 circle_event: Optional[CircleEvent] = None) -> None:
        self.edge = edge
        self.circle_event = circle_event

    __repr__ = generate_repr(__init__)
