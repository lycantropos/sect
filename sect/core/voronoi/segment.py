from reprit.base import generate_repr

from sect.hints import Point


class Segment:
    __slots__ = 'start', 'end'

    def __init__(self, start: Point, end: Point) -> None:
        self.start = start
        self.end = end

    __repr__ = generate_repr(__init__)

    def __eq__(self, other: 'Segment') -> bool:
        return (self.start == other.start and self.end == other.end
                if isinstance(other, Segment)
                else NotImplemented)

    def __iter__(self):
        yield self.start
        yield self.end
