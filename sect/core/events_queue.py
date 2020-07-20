from typing import (Iterable,
                    Optional)

from prioq.base import PriorityQueue
from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)
from robust.linear import (SegmentsRelationship,
                           segments_intersection,
                           segments_relationship)

from sect.hints import (Point,
                        Segment)
from .event import Event
from .quad_edge import QuadEdge
from .sweep_line import SweepLine


class EventsQueueKey:
    __slots__ = 'event',

    def __init__(self, event: Event) -> None:
        self.event = event

    __repr__ = generate_repr(__init__)

    def __lt__(self, other: 'EventsQueueKey') -> bool:
        event, other_event = self.event, other.event
        start_x, start_y = event.start
        other_start_x, other_start_y = other_event.start
        if start_x != other_start_x:
            # different x-coordinate,
            # the event with lower x-coordinate is processed first
            return start_x < other_start_x
        elif start_y != other_start_y:
            # different points, but same x-coordinate,
            # the event with lower y-coordinate is processed first
            return start_y < other_start_y
        elif event.is_left_endpoint is not other_event.is_left_endpoint:
            # same start, but one is a left endpoint
            # and the other a right endpoint,
            # the right endpoint is processed first
            return other_event.is_left_endpoint
        # same start, both events are left endpoints
        # or both are right endpoints
        else:
            other_end_orientation = orientation(event.end, event.start,
                                                other_event.end)
            # the lowest segment is processed first
            return (other_event.from_left
                    if other_end_orientation is Orientation.COLLINEAR
                    else other_end_orientation is (Orientation.COUNTERCLOCKWISE
                                                   if event.is_left_endpoint
                                                   else Orientation.CLOCKWISE))


class EventsQueue:
    __slots__ = '_queue',

    def __init__(self) -> None:
        self._queue = PriorityQueue(key=EventsQueueKey)

    @staticmethod
    def compute_position(below_event: Optional[Event], event: Event) -> None:
        if below_event is not None:
            event.other_interior_to_left = (below_event.other_interior_to_left
                                            if (event.from_left
                                                is below_event.from_left)
                                            else below_event.interior_to_left)

    def detect_intersection(self, below_event: Event, event: Event) -> bool:
        """
        Populates events queue with intersection events.
        Checks if events' segments overlap and have the same start.
        """
        below_segment, segment = below_event.segment, event.segment
        relationship = segments_relationship(below_segment, segment)
        if relationship is SegmentsRelationship.OVERLAP:
            # segments overlap
            if below_event.from_left is event.from_left:
                raise ValueError(
                        'Edges of the same polygon should not overlap.')
            starts_equal = below_event.start == event.start
            ends_equal = below_event.end == event.end
            start_min, start_max = ((None, None)
                                    if starts_equal
                                    else ((event, below_event)
                                          if (EventsQueueKey(event)
                                              < EventsQueueKey(below_event))
                                          else (below_event, event)))
            end_min, end_max = ((None, None)
                                if ends_equal
                                else
                                (event.complement, below_event.complement
                                if (EventsQueueKey(event.complement)
                                    < EventsQueueKey(below_event.complement))
                                else (
                                    below_event.complement, event.complement)))
            if starts_equal:
                # both line segments are equal or share the left endpoint
                event.is_overlap = below_event.is_overlap = True
                if not ends_equal:
                    self.divide_segment(end_max.complement,
                                        end_min.start)
                return True
            elif ends_equal:
                # the line segments share the right endpoint
                self.divide_segment(start_min, start_max.start)
            else:
                self.divide_segment(
                        start_min
                        # one line segment includes the other one
                        if start_min is end_max.complement
                        # no line segment includes the other one
                        else start_max,
                        end_min.start)
                self.divide_segment(start_min, start_max.start)
        elif (relationship is not SegmentsRelationship.NONE
              and below_event.start != event.start
              and below_event.end != event.end):
            # segments do not intersect at endpoints
            point = segments_intersection(below_segment, segment)
            if point != below_event.start and point != below_event.end:
                self.divide_segment(below_event, point)
            if point != event.start and point != event.end:
                self.divide_segment(event, point)
        return False

    def divide_segment(self, event: Event, point: Point) -> None:
        left_event = Event(True, point, event.complement, event.from_left,
                           event.interior_to_left, event.edge)
        right_event = Event(False, point, event, event.from_left,
                            event.interior_to_left, event.edge)
        event.complement.complement, event.complement = left_event, right_event
        self._queue.push(left_event)
        self._queue.push(right_event)

    def register_edge(self, edge: QuadEdge,
                      *,
                      from_left: bool,
                      is_counterclockwise_contour: bool) -> None:
        start, end = edge.start, edge.end
        interior_on_left = is_counterclockwise_contour
        if start > end:
            interior_on_left = not interior_on_left
            start, end = end, start
        start_event = Event(True, start, None, from_left, interior_on_left,
                            edge)
        end_event = Event(False, end, start_event, from_left, interior_on_left,
                          edge)
        start_event.complement = end_event
        self._queue.push(start_event)
        self._queue.push(end_event)

    def register_segment(self, segment: Segment,
                         *,
                         from_left: bool,
                         is_counterclockwise_contour: bool) -> None:
        start, end = segment
        interior_to_left = is_counterclockwise_contour
        if start > end:
            interior_to_left = not interior_to_left
            start, end = end, start
        start_event = Event(True, start, None, from_left, interior_to_left)
        end_event = Event(False, end, start_event, from_left, interior_to_left)
        start_event.complement = end_event
        self._queue.push(start_event)
        self._queue.push(end_event)

    def sweep(self) -> Iterable[Event]:
        sweep_line = SweepLine()
        while self._queue:
            event = self._queue.pop()
            start_x, _ = event.start
            if event.is_left_endpoint:
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
                event = event.complement
                if event in sweep_line:
                    above_event, below_event = (sweep_line.above(event),
                                                sweep_line.below(event))
                    sweep_line.remove(event)
                    if above_event is not None and below_event is not None:
                        self.detect_intersection(below_event, above_event)
                yield event
