from __future__ import annotations

from functools import partial
from typing import (Iterable,
                    Optional)

from ground.base import (Context,
                         Orientation,
                         Relation)
from ground.hints import Point
from prioq.base import PriorityQueue
from reprit.base import generate_repr

from sect.core.hints import Orienteer
from .event import (Event,
                    LeftEvent)
from .hints import SegmentEndpoints
from .quad_edge import QuadEdge
from .sweep_line import SweepLine
from .utils import to_endpoints


class EventsQueueKey:
    __slots__ = 'event', 'orienteer'

    def __init__(self, orienteer: Orienteer, event: Event) -> None:
        self.orienteer, self.event = orienteer, event

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: EventsQueueKey) -> bool:
        event, other_event = self.event, other.event
        start, other_start = event.start, other_event.start
        if start.x != other_start.x:
            # different x-coordinate,
            # the event with lower x-coordinate is processed first
            return start.x < other_start.x
        elif start.y != other_start.y:
            # different points, but same x-coordinate,
            # the event with lower y-coordinate is processed first
            return start.y < other_start.y
        elif event.is_left is not other_event.is_left:
            # same start, but one is a left endpoint
            # and the other a right endpoint,
            # the right endpoint is processed first
            return other_event.is_left
        # same start, both events are left endpoints
        # or both are right endpoints
        else:
            other_end_orientation = self.orienteer(event.start, event.end,
                                                   other_event.end)
            # the lowest segment is processed first
            return (other_event.from_first
                    if other_end_orientation is Orientation.COLLINEAR
                    else other_end_orientation is (Orientation.COUNTERCLOCKWISE
                                                   if event.is_left
                                                   else Orientation.CLOCKWISE))


class EventsQueue:
    __slots__ = 'context', '_queue'

    def __init__(self, context: Context) -> None:
        self.context = context
        self._queue = PriorityQueue(key=partial(EventsQueueKey,
                                                context.angle_orientation))

    @staticmethod
    def compute_position(below_event: Optional[LeftEvent],
                         event: LeftEvent) -> None:
        if below_event is not None:
            event.other_interior_to_left = (below_event.other_interior_to_left
                                            if (event.from_first
                                                is below_event.from_first)
                                            else below_event.interior_to_left)

    def detect_intersection(self,
                            below_event: LeftEvent,
                            event: LeftEvent) -> bool:
        """
        Populates events queue with intersection events.
        Checks if events' segments overlap and have the same start.
        """
        relation = self.context.segments_relation(below_event, event)
        if relation is Relation.CROSS or relation is Relation.TOUCH:
            point = self.context.segments_intersection(below_event, event)
            if point != below_event.start and point != below_event.end:
                self.divide_segment(below_event, point)
            if point != event.start and point != event.end:
                self.divide_segment(event, point)
        elif relation is not Relation.DISJOINT:
            # segments overlap
            if below_event.from_first is event.from_first:
                raise ValueError('Edges of the same polygon '
                                 'should not overlap.')
            starts_equal = below_event.start == event.start
            ends_equal = below_event.end == event.end
            start_min, start_max = (
                (event, below_event)
                if starts_equal or (self._queue.key(event)
                                    < self._queue.key(below_event))
                else (below_event, event)
            )
            end_min, end_max = (
                (event.right, below_event.right)
                if ends_equal or (self._queue.key(event.right)
                                  < self._queue.key(below_event.right))
                else (below_event.right, event.right)
            )
            if starts_equal:
                # both line segments are equal or share the left endpoint
                event.is_overlap = below_event.is_overlap = True
                if not ends_equal:
                    self.divide_segment(end_max.left, end_min.start)
                return True
            elif ends_equal:
                # the line segments share the right endpoint
                self.divide_segment(start_min, start_max.start)
            else:
                self.divide_segment(start_min
                                    # one line segment includes the other one
                                    if start_min is end_max.left
                                    # no line segment includes the other one
                                    else start_max,
                                    end_min.start)
                self.divide_segment(start_min, start_max.start)
        return False

    def divide_segment(self, event: LeftEvent, point: Point) -> None:
        self.push(event.divide(point))
        self.push(event.right)

    def push(self, event: Event) -> None:
        self._queue.push(event)

    def register_edge(self,
                      edge: QuadEdge,
                      *,
                      from_first: bool,
                      is_counterclockwise_contour: bool) -> None:
        start_event = LeftEvent.from_segment_endpoints(
                to_endpoints(edge), from_first, is_counterclockwise_contour
        )
        start_event.edge = edge
        self.push(start_event)
        self.push(start_event.right)

    def register_segment(self,
                         endpoints: SegmentEndpoints,
                         *,
                         from_first: bool,
                         is_counterclockwise_contour: bool) -> None:
        start_event = LeftEvent.from_segment_endpoints(
                endpoints, from_first, is_counterclockwise_contour
        )
        self.push(start_event)
        self.push(start_event.right)

    def sweep(self) -> Iterable[LeftEvent]:
        sweep_line = SweepLine(self.context)
        queue = self._queue
        while queue:
            event = queue.pop()
            if event.is_left:
                sweep_line.add(event)
                above_event, below_event = (sweep_line.above(event),
                                            sweep_line.below(event))
                self.compute_position(below_event, event)
                if (above_event is not None
                        and self.detect_intersection(event, above_event)):
                    self.compute_position(event, above_event)
                if (below_event is not None
                        and self.detect_intersection(below_event, event)):
                    self.compute_position(sweep_line.below(below_event),
                                          below_event)
            else:
                event = event.left
                if event in sweep_line:
                    above_event, below_event = (sweep_line.above(event),
                                                sweep_line.below(event))
                    sweep_line.remove(event)
                    if above_event is not None and below_event is not None:
                        self.detect_intersection(below_event, above_event)
                yield event
