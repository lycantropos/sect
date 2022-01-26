from ground.base import (Context,
                         Orientation)

from .models import Site


def point_point_point_circle_exists(first_point_site: Site,
                                    second_point_site: Site,
                                    third_point_site: Site,
                                    context: Context) -> bool:
    return (context.angle_orientation(first_point_site.start,
                                      second_point_site.start,
                                      third_point_site.start)
            is Orientation.CLOCKWISE)


def point_point_segment_circle_exists(first_point_site: Site,
                                      second_point_site: Site,
                                      segment_site: Site,
                                      segment_index: int,
                                      context: Context) -> bool:
    if segment_index == 2:
        return (not context.segment_contains_point(segment_site,
                                                   first_point_site.start)
                or not context.segment_contains_point(segment_site,
                                                      second_point_site.start))
    else:
        first_point, second_point = (first_point_site.start,
                                     second_point_site.start)
        start_orientation = context.angle_orientation(
                first_point, second_point, segment_site.start)
        end_orientation = context.angle_orientation(first_point, second_point,
                                                    segment_site.end)
        if segment_index == 1 and second_point.x <= first_point.x:
            return start_orientation is Orientation.CLOCKWISE
        elif segment_index == 3 and first_point.x <= second_point.x:
            return end_orientation is Orientation.CLOCKWISE
        else:
            return (start_orientation is Orientation.CLOCKWISE
                    or end_orientation is Orientation.CLOCKWISE)


def point_segment_segment_circle_exists(point_site: Site,
                                        first_segment_site: Site,
                                        second_segment_site: Site,
                                        point_index: int,
                                        context: Context) -> bool:
    return (first_segment_site.sorted_index
            != second_segment_site.sorted_index
            and (point_index != 2 or (first_segment_site.is_inverse
                                      or not second_segment_site.is_inverse)
                 and (first_segment_site.is_inverse
                      is not second_segment_site.is_inverse
                      or context.angle_orientation(first_segment_site.start,
                                                   point_site.start,
                                                   second_segment_site.end)
                      is Orientation.CLOCKWISE)))


def segment_segment_segment_circle_exists(first_segment_site: Site,
                                          second_segment_site: Site,
                                          third_segment_site: Site) -> bool:
    return (first_segment_site.sorted_index
            != second_segment_site.sorted_index
            != third_segment_site.sorted_index)
