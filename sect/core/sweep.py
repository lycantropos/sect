from typing import (Iterable,
                    Optional)

from robust.linear import (SegmentsRelationship,
                           segments_intersection,
                           segments_relationship)

from .event import (EdgeKind,
                    Event)
from .events_queue import (EventsQueue,
                           EventsQueueKey)
from .sweep_line import SweepLine


def sweep(events_queue: EventsQueue) -> Iterable[Event]:
    sweep_line = SweepLine()
    while events_queue:
        event = events_queue.pop()
        start_x, _ = event.start
        if event.is_left_endpoint:
            sweep_line.add(event)
            above_event, below_event = (sweep_line.above(event),
                                        sweep_line.below(event))
            compute_transition(below_event, event)
            if (above_event is not None
                    and detect_intersection(event, above_event, events_queue)):
                compute_transition(below_event, event)
                compute_transition(event, above_event)
            if (below_event is not None
                    and detect_intersection(below_event, event, events_queue)):
                below_below_event = sweep_line.below(below_event)
                compute_transition(below_below_event, below_event)
                compute_transition(below_event, event)
            yield event
        else:
            event = event.complement
            if event in sweep_line:
                above_event, below_event = (sweep_line.above(event),
                                            sweep_line.below(event))
                sweep_line.remove(event)
                if above_event is not None and below_event is not None:
                    detect_intersection(below_event, above_event, events_queue)


def compute_transition(below_event: Optional[Event], event: Event) -> None:
    if below_event is None:
        event.in_out, event.other_in_out = False, True
    elif event.from_left is below_event.from_left:
        event.in_out, event.other_in_out = (not below_event.in_out,
                                            below_event.other_in_out)
    else:
        event.in_out, event.other_in_out = (not below_event.other_in_out,
                                            below_event.in_out)


def detect_intersection(below_event: Event,
                        event: Event,
                        events_queue: EventsQueue) -> bool:
    """
    Populates events queue with intersection events.
    Checks if events' segments overlap and have the same start.
    """
    below_segment, segment = below_event.segment, event.segment
    relationship = segments_relationship(below_segment, segment)
    if relationship is SegmentsRelationship.OVERLAP:
        # segments overlap
        if below_event.from_left is event.from_left:
            raise ValueError('Edges of the same polygon '
                             'should not overlap.')
        starts_equal = below_event.start == event.start
        if starts_equal:
            start_min = start_max = None
        elif EventsQueueKey(event) < EventsQueueKey(below_event):
            start_min, start_max = event, below_event
        else:
            start_min, start_max = below_event, event

        ends_equal = event.end == below_event.end
        if ends_equal:
            end_min = end_max = None
        elif (EventsQueueKey(event.complement)
              < EventsQueueKey(below_event.complement)):
            end_min, end_max = event.complement, below_event.complement
        else:
            end_min, end_max = below_event.complement, event.complement

        if starts_equal:
            # both line segments are equal or share the left endpoint
            below_event.edge_kind = EdgeKind.NON_CONTRIBUTING
            event.edge_kind = (EdgeKind.SAME_TRANSITION
                               if event.in_out is below_event.in_out
                               else EdgeKind.DIFFERENT_TRANSITION)
            if not ends_equal:
                events_queue.divide_segment(end_max.complement, end_min.start)
            return True
        elif ends_equal:
            # the line segments share the right endpoint
            events_queue.divide_segment(start_min, start_max.start)
        else:
            events_queue.divide_segment(
                    start_min
                    # one line segment includes the other one
                    if start_min is end_max.complement
                    # no line segment includes the other one
                    else start_max,
                    end_min.start)
            events_queue.divide_segment(start_min, start_max.start)
    elif (relationship is not SegmentsRelationship.NONE
          and below_event.start != event.start
          and below_event.end != event.end):
        # segments do not intersect at endpoints
        point = segments_intersection(below_segment, segment)
        if point != below_event.start and point != below_event.end:
            events_queue.divide_segment(below_event, point)
        if point != event.start and point != event.end:
            events_queue.divide_segment(event, point)
    return False
