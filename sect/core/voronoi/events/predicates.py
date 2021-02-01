from sect.core.utils import (Orientation,
                             orientation)

from .models import Site


def point_point_point_circle_exists(first_point_site: Site,
                                    second_point_site: Site,
                                    third_point_site: Site) -> bool:
    return orientation(first_point_site.start, second_point_site.start,
                       third_point_site.start) is Orientation.CLOCKWISE


def point_point_segment_circle_exists(first_point_site: Site,
                                      second_point_site: Site,
                                      segment_site: Site,
                                      segment_index: int) -> bool:
    if segment_index == 2:
        return (segment_site.start != first_point_site.start
                or segment_site.end != second_point_site.start)
    else:
        first_orientation = orientation(first_point_site.start,
                                        second_point_site.start,
                                        segment_site.start)
        second_orientation = orientation(first_point_site.start,
                                         second_point_site.start,
                                         segment_site.end)
        first_point, second_point = (first_point_site.start,
                                     second_point_site.start)
        if segment_index == 1 and second_point.x <= first_point.x:
            return first_orientation is Orientation.CLOCKWISE
        elif segment_index == 3 and first_point.x <= second_point.x:
            return second_orientation is Orientation.CLOCKWISE
        else:
            return (first_orientation is Orientation.CLOCKWISE
                    or second_orientation is Orientation.CLOCKWISE)


def point_segment_segment_circle_exists(point_site: Site,
                                        first_segment_site: Site,
                                        second_segment_site: Site,
                                        point_index: int) -> bool:
    return (first_segment_site.sorted_index
            != second_segment_site.sorted_index
            and (point_index != 2 or (first_segment_site.is_inverse
                                      or not second_segment_site.is_inverse)
                 and (first_segment_site.is_inverse
                      is not second_segment_site.is_inverse
                      or orientation(first_segment_site.start,
                                     point_site.start, second_segment_site.end)
                      is Orientation.CLOCKWISE)))


def segment_segment_segment_circle_exists(first_segment_site: Site,
                                          second_segment_site: Site,
                                          third_segment_site: Site) -> bool:
    return (first_segment_site.sorted_index
            != second_segment_site.sorted_index
            != third_segment_site.sorted_index)
