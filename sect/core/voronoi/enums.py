from enum import (IntEnum,
                  unique)


class Base(IntEnum):
    def __repr__(self) -> str:
        return type(self).__qualname__ + '.' + self._name_


@unique
class ComparisonResult(Base):
    LESS = -1
    EQUAL = 0
    MORE = 1


@unique
class GeometryCategory(Base):
    POINT = 0x0,
    SEGMENT = 0x1


@unique
class SourceCategory(Base):
    # point subtypes
    SINGLE_POINT = 0x0
    SEGMENT_START_POINT = 0x1
    SEGMENT_END_POINT = 0x2

    # segment subtypes
    INITIAL_SEGMENT = 0x8
    REVERSE_SEGMENT = 0x9

    def belongs(self, geometry_category: GeometryCategory) -> bool:
        return (self.value >> 0x3) == geometry_category
