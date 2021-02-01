from typing import (FrozenSet,
                    Iterable,
                    List,
                    Optional,
                    Set,
                    Type)

from ground.base import Context
from ground.hints import Point
from reprit.base import generate_repr

from sect.core.utils import Orientation
from .hints import QuadEdge


def to_quad_edge_cls(context: Context) -> Type[QuadEdge]:
    class Result(QuadEdge):
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
                     left_from_start: Optional[QuadEdge] = None,
                     rotated: Optional[QuadEdge] = None) -> None:
            self._start, self._left_from_start, self._rotated = (
                start, left_from_start, rotated)

        orientation = staticmethod(context.angle_orientation)

        @property
        def left_from_start(self) -> QuadEdge:
            return self._left_from_start

        @property
        def start(self) -> Point:
            return self._start

        @property
        def rotated(self) -> QuadEdge:
            return self._rotated

        @classmethod
        def from_endpoints(cls, start: Point, end: Point) -> QuadEdge:
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

        __repr__ = generate_repr(from_endpoints)

        def connect(self, other: QuadEdge) -> QuadEdge:
            result = self.from_endpoints(self.end, other.start)
            result.splice(self.left_from_end)
            result.opposite.splice(other)
            return result

        def delete(self) -> None:
            self.splice(self.right_from_start)
            self.opposite.splice(self.opposite.right_from_start)

        def orientation_of(self, point: Point) -> Orientation:
            return self.orientation(self.start, self.end, point)

        def splice(self, other: QuadEdge) -> None:
            alpha = self.left_from_start.rotated
            beta = other.left_from_start.rotated
            self._left_from_start, other._left_from_start = (
                other.left_from_start, self.left_from_start)
            alpha._left_from_start, beta._left_from_start = (
                beta.left_from_start, alpha.left_from_start)

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

    Result.__name__ = Result.__qualname__ = QuadEdge.__name__
    return Result


def edge_to_endpoints(edge: QuadEdge) -> FrozenSet[Point]:
    return frozenset((edge.start, edge.end))


def edge_to_neighbours(edge: QuadEdge) -> List[QuadEdge]:
    return (list(_edge_to_incidents(edge))
            + list(_edge_to_incidents(edge.opposite)))


def edge_to_non_adjacent_vertices(edge: QuadEdge) -> Set[Point]:
    return {neighbour.end for neighbour in _edge_to_incidents(edge)}


def _edge_to_incidents(edge: QuadEdge) -> Iterable[QuadEdge]:
    if (edge.orientation_of(edge.right_from_start.end)
            is Orientation.CLOCKWISE):
        yield edge.right_from_start
    if (edge.orientation_of(edge.left_from_start.end)
            is Orientation.COUNTERCLOCKWISE):
        yield edge.left_from_start


def edges_with_opposites(edges: Iterable[QuadEdge]) -> Iterable[QuadEdge]:
    for edge in edges:
        yield edge
        yield edge.opposite
