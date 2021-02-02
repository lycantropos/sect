from abc import (ABC,
                 abstractmethod)
from typing import (Callable,
                    Sequence,
                    Tuple,
                    Type)

from ground.base import (Orientation,
                         Relation)
from ground.hints import (Contour,
                          Point,
                          Polygon,
                          Segment)

from sect.core.utils import Domain

QuaternaryPointPredicate = Callable[[Point, Point, Point, Point], bool]
SegmentPointRelater = Callable[[Point, Point, Point], bool]
SegmentsRelater = Callable[[Point, Point, Point, Point], Relation]


class QuadEdge(ABC):
    """
    Based on:
        quad-edge data structure.

    Reference:
        https://en.wikipedia.org/wiki/Quad-edge
        http://www.sccg.sk/~samuelcik/dgs/quad_edge.pdf
    """
    __slots__ = ()

    @classmethod
    @abstractmethod
    def from_endpoints(cls, start: Point, end: Point) -> 'QuadEdge':
        """Creates new edge from endpoints."""

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
    @abstractmethod
    def left_from_start(self) -> 'QuadEdge':
        """
        aka "Onext" in L. Guibas and J. Stolfi notation.
        """

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
    @abstractmethod
    def rotated(self) -> 'QuadEdge':
        """
        aka "Rot" in L. Guibas and J. Stolfi notation.
        """

    @property
    @abstractmethod
    def start(self) -> Point:
        """
        aka "Org" in L. Guibas and J. Stolfi notation.
        """

    @abstractmethod
    def connect(self, other: 'QuadEdge') -> 'QuadEdge':
        """Connects the edge with the other."""

    @abstractmethod
    def delete(self) -> None:
        """Deletes the edge."""

    @abstractmethod
    def orientation_of(self, point: Point) -> Orientation:
        """Returns orientation of the point relative to the edge."""

    @abstractmethod
    def splice(self, other: 'QuadEdge') -> None:
        """Splices the edge with the other."""

    @abstractmethod
    def swap(self) -> None:
        """
        Swaps diagonal in a quadrilateral formed by triangles
        in both clockwise and counterclockwise order around the start.
        """


class Triangulation(ABC):
    __slots__ = ()

    edge_cls = ...  # type: Type[QuadEdge]

    @classmethod
    @abstractmethod
    def constrained_delaunay(cls: Type[Domain],
                             polygon: Polygon,
                             *,
                             extra_constraints: Sequence[Segment] = (),
                             extra_points: Sequence[Point] = ()) -> Domain:
        """
        Constructs constrained Delaunay triangulation of given polygon
        (with potentially extra points and constraints).
        """

    @classmethod
    @abstractmethod
    def delaunay(cls: Type[Domain], points: Sequence[Point]) -> Domain:
        """Constructs Delaunay triangulation of given points."""

    @classmethod
    @abstractmethod
    def from_sides(cls: Type[Domain],
                   left_side: QuadEdge,
                   right_side: QuadEdge) -> Domain:
        """Constructs triangulation given its sides."""

    left_side = ...  # type: QuadEdge
    right_side = ...  # type: QuadEdge

    @abstractmethod
    def delete(self, edge: QuadEdge) -> None:
        """Deletes given edge from the triangulation."""

    @abstractmethod
    def triangles(self) -> Sequence[Contour]:
        """Returns triangles of the triangulation."""


SegmentEndpoints = Tuple[Point, Point]
