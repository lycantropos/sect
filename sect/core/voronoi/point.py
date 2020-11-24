from sect.hints import Point


def are_vertical_endpoints(start: Point, end: Point) -> bool:
    start_x, _ = start
    end_x, _ = end
    return start_x == end_x
