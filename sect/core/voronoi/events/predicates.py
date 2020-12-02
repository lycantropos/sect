from robust.angular import (Orientation,
                            orientation)

from .models import SiteEvent


def point_point_point_circle_exists(first_point_event: SiteEvent,
                                    second_point_event: SiteEvent,
                                    third_point_event: SiteEvent) -> bool:
    return orientation(second_point_event.start, first_point_event.start,
                       third_point_event.start) is Orientation.CLOCKWISE


def point_point_segment_circle_exists(first_point_event: SiteEvent,
                                      second_point_event: SiteEvent,
                                      segment_event: SiteEvent,
                                      segment_index: int) -> bool:
    if segment_index == 2:
        return (segment_event.start != first_point_event.start
                or segment_event.end != second_point_event.start)
    else:
        first_orientation = orientation(second_point_event.start,
                                        first_point_event.start,
                                        segment_event.start)
        second_orientation = orientation(second_point_event.start,
                                         first_point_event.start,
                                         segment_event.end)
        first_site_start_x, _ = first_point_event.start
        second_site_start_x, _ = second_point_event.start
        if segment_index == 1 and second_site_start_x <= first_site_start_x:
            return first_orientation is Orientation.CLOCKWISE
        elif segment_index == 3 and first_site_start_x <= second_site_start_x:
            return second_orientation is Orientation.CLOCKWISE
        else:
            return (first_orientation is Orientation.CLOCKWISE
                    or second_orientation is Orientation.CLOCKWISE)


def point_segment_segment_circle_exists(point_event: SiteEvent,
                                        first_segment_event: SiteEvent,
                                        second_segment_event: SiteEvent,
                                        point_index: int) -> bool:
    return (first_segment_event.sorted_index
            != second_segment_event.sorted_index
            and (point_index != 2 or (first_segment_event.is_inverse
                                      or not second_segment_event.is_inverse)
                 and (first_segment_event.is_inverse
                      is not second_segment_event.is_inverse
                      or orientation(point_event.start,
                                     first_segment_event.start,
                                     second_segment_event.end)
                      is Orientation.CLOCKWISE)))


def segment_segment_segment_circle_exists(first_segment_event: SiteEvent,
                                          second_segment_event: SiteEvent,
                                          third_segment_event: SiteEvent
                                          ) -> bool:
    return (first_segment_event.sorted_index
            != second_segment_event.sorted_index
            != third_segment_event.sorted_index)
