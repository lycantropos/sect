from typing import (Iterable,
                    List,
                    Optional,
                    Set)

from reprit.base import generate_repr
from robust.angular import (Orientation,
                            orientation)

from sect.hints import (Point,
                        Segment)
from .hints import Endpoints


class QuadEdge:
    """
    Based on:
        quad-edge data structure.

    Reference:
        https://en.wikipedia.org/wiki/Quad-edge
        http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf
    """
    __slots__ = '_start', '_left_from_start', '_rotated'

    def __init__(self,
                 start: Optional[Point] = None,
                 left_from_start: Optional['QuadEdge'] = None,
                 rotated: Optional['QuadEdge'] = None) -> None:
        self._start = start
        self._left_from_start = left_from_start
        self._rotated = rotated

    @property
    def start(self) -> Point:
        """
        aka "Org" in L. Guibas and J. Stolfi notation.
        """
        return self._start

    @property
    def end(self) -> Point:
        """
        aka "Dest" in L. Guibas and J. Stolfi notation.
        """
        return self.opposite._start

    @property
    def rotated(self) -> 'QuadEdge':
        """
        aka "Rot" in L. Guibas and J. Stolfi notation.
        """
        return self._rotated

    @property
    def opposite(self) -> 'QuadEdge':
        """
        aka "Sym" in L. Guibas and J. Stolfi notation.
        """
        return self._rotated._rotated

    @property
    def left_from_start(self) -> 'QuadEdge':
        """
        aka "Onext" in L. Guibas and J. Stolfi notation.
        """
        return self._left_from_start

    @property
    def right_from_start(self) -> 'QuadEdge':
        """
        aka "Oprev" in L. Guibas and J. Stolfi notation.
        """
        return self._rotated._left_from_start._rotated

    @property
    def right_from_end(self) -> 'QuadEdge':
        """
        aka "Rprev" in L. Guibas and J. Stolfi notation.
        """
        return self.opposite._left_from_start

    @property
    def left_from_end(self) -> 'QuadEdge':
        """
        aka "Lnext" in L. Guibas and J. Stolfi notation.
        """
        return self._rotated.opposite._left_from_start._rotated

    @classmethod
    def factory(cls, start: Point, end: Point) -> 'QuadEdge':
        result, opposite = cls(start), cls(end)
        rotated, triple_rotated = cls(), cls()
        result._left_from_start = result
        opposite._left_from_start = opposite
        rotated._left_from_start = triple_rotated
        triple_rotated._left_from_start = rotated
        result._rotated = rotated
        rotated._rotated = opposite
        opposite._rotated = triple_rotated
        triple_rotated._rotated = result
        return result

    __repr__ = generate_repr(factory)

    def splice(self, other: 'QuadEdge') -> None:
        alpha = self._left_from_start.rotated
        beta = other._left_from_start.rotated
        self._left_from_start, other._left_from_start = (
            other._left_from_start, self._left_from_start)
        alpha._left_from_start, beta._left_from_start = (
            beta._left_from_start, alpha._left_from_start)

    def swap(self) -> None:
        side = self.right_from_start
        opposite = self.opposite
        opposite_side = opposite.right_from_start
        self.splice(side)
        opposite.splice(opposite_side)
        self.splice(side.left_from_end)
        opposite.splice(opposite_side.left_from_end)
        self._start = side.end
        opposite._start = opposite_side.end

    def connect(self, other: 'QuadEdge') -> 'QuadEdge':
        result = QuadEdge.factory(self.end, other._start)
        result.splice(self.left_from_end)
        result.opposite.splice(other)
        return result

    def delete(self) -> None:
        self.splice(self.right_from_start)
        self.opposite.splice(self.opposite.right_from_start)

    def orientation_with(self, point: Point) -> Orientation:
        return orientation(self.end, self._start, point)

    @property
    def segment(self) -> Segment:
        return self.start, self.end

    @property
    def endpoints(self) -> Endpoints:
        """
        Returns endpoints of the edge.

        >>> edge = QuadEdge.factory((0, 0), (1, 1))
        >>> edge.endpoints
        frozenset({(0, 0), (1, 1)})
        """
        return frozenset((self.start, self.end))


def edge_to_neighbours(edge: QuadEdge) -> List[QuadEdge]:
    return (list(_edge_to_incidents(edge))
            + list(_edge_to_incidents(edge.opposite)))


def edge_to_non_adjacent_vertices(edge: QuadEdge) -> Set[Point]:
    return {neighbour.end
            for neighbour in _edge_to_incidents(edge)}


def _edge_to_incidents(edge: QuadEdge) -> Iterable[QuadEdge]:
    if (edge.orientation_with(edge.right_from_start.end)
            is Orientation.CLOCKWISE):
        yield edge.right_from_start
    if (edge.orientation_with(edge.left_from_start.end)
            is Orientation.COUNTERCLOCKWISE):
        yield edge.left_from_start


def edges_with_opposites(edges: Iterable[QuadEdge]) -> Iterable[QuadEdge]:
    for edge in edges:
        yield edge
        yield edge.opposite
