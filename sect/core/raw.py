from ground.hints import Multipoint, Multipolygon, Multisegment, Polygon, \
    Segment


def from_segment(segment: Segment):
    return segment.start, segment.end


def from_multisegment(multisegment: Multisegment):
    return [from_segment(segment) for segment in multisegment.segments]


def from_polygon(polygon: Polygon):
    return polygon.border, polygon.holes


def from_multipolygon(multipolygon: Multipolygon):
    return [from_polygon(polygon) for polygon in multipolygon.polygons]


def from_multipoint(multipoint: Multipoint):
    return multipoint.points
