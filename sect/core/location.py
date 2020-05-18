from enum import (IntEnum,
                  unique)


@unique
class Location(IntEnum):
    """
    Represents kinds of locations in which point can be relative to contour.
    """
    #: point lies in the exterior of the contour
    EXTERIOR = 0
    #: point lies on the boundary of the contour
    BOUNDARY = 1
    #: point lies in the interior of the contour
    INTERIOR = 2
