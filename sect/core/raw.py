from ground.hints import Multipoint, Multipolygon, Multisegment, Polygon


def from_multisegment(multisegment: Multisegment):
    return multisegment.segments


def from_polygon(polygon: Polygon):
    return polygon.border, polygon.holes


def from_multipolygon(multipolygon: Multipolygon):
    return [from_polygon(polygon) for polygon in multipolygon.polygons]


def from_multipoint(multipoint: Multipoint):
    return multipoint.points
