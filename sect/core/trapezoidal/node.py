from abc import (ABC,
                 abstractmethod)
from typing import List

from sect.hints import Point
from .edge import Edge
from .location import Location
from .trapezoid import Trapezoid


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
