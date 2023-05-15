from typing import (Iterable,
                    List,
                    Optional)

from ground.base import (Context,
                         Orientation)
from ground.hints import Point
from reprit.base import generate_repr


class QuadEdge:
    """
    Based on:
        quad-edge data structure.

    Reference:
        https://en.wikipedia.org/wiki/Quad-edge
        http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf
    """

    @classmethod
    def from_endpoints(cls, start: Point, end: Point,
                       *,
                       context: Context) -> 'QuadEdge':
        """Creates new edge from endpoints."""
        result, opposite = (cls(start,
                                context=context),
                            cls(end,
                                context=context))
        rotated, triple_rotated = (cls(context=context),
                                   cls(context=context))
        result._left_from_start = result
        opposite._left_from_start = opposite
        rotated._left_from_start = triple_rotated
        triple_rotated._left_from_start = rotated
        result._rotated = rotated
        rotated._rotated = opposite
        opposite._rotated = triple_rotated
        triple_rotated._rotated = result
        return result

    @property
    def context(self) -> Context:
        return self._context

    @property
    def end(self) -> Point:
        """
        aka "Dest" in L. Guibas and J. Stolfi notation.
        """
        return self.opposite.start

    @property
    def left_from_end(self) -> 'QuadEdge':
        """
        aka "Lnext" in L. Guibas and J. Stolfi notation.
        """
        return self.rotated.opposite.left_from_start.rotated

    @property
    def left_from_start(self) -> 'QuadEdge':
        """
        aka "Onext" in L. Guibas and J. Stolfi notation.
        """
        return self._left_from_start

    @property
    def opposite(self) -> 'QuadEdge':
        """
        aka "Sym" in L. Guibas and J. Stolfi notation.
        """
        return self.rotated.rotated

    @property
    def right_from_end(self) -> 'QuadEdge':
        """
        aka "Rprev" in L. Guibas and J. Stolfi notation.
        """
        return self.opposite.left_from_start

    @property
    def right_from_start(self) -> 'QuadEdge':
        """
        aka "Oprev" in L. Guibas and J. Stolfi notation.
        """
        return self.rotated.left_from_start.rotated

    @property
    def rotated(self) -> 'QuadEdge':
        """
        aka "Rot" in L. Guibas and J. Stolfi notation.
        """
        return self._rotated

    @property
    def start(self) -> Point:
        """
        aka "Org" in L. Guibas and J. Stolfi notation.
        """
        return self._start

    __slots__ = '_context', '_left_from_start', '_rotated', '_start'

    def __init__(self,
                 start: Optional[Point] = None,
                 left_from_start: Optional['QuadEdge'] = None,
                 rotated: Optional['QuadEdge'] = None,
                 *,
                 context: Context) -> None:
        (self._context, self._left_from_start, self._rotated,
         self._start) = context, left_from_start, rotated, start

    __repr__ = generate_repr(from_endpoints)

    def connect(self, other: 'QuadEdge') -> 'QuadEdge':
        """Connects the edge with the other."""
        result = self.from_endpoints(self.end, other.start,
                                     context=self.context)
        result.splice(self.left_from_end)
        result.opposite.splice(other)
        return result

    def delete(self) -> None:
        """Deletes the edge."""
        self.splice(self.right_from_start)
        self.opposite.splice(self.opposite.right_from_start)

    def orientation_of(self, point: Point) -> Orientation:
        """Returns orientation of the point relative to the edge."""
        return self.context.angle_orientation(self.start, self.end, point)

    def splice(self, other: 'QuadEdge') -> None:
        """Splices the edge with the other."""
        alpha = self.left_from_start.rotated
        beta = other.left_from_start.rotated
        self._left_from_start, other._left_from_start = (
            other.left_from_start, self.left_from_start
        )
        alpha._left_from_start, beta._left_from_start = (
            beta.left_from_start, alpha.left_from_start
        )

    def swap(self) -> None:
        """
        Swaps diagonal in a quadrilateral formed by triangles
        in both clockwise and counterclockwise order around the start.
        """
        side = self.right_from_start
        opposite = self.opposite
        opposite_side = opposite.right_from_start
        self.splice(side)
        opposite.splice(opposite_side)
        self.splice(side.left_from_end)
        opposite.splice(opposite_side.left_from_end)
        self._start = side.end
        opposite._start = opposite_side.end


def edge_to_neighbours(edge: QuadEdge) -> List[QuadEdge]:
    return (list(_edge_to_incidents(edge))
            + list(_edge_to_incidents(edge.opposite)))


def edges_with_opposites(edges: Iterable[QuadEdge]) -> Iterable[QuadEdge]:
    for edge in edges:
        yield edge
        yield edge.opposite


def _edge_to_incidents(edge: QuadEdge) -> Iterable[QuadEdge]:
    if (edge.orientation_of(edge.right_from_start.end)
            is Orientation.CLOCKWISE):
        yield edge.right_from_start
    if (edge.orientation_of(edge.left_from_start.end)
            is Orientation.COUNTERCLOCKWISE):
        yield edge.left_from_start
