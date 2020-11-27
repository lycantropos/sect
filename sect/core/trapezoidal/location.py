from enum import (IntEnum,
                  unique)


@unique
class Location(IntEnum):
    """
    Represents kinds of locations in which point can be relative to geometry.
    """
    #: point lies in the exterior of the geometry
    EXTERIOR = 0
    #: point lies on the boundary of the geometry
    BOUNDARY = 1
    #: point lies in the interior of the geometry
    INTERIOR = 2
