from robust.angular import (Orientation,
                            orientation)

from .models import Site


def point_point_point_circle_exists(first_point_site: Site,
                                    second_point_site: Site,
                                    third_point_site: Site) -> bool:
    return orientation(second_point_site.start, first_point_site.start,
                       third_point_site.start) is Orientation.CLOCKWISE


def point_point_segment_circle_exists(first_point_site: Site,
                                      second_point_site: Site,
                                      segment_site: Site,
                                      segment_index: int) -> bool:
    if segment_index == 2:
        return (segment_site.start != first_point_site.start
                or segment_site.end != second_point_site.start)
    else:
        first_orientation = orientation(second_point_site.start,
                                        first_point_site.start,
                                        segment_site.start)
        second_orientation = orientation(second_point_site.start,
                                         first_point_site.start,
                                         segment_site.end)
        first_site_start_x, _ = first_point_site.start
        second_site_start_x, _ = second_point_site.start
        if segment_index == 1 and second_site_start_x <= first_site_start_x:
            return first_orientation is Orientation.CLOCKWISE
        elif segment_index == 3 and first_site_start_x <= second_site_start_x:
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
                      or orientation(point_site.start,
                                     first_segment_site.start,
                                     second_segment_site.end)
                      is Orientation.CLOCKWISE)))


def segment_segment_segment_circle_exists(first_segment_site: Site,
                                          second_segment_site: Site,
                                          third_segment_site: Site) -> bool:
    return (first_segment_site.sorted_index
            != second_segment_site.sorted_index
            != third_segment_site.sorted_index)
