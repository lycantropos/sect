from sect.core.voronoi.enums import Orientation
from sect.core.voronoi.utils import orientation
from .models import SiteEvent


def point_point_point_circle_exists(first_site: SiteEvent,
                                    second_site: SiteEvent,
                                    third_site: SiteEvent) -> bool:
    return orientation(second_site.start, first_site.start,
                       third_site.start) is Orientation.RIGHT


def point_point_segment_circle_exists(first_site: SiteEvent,
                                      second_site: SiteEvent,
                                      third_site: SiteEvent,
                                      segment_index: int) -> bool:
    if segment_index == 2:
        return (third_site.start != first_site.start
                or third_site.end != second_site.start)
    else:
        first_orientation = orientation(second_site.start, first_site.start,
                                        third_site.start)
        second_orientation = orientation(second_site.start,
                                         first_site.start, third_site.end)
        first_site_start_x, _ = first_site.start
        second_site_start_x, _ = second_site.start
        if segment_index == 1 and second_site_start_x <= first_site_start_x:
            return first_orientation is Orientation.RIGHT
        elif segment_index == 3 and first_site_start_x <= second_site_start_x:
            return second_orientation is Orientation.RIGHT
        else:
            return (first_orientation is Orientation.RIGHT
                    or second_orientation is Orientation.RIGHT)


def point_segment_segment_circle_exists(first_site: SiteEvent,
                                        second_site: SiteEvent,
                                        third_site: SiteEvent,
                                        point_index: int) -> bool:
    return (second_site.sorted_index != third_site.sorted_index
            and (point_index != 2
                 or (second_site.is_inverse or not third_site.is_inverse)
                 and (second_site.is_inverse is not third_site.is_inverse
                      or orientation(first_site.start, second_site.start,
                                     third_site.end)
                      is Orientation.RIGHT)))


def segment_segment_segment_circle_exists(first_site: SiteEvent,
                                          second_site: SiteEvent,
                                          third_site: SiteEvent) -> bool:
    return (first_site.sorted_index != second_site.sorted_index
            != third_site.sorted_index)
