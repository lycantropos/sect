from reprit.base import generate_repr


class Point:
    __slots__ = 'x', 'y'

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    __repr__ = generate_repr(__init__)

    def __eq__(self, other: 'Point') -> bool:
        return (self.x == other.x and self.y == other.y
                if isinstance(other, Point)
                else NotImplemented)

    def __iter__(self):
        yield self.x
        yield self.y

    def __lt__(self, other: 'Point') -> bool:
        return ((self.x, self.y) < (other.x, other.y)
                if isinstance(other, Point)
                else NotImplemented)


def are_vertical_endpoints(start: Point, end: Point) -> bool:
    return start.x == end.x
