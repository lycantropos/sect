from __future__ import annotations

from functools import partial
from typing import Optional

from dendroid import red_black
from ground.base import (Context,
                         Orientation)
from reprit.base import generate_repr

from sect.core.hints import Orienteer
from .event import LeftEvent


class SweepLine:
    __slots__ = 'context', '_tree'

    def __init__(self, context: Context) -> None:
        self._tree = red_black.set_(key=partial(SweepLineKey,
                                                context.angle_orientation))

    __repr__ = generate_repr(__init__)

    def __contains__(self, event: LeftEvent) -> bool:
        return event in self._tree

    def add(self, event: LeftEvent) -> None:
        self._tree.add(event)

    def remove(self, event: LeftEvent) -> None:
        self._tree.remove(event)

    def above(self, event: LeftEvent) -> Optional[LeftEvent]:
        try:
            return self._tree.next(event)
        except ValueError:
            return None

    def below(self, event: LeftEvent) -> Optional[LeftEvent]:
        try:
            return self._tree.prev(event)
        except ValueError:
            return None


class SweepLineKey:
    __slots__ = 'event', 'orienteer'

    def __init__(self, orienteer: Orienteer, event: LeftEvent) -> None:
        self.orienteer, self.event = orienteer, event

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: SweepLineKey) -> bool:
        """
        Checks if the segment (or at least the point) associated with event
        is lower than other's.
        """
        event, other_event = self.event, other.event
        if event is other_event:
            return False
        start, end = event.start, event.end
        other_start, other_end = other_event.start, other_event.end
        other_start_orientation = self.orienteer(start, end, other_start)
        other_end_orientation = self.orienteer(start, end, other_end)
        if other_start_orientation is other_end_orientation:
            return (other_event.from_first
                    if other_start_orientation is Orientation.COLLINEAR
                    else (other_start_orientation
                          is Orientation.COUNTERCLOCKWISE))
        start_orientation = self.orienteer(other_start, other_end, start)
        end_orientation = self.orienteer(other_start, other_end, end)
        if start_orientation is end_orientation:
            return start_orientation is Orientation.CLOCKWISE
        elif other_start_orientation is Orientation.COLLINEAR:
            return other_end_orientation is Orientation.COUNTERCLOCKWISE
        elif start_orientation is Orientation.COLLINEAR:
            return end_orientation is Orientation.CLOCKWISE
        elif end_orientation is Orientation.COLLINEAR:
            return start_orientation is Orientation.CLOCKWISE
        else:
            return other_start_orientation is Orientation.COUNTERCLOCKWISE
