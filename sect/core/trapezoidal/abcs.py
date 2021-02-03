from abc import (ABC,
                 abstractmethod)
from typing import List

from ground.base import Orientation
from ground.hints import (Multisegment,
                          Point,
                          Polygon)

from .hints import Shuffler
from .location import Location
from .trapezoid import Trapezoid


class Edge(ABC):
    left = ...  # type: Point
    right = ...  # type: Point
    interior_to_left = ...  # type: bool

    @classmethod
    @abstractmethod
    def from_endpoints(cls,
                       left: Point,
                       right: Point,
                       interior_to_left: bool) -> 'Edge':
        """Constructs edge given its endpoints."""

    @abstractmethod
    def __lt__(self, other: 'Edge') -> bool:
        """Checks if the edge is lower than the other."""

    @abstractmethod
    def orientation_of(self, point: Point) -> Orientation:
        """Returns orientation of the point relative to the edge."""


class Node(ABC):
    __slots__ = '_parents',

    def __init__(self) -> None:
        self._parents = []  # type: List['Node']

    @property
    @abstractmethod
    def height(self) -> int:
        """
        Returns height of the node.
        """

    @abstractmethod
    def locate(self, point: Point) -> Location:
        """
        Finds location of given point relative to the contour.
        """

    @abstractmethod
    def search_edge(self, edge: Edge) -> Trapezoid:
        """
        Recursive search for the trapezoid
        which contains the left endpoint of the given segment.
        """

    def replace_with(self, other: 'Node') -> None:
        """
        Replaces the node with given one in all parents.
        """
        for parent in self._parents:
            parent._replace_child(self, other)
            other._add_parent(parent)
        self._parents.clear()

    def _add_parent(self, parent: 'Node') -> None:
        self._parents.append(parent)

    @abstractmethod
    def _replace_child(self, current: 'Node', replacement: 'Node') -> None:
        """
        Replaces child node with given one.
        """


class Graph(ABC):
    __slots__ = ()
    root = ...  # type: Node

    def __contains__(self, point: Point) -> bool:
        """Checks if point is contained in decomposed geometry."""
        return bool(self.root.locate(point))

    @property
    def height(self) -> int:
        """
        Returns height of the root node.
        """
        return self.root.height

    def locate(self, point: Point) -> Location:
        """Finds location of point relative to decomposed geometry."""
        return self.root.locate(point)

    @classmethod
    @abstractmethod
    def from_multisegment(cls,
                          multisegment: Multisegment,
                          *,
                          shuffler: Shuffler = ...) -> 'Graph':
        """
        Constructs trapezoidal decomposition graph of given multisegment.
        """

    @classmethod
    @abstractmethod
    def from_polygon(cls,
                     polygon: Polygon,
                     *,
                     shuffler: Shuffler = ...) -> 'Graph':
        """Constructs trapezoidal decomposition graph of given polygon."""
